# Build from the repository root: python -m PyInstaller packaging/HAL2030.spec
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs

root = Path(SPECPATH).parent
sys.path.insert(0, str(root))
from tools.build_resources import tracked_resources
a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    # Vosk loads its native decoder with CFFI; import analysis cannot find its DLLs.
    binaries=collect_dynamic_libs("vosk"),
    datas=tracked_resources(root),
    hiddenimports=collect_submodules("hal2030", on_error="raise"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="HAL2030",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
