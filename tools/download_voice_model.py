"""Download lightweight CPU voice models once; subsequent voice TTS & STT run 100% offline.

Default (`--engine natural`) installs:
  1. Kokoro-82M INT8 ONNX (~88 MB) + voices-v1.0.bin (~27 MB) for natural human speech synthesis
  2. Faster-Whisper tiny.en INT8 (~40 MB) for conversational speech understanding on CPU

Optional `--engine vosk` installs the checksum-pinned Vosk small English grammar model.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hal2030.downlink import DownlinkService
from hal2030.voice_model import MODEL_NAME as MODEL, MODEL_URL as URL, MODEL_SHA256, model_present

KOKORO_MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/latest/download/kokoro-v1.0.int8.onnx"
KOKORO_VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/latest/download/voices-v1.0.bin"


def _download_atomic(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def download_kokoro(target: Path) -> None:
    """Download quantized Kokoro-82M ONNX + voices bundle."""
    kdir = target / "kokoro"
    kdir.mkdir(parents=True, exist_ok=True)
    model_path = kdir / "kokoro-v1.0.int8.onnx"
    voices_path = kdir / "voices-v1.0.bin"
    if not model_path.is_file() or model_path.stat().st_size <= 1024:
        print(f"Downloading {KOKORO_MODEL_URL} -> {model_path}")
        _download_atomic(KOKORO_MODEL_URL, model_path)
    else:
        print(f"Kokoro model already present: {model_path}")
    if not voices_path.is_file() or voices_path.stat().st_size <= 1024:
        print(f"Downloading {KOKORO_VOICES_URL} -> {voices_path}")
        _download_atomic(KOKORO_VOICES_URL, voices_path)
    else:
        print(f"Kokoro voices already present: {voices_path}")


def download_whisper(target: Path) -> None:
    """Download Faster-Whisper tiny.en INT8 CTranslate2 snapshot for CPU inference."""
    from faster_whisper import WhisperModel
    wdir = target / "whisper-tiny-en"
    wdir.mkdir(parents=True, exist_ok=True)
    print(f"Caching Faster-Whisper tiny.en (int8 CPU) -> {wdir}")
    WhisperModel("tiny.en", device="cpu", compute_type="int8", download_root=str(wdir))
    print(f"Ready: {wdir}")


def download_vosk(target: Path) -> None:
    """Download the checksum-pinned official English Vosk model."""
    target.mkdir(parents=True, exist_ok=True)
    if model_present(target / MODEL):
        print(f"Model already present: {target / MODEL}")
        return
    archive = target / (MODEL + ".zip")
    print(f"Downloading {URL}")
    urllib.request.urlretrieve(URL, archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != MODEL_SHA256:
        archive.unlink()
        raise ValueError("Model download checksum mismatch")
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            resolved = (target / info.filename).resolve()
            if not resolved.is_relative_to(target.resolve()) or Path(info.filename).parts[0] != MODEL:
                raise ValueError("Unexpected path in model archive")
        bundle.extractall(target)
    archive.unlink()
    print(f"Ready: {target / MODEL}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path)
    parser.add_argument(
        "--engine",
        choices=("natural", "kokoro", "whisper", "vosk", "all"),
        default="natural",
        help="natural (default): Kokoro INT8 + Faster-Whisper tiny.en; vosk: legacy Qt offline grammar model",
    )
    args = parser.parse_args()
    target = args.destination or DownlinkService().output_dir.parent / "voice-model"
    if args.engine in ("natural", "kokoro", "all"):
        download_kokoro(target)
    if args.engine in ("natural", "whisper", "all"):
        download_whisper(target)
    if args.engine in ("vosk", "all"):
        download_vosk(target)


if __name__ == "__main__":
    main()
