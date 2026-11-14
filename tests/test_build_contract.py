"""Check that packaging follows tracked resources and app-owned navigation."""
import json
from pathlib import Path
import struct
import subprocess

import pytest

from tools.build_resources import tracked_resources
from tools.smoke_executable import validate_capture


def png():
    return b'\x89PNG\r\n\x1a\n' + bytes(8) + struct.pack('>II', 800, 720)


def test_resources_include_new_data_but_not_local_downloads(tmp_path):
    subprocess.run(['git', 'init', str(tmp_path)], check=True, capture_output=True)
    paths = ['assets/new/icon.png', 'data/new-experiment.csv', 'hal2030/feature/template.json',
             'hal2030/feature/module.py', 'LICENSE', 'runtime/private.json', 'data/local-download.csv']
    for name in paths:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('example')
    subprocess.run(['git', '-C', str(tmp_path), 'add', '--', *paths[:-2]], check=True, capture_output=True)
    resources = tracked_resources(tmp_path)
    included = {Path(source).relative_to(tmp_path).as_posix() for source, _ in resources}
    assert included == set(paths[:3] + ['LICENSE'])
    assert (str(tmp_path / paths[2]), 'hal2030/feature') in resources


def test_smoke_discovers_additional_navigation_pages(tmp_path, monkeypatch):
    from hal2030 import smoke
    monkeypatch.setattr(smoke.QTimer, 'singleShot', lambda delay, callback: callback())
    class Stack:
        def count(self):
            return 8  # A future app has more pages than the original five.
    class Title:
        def text(self):
            return 'Feature'
    class Picture:
        def save(self, filename):
            Path(filename).write_bytes(png())
            return True
    class Window:
        stack, page_title = Stack(), Title()
        selected = []
        def navigate(self, index):
            self.selected.append(index)
        def grab(self):
            return Picture()
        def close(self):
            self.closed = True
    class App:
        def exit(self, code):
            self.code = code
    window, app = Window(), App()
    smoke.capture_navigation(window, app, tmp_path)
    assert window.selected == list(range(8))
    assert app.code == 0 and window.closed
    assert validate_capture(tmp_path) == 8


@pytest.mark.parametrize('filename', ['../escape.png', 'nested\\escape.png'])
def test_manifest_rejects_escaping_screenshot_names(tmp_path, filename):
    manifest = {'schema': 'hal2030.smoke.v1', 'pages': [dict(index=0, title='Page', screenshot=filename)]}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        validate_capture(tmp_path)


def test_missing_screenshot_is_not_a_success(tmp_path):
    manifest = {'schema': 'hal2030.smoke.v1', 'pages': [dict(index=0, title='Page', screenshot='missing.png')]}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(FileNotFoundError):
        validate_capture(tmp_path)
