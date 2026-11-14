"""Regression checks for durable runtime storage in one-file builds."""
from pathlib import Path
import sys

from hal2030 import paths
from hal2030.downlink import DownlinkService
from hal2030.telemetry import CsvReplaySource


def test_source_runtime_stays_repo_local(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert paths.runtime_root() == Path(paths.__file__).resolve().parent.parent / "runtime"


def test_frozen_queue_survives_new_extraction_and_working_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "user-data"))
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "extraction-1"), raising=False)
    first = DownlinkService()
    first.set_connected(False)
    packet = first.enqueue(CsvReplaySource().frame(0), [], 0)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "extraction-2"))
    monkeypatch.chdir(tmp_path)
    restored = DownlinkService()
    assert restored.output_dir == tmp_path / "user-data" / "HAL2030" / "runtime" / "downlink"
    assert restored.queue[0]["id"] == packet["id"]
    assert (restored.output_dir / packet["filename"]).is_file()
