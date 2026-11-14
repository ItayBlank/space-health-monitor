"""Run an executable's own smoke contract from outside the checkout."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


def validate_capture(output: Path) -> int:
    """Validate the app's manifest and each PNG; reject empty or unsafe manifests."""
    manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    pages = manifest.get('pages', [])
    if manifest.get('schema') != 'hal2030.smoke.v1' or not pages:
        raise ValueError('Missing or unsupported smoke manifest')
    seen = set()
    for index, page in enumerate(pages):
        filename = page['screenshot']
        if (page['index'] != index or not page['title'] or filename in seen
                or Path(filename).name != filename or '\\' in filename):
            raise ValueError('Invalid smoke page entry')
        seen.add(filename)
        png = (output / filename).read_bytes()
        if len(png) < 24 or png[:8] != b'\x89PNG\r\n\x1a\n' or min(struct.unpack('>II', png[16:24])) < 600:
            raise ValueError(f'Invalid screenshot: {filename}')
    return len(pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'manifest.json').unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix='hal2030-smoke-') as temp:
        cwd = Path(temp)
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', LOCALAPPDATA=str(cwd / 'local'))
        subprocess.run([str(executable), '--paused', '--smoke-test', str(output)],
                       cwd=cwd, env=env, check=True, timeout=180)
        count = validate_capture(output)
        queue = cwd / 'local' / 'HAL2030' / 'runtime' / 'downlink' / 'queue.json'
        if json.loads(queue.read_text(encoding='utf-8')) != []:
            raise RuntimeError('Unexpected smoke-test queue contents')
    print(f'Packaged app: {count} registered pages rendered; durable per-user runtime verified.')


if __name__ == '__main__':
    main()
