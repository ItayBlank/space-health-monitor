"""Unit tests for CPU Kokoro/Faster-Whisper voice engine helpers and fallback paths."""

from __future__ import annotations

from pathlib import Path

from hal2030 import voice_engine


def test_clean_speech_text_and_chunking() -> None:
    raw = "Attention · SpO2 87% — Move to Destiny Core → 0.34 mSv/d ✓"
    cleaned = voice_engine._clean_speech_text(raw)
    assert "·" not in cleaned
    assert "→" not in cleaned
    assert "✓" not in cleaned
    assert "oxygen saturation" in cleaned
    assert "millisieverts per day" in cleaned

    long_text = " ".join(["Cabin air quality is nominal inside Destiny Lab."] * 12)
    chunks = voice_engine._split_speech_chunks(long_text, max_chars=180)
    assert len(chunks) >= 3
    assert all(len(c) <= 180 for c in chunks)


def test_voice_model_dirs_contains_project_runtime() -> None:
    dirs = voice_engine.voice_model_dirs()
    assert len(dirs) >= 1
    assert any(d.name == "voice-model" for d in dirs)


def test_synthesize_wav_cache_and_fallback(monkeypatch, tmp_path: Path) -> None:
    calls = {"n": 0}

    class _FakeKokoro:
        def create(self, text: str, voice: str, speed: float, lang: str):
            calls["n"] += 1
            import numpy as np

            return np.zeros(2400, dtype=np.float32), 24000

    voice_engine._TTS_CACHE.clear()
    monkeypatch.setattr(voice_engine, "_get_kokoro", lambda auto_download=False: _FakeKokoro())

    w1 = voice_engine.synthesize_wav("Check cabin CO2 · Stay hydrated.", voice="unknown_voice", speed=0.95)
    w2 = voice_engine.synthesize_wav("Check cabin CO2 · Stay hydrated.", voice="af_heart", speed=0.95)
    assert w1 is not None and w1[:4] == b"RIFF"
    assert w2 == w1
    assert calls["n"] == 1  # second identical normalized prompt served from WAV cache

    monkeypatch.setattr(voice_engine, "_get_kokoro", lambda auto_download=False: None)
    assert voice_engine.synthesize_wav("Unique uncached fallback prompt", auto_download=False) is None
