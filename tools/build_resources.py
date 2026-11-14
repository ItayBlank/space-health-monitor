"""Select version-controlled distributable resources for PyInstaller."""
from pathlib import Path
import subprocess


def tracked_resources(root: Path) -> list[tuple[str, str]]:
    """Return (source, bundle directory) pairs; fail on Git errors or escaping paths.

    Only tracked assets/data and non-Python package resources are included. Local
    runtime data and downloads cannot silently enter a release from a developer PC.
    """
    root = root.resolve()
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z', '--',
                             'assets', 'data', 'hal2030', 'LICENSE'],
                            check=True, capture_output=True)
    files = []
    for name in result.stdout.decode('utf-8').split('\0'):
        if not name:
            continue
        relative = Path(name)
        if relative.parts[0] == 'hal2030' and relative.suffix in ('.py', '.pyc', '.pyo'):
            continue
        path = root / relative
        if not path.resolve().is_relative_to(root) or not path.is_file():
            raise ValueError(f'Invalid tracked resource: {name}')
        files.append((str(path), relative.parent.as_posix()))
    return files
