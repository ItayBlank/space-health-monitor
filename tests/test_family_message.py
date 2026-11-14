"""Check the shipped payload boundary and benchmark accounting."""
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "static" / "family-media"


def test_shipped_family_messages():
    registry = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    source = next(record for record in registry["sources"] if record["id"] == "astra.family-message.synthetic.v2")
    page = (ROOT / "static" / "family-message.html").read_text(encoding="utf-8")
    assert sorted(record["path"] for record in source["files"]) == [
        path.relative_to(ROOT).as_posix() for path in sorted(ASSETS.iterdir())
    ]
    for record in source["files"]:
        assert sha256((ROOT / record["path"]).read_bytes()).hexdigest() == record["sha256"]
        assert f'"/{record["path"]}"' in page

    assert f"{(ASSETS / 'portrait.png').stat().st_size:,}-byte portrait" in page
    for name in ("one", "two"):
        message = ASSETS / f"{name}.zip"
        baseline_size = (ASSETS / f"{name}-baseline.mp4").stat().st_size
        message_size = message.stat().st_size
        reference_size = (ASSETS / f"{name}-reference.mp4").stat().st_size
        for size in (baseline_size, message_size, reference_size):
            assert f"{size:,} bytes" in page
        assert f"{100 * (1 - message_size / baseline_size):.1f}% smaller" in page
        with ZipFile(message) as payload:
            assert sorted(payload.namelist()) == ["audio.ogg", "message.json", "motion.npy"]
            assert payload.testzip() is None
            metadata = json.loads(payload.read("message.json"))
            assert metadata["version"] == 1 and metadata["fps"] == 5 and metadata["frames"] > 1
            assert payload.read("audio.ogg").startswith(b"OggS")
            assert payload.read("motion.npy").startswith(b"\x93NUMPY")
