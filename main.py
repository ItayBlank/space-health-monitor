"""Launch HAL2030. Run: python main.py"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from hal2030.config import CREW


def main():
    parser = argparse.ArgumentParser(description="HAL2030 astronaut health console")
    parser.add_argument("--data", type=Path, help="Custom telemetry CSV matching the supplied schema")
    parser.add_argument("--start-at", type=int, default=0, help="Start at this recording second, 0–599")
    parser.add_argument("--paused", action="store_true", help="Open with telemetry replay paused")
    parser.add_argument("--page", type=int, default=0, help="Initial page index in the application navigation")
    parser.add_argument("--crew", choices=[crew["id"] for crew in CREW], default=CREW[0]["id"])
    parser.add_argument("--runtime-dir", type=Path, help="Alternative folder for the local simulated outbox")
    parser.add_argument("--screenshot", type=Path, help="Save a PNG of the initial page and exit (developer QA)")
    parser.add_argument("--smoke-test", type=Path, metavar="OUTPUT_DIR", help="Render every navigation page and write a manifest, then exit (developer QA)")
    parser.add_argument("--verify-voice-model", type=Path, metavar="RECEIPT", help="Load the offline model without microphone access and exit (developer QA)")
    args = parser.parse_args()
    if args.verify_voice_model:
        try:
            from hal2030.voice_smoke import verify_voice_model
            verify_voice_model(args.verify_voice_model)
        except Exception:
            import traceback
            args.verify_voice_model.parent.mkdir(parents=True, exist_ok=True)
            args.verify_voice_model.with_suffix('.error.txt').write_text(traceback.format_exc(), encoding='utf-8')
            return 1
        return 0
    if args.smoke_test and args.screenshot:
        parser.error("Use either --smoke-test or --screenshot, not both.")
    if (args.screenshot or args.smoke_test) and sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication, QMessageBox
        from hal2030.telemetry import CsvReplaySource
        from hal2030.ui.theme import apply_theme
        from hal2030.ui.window import MainWindow
    except ImportError as error:
        print(f"A dependency is missing: {error}\nInstall with: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1
    app = QApplication(sys.argv[:1])
    app.setApplicationName("HAL2030")
    app.setOrganizationName("HAL2030 Demo")
    apply_theme(app)
    try:
        source = CsvReplaySource(args.data)
        window = MainWindow(source=source, runtime_dir=args.runtime_dir,
                            start_at=args.start_at, autoplay=not args.paused)
    except (OSError, ValueError) as error:
        if args.screenshot or args.smoke_test:
            print(f"Could not load the demonstration: {error}", file=sys.stderr)
        else:
            QMessageBox.critical(None, "HAL2030 startup error", f"Could not load the demonstration:\n\n{error}")
        return 1
    if not 0 <= args.page < window.stack.count():
        print(f"Page index must be between 0 and {window.stack.count()-1}.", file=sys.stderr)
        window.close()
        return 2
    window.detail.set_crew(args.crew)
    window.companion.set_crew(args.crew)
    window.current_crew = args.crew
    window.navigate(args.page)
    if not args.screenshot and app.primaryScreen() is not None:
        available = app.primaryScreen().availableGeometry()
        window.resize(min(window.width(), available.width()-40),
                      min(window.height(), available.height()-60))
        window.move(available.center()-window.rect().center())
    window.show()
    if args.smoke_test:
        from hal2030.smoke import capture_navigation
        capture_navigation(window, app, args.smoke_test)
    elif args.screenshot:
        def capture():
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            window.grab().save(str(args.screenshot))
            window.close()
            app.quit()
        QTimer.singleShot(650, capture)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
