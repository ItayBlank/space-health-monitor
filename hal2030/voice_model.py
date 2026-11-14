"""Offline model locations shared by source runs, distribution, and setup UI."""
from pathlib import Path
import sys

MODEL_NAME = 'vosk-model-small-en-us-0.15'
MODEL_URL = f'https://alphacephei.com/vosk/models/{MODEL_NAME}.zip'
MODEL_SHA256 = '30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498'
MODEL_FILES = ('am/final.mdl', 'conf/model.conf', 'conf/mfcc.conf',
               'graph/HCLr.fst', 'graph/Gr.fst', 'graph/phones/word_boundary.int')


def model_present(path: Path) -> bool:
    """Check required model files; actual Vosk loading validates their contents."""
    return all((path / name).is_file() for name in MODEL_FILES)


def default_model_path(runtime_dir: Path) -> Path:
    """Prefer a complete model beside a frozen executable; otherwise use runtime.

    Never searches the current working directory or downloads at app startup.
    Returns the runtime path even if absent so setup can offer manual selection.
    """
    if getattr(sys, 'frozen', False):
        bundled = Path(sys.executable).resolve().parent / 'voice-model' / MODEL_NAME
        if model_present(bundled):
            return bundled
    return runtime_dir / 'voice-model' / MODEL_NAME
