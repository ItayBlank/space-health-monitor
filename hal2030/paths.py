"""Separate bundled resources from writable runtime files."""
import os
from pathlib import Path
import sys
from tempfile import gettempdir


def resource_root() -> Path:
    """Return read-only bundled asset root (PyInstaller _MEIPASS when frozen)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def runtime_root() -> Path:
    """Return the writable runtime location; callers create it or surface I/O errors.

    Vercel uses temporary storage. Source runs keep repository-local runtime
    data. Frozen Windows builds use LocalAppData so one-file extraction cleanup
    cannot erase the outbox.
    """
    if os.environ.get("VERCEL") == "1":
        return Path(gettempdir()) / "astra-core"
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parent.parent / "runtime"
    local = os.environ.get("LOCALAPPDATA")
    base = Path(local) if local else Path.home() / "AppData" / "Local"
    return base / "HAL2030" / "runtime"

