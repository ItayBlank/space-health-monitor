"""Lightweight CPU-friendly natural voice engine (Kokoro-82M INT8 TTS + Faster-Whisper STT).

Runs on standard laptop CPUs without GPU requirements (~116 MB Kokoro INT8 + voices,
~40 MB Whisper tiny.en INT8). Falls back gracefully to client browser speech when
optional local model files are not yet downloaded.
"""

from __future__ import annotations

import importlib.util
import io
import os
import re
import sys
import tempfile
import threading
import urllib.request
import wave
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from hal2030.config import CREW
from hal2030.paths import resource_root, runtime_root

DEFAULT_VOICE = "af_heart"
DEFAULT_SPEED = 0.94
SUPPORTED_VOICES = ("af_heart", "af_bella", "af_sarah", "am_adam", "am_michael")

KOKORO_MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/latest/download/kokoro-v1.0.int8.onnx"
KOKORO_VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/latest/download/voices-v1.0.bin"

_KOKORO_LOCK = threading.Lock()
_KOKORO_DL_LOCK = threading.Lock()
_WHISPER_LOCK = threading.Lock()
_TTS_CACHE_LOCK = threading.Lock()
_KOKORO_INSTANCE: Any = None
_KOKORO_KEY: Optional[Tuple[str, str]] = None
_WHISPER_INSTANCE: Any = None
_WHISPER_KEY: Optional[str] = None
_TTS_CACHE: "OrderedDict[Tuple[str, str, float], bytes]" = OrderedDict()
_TTS_CACHE_MAX = 64


def voice_model_dirs() -> List[Path]:
    """Return candidate directories for downloaded offline voice models."""
    candidates = [
        runtime_root() / "voice-model",
        resource_root() / "runtime" / "voice-model",
        Path(__file__).resolve().parents[1] / "runtime" / "voice-model",
        Path.cwd() / "runtime" / "voice-model",
    ]
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "voice-model")
    unique: List[Path] = []
    for path in candidates:
        resolved = path.resolve() if path.exists() else path
        if resolved not in unique:
            unique.append(resolved)
    return unique


def find_kokoro_files() -> Optional[Tuple[Path, Path]]:
    """Locate (kokoro-onnx-file, voices-bin-file) if present locally."""
    model_names = ("kokoro-v1.0.int8.onnx", "kokoro-v1.0.fp16.onnx", "kokoro-v1.0.onnx")
    voice_names = ("voices-v1.0.bin", "voices.bin")
    for base in voice_model_dirs():
        for folder in (base / "kokoro", base):
            if not folder.is_dir():
                continue
            model_file = next((folder / n for n in model_names if (folder / n).is_file() and (folder / n).stat().st_size > 1024), None)
            voice_file = next((folder / n for n in voice_names if (folder / n).is_file() and (folder / n).stat().st_size > 1024), None)
            if model_file and voice_file:
                return model_file, voice_file
    return None


def _atomic_download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def ensure_kokoro_files(download_if_missing: bool = False) -> Optional[Tuple[Path, Path]]:
    """Return Kokoro ONNX + voices files, optionally auto-downloading into runtime_root."""
    found = find_kokoro_files()
    if found is not None or not download_if_missing:
        return found
    if importlib.util.find_spec("kokoro_onnx") is None:
        return None
    with _KOKORO_DL_LOCK:
        found = find_kokoro_files()
        if found is not None:
            return found
        kdir = runtime_root() / "voice-model" / "kokoro"
        model_path = kdir / "kokoro-v1.0.int8.onnx"
        voices_path = kdir / "voices-v1.0.bin"
        try:
            if not model_path.is_file() or model_path.stat().st_size <= 1024:
                _atomic_download(KOKORO_MODEL_URL, model_path)
            if not voices_path.is_file() or voices_path.stat().st_size <= 1024:
                _atomic_download(KOKORO_VOICES_URL, voices_path)
            return find_kokoro_files()
        except Exception:
            return None


def find_whisper_cache() -> Optional[Path]:
    """Return directory for Faster-Whisper tiny.en model cache if downloaded."""
    for base in voice_model_dirs():
        target = base / "whisper-tiny-en"
        if target.is_dir() and any(target.rglob("model.bin")):
            return target
    return None


def get_voice_status() -> Dict[str, Any]:
    """Inspect installed CPU TTS/STT packages and local model availability."""
    kokoro_pkg = importlib.util.find_spec("kokoro_onnx") is not None
    whisper_pkg = importlib.util.find_spec("faster_whisper") is not None

    kokoro_files = find_kokoro_files()
    whisper_dir = find_whisper_cache()
    voices = list(SUPPORTED_VOICES)
    return {
        "tts_engine": "kokoro-82m-int8" if (kokoro_pkg and kokoro_files) else "browser-fallback",
        "tts_ready": bool(kokoro_pkg and kokoro_files),
        "tts_package_installed": kokoro_pkg,
        "tts_can_autodownload": kokoro_pkg,
        "stt_engine": "faster-whisper-tiny.en" if whisper_pkg else "browser-fallback",
        "stt_ready": bool(whisper_pkg and whisper_dir is not None),
        "stt_package_installed": whisper_pkg,
        "stt_can_autodownload": whisper_pkg,
        "kokoro_model": str(kokoro_files[0]) if kokoro_files else None,
        "whisper_model_dir": str(whisper_dir) if whisper_dir else str(runtime_root() / "voice-model" / "whisper-tiny-en"),
        "recommended_voice": DEFAULT_VOICE,
        "voices": voices,
        "hardware_profile": "CPU-only (~155 MB total ONNX + CTranslate2 int8, 0 GPU required)",
    }


