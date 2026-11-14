"""Launch a packaged Windows app from outside its checkout and verify outputs."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hal2030-smoke-") as temp:
        cwd = Path(temp)
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen", LOCALAPPDATA=str(cwd / "local"))
        for page in range(5):
            screenshot = output / f"page-{page}.png"
            screenshot.unlink(missing_ok=True)
            subprocess.run([
                str(executable), "--paused", "--start-at", "40", "--crew", "anton",
                "--page", str(page), "--screenshot", str(screenshot),
            ], cwd=cwd, env=env, check=True, timeout=120)
            png = screenshot.read_bytes()
            if png[:8] != b"\x89PNG\r\n\x1a\n" or min(struct.unpack(">II", png[16:24])) < 600:
                raise RuntimeError(f"Invalid screenshot: {screenshot}")
            # Window close flushes the queue. It must survive process teardown,
            # outside both the checkout and the one-file extraction directory.
            queue = cwd / "local" / "HAL2030" / "runtime" / "downlink" / "queue.json"
            if json.loads(queue.read_text(encoding="utf-8")) != []:
                raise RuntimeError("Unexpected smoke-test queue contents")
    print("Packaged app: five pages rendered; durable per-user runtime verified.")


if __name__ == "__main__":
    main()
