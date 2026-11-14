"""Application-owned navigation smoke capture, independent of today's page count."""
import json
from pathlib import Path
import sys

from PySide6.QtCore import QTimer


def capture_navigation(window, app, output_dir: Path):
    """Render every registered stacked page and exit; write a manifest only on success.

    Runs on the GUI event loop. It verifies startup/rendering, not interactive
    features. Errors exit nonzero so a partial build cannot be published as passing.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = output_dir / 'manifest.json'
    manifest.unlink(missing_ok=True)
    pages = []
    count = window.stack.count()

    def fail(error):
        print(f'Smoke capture failed: {error}', file=sys.stderr)
        window.close()
        app.exit(1)

    def select(index):
        try:
            if count == 0:
                raise ValueError('No navigation pages registered')
            window.navigate(index)
            QTimer.singleShot(650, lambda: capture(index))
        except Exception as error:
            fail(error)

    def capture(index):
        try:
            filename = f'page-{index}.png'
            if not window.grab().save(str(output_dir / filename)):
                raise OSError(f'Could not save {filename}')
            pages.append(dict(index=index, title=window.page_title.text(), screenshot=filename))
            if index + 1 < count:
                select(index + 1)
            else:
                window.close()
                manifest.write_text(json.dumps(dict(schema='hal2030.smoke.v1', pages=pages), indent=2), encoding='utf-8')
                app.exit(0)
        except Exception as error:
            fail(error)

    QTimer.singleShot(0, lambda: select(0))