def _get_kokoro(auto_download: bool = False):
    global _KOKORO_INSTANCE, _KOKORO_KEY
    if importlib.util.find_spec("kokoro_onnx") is None:
        return None
    files = ensure_kokoro_files(download_if_missing=auto_download)
    if files is None:
        return None
    key = (str(files[0]), str(files[1]))
    with _KOKORO_LOCK:
        if _KOKORO_INSTANCE is None or _KOKORO_KEY != key:
            from kokoro_onnx import Kokoro
            _KOKORO_INSTANCE = Kokoro(str(files[0]), str(files[1]))
            _KOKORO_KEY = key
    return _KOKORO_INSTANCE


def _get_whisper():
    global _WHISPER_INSTANCE, _WHISPER_KEY
    from faster_whisper import WhisperModel
    cache_dir = find_whisper_cache() or (runtime_root() / "voice-model" / "whisper-tiny-en")
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = str(cache_dir)
    with _WHISPER_LOCK:
        if _WHISPER_INSTANCE is None or _WHISPER_KEY != key:
            _WHISPER_INSTANCE = WhisperModel(
                "tiny.en",
                device="cpu",
                compute_type="int8",
                cpu_threads=4,
                download_root=str(cache_dir),
                local_files_only=find_whisper_cache() is not None,
            )
            _WHISPER_KEY = key
    return _WHISPER_INSTANCE


