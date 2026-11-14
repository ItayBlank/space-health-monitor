"""Windows Qt workflow tests with no microphone or audible narration."""
import os
import sys

import pytest

if sys.platform != 'win32':
    pytest.skip('Native Qt workflow validation runs on Windows.', allow_module_level=True)
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication
from hal2030.downlink import DownlinkService
from hal2030.ui.vision import VisionDialog


@pytest.fixture
def dialog(tmp_path):
    app = QApplication.instance() or QApplication([])
    view = VisionDialog('anton', DownlinkService(tmp_path), 40, enable_narration=False)
    yield view
    view.voice.stop()
    view.watch.stop()
    view.deleteLater()
    app.processEvents()


def setup(view):
    view.button_mode.setChecked(True)
    view.symptom.setText('Routine demo')
    view.correction.setCurrentIndex(1)
    view.lighting.setText('Cabin, no glare')
    view.brightness.setText('70%')
    view.ruler_confirm.setChecked(True)
    view.distance_confirm.setChecked(True)
    view.command('continue')


def practice(view):
    view.command('continue')
    assert view.stage == 'practice'
    for _ in range(4):
        view.command(view.chart.direction)
        view.command('continue')
    assert view.stage == 'test'


def test_confirmation_practice_and_both_eye_report(dialog):
    view = dialog
    view.command('continue')
    assert view.stage == 'setup'
    setup(view)
    assert view.stage == 'eye_setup'
    view.command('continue')
    view.command('unable')
    view.command('continue')
    assert view.practice_index == 0  # wrong practice response must not advance
    for _ in range(4):
        view.command(view.chart.direction)
        view.command('continue')
    view.command('up')
    assert len(view.test.trials) == 0
    view.command('back')
    assert view.pending is None and len(view.test.trials) == 0
    view.command('pause')
    view.command('unable')
    assert view.pending is None
    view.command('resume')
    for _ in range(5):
        view.command('unable')
        view.command('continue')
    assert view.eye == 'left' and view.stage == 'eye_setup'
    practice(view)
    for _ in range(5):
        view.command('unable')
        view.command('continue')
    assert view.stage == 'summary' and set(view.report['attempts'][0]['eyes']) == {'right', 'left'}
    view.save_report()
    view.save_report()
    assert len(view.service.queue) == 1


def test_display_change_invalidates_calibration(dialog, monkeypatch):
    setup(dialog)
    monkeypatch.setattr(dialog, 'display_signature', lambda: 'different-monitor')
    dialog.check_display()
    assert dialog.stage == 'setup' and dialog.calibration is None
    assert not dialog.ruler_confirm.isChecked()


def test_voice_ignores_stale_or_speaking_commands(dialog):
    voice = dialog.voice
    commands = []
    voice.command.connect(commands.append)
    voice.active = True
    voice.listening = True
    voice._recognized(voice.generation-1, 'continue')
    assert commands == []
    voice.say('Instruction')
    voice._recognized(voice.generation, 'continue')
    assert commands == []


def test_repeat_preserves_previous_attempt(dialog):
    setup(dialog)
    for _ in range(2):
        practice(dialog)
        for _ in range(5):
            dialog.command('unable')
            dialog.command('continue')
    previous = dialog.attempts[0]
    dialog.repeat_test()
    assert dialog.stage == 'eye_setup' and dialog.attempts == [previous]


def test_microphone_prompt_and_persistent_controls(dialog):
    setup(dialog)
    dialog.stage = 'setup'
    dialog.button_mode.setChecked(False)
    dialog.start_test()
    assert dialog.stage == 'setup'
    assert 'Enable microphone' in dialog.instructions.text()
    assert not dialog.setup_page.isAncestorOf(dialog.microphone_button)
    assert not dialog.setup_page.isAncestorOf(dialog.voice_light)
    dialog.voice.active = True
    dialog.start_test()
    assert dialog.stage == 'eye_setup'


def test_voice_light_tracks_speaking_listening_and_failure(dialog):
    voice = dialog.voice
    voice.active = True
    voice.speaking = True
    voice.publish_mode()
    assert 'SPEAKING' in dialog.voice_light.text()
    assert '#ff6a76' in dialog.voice_light.styleSheet()
    voice.speaking = False
    voice._arm(voice.generation)
    assert 'LISTENING' in dialog.voice_light.text()
    assert '#55dfad' in dialog.voice_light.styleSheet()
    voice._failed('No input device')
    assert 'UNAVAILABLE' in dialog.voice_light.text()
    assert dialog.microphone_button.isEnabled()
    voice._arm(voice.generation)
    assert dialog.voice_status.text() == 'No input device'
