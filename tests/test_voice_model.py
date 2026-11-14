"""Model discovery must survive extraction, relocation, and arbitrary launch cwd."""
import sys
from hal2030.voice_model import MODEL_NAME, MODEL_FILES, default_model_path


def install_stub(path):
    for name in MODEL_FILES:
        file = path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b'model fixture')


def test_frozen_model_uses_executable_directory(tmp_path, monkeypatch):
    app = tmp_path / 'Extracted app with spaces'
    bundled = app / 'voice-model' / MODEL_NAME
    install_stub(bundled)
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(app / 'HAL2030.exe'))
    monkeypatch.chdir(tmp_path)
    assert default_model_path(tmp_path / 'runtime') == bundled


def test_partial_bundle_falls_back_to_runtime(tmp_path, monkeypatch):
    app = tmp_path / 'app'
    partial = app / 'voice-model' / MODEL_NAME / 'am'
    partial.mkdir(parents=True)
    (partial / 'final.mdl').write_bytes(b'incomplete')
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(app / 'HAL2030.exe'))
    assert default_model_path(tmp_path / 'runtime') == tmp_path / 'runtime' / 'voice-model' / MODEL_NAME


def test_source_uses_runtime_not_python_directory(tmp_path, monkeypatch):
    install_stub(tmp_path / 'voice-model' / MODEL_NAME)
    monkeypatch.setattr(sys, 'frozen', False, raising=False)
    monkeypatch.setattr(sys, 'executable', str(tmp_path / 'python.exe'))
    assert default_model_path(tmp_path / 'runtime') == tmp_path / 'runtime' / 'voice-model' / MODEL_NAME