def _clean_speech_text(text: str) -> str:
    """Normalize dashboard symbols & abbreviations so Kokoro reads naturally."""
    cleaned = str(text or "")
    for sym, repl in (
        ("·", ", "),
        ("•", ", "),
        ("—", ", "),
        ("–", ", "),
        ("→", " to "),
        ("✓", ""),
        ("⏱", ""),
        ("👁", ""),
        ("🔊", ""),
        ("🔇", ""),
        ("♪", ""),
        ("⚠", ""),
    ):
        cleaned = cleaned.replace(sym, repl)
    cleaned = re.sub(r"\bppCO2\b", "C O 2", cleaned)
    cleaned = re.sub(r"\bCO2\b", "C O 2", cleaned)
    cleaned = re.sub(r"\bSpO2\b", "oxygen saturation", cleaned)
    cleaned = re.sub(r"\bmSv/d\b", "millisieverts per day", cleaned)
    cleaned = re.sub(r"\bmSv\b", "millisieverts", cleaned)
    cleaned = re.sub(r"°C\b", " degrees Celsius", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,")
    return cleaned


def _split_speech_chunks(text: str, max_chars: int = 240) -> List[str]:
    """Split long speech into <=max_chars clauses so Kokoro never hits token limits."""
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    cur = ""
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        if len(cur) + len(sent) + 1 <= max_chars:
            cur = f"{cur} {sent}".strip()
        else:
            if cur:
                chunks.append(cur)
            if len(sent) <= max_chars:
                cur = sent
            else:
                words = sent.split()
                cur = ""
                for w in words:
                    if len(cur) + len(w) + 1 <= max_chars:
                        cur = f"{cur} {w}".strip()
                    else:
                        if cur:
                            chunks.append(cur)
                        cur = w
    if cur:
        chunks.append(cur)
    return chunks or [text[:max_chars]]


def synthesize_wav(
    text: str,
    voice: str = DEFAULT_VOICE,
    speed: float = DEFAULT_SPEED,
    auto_download: Optional[bool] = None,
) -> Optional[bytes]:
    """Synthesize natural human speech to PCM WAV bytes using Kokoro-ONNX on CPU."""
    cleaned = _clean_speech_text(text)
    if not cleaned:
        return None
    chosen_voice = voice if voice in SUPPORTED_VOICES else DEFAULT_VOICE
    clamped_speed = round(max(0.7, min(1.3, float(speed))), 2)
    cache_key = (cleaned, chosen_voice, clamped_speed)

    with _TTS_CACHE_LOCK:
        cached = _TTS_CACHE.get(cache_key)
        if cached is not None:
            _TTS_CACHE.move_to_end(cache_key)
            return cached

    if auto_download is None:
        auto_download = "PYTEST_CURRENT_TEST" not in os.environ
    kokoro = _get_kokoro(auto_download=auto_download)
    if kokoro is None:
        return None

    chunks = _split_speech_chunks(cleaned, max_chars=240)
    pcm_parts: List[np.ndarray] = []
    out_sr = 24000
    for idx, chunk in enumerate(chunks):
        samples, sample_rate = kokoro.create(chunk, voice=chosen_voice, speed=clamped_speed, lang="en-us")
        out_sr = int(sample_rate)
        arr = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
        if idx > 0 and len(pcm_parts) > 0:
            pcm_parts.append(np.zeros(int(out_sr * 0.08), dtype=np.float32))
        pcm_parts.append(arr)

    merged = np.concatenate(pcm_parts) if len(pcm_parts) > 1 else pcm_parts[0]
    pcm16 = (merged * 32767.0).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(out_sr)
        wf.writeframes(pcm16.tobytes())
    wav_bytes = buf.getvalue()

    with _TTS_CACHE_LOCK:
        _TTS_CACHE[cache_key] = wav_bytes
        _TTS_CACHE.move_to_end(cache_key)
        while len(_TTS_CACHE) > _TTS_CACHE_MAX:
            _TTS_CACHE.popitem(last=False)
    return wav_bytes


def warmup_voice_engine() -> None:
    """Load Kokoro ONNX session and pre-cache common dashboard prompts in background."""
    try:
        if _get_kokoro(auto_download=True) is None:
            return
        for phrase in (
            "Right eye practice. Which side do the E legs point toward?",
            "Begin scored trials for right eye.",
            "Begin scored trials for left eye.",
            "Right eye complete. Switch to left eye practice.",
            "Attention: Crew-wide cabin air alert. Check oxygen and scrubber.",
        ):
            synthesize_wav(phrase, auto_download=False)
    except Exception:
        pass


_DIRECTION_PATTERNS = [
    ("up", r"\b(up|upward|upwards|top|north|pointing up|facing up)\b"),
    ("down", r"\b(down|downward|downwards|bottom|south|pointing down|facing down)\b"),
    ("left", r"\b(left|leftward|west|pointing left|facing left)\b"),
    ("right", r"\b(right|rightward|east|pointing right|facing right)\b"),
    ("unable", r"\b(unable|cant see|can't see|cannot see|blurry|too small|unsure|skip|no idea)\b"),
    ("continue", r"\b(continue|confirm|next|yes|correct|looks good|go ahead|submit)\b"),
    ("repeat", r"\b(repeat|say again|again|pardon)\b"),
    ("back", r"\b(back|undo|clear|wrong|mistake)\b"),
    ("pause", r"\b(pause|hold on|wait|stop)\b"),
    ("resume", r"\b(resume|start again|unpause)\b"),
]


def parse_voice_intent(transcript: str) -> Dict[str, Any]:
    """Extract structured vision command and/or dashboard navigation intent from natural speech."""
    raw = (transcript or "").strip()
    norm = re.sub(r"[^a-z0-9\s']", " ", raw.lower())
    norm = re.sub(r"\s+", " ", norm).strip()

    vision_cmd: Optional[str] = None
    for cmd, pattern in _DIRECTION_PATTERNS:
        if re.search(pattern, norm):
            vision_cmd = cmd
            break

    crew_id: Optional[str] = None
    for person in CREW:
        first = person["name"].lower().split()[0]
        if re.search(rf"\b({re.escape(person['id'])}|{re.escape(first)})\b", norm):
            crew_id = person["id"]
            break

    nav_level: Optional[str] = None
    action: Optional[str] = None
    if re.search(r"\b(simulation|simulate|24 hour|demo)\b", norm):
        action = "toggle_sim"
    elif re.search(r"\b(heart|cardio|pulse|ecg|vitals)\b", norm):
        nav_level = "cardio"
    elif re.search(r"\b(radiation|radlab|shield|storm|shelter)\b", norm):
        nav_level = "engineer"
    elif re.search(r"\b(vision|eye|sans|sensor|sensors|pvt)\b", norm):
        nav_level = "sensors"
    elif re.search(r"\b(downlink|packet|mission control|earth link)\b", norm):
        nav_level = "downlink"
    elif re.search(r"\b(overview|glance|home|everyone|all crew)\b", norm):
        nav_level = "glance"
    elif re.search(r"\b(to do|todo|action|actions|checklist|tasks|what should)\b", norm):
        nav_level = "body"
    elif re.search(r"\b(body map|scanner|3d|anatomy)\b", norm):
        action = "open_body_map"

    return {
        "transcript": raw,
        "vision_command": vision_cmd,
        "crew_id": crew_id,
        "nav_level": nav_level,
        "action": action,
    }


def transcribe_audio_bytes(data: bytes, suffix: str = ".webm") -> Dict[str, Any]:
    """Transcribe short audio clip bytes using Faster-Whisper tiny.en on CPU and parse intent."""
    if not data:
        raise ValueError("Audio payload is empty.")
    model = _get_whisper()
    clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=clean_suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        segments, info = model.transcribe(
            str(tmp_path),
            language="en",
            beam_size=1,
            vad_filter=True,
            initial_prompt="Astronaut medical check: up down left right unable continue repeat back pause resume Anton Idan Itay Emily Sofia Camila heart oxygen radiation sleep",
        )
        transcript = " ".join(seg.text.strip() for seg in segments if seg.text.strip()).strip()
        intent = parse_voice_intent(transcript)
        intent["language"] = getattr(info, "language", "en")
        intent["engine"] = "faster-whisper-tiny.en-int8"
        return intent
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
