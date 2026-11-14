"""Main navigation, replay clock, and the single application update loop."""

from __future__ import annotations

from pathlib import Path
import time

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QShortcut, QKeySequence
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QFrame, QStackedWidget, QButtonGroup, QComboBox,
                               QSlider, QCheckBox, QFileDialog, QMessageBox)

from hal2030.config import CREW, SCENARIOS, ROOT
from hal2030.telemetry import CsvReplaySource
from hal2030.alerts import AlertEngine
from hal2030.downlink import DownlinkService
from .theme import COLORS
from .widgets import label, button, HalEye, StatusChip
from .dashboard import DashboardPage, RecommendationDialog
from .detail import DetailPage
from .sensors import SensorsPage
from .mission_control import MissionControlPage
from .companion import CompanionPage


def _nav_icon(index):
    px = QPixmap(24, 24)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("#89b8c9"), 1.5))
    if index == 0:
        for x, y in ((4, 4), (14, 4), (4, 14), (14, 14)):
            p.drawRoundedRect(x, y, 6, 6, 1, 1)
    elif index == 1:
        p.drawEllipse(8, 3, 8, 8)
        p.drawArc(4, 12, 16, 16, 0, 180*16)
    elif index == 2:
        p.drawLine(2, 13, 6, 13)
        p.drawLine(6, 13, 9, 5)
        p.drawLine(9, 5, 13, 20)
        p.drawLine(13, 20, 16, 10)
        p.drawLine(16, 10, 19, 13)
        p.drawLine(19, 13, 22, 13)
    elif index == 3:
        p.drawLine(4, 20, 19, 5)
        p.drawLine(10, 5, 19, 5)
        p.drawLine(19, 5, 19, 14)
        p.drawLine(4, 15, 4, 20)
        p.drawLine(4, 20, 9, 20)
    else:
        p.drawEllipse(3, 3, 18, 18)
        p.drawEllipse(7, 7, 10, 10)
        p.setBrush(QColor("#ed6a6a"))
        p.drawEllipse(10, 10, 4, 4)
    p.end()
    return QIcon(px)


