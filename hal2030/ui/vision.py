"""Separate self-administered near-vision window, with explicit calibration gates."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QShortcut, QKeySequence
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QWidget, QLabel, QSpinBox, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QStackedWidget, QScrollArea, QFileDialog, QMessageBox, QPlainTextEdit)

from hal2030.config import CREW
from hal2030.vision import Calibration, DIRECTIONS, EyeTest, levels_for, make_report, utcnow
from hal2030.vision_voice import VoiceGuide
from hal2030.voice_model import default_model_path


class Chart(QWidget):
    """Paint ruler bars or a geometric E on integer physical pixels, without smoothing."""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(480, 300)
        self.mode = 'calibration'
        self.bar_x = self.bar_y = 190
        self.direction = 'right'
        self.strokes = (16, 16)
        self.practice = False
        self.setAccessibleName('Vision chart; directions are relative to the screen edges')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('white'))
        painter.setPen(QColor('black'))
        painter.drawText(QRectF(0, 4, self.width(), 24), Qt.AlignmentFlag.AlignCenter, 'TOP ↑')
        painter.drawText(QRectF(0, self.height()-28, self.width(), 24), Qt.AlignmentFlag.AlignCenter, 'BOTTOM ↓')
        painter.drawText(QRectF(6, self.height()/2-12, 75, 24), Qt.AlignmentFlag.AlignLeft, 'LEFT ←')
        painter.drawText(QRectF(self.width()-85, self.height()/2-12, 80, 24), Qt.AlignmentFlag.AlignRight, 'RIGHT →')
        if self.mode == 'calibration':
            x, y = (self.width()-self.bar_x)/2, 64
            painter.setPen(QPen(QColor('black'), 1))
            painter.drawLine(int(x), y, int(x+self.bar_x), y)
            for end in (x, x+self.bar_x):
                painter.drawLine(int(end), y-6, int(end), y+6)
            painter.drawText(QRectF(x, y+10, self.bar_x, 22), Qt.AlignmentFlag.AlignCenter, 'Horizontal: 50 mm between ticks')
            vx, vy = self.width()/2 + 155, (self.height()-self.bar_y)/2
            painter.drawLine(int(vx), int(vy), int(vx), int(vy+self.bar_y))
            for end in (vy, vy+self.bar_y):
                painter.drawLine(int(vx-6), int(end), int(vx+6), int(end))
            painter.drawText(QRectF(vx+12, self.height()/2+20, 180, 44), 'Vertical: 50 mm\nbetween ticks')
        elif self.mode == 'symbol':
            # Rows/columns rotate before rasterization, retaining independent axis calibration.
            cells = {(0, y) for y in range(5)} | {(x, y) for y in (0, 2, 4) for x in range(5)}
            rotations = {'right': 0, 'down': 1, 'left': 2, 'up': 3}
            for _ in range(rotations[self.direction]):
                cells = {(4-y, x) for x, y in cells}
            dpr = self.devicePixelRatioF()
            sx, sy = self.strokes
            ox = round((self.width()*dpr-5*sx)/2)
            oy = round((self.height()*dpr-5*sy)/2)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            for x, y in cells:
                painter.fillRect(QRectF((ox+x*sx)/dpr, (oy+y*sy)/dpr, sx/dpr, sy/dpr), QColor('black'))
            if self.practice:
                arrows = {'up': '↑', 'down': '↓', 'left': '←', 'right': '→'}
                painter.drawText(QRectF(0, self.height()-65, self.width(), 25),
                                 Qt.AlignmentFlag.AlignCenter, f'PRACTICE: {arrows[self.direction]} {self.direction.upper()}')
        painter.end()


class VisionDialog(QDialog):
    """Guide one selected crew member through both eyes; queue only explicit saves.

    All workflow state belongs to this dialog. The parent owns the downlink
    service. Display changes invalidate calibration; no camera distance claim.
    """
    def __init__(self, crew_id, service, mission_time, parent=None, enable_narration=True):
        super().__init__(parent)
        self.crew_id, self.service, self.mission_time = crew_id, service, mission_time
        name = next(c['name'] for c in CREW if c['id'] == crew_id)
        self.setWindowTitle(f'Near-vision check · {name}')
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(1060, 820)
        self.stage = 'setup'
        self.calibration = None
        self.eye = 'right'
        self.test = None
        self.pending = None
        self.paused = False
        self.saved = False
        self.attempts = []
        self.eyes = {}
        self.practice_log = []
        self.practice_index = 0
        self.started_at = utcnow()
        self.session_signature = None
        self.last_instruction = ''
        self.report = None
        self.voice = VoiceGuide(self)
        self.voice.narration = enable_narration
        self.voice.command.connect(self.command)

        root = QVBoxLayout(self)
        title = QLabel(f'Near-vision check · {name}')
        title.setStyleSheet('font-size:24px;font-weight:700;')
        root.addWidget(title)
        note = QLabel('Functional vision demo • user-performed responses • simulated preflight baseline • not a diagnosis')
        note.setWordWrap(True)
        root.addWidget(note)
        voice_controls = QHBoxLayout()
        self.microphone_button = QPushButton('Enable microphone')
        self.microphone_button.setMinimumHeight(42)
        self.microphone_button.clicked.connect(lambda: self.voice.start(self.model_path.text()))
        voice_controls.addWidget(self.microphone_button)
        self.voice_light = QLabel('● MICROPHONE OFF')
        self.voice_light.setMinimumWidth(210)
        self.voice_light.setAccessibleName('Voice activity: microphone off')
        voice_controls.addWidget(self.voice_light)
        voice_controls.addStretch()
        self.button_mode = QCheckBox('Use buttons instead of microphone')
        voice_controls.addWidget(self.button_mode)
        root.addLayout(voice_controls)
        self.voice.mode_changed.connect(self._voice_mode_changed)
        self.voice.publish_mode()
        self.instructions = QLabel()
        self.instructions.setWordWrap(True)
        self.instructions.setMinimumHeight(75)
        self.instructions.setStyleSheet('font-size:19px;color:#b9f5f5;')
        root.addWidget(self.instructions)
        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)
        self.setup_page = self._setup_page()
        self.pages.addWidget(self.setup_page)
        self.test_page = QWidget()
        test_layout = QVBoxLayout(self.test_page)
        self.progress = QLabel()
        test_layout.addWidget(self.progress)
        self.chart = Chart()
        test_layout.addWidget(self.chart, 1)
        answer_row = QHBoxLayout()
        for direction in (*DIRECTIONS, 'unable'):
            b = QPushButton(direction.capitalize() if direction != 'unable' else 'Unable to see')
            b.clicked.connect(lambda checked=False, d=direction: self.command(d))
            answer_row.addWidget(b)
        test_layout.addLayout(answer_row)
        self.pages.addWidget(self.test_page)
        self.summary = QPlainTextEdit()
        self.summary.setReadOnly(True)
        self.pages.addWidget(self.summary)
        self.voice_status = QLabel('Microphone off. Use buttons or keyboard.')
        self.voice_status.setWordWrap(True)
        self.voice.status.connect(self.voice_status.setText)
        root.addWidget(self.voice_status)
        controls = QHBoxLayout()
        for text, command in [('Repeat instruction', 'repeat'), ('Back', 'back'), ('Pause / Resume', 'pause')]:
            b = QPushButton(text)
            b.clicked.connect(lambda checked=False, c=command: self.command(c))
            controls.addWidget(b)
        self.continue_button = QPushButton('Continue')
        self.continue_button.clicked.connect(lambda: self.command('continue'))
        controls.addWidget(self.continue_button)
        self.retry_button = QPushButton('Repeat both eyes (same conditions)')
        self.retry_button.clicked.connect(self.repeat_test)
        self.retry_button.hide()
        controls.addWidget(self.retry_button)
        self.save_button = QPushButton('Save and queue report')
        self.save_button.clicked.connect(self.save_report)
        self.save_button.hide()
        controls.addWidget(self.save_button)
        close = QPushButton('Close')
        close.clicked.connect(self.reject)
        controls.addWidget(close)
        root.addLayout(controls)
        for key, cmd in [('Up', 'up'), ('Down', 'down'), ('Left', 'left'), ('Right', 'right'),
                         ('Space', 'continue')]:
            shortcut = QShortcut(QKeySequence(key), self.test_page)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(lambda c=cmd: self.command(c))
        self.watch = QTimer(self)
        self.watch.setInterval(500)
        self.watch.timeout.connect(self.check_display)
        self.watch.start()
        self.instruct('First, click Enable microphone above for spoken answers, or choose Use buttons instead. '
                      'Then record your symptom and viewing conditions. '
                      'Use a ruler to make both calibration bars exactly fifty millimetres long.')

    def _setup_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        form = QFormLayout()
        self.symptom = QLineEdit()
        self.symptom.setPlaceholderText('Describe the reported change, or enter “routine check”')
        form.addRow('Symptom / reason', self.symptom)
        self.correction = QComboBox()
        self.correction.addItems(['Select correction worn…', 'None', 'Glasses', 'Contact lenses'])
        form.addRow('Correction worn', self.correction)
        self.lighting = QLineEdit()
        self.lighting.setPlaceholderText('e.g. cabin lights on, no glare')
        form.addRow('Lighting', self.lighting)
        self.brightness = QLineEdit()
        self.brightness.setPlaceholderText('Record screen setting, e.g. 70%; keep it fixed')
        form.addRow('Screen brightness', self.brightness)
        layout.addLayout(form)
        self.cal_chart = Chart()
        self.cal_chart.setFixedHeight(320)
        layout.addWidget(self.cal_chart)
        bars = QHBoxLayout()
        self.x_size, self.y_size = QSpinBox(), QSpinBox()
        for box in (self.x_size, self.y_size):
            box.setRange(50, 260)
            box.setValue(190)
            box.setSuffix(' display units')
        bars.addWidget(QLabel('Horizontal bar'))
        bars.addWidget(self.x_size)
        bars.addWidget(QLabel('Vertical bar'))
        bars.addWidget(self.y_size)
        self.x_size.valueChanged.connect(self._bars_changed)
        self.y_size.valueChanged.connect(self._bars_changed)
        layout.addLayout(bars)
        self.ruler_confirm = QCheckBox('I measured both bars with a ruler: each is 50 mm between the end ticks.')
        self.distance_confirm = QCheckBox('Tested eye is 40 cm from screen; device supported, face straight-on, rotation locked.')
        layout.addWidget(self.ruler_confirm)
        layout.addWidget(self.distance_confirm)
        voice_row = QHBoxLayout()
        self.model_path = QLineEdit(str(default_model_path(self.service.output_dir.parent)))
        self.model_path.setPlaceholderText('Extracted offline Vosk model directory')
        voice_row.addWidget(self.model_path, 1)
        browse = QPushButton('Model folder…')
        browse.clicked.connect(self._browse_model)
        voice_row.addWidget(browse)
        layout.addLayout(voice_row)
        self.narration = QCheckBox('Speak instructions slowly (local English voice)')
        self.narration.setChecked(self.voice.narration)
        self.narration.toggled.connect(self._narration_changed)
        layout.addWidget(self.narration)
        privacy = QLabel('Microphone runs only during this window, after you enable it. Audio is neither saved nor sent. '
                         'If speech is unavailable, use the buttons. Say “continue” to confirm an answer.')
        privacy.setWordWrap(True)
        layout.addWidget(privacy)
        scroll.setWidget(content)
        return scroll

    def _voice_mode_changed(self, mode):
        labels = {'speaking': ('SPEAKING — please wait', '#ff6a76'),
                  'listening': ('LISTENING — speak now', '#55dfad'),
                  'loading': ('STARTING MICROPHONE', '#f7c469'),
                  'waiting': ('WAIT — preparing to listen', '#f7c469'),
                  'error': ('MICROPHONE UNAVAILABLE', '#f7c469'),
                  'off': ('MICROPHONE OFF', '#8496ad')}
        text, color = labels[mode]
        self.voice_light.setText('● ' + text)
        self.voice_light.setStyleSheet(f'color:{color};font-size:15px;font-weight:700;')
        self.voice_light.setAccessibleName('Voice activity: ' + text.lower())
        self.microphone_button.setText('Microphone enabled' if self.voice.active else
                                       'Starting microphone…' if self.voice.loading else 'Enable microphone')
        self.microphone_button.setEnabled(not self.voice.active and not self.voice.loading)

    def _browse_model(self):
        path = QFileDialog.getExistingDirectory(self, 'Select extracted Vosk model')
        if path:
            self.model_path.setText(path)

    def _narration_changed(self, checked):
        self.voice.narration = checked
        self.voice.say(self.last_instruction)

    def _bars_changed(self):
        self.cal_chart.bar_x, self.cal_chart.bar_y = self.x_size.value(), self.y_size.value()
        self.cal_chart.update()
        if hasattr(self, 'ruler_confirm'):
            self.ruler_confirm.setChecked(False)

    def display_signature(self):
        screen = self.screen()
        return json.dumps(dict(name=screen.name(), serial=screen.serialNumber(),
                               geometry=[screen.geometry().width(), screen.geometry().height()],
                               dpi=screen.logicalDotsPerInch(), dpr=self.devicePixelRatioF(),
                               orientation=screen.orientation().value), sort_keys=True)

    def check_display(self):
        if self.calibration and self.stage != 'summary' and self.display_signature() != self.session_signature:
            self.stage = 'setup'
            self.calibration = None
            self.pending = None
            self.eyes = {}
            self.attempts = []
            self.practice_log = []
            self.paused = False
            self.pages.setCurrentIndex(0)
            self.ruler_confirm.setChecked(False)
            self.distance_confirm.setChecked(False)
            self.instruct('Display or scaling changed. This unfinished session is invalid. Recalibrate before starting again.')

    def instruct(self, text):
        self.last_instruction = text
        self.instructions.setText(text)
        self.voice.say(text)

    def command(self, command):
        if (self.calibration and self.stage != 'summary'
                and self.display_signature() != self.session_signature):
            self.check_display()
            return
        if command == 'repeat':
            self.instruct(self.last_instruction)
            return
        if command in ('pause', 'resume'):
            self.paused = not self.paused if command == 'pause' else False
            self.voice.say('Paused. Say resume when ready.' if self.paused else self.last_instruction)
            self.instructions.setText('PAUSED — say resume or use Pause / Resume.' if self.paused else self.last_instruction)
            return
        if self.paused:
            self.voice.say('Paused. Say resume when ready.')
            return
        if command == 'back':
            if self.pending:
                self.pending = None
                self.prompt_symbol()
            elif self.stage in ('practice', 'test', 'eye_setup'):
                # Previous scored responses remain immutable. Restart only this eye with practice.
                self.pending = None
                self.eyes.pop(self.eye, None)
                self.begin_eye()
            else:
                self.voice.say('Use the setup fields, or close the window to leave.')
            return
        if self.stage == 'setup':
            if command == 'continue':
                self.start_test()
            else:
                self.voice.say('Complete setup, then say continue.')
        elif self.stage == 'eye_setup':
            if command == 'continue':
                self.distance_confirmed_at = utcnow()
                self.stage = 'practice'
                self.practice_index = 0
                self.show_symbol()
            else:
                self.voice.say(self.last_instruction)
        elif self.stage in ('practice', 'test'):
            if command in (*DIRECTIONS, 'unable'):
                self.pending = command
                self.instruct(f'Heard {command}. Say continue to confirm, or say a different answer.')
            elif command == 'continue' and self.pending:
                answer, self.pending = self.pending, None
                self.accept_answer(answer)
            else:
                self.voice.say('Say up, down, left, right, or unable. Then say continue to confirm.')
        elif self.stage == 'summary':
            self.voice.say('Review the report. Use Save and queue report, or repeat both eyes.')

    def start_test(self):
        if not self.voice.active and not self.button_mode.isChecked():
            self.instruct('Before starting, click Enable microphone at the top and wait for it to connect. '
                          'If you prefer, select Use buttons instead of microphone.')
            self.microphone_button.setFocus()
            return
        if not (self.symptom.text().strip() and self.lighting.text().strip() and self.brightness.text().strip()
                and self.correction.currentIndex() > 0 and self.ruler_confirm.isChecked()
                and self.distance_confirm.isChecked()):
            self.instruct('Complete the symptom and conditions, then confirm both ruler calibration and forty centimetre distance.')
            return
        self.session_signature = self.display_signature()
        self.calibration = Calibration(self.x_size.value()/50, self.y_size.value()/50,
                                       self.devicePixelRatioF(), self.session_signature)
        try:
            self.levels = levels_for(self.calibration)
        except ValueError as error:
            self.instruct(str(error))
            return
        self.conditions = dict(correction=self.correction.currentText(), lighting=self.lighting.text().strip(),
                               brightness=self.brightness.text().strip(), distance_mm=400,
                               position='user-confirmed straight-on; device supported and rotation locked')
        self.eye = 'right'
        self.started_at = utcnow()
        self.begin_eye()

    def begin_eye(self):
        self.stage = 'eye_setup'
        self.pages.setCurrentIndex(1)
        self.chart.mode = 'blank'
        self.chart.update()
        self.progress.setText(f'{self.eye.capitalize()} eye • distance and orientation check')
        other = 'left' if self.eye == 'right' else 'right'
        self.instruct(f'Keep your {self.eye} eye open. Cover your {other} eye without pressing on it. '
                      'Confirm forty centimetres from eye to screen and face the screen straight-on. '
                      'Keep the device and your head orientation fixed. Directions refer to screen edges, not gravity. '
                      'Say continue when ready.')

    def show_symbol(self, prefix=''):
        self.chart.mode = 'symbol'
        self.chart.practice = self.stage == 'practice'
        if self.chart.practice:
            self.chart.direction = DIRECTIONS[self.practice_index]
            self.chart.strokes = (16, 16)
            self.progress.setText(f'{self.eye.capitalize()} eye • direction practice {self.practice_index+1}/4 • not scored')
        else:
            self.chart.direction = self.test.direction
            self.chart.strokes = self.test.level['stroke_device_px']
            xy = self.test.level['actual_logmar_xy']
            self.progress.setText(f'{self.eye.capitalize()} eye • symbol {len(self.test.batch)+1}/5 • '
                                  f'actual logMAR X/Y {xy[0]:.2f}/{xy[1]:.2f}' +
                                  (' • confirming previous passing size' if self.test.confirming else ''))
        self.chart.update()
        self.prompt_symbol(prefix)

    def prompt_symbol(self, prefix=''):
        if self.stage == 'practice':
            self.instruct(prefix + f'Practice. The arms point {self.chart.direction}, relative to the screen. '
                          f'Say {self.chart.direction}, then say continue to confirm.')
        else:
            self.instruct(prefix + 'Which screen edge do the three arms point toward? Say up, down, left, or right. '
                          'Say unable if you cannot see the direction. Then say continue to confirm.')

    def accept_answer(self, answer):
        if self.stage == 'practice':
            correct = answer == self.chart.direction
            self.practice_log.append(dict(eye=self.eye, expected=self.chart.direction, response=answer,
                                          correct=correct, timestamp_utc=utcnow()))
            if not correct:
                self.instruct(f'Practice correction: the arms point {self.chart.direction}. '
                              f'Try saying {self.chart.direction}, then continue. Nothing was scored.')
                return
            self.practice_index += 1
            if self.practice_index == 4:
                self.stage = 'test'
                self.test = EyeTest(self.levels)
            self.show_symbol('Correct. ' if self.stage == 'practice' else 'Direction practice complete. Now the scored test. ')
        else:
            result = self.test.submit(answer)
            if result is None:
                self.show_symbol()
            else:
                self.eyes[self.eye] = dict(result=result, trials=self.test.trials,
                                          distance_confirmed_at=self.distance_confirmed_at)
                if self.eye == 'right':
                    self.eye = 'left'
                    self.begin_eye()
                else:
                    self.finish_attempt()

    def finish_attempt(self):
        self.attempts.append(dict(started_at_utc=self.started_at, completed_at_utc=utcnow(), eyes=self.eyes.copy()))
        self.report = make_report(self.crew_id, self.symptom.text().strip(), self.conditions,
                                  self.calibration, self.attempts, self.practice_log)
        self.stage = 'summary'
        self.pages.setCurrentIndex(2)
        self.continue_button.setEnabled(False)
        self.retry_button.show()
        self.save_button.show()
        lines = ['FUNCTIONAL NEAR-VISION DEMO — REVIEW REQUIRED', '',
                 'Simulated preflight baseline: right 0.00 / left 0.00 logMAR.',
                 'Baseline is illustrative and not a matched clinical comparison.', '']
        labels = {'confirmed': 'Smallest confirmed passing level', 'display_limit': 'Display limit reached; threshold not established',
                  'outside_range': 'Largest available level failed; outside measurable range',
                  'inconsistent': 'Confirmation failed; inconsistent result — repeat offered'}
        for number, attempt in enumerate(self.attempts, 1):
            lines.append(f'Attempt {number}')
            for eye, entry in attempt['eyes'].items():
                result = entry['result']
                lines.append(f"  {eye.capitalize()}: {labels[result['status']]}")
                if result['level']:
                    x, y = result['level']['actual_logmar_xy']
                    lines.append(f'    Rendered logMAR X/Y: {x:.2f}/{y:.2f}; difference from simulated 0.00: {x:+.2f}/{y:+.2f}.')
            lines.append('')
        lines.extend(['Distance: 40 cm, user-confirmed; not continuously tracked.',
                      'Protocol: five E symbols per size, pass at least four; first failure confirms previous pass.',
                      'Single-symbol demo; not interchangeable with a validated clinical chart.', '',
                      'Saving writes a local report and queues simulated delivery. No remote service is contacted.'])
        self.summary.setPlainText('\n'.join(lines))
        self.instruct('Both eyes are complete. Review the results and display limits. '
                      'You can repeat under the same conditions or save the report for review.')

    def repeat_test(self):
        if self.display_signature() != self.session_signature:
            self.instruct('Display changed. Save this completed report, then reopen the test to recalibrate.')
            return
        self.saved = False
        self.report = None
        self.eyes = {}
        self.eye = 'right'
        self.pending = None
        self.started_at = utcnow()
        self.continue_button.setEnabled(True)
        self.save_button.hide()
        self.retry_button.hide()
        self.begin_eye()

    def save_report(self):
        if self.saved or not self.report:
            return
        try:
            packet = self.service.enqueue_report(self.report, self.mission_time)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, 'Report could not be queued', str(error))
            return
        self.saved = True
        self.save_button.setEnabled(False)
        self.retry_button.setEnabled(False)
        self.instruct(f'Report saved locally and queued. Packet {packet["id"]}. Delivery is simulated.')

    def done(self, result):
        if self.stage not in ('setup', 'summary'):
            answer = QMessageBox.question(self, 'End unfinished check?', 'This check is incomplete. Close without a scored report?')
            if answer != QMessageBox.StandardButton.Yes:
                return
        elif self.stage == 'summary' and not self.saved:
            answer = QMessageBox.question(self, 'Leave without saving?', 'The completed report has not been queued. Close without saving?')
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.watch.stop()
        self.voice.stop()
        super().done(result)
