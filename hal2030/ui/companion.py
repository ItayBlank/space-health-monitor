"""Private per-crew companion sessions with honest offline-engine placeholders."""
from __future__ import annotations

import math
from html import escape
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QTimer, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QScrollArea, QTabBar,
    QTextBrowser, QVBoxLayout, QWidget,
)

from hal2030.config import CREW
from hal2030.ui.theme import COLORS
from hal2030.ui.widgets import HalEye, Panel, Portrait, button, label


class VoiceMeter(QWidget):
    """A purely visual preview; this widget never accesses an audio device."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.active = False
        self.clock = QElapsedTimer()
        self.clock.start()
        self.timer = QTimer(self)
        self.timer.setInterval(70)
        self.timer.timeout.connect(self.update)

    def set_active(self, value):
        self.active = bool(value)
        if value:
            self.clock.restart()
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        count = 35
        gap = 3
        width = max(2.0, (self.width() - gap * (count - 1)) / count)
        phase = self.clock.elapsed() / 290 if self.active else 0
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(count):
            envelope = 0.22 + 0.78 * math.sin(math.pi * (i + 1) / (count + 1))
            height = (8 + (0.5 + 0.5 * math.sin(i * 1.39 + phase)) * 42 * envelope) if self.active else 4
            painter.setBrush(QColor(COLORS["cyan"] if self.active else COLORS["border"]))
            painter.drawRoundedRect(int(i * (width + gap)), int((self.height() - height) / 2), int(width), int(height), 2, 2)


class CompanionPage(QWidget):
    """Six independent sessions. The prototype uses scripted, local replies."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.crew_id = CREW[0]["id"]
        self._frame = {}
        self._alerts = []
        self._t = 0.0
        self._model_path = ""
        self._archive_paths = {}
        self._modes = {crew["id"]: 0 for crew in CREW}
        self._histories = {
            crew["id"]: [{
                "speaker": "HAL2030 · scripted preview",
                "text": f"Hello, {crew['name'].split()[0]}. This is your private onboard space. We can review the demonstration readings, plan a short pause, or prepare a message for home. What would help right now?",
                "kind": "assistant",
            }]
            for crew in CREW
        }
        self._voice_crew = None
        self._voice_steps = 0
        self._voice_timer = QTimer(self)
        self._voice_timer.setInterval(1500)
        self._voice_timer.timeout.connect(self._voice_step)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("Private cabin", "heading"))
        subtitle = label("An onboard companion concept. Six crew members, six separate conversations.", "muted")
        subtitle.setWordWrap(True)
        titles.addWidget(subtitle)
        header.addLayout(titles, 1)
        preview = label("● SCRIPTED PREVIEW", "body")
        preview.setStyleSheet(f"color: {COLORS['amber']}; font-size: 11px; font-weight: 700;")
        header.addWidget(preview)
        layout.addLayout(header)

        self.tabs = QTabBar()
        self.tabs.setExpanding(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.setDocumentMode(True)
        for crew in CREW:
            self.tabs.addTab(crew["name"])
        self.tabs.currentChanged.connect(self._tab_changed)
        layout.addWidget(self.tabs)

        body = QHBoxLayout()
        body.setSpacing(16)
        chat_panel = Panel()
        chat_header = QHBoxLayout()
        self.portrait_holder = QVBoxLayout()
        self.portrait = Portrait(CREW[0], size=52)
        self.portrait_holder.addWidget(self.portrait)
        chat_header.addLayout(self.portrait_holder)
        names = QVBoxLayout()
        self.person_name = label(CREW[0]["name"], "heading")
        self.context = label("Private session · local memory only", "muted")
        names.addWidget(self.person_name)
        names.addWidget(self.context)
        chat_header.addLayout(names, 1)
        chat_panel.body.addLayout(chat_header)

        mode_row = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItem("HAL2030 support")
        self.mode.addItem("Family archive · simulated")
        self.mode.currentIndexChanged.connect(self._mode_changed)
        mode_row.addWidget(self.mode, 1)
        self.clear_button = button("Clear session")
        self.clear_button.clicked.connect(self._clear_session)
        mode_row.addWidget(self.clear_button)
        chat_panel.body.addLayout(mode_row)

        self.mode_note = label("Prepared replies only. No language model is connected.", "muted")
        self.mode_note.setWordWrap(True)
        chat_panel.body.addWidget(self.mode_note)

        self.transcript = QTextBrowser()
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setMinimumHeight(225)
        self.transcript.setFrameShape(QTextBrowser.Shape.NoFrame)
        self.transcript.setStyleSheet(
            f"QTextBrowser {{ background: {COLORS['bg']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; border-radius: 10px; padding: 14px; font-size: 13px; }}"
        )
        chat_panel.body.addWidget(self.transcript, 1)

        prompts = QHBoxLayout()
        for title in ("I miss home", "Review my readings", "Help me unwind"):
            quick = button(title)
            quick.setMinimumWidth(0)
            quick.clicked.connect(lambda checked=False, value=title: self._send(value))
            prompts.addWidget(quick)
        chat_panel.body.addLayout(prompts)
        compose = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setMinimumHeight(42)
        self.input.setPlaceholderText("Type a message to the scripted companion…")
        self.input.returnPressed.connect(self._send_input)
        send = button("Send", accent=True)
        send.setMinimumHeight(42)
        send.clicked.connect(self._send_input)
        compose.addWidget(self.input, 1)
        compose.addWidget(send)
        chat_panel.body.addLayout(compose)
        foot = label("Conversations stay in this app session and are never included in mission-control telemetry.", "muted")
        foot.setWordWrap(True)
        chat_panel.body.addWidget(foot)
        body.addWidget(chat_panel, 3)

        side_scroll = QScrollArea()
        side_scroll.setWidgetResizable(True)
        side_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        side_scroll.setMinimumWidth(275)
        side_scroll.setMaximumWidth(370)
        side_widget = QWidget()
        side = QVBoxLayout(side_widget)
        side.setContentsMargins(0, 0, 6, 0)
        side.setSpacing(14)
        side_scroll.setWidget(side_widget)

        voice = Panel("VOICE CHANNEL")
        lens_row = QHBoxLayout()
        lens_row.addStretch(1)
        lens_row.addWidget(HalEye(size=128))
        lens_row.addStretch(1)
        voice.body.addLayout(lens_row)
        callsign = label("HAL2030", "heading")
        callsign.setAlignment(Qt.AlignmentFlag.AlignCenter)
        callsign.setStyleSheet(f"color: {COLORS['text']}; font-size: 19px; font-weight: 700; letter-spacing: 5px;")
        voice.body.addWidget(callsign)
        self.voice_meter = VoiceMeter()
        voice.body.addWidget(self.voice_meter)
        self.voice_label = label("MICROPHONE OFF · VISUAL PREVIEW", "muted")
        self.voice_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.voice_label.setWordWrap(True)
        voice.body.addWidget(self.voice_label)
        self.voice_button = button("Start voice demo", accent=True)
        self.voice_button.clicked.connect(self._toggle_voice)
        voice.body.addWidget(self.voice_button)
        voice_note = label("Illustrated listening and reply states. No microphone, speech recognition or audio output is active.", "muted")
        voice_note.setWordWrap(True)
        voice.body.addWidget(voice_note)
        side.addWidget(voice)

        engine = Panel("ONBOARD AI ENGINE")
        self.engine_status = label("● MODEL NOT CONNECTED", "body")
        self.engine_status.setStyleSheet(f"color: {COLORS['amber']}; font-size: 11px; font-weight: 700;")
        engine.body.addWidget(self.engine_status)
        engine_note = label("Local inference, speech recognition and voice synthesis are connection points for a future offline model.", "muted")
        engine_note.setWordWrap(True)
        engine.body.addWidget(engine_note)
        connect = button("Connect local model")
        connect.clicked.connect(self._model_dialog)
        engine.body.addWidget(connect)
        side.addWidget(engine)

        archive = Panel("FAMILY ARCHIVE")
        self.archive_status = label("Fictional sample · no personal archive", "muted")
        self.archive_status.setWordWrap(True)
        archive.body.addWidget(self.archive_status)
        archive_note = label("A clearly marked simulation can offer familiar conversation patterns while messages to Earth travel through the real link.", "muted")
        archive_note.setWordWrap(True)
        archive.body.addWidget(archive_note)
        manage = button("Preview archive setup")
        manage.clicked.connect(self._archive_dialog)
        archive.body.addWidget(manage)
        side.addWidget(archive)
        side.addStretch(1)
        body.addWidget(side_scroll, 2)
        body_scroll = QScrollArea()
        body_scroll.setWidgetResizable(True)
        body_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        body_widget = QWidget()
        body_widget.setLayout(body)
        body.setContentsMargins(0, 0, 6, 0)
        body_scroll.setWidget(body_widget)
        layout.addWidget(body_scroll, 1)
        self._render_history()

    def _tab_changed(self, index):
        self.set_crew(CREW[index]["id"])

    def set_crew(self, crew_id):
        match = next((crew for crew in CREW if crew["id"] == crew_id), None)
        if match is None:
            return
        if crew_id != self.crew_id:
            self._stop_voice()
            self.input.clear()
        self.crew_id = crew_id
        self.tabs.blockSignals(True)
        self.tabs.setCurrentIndex(next(index for index, crew in enumerate(CREW) if crew["id"] == crew_id))
        self.tabs.blockSignals(False)
        self.mode.blockSignals(True)
        self.mode.setCurrentIndex(self._modes[crew_id])
        self.mode.blockSignals(False)
        self.person_name.setText(match["name"])
        old = self.portrait
        self.portrait = Portrait(match, size=52)
        self.portrait_holder.replaceWidget(old, self.portrait)
        old.hide()
        old.deleteLater()
        self._update_mode_note()
        self._update_archive_status()
        self._render_history()
        if self._frame:
            self.update_frame(self._frame, self._alerts, self._t)

    def _mode_changed(self, index):
        self._modes[self.crew_id] = index
        self._update_mode_note()

    def _update_mode_note(self):
        family = self._modes[self.crew_id] == 1
        self.mode_note.setText(
            "FAMILY SIMULATION · Fictional sample replies. This is not a live conversation with a family member."
            if family else "SCRIPTED COMPANION · Prepared replies only. No language model is connected."
        )
        self.mode_note.setStyleSheet(f"color: {COLORS['amber'] if family else COLORS['muted']}; font-size: 11px;")

    def _render_history(self):
        chunks = []
        for message in self._histories[self.crew_id]:
            mine = message["kind"] == "user"
            color = COLORS["cyan"] if mine else (COLORS["amber"] if message["kind"] == "family" else COLORS["green"])
            chunks.append(
                f"<p style='margin-top:16px; margin-bottom:4px; color:{color}; font-size:11px; font-weight:700'>{escape(message['speaker'])}</p>"
                f"<p style='margin-top:0; margin-bottom:16px; line-height:150%'>{escape(message['text']).replace(chr(10), '<br>')}</p>"
            )
        self.transcript.setHtml("".join(chunks))
        scroll = self.transcript.verticalScrollBar()
        scroll.setValue(scroll.maximum())

    def _send_input(self):
        text = self.input.text().strip()
        if text:
            self.input.clear()
            self._send(text)

    def _send(self, text, crew_id=None):
        crew_id = crew_id or self.crew_id
        crew = next(person for person in CREW if person["id"] == crew_id)
        history = self._histories[crew_id]
        history.append({"speaker": crew["name"], "text": str(text), "kind": "user"})
        family = self._modes[crew_id] == 1
        reply = self._reply(str(text), crew_id, family)
        history.append({
            "speaker": "Family archive · simulated sample" if family else "HAL2030 · scripted preview",
            "text": reply,
            "kind": "family" if family else "assistant",
        })
        if crew_id == self.crew_id:
            self._render_history()

    def _reply(self, text, crew_id, family):
        lower = text.lower()
        name = next(person["name"].split()[0] for person in CREW if person["id"] == crew_id)
        if family:
            if any(word in lower for word in ("sleep", "rest", "tired")):
                return "A fictional message from the archive: Take a quiet moment and tell me about one good thing from your day. We can turn that into a message for home when you are ready."
            return f"This is a simulated family conversation, {name}. Imagine a familiar voice asking: what was the most interesting part of your day? We can keep a thought ready for your next real message to Earth."
        if any(word in lower for word in ("reading", "health", "oxygen", "heart", "sensor", "status")):
            sample = self._frame.get(crew_id)
            if sample is None:
                return "I am waiting for the demonstration telemetry frame. Your Crew health tab will show readings as soon as replay begins."
            def number(metric, unit):
                value = sample.values.get(metric)
                return "no signal" if value is None else f"{value:.0f} {unit}"
            return (
                f"Your current simulated readings are: heart rate {number('heart_rate', 'bpm')}, "
                f"blood oxygen {number('spo2', '%')}, and breathing rate {number('resp_rate', 'breaths/min')}. "
                "Open Crew health for trends and any rule-based alerts. A crew medical officer should review an abnormal measurement; this scripted chat cannot diagnose it."
            )
        if any(word in lower for word in ("miss", "home", "family", "lonely")):
            return f"Being far from familiar people can feel difficult, {name}. What would you most like them to hear today? You can put that into words here. The Family archive mode is a clearly marked simulation, and any real message would still need the communication link."
        if any(word in lower for word in ("sleep", "tired", "rest")):
            return "We can make space for a short pause. Check your scheduled rest window, reduce distractions where practical, and note how you are feeling. If fatigue is affecting your tasks, let a crew member know. Your sleep label in this prototype comes from the scenario, not a diagnosis."
        if any(word in lower for word in ("unwind", "stress", "worry", "anxious", "break", "calm")):
            return "Let us pause for a moment. Settle into a comfortable position, relax your shoulders, and notice three things around you. You can breathe at your own comfortable pace. What is the one thing you would like to take off your mind?"
        if any(word in lower for word in ("privacy", "private", "send", "ground")):
            return "This conversation is held only in this app session. It is excluded from telemetry packets. The mission-control panel simulates queued health snapshots; no external service is contacted by this prototype."
        if any(word in lower for word in ("hello", "hi", "hey")):
            return f"Hello, {name}. We can look at your demonstration readings or take a moment to talk about the day. I am using a small set of prepared responses until a local model is connected."
        return "I am listening through this scripted preview. Tell me whether you would like to review your readings, unwind, talk about home, or plan some rest. A future offline model can provide a richer conversation through the connection panel."

    def _clear_session(self):
        self._stop_voice()
        self._histories[self.crew_id] = [{
            "speaker": "HAL2030 · scripted preview", "kind": "assistant",
            "text": "Your session has been cleared. We can begin again whenever you are ready.",
        }]
        self._render_history()

    def _toggle_voice(self):
        if self._voice_timer.isActive():
            self._stop_voice()
            return
        self._voice_crew = self.crew_id
        self._voice_steps = 0
        self.voice_label.setText("DEMO LISTENING · MICROPHONE OFF")
        self.voice_button.setText("Stop voice demo")
        self.voice_meter.set_active(True)
        self._voice_timer.start()

    def _voice_step(self):
        self._voice_steps += 1
        if self._voice_steps == 1:
            self.voice_label.setText("DEMO TRANSCRIPT · “I could use a break.”")
        elif self._voice_steps == 2:
            self.voice_label.setText("DEMO REPLY · TEXT ONLY")
            self._send("[Voice demo] I could use a short break.", self._voice_crew)
        else:
            self._stop_voice()

    def _stop_voice(self):
        self._voice_timer.stop()
        self._voice_crew = None
        if hasattr(self, "voice_meter"):
            self.voice_meter.set_active(False)
            self.voice_label.setText("MICROPHONE OFF · VISUAL PREVIEW")
            self.voice_button.setText("Start voice demo")

    def _model_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("HAL2030 · local engine connection preview")
        dialog.resize(560, 350)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label("OFFLINE ENGINE · CONNECTION PLACEHOLDER", "heading"))
        explanation = label("Choose a model path to preview setup. This build does not load a model or run inference.", "muted")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        fields = QFormLayout()
        path = QLineEdit(self._model_path or "No model selected")
        path.setReadOnly(True)
        fields.addRow("Local model", path)
        fields.addRow("Inference bridge", label("Not implemented", "muted"))
        fields.addRow("Speech recognition", label("Not connected", "muted"))
        fields.addRow("Voice synthesis", label("Not connected", "muted"))
        fields.addRow("Network requirement", label("Designed for onboard / offline operation", "muted"))
        layout.addLayout(fields)
        choose = button("Choose model file · preview only")
        def select_model():
            selected, _ = QFileDialog.getOpenFileName(dialog, "Select local model path (not loaded)", "", "Local model (*.gguf *.onnx);;All files (*)")
            if selected:
                self._model_path = selected
                path.setText(selected)
                self.engine_status.setText("● PATH SELECTED · ENGINE OFF")
        choose.clicked.connect(select_model)
        layout.addWidget(choose)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(dialog.reject)
        layout.addWidget(close)
        dialog.exec()

    def _update_archive_status(self):
        path = self._archive_paths.get(self.crew_id)
        self.archive_status.setText(f"Selected: {Path(path).name}\nPreview only · contents not imported" if path else "Fictional sample · no personal archive")

    def _archive_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Family archive · setup preview")
        dialog.resize(550, 340)
        layout = QVBoxLayout(dialog)
        layout.addWidget(label("PERSONAL ARCHIVE · SIMULATION CONCEPT", "heading"))
        explanation = label(
            "A future onboard engine could use a family-approved archive of messages, voice recordings and photographs. "
            "Its replies would remain explicitly labelled as simulated. This build provides fictional sample replies and a file-selection preview only.",
            "body",
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        selected_label = label(self._archive_paths.get(self.crew_id, "No archive selected"), "muted")
        selected_label.setWordWrap(True)
        layout.addWidget(selected_label)
        choose = button("Select archive · preview only")
        def select_archive():
            filename, _ = QFileDialog.getOpenFileName(dialog, "Select archive path (contents are not imported)", "", "Archive files (*.zip *.json *.txt);;All files (*)")
            if filename:
                self._archive_paths[self.crew_id] = filename
                selected_label.setText(f"{filename}\nNot imported; no data has been read.")
                self._update_archive_status()
        choose.clicked.connect(select_archive)
        layout.addWidget(choose)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(dialog.reject)
        layout.addWidget(close)
        dialog.exec()

    def update_frame(self, frame, alerts, t):
        self._frame, self._alerts, self._t = frame, alerts, float(t)
        sample = frame.get(self.crew_id)
        if sample is not None:
            self.portrait.set_activity(sample.activity)
            self.context.setText(f"{sample.activity.title()} · private session · local memory only")
            own = [a for a in alerts if a.crew_id == self.crew_id]
            status = "critical" if any(a.severity == "critical" for a in own) else ("warning" if own else "nominal")
            self.portrait.set_status(status)