class MainWindow(QMainWindow):
    PAGE_TITLES = [
        ("Crew overview", "Expedition 07  /  Shared health picture"),
        ("Crew detail", "Individual telemetry  /  Trends and context"),
        ("Sensor network", "42 assigned devices  /  Signal and measurement status"),
        ("Mission control", "Store, forward, acknowledge  /  Simulated ground link"),
        ("HAL2030 companion", "Private crew sessions  /  Onboard AI concept"),
    ]

    def __init__(self, source=None, runtime_dir=None, start_at=0, autoplay=True):
        super().__init__()
        self.setWindowTitle("HAL2030 · Astronaut Health Console")
        self.resize(1540, 1000)
        self.setMinimumSize(1120, 720)
        self.source = source or CsvReplaySource()
        self.engine = AlertEngine()
        self.service = DownlinkService(Path(runtime_dir) / "downlink" if runtime_dir else None)
        self.position = float(max(0, min(self.source.duration-1, start_at)))
        self.playing = autoplay
        self.speed = 1.0
        self.last_clock = time.monotonic()
        self.last_second = -1
        self.auto_elapsed = 0.0
        self._auto_was_enabled = False
        self._last_alert_signature = None
        self._last_link_status = None
        self.frame = self.source.frame(int(self.position))
        self.alerts = self.engine.evaluate(self.frame)
        self.current_crew = CREW[0]["id"]
        self.active_dialog = None

        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        shell.addWidget(self._make_sidebar())
        main = QVBoxLayout()
        main.setContentsMargins(25, 23, 25, 12)
        main.setSpacing(15)

        header = QHBoxLayout()
        titlebox = QVBoxLayout()
        titlebox.setSpacing(3)
        self.page_title = label("Crew overview", "title")
        self.page_subtitle = label(self.PAGE_TITLES[0][1], "muted")
        titlebox.addWidget(self.page_title)
        titlebox.addWidget(self.page_subtitle)
        header.addLayout(titlebox, 1)
        header.addWidget(StatusChip("DEMO TELEMETRY", "warning"))
        header.addSpacing(14)
        self.clock_label = label("MET  00:00", "heading")
        self.clock_label.setStyleSheet("font-size: 18px; color: #d5e8f8; font-family: 'Consolas', monospace;")
        header.addWidget(self.clock_label)
        main.addLayout(header)

        main.addWidget(self._make_playback())
        self.global_alert = button("")
        self.global_alert.setVisible(False)
        self.global_alert.setMinimumHeight(36)
        self.global_alert.clicked.connect(self._show_priority)
        main.addWidget(self.global_alert)

        self.stack = QStackedWidget()
        self.dashboard = DashboardPage(self.source)
        self.detail = DetailPage(self.source)
        self.sensors = SensorsPage()
        self.mission = MissionControlPage(self.service)
        self.companion = CompanionPage()
        for page in (self.dashboard, self.detail, self.sensors, self.mission, self.companion):
            self.stack.addWidget(page)
        self.dashboard.select_crew.connect(self.show_crew)
        self.dashboard.send_requested.connect(self.send_snapshot)
        self.dashboard.select_sensors.connect(lambda: self.navigate(2))
        self.dashboard.select_companion.connect(self.show_companion)
        self.detail.open_companion.connect(self.show_companion)
        self.detail.selector.currentIndexChanged.connect(
            lambda index: setattr(self, "current_crew", self.detail.selector.itemData(index)))
        self.companion.tabs.currentChanged.connect(
            lambda index: setattr(self, "current_crew", CREW[index]["id"]))
        if hasattr(self.sensors, "select_crew"):
            self.sensors.select_crew.connect(self.show_crew)
        self.mission.send_requested.connect(self.send_snapshot)
        self.mission.export_requested.connect(self.export_snapshot)
        main.addWidget(self.stack, 1)

        footer = QHBoxLayout()
        self.toast = label("Synthetic data · Local operation · Rule-based decision support", "muted")
        self.toast.setWordWrap(True)
        footer.addWidget(self.toast, 1)
        help_btn = button("About this demo")
        help_btn.setStyleSheet("QPushButton { color: #8496ad; background: transparent; border: none; font-size: 11px; padding: 3px; } QPushButton:hover { color: #d0f5ff; }")
        help_btn.clicked.connect(self.show_about)
        footer.addWidget(help_btn)
        main.addLayout(footer)
        shell.addLayout(main, 1)

        self._refresh(force=True)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        for number in range(5):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{number+1}"), self)
            shortcut.activated.connect(lambda page=number: self.navigate(page))
        play_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        play_shortcut.activated.connect(self.toggle_playback)
        if self.service.recovery_warning:
            self.toast.setText(self.service.recovery_warning)

    def _make_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(208)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(17, 27, 17, 18)
        layout.setSpacing(8)
        brand = QHBoxLayout()
        eye = HalEye(36)
        brand.addWidget(eye)
        logo = label("HAL2030", "heading")
        logo.setStyleSheet("font-size: 22px; color: #f1f6ff; font-weight: 700; letter-spacing: 1px;")
        brand.addWidget(logo)
        layout.addLayout(brand)
        strap = label("ONBOARD HEALTH SYSTEM", "small")
        strap.setStyleSheet("font-size: 9px; letter-spacing: 1.5px; color: #6f849d;")
        layout.addWidget(strap)
        layout.addSpacing(31)
        layout.addWidget(label("FLIGHT OPERATIONS", "small"))
        layout.addSpacing(6)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        for i, name in enumerate(["Crew overview", "Crew detail", "Sensor network", "Mission control", "HAL2030"]):
            b = button(name)
            b.setObjectName("NavButton")
            b.setCheckable(True)
            b.setIcon(_nav_icon(i))
            b.setIconSize(QSize(21, 21))
            b.setMinimumHeight(47)
            b.setToolTip(f"{name} · Ctrl+{i+1}")
            b.clicked.connect(lambda checked=False, idx=i: self.navigate(idx))
            self.nav_group.addButton(b, i)
            self.nav_buttons.append(b)
            layout.addWidget(b)
        self.nav_buttons[0].setChecked(True)
        layout.addStretch()
        eye_panel = QFrame()
        eye_panel.setObjectName("Panel")
        eye_box = QVBoxLayout(eye_panel)
        eye_box.setContentsMargins(12, 16, 12, 15)
        self.sidebar_eye = HalEye(102)
        eye_box.addWidget(self.sidebar_eye, 0, Qt.AlignmentFlag.AlignHCenter)
        online = label("I am here with you.", "body")
        online.setAlignment(Qt.AlignmentFlag.AlignCenter)
        eye_box.addWidget(online)
        local = label("COMPANION DEMO", "small")
        local.setAlignment(Qt.AlignmentFlag.AlignCenter)
        eye_box.addWidget(local)
        talk = button("Open private session")
        talk.setStyleSheet("QPushButton { color: #cfdee8; border: 1px solid #354451; font-size: 11px; padding: 8px 4px; border-radius: 6px; background: #1a2733; } QPushButton:hover { background: #263a4a; }")
        talk.clicked.connect(lambda: self.show_companion(self.current_crew))
        eye_box.addWidget(talk)
        layout.addWidget(eye_panel)
        layout.addSpacing(12)
        self.side_link = label("●  Local systems ready", "muted")
        layout.addWidget(self.side_link)
        layout.addWidget(label("ODYSSEY  /  EXPEDITION 07", "small"))
        return sidebar

    def _make_playback(self):
        frame = QFrame()
        frame.setObjectName("Panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)
        controls = QHBoxLayout()
        controls.setSpacing(9)
        self.play_button = button("Pause" if self.playing else "Resume")
        self.play_button.setFixedWidth(83)
        self.play_button.clicked.connect(self.toggle_playback)
        controls.addWidget(self.play_button)
        restart = button("Restart")
        restart.clicked.connect(lambda: self.seek(0))
        controls.addWidget(restart)
        self.speed_combo = QComboBox()
        for speed in (1, 5, 10):
            self.speed_combo.addItem(f"{speed}×", speed)
        self.speed_combo.setFixedWidth(73)
        self.speed_combo.currentIndexChanged.connect(lambda: setattr(self, "speed", float(self.speed_combo.currentData())))
        controls.addWidget(self.speed_combo)
        self.loop_check = QCheckBox("Loop")
        controls.addWidget(self.loop_check)
        controls.addStretch()
        controls.addWidget(label("SCENARIO", "small"))
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItem("Jump to an event…", None)
        for scenario in SCENARIOS:
            self.scenario_combo.addItem(scenario["label"], scenario["t"])
        self.scenario_combo.setMinimumWidth(280)
        self.scenario_combo.activated.connect(self._scenario_selected)
        controls.addWidget(self.scenario_combo)
        layout.addLayout(controls)
        timeline = QHBoxLayout()
        self.playback_label = label("PLAYING", "small")
        self.playback_label.setMinimumWidth(68)
        timeline.addWidget(self.playback_label)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, self.source.duration-1)
        self.slider.setValue(int(self.position))
        self.slider.setToolTip("Seek within the 10-minute recording; downlink delay uses real elapsed time")
        self.slider.sliderReleased.connect(lambda: self.seek(self.slider.value()))
        self.slider.valueChanged.connect(self._timeline_changed)
        timeline.addWidget(self.slider, 1)
        self.timeline_label = label("00:00 / 10:00", "muted")
        self.timeline_label.setMinimumWidth(85)
        timeline.addWidget(self.timeline_label)
        layout.addLayout(timeline)
        return frame

    def navigate(self, index):
        if not hasattr(self, "stack"):
            return
        self.stack.setCurrentIndex(index)
        self.nav_buttons[index].setChecked(True)
        self.page_title.setText(self.PAGE_TITLES[index][0])
        self.page_subtitle.setText(self.PAGE_TITLES[index][1])
        if index == 1 and self.detail.crew_id != self.current_crew:
            self.detail.set_crew(self.current_crew)
        if index == 4 and self.companion.crew_id != self.current_crew:
            self.companion.set_crew(self.current_crew)
        self.stack.currentWidget().update_frame(self.frame, self.alerts, self.position)

    def show_crew(self, crew_id):
        self.current_crew = crew_id
        self.detail.set_crew(crew_id)
        self.navigate(1)

    def show_companion(self, crew_id):
        self.current_crew = crew_id
        self.companion.set_crew(crew_id)
        self.navigate(4)

    def toggle_playback(self):
        if self.position >= self.source.duration-1 and not self.playing:
            self.position = 0
        self.playing = not self.playing
        self.last_clock = time.monotonic()
        self.play_button.setText("Pause" if self.playing else "Resume")
        self._refresh(force=True)

    def seek(self, seconds):
        self.position = max(0.0, min(self.source.duration-1, float(seconds)))
        self.last_clock = time.monotonic()
        self._refresh(force=True)

    def _scenario_selected(self, index):
        t = self.scenario_combo.itemData(index)
        if t is not None:
            self.seek(t)

    def _timeline_changed(self, seconds):
        # Drag commits on release; keyboard and track clicks commit immediately.
        if not self.slider.isSliderDown():
            self.seek(seconds)

    def _tick(self):
        now = time.monotonic()
        delta = max(0.0, now-self.last_clock)
        self.last_clock = now
        try:
            self.service.tick(delta)
            if self.playing and not self.slider.isSliderDown():
                self.position += delta*self.speed
                if self.position >= self.source.duration:
                    if self.loop_check.isChecked():
                        self.position %= self.source.duration
                    else:
                        self.position = self.source.duration-1
                        self.playing = False
                        self.play_button.setText("Resume")
                        self.toast.setText("Replay complete · Restart, choose a scenario, or enable Loop to run again.")
            self._refresh()
            if self.service.auto_send and self.playing:
                self.auto_elapsed = self.auto_elapsed + delta if self._auto_was_enabled else 0.0
                if self.auto_elapsed >= 30:
                    self.auto_elapsed %= 30
                    self.send_snapshot()
            else:
                self.auto_elapsed = 0.0
            self._auto_was_enabled = self.service.auto_send
        except (OSError, ValueError, KeyError) as error:
            self.playing = False
            self.play_button.setText("Resume")
            self.timer.stop()
            QMessageBox.critical(self, "HAL2030 update error", f"The update loop stopped safely.\n\n{error}\n\nCheck local files and restart the application.")

    def _refresh(self, force=False):
        second = int(self.position)
        changed = second != self.last_second or force
        if changed:
            self.last_second = second
            self.frame = self.source.frame(second)
            self.alerts = self.engine.evaluate(self.frame)
            self.dashboard.update_frame(self.frame, self.alerts, self.position)
            self._update_alert_banner()
        page = self.stack.currentWidget()
        if self.stack.currentIndex() in (1, 3) or changed:
            page.update_frame(self.frame, self.alerts, self.position)
        self.dashboard.update_link(self.service)
        if not self.slider.isSliderDown():
            self.slider.blockSignals(True)
            self.slider.setValue(second)
            self.slider.blockSignals(False)
        timecode = f"{second//60:02d}:{second%60:02d}"
        self.clock_label.setText(f"MET  {timecode}")
        self.timeline_label.setText(f"{timecode} / 10:00")
        self.playback_label.setText("PLAYING" if self.playing else "PAUSED")
        self.sidebar_eye.set_phase(time.monotonic())
        self.dashboard.eye.set_phase(time.monotonic())
        self.side_link.setText("●  Ground link: simulated" if self.service.connected else "●  Ground link: offline")

    def _update_alert_banner(self):
        self.global_alert.setVisible(bool(self.alerts))
        if not self.alerts:
            return
        alert = sorted(self.alerts, key=lambda a: a.severity != "critical")[0]
        crew = next(c for c in CREW if c["id"] == alert.crew_id)
        color = COLORS["red"] if alert.severity == "critical" else COLORS["amber"]
        self.global_alert.setStyleSheet(f"QPushButton {{ background: #221c28; color: {color}; border: 1px solid {color}; border-radius: 8px; padding: 8px 13px; text-align: left; }} QPushButton:hover {{ background: #322638; }}")
        people = len({a.crew_id for a in self.alerts})
        self.global_alert.setText(f"●  {alert.severity.upper()}   {crew['name']} · {alert.title}     |     Review actions  →" + (f"   ({people} crew need attention)" if people > 1 else ""))

    def _show_priority(self):
        if not self.alerts:
            return
        alert = sorted(self.alerts, key=lambda a: a.severity != "critical")[0]
        crew = next(c for c in CREW if c["id"] == alert.crew_id)
        self.active_dialog = RecommendationDialog(crew, self.alerts, self)
        self.active_dialog.inspect_requested.connect(self.show_crew)
        self.active_dialog.open()

    def send_snapshot(self):
        try:
            packet = self.service.enqueue(self.frame, self.alerts, self.position)
            self.toast.setText(f"{packet['id']} saved locally · {packet['status'].replace('_', ' ')} in the NASA Mission Control simulator.")
            self.mission.update_frame(self.frame, self.alerts, self.position)
            self.dashboard.update_link(self.service)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Snapshot could not be saved", str(error))

    def export_snapshot(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export health snapshot", str(ROOT / "health_snapshot.json"), "JSON files (*.json)")
        if path:
            try:
                self.service.export_snapshot(self.frame, self.alerts, Path(path))
                self.toast.setText(f"Health snapshot exported to {Path(path).name}.")
            except (OSError, ValueError) as error:
                QMessageBox.warning(self, "Export failed", str(error))

    def show_about(self):
        QMessageBox.information(self, "About HAL2030", "HAL2030 · Astronaut Health Console\n\n"
            "NASA Space Apps Challenge 2026 concept prototype.\n"
            "Six fictional crew members · 42 sensor assignments · 10 minutes of synthetic telemetry.\n\n"
            "The app operates locally after installation. ECG, respiration and EEG waveforms are illustrative synthetic signals. "
            "Rule thresholds are demonstration settings, not NASA medical limits. Clinical actions require a crew medical officer.\n\n"
            "Mission Control is a local queue simulator. No NASA endpoint is connected. "
            "HAL2030 voice, local AI, and family archive modes are scripted placeholders. "
            "Family archive replies are always labeled as simulations.\n\n"
            "Sources, architecture, and extension guidance are in README.md and docs/.\n"
            "Ctrl+1…5: navigation · Ctrl+Space: pause / resume.")

    def closeEvent(self, event):
        self.timer.stop()
        try:
            self.service.flush()
        except OSError as error:
            QMessageBox.warning(self, "Queue save warning", str(error))
        super().closeEvent(event)
