"""Fleet overview with live crew cards and a prominent actionable watch panel."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QScrollArea, QDialog, QDialogButtonBox)

from hal2030.config import CREW, SENSORS
from hal2030.alerts import crew_status
from .theme import COLORS, STATUS_COLORS
from .widgets import (label, button, Panel, Portrait, MetricTile, Sparkline,
                      HalEye, StatusChip, format_value)


class RecommendationDialog(QDialog):
    inspect_requested = Signal(str)

    def __init__(self, crew, alerts, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"HAL2030 · {crew['name']} · Recommended actions")
        self.resize(650, 570)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 22)
        layout.setSpacing(16)
        header = QHBoxLayout()
        portrait = Portrait(crew, 92)
        portrait.set_status(crew_status(crew["id"], alerts))
        header.addWidget(portrait)
        title = QVBoxLayout()
        title.addWidget(label(crew["name"], "title"))
        title.addWidget(label("ONBOARD ACTION CARD", "section"))
        header.addLayout(title)
        header.addStretch()
        layout.addLayout(header)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        box = QVBoxLayout(content)
        box.setContentsMargins(0, 0, 5, 0)
        relevant = [a for a in alerts if a.crew_id == crew["id"]]
        if not relevant:
            box.addWidget(label("All monitored values are within demonstration limits.", "body"))
        for alert in relevant:
            panel = Panel()
            row = QHBoxLayout()
            row.addWidget(StatusChip(alert.severity.upper(), alert.severity))
            row.addStretch()
            panel.body.addLayout(row)
            headline = label(alert.title, "heading")
            headline.setWordWrap(True)
            panel.body.addWidget(headline)
            recommendation = label(alert.recommendation)
            recommendation.setWordWrap(True)
            panel.body.addWidget(recommendation)
            for i, step in enumerate(alert.steps, 1):
                line = label(f"{i:02d}   {step}")
                line.setWordWrap(True)
                panel.body.addWidget(line)
            box.addWidget(panel)
        box.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        note = label("Demonstration decision support · Confirm readings and follow the crew medical officer's protocol.", "muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        actions = QHBoxLayout()
        close = button("Close")
        close.clicked.connect(self.accept)
        inspect = button("Open crew detail  →", True)
        inspect.clicked.connect(lambda: (self.inspect_requested.emit(crew["id"]), self.accept()))
        actions.addWidget(close)
        actions.addStretch()
        actions.addWidget(inspect)
        layout.addLayout(actions)


class CrewCard(QFrame):
    selected = Signal(str)
    actions_requested = Signal(str)

    def __init__(self, crew, source, parent=None):
        super().__init__(parent)
        self.crew, self.source = crew, source
        self.setObjectName("Card")
        self.setMinimumWidth(215)
        self.setMinimumHeight(249)
        self.last_second = None
        self.current_status = None
        box = QVBoxLayout(self)
        box.setContentsMargins(15, 12, 15, 12)
        box.setSpacing(7)
        top = QHBoxLayout()
        self.portrait = Portrait(crew, 62)
        self.portrait.clicked.connect(lambda: self.selected.emit(crew["id"]))
        top.addWidget(self.portrait)
        identity = QVBoxLayout()
        identity.setSpacing(3)
        name = label(crew["name"], "heading")
        name.setStyleSheet("font-size: 16px; font-weight: 650; color: #edf5ff;")
        identity.addWidget(name)
        identity.addWidget(label(crew["role"], "muted"))
        top.addLayout(identity, 1)
        box.addLayout(top)
        status_row = QHBoxLayout()
        self.status = StatusChip()
        self.activity = label("ACTIVE", "small")
        self.activity.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        status_row.addWidget(self.status)
        status_row.addStretch()
        status_row.addWidget(self.activity)
        box.addLayout(status_row)
        metrics = QGridLayout()
        metrics.setVerticalSpacing(2)
        metrics.setHorizontalSpacing(12)
        self.values = {}
        for i, (key, title, unit) in enumerate([
            ("heart_rate", "HEART RATE", "bpm"),
            ("spo2", "SpO₂", "%"),
            ("resp_rate", "BREATHING", "/min"),
        ]):
            metrics.addWidget(label(title, "small"), 0, i)
            self.values[key] = label("—", "value")
            self.values[key].setStyleSheet("font-size: 24px; font-weight: 600; color: #e6f2ff;")
            metrics.addWidget(self.values[key], 1, i)
            metrics.addWidget(label(unit, "muted"), 2, i)
        box.addLayout(metrics)
        self.spark = Sparkline()
        self.spark.setToolTip("Heart-rate trend · latest 60 seconds · from the CSV replay")
        box.addWidget(self.spark)
        bottom = QHBoxLayout()
        self.sensor_hint = label("7 / 7 sensors", "muted")
        bottom.addWidget(self.sensor_hint)
        bottom.addStretch()
        self.open_button = button("View  →")
        self.open_button.setStyleSheet("QPushButton { background: transparent; border: none; color: #6be4e8; padding: 3px 0; font-size: 12px; } QPushButton:hover { color: #d1ffff; }")
        self.open_button.clicked.connect(lambda: self.selected.emit(crew["id"]))
        bottom.addWidget(self.open_button)
        box.addLayout(bottom)

    def update_sample(self, sample, alerts, t):
        status = crew_status(self.crew["id"], alerts)
        self.portrait.set_status(status)
        self.portrait.set_activity(sample.activity)
        self.portrait.set_phase(float(t))
        if status != self.current_status:
            self.current_status = status
            color = STATUS_COLORS[status]
            border = "#233246" if status == "nominal" else color
            self.setStyleSheet(f"QFrame#Card {{ background: #131e2c; border: 1px solid {border}; border-radius: 14px; }}")
            self.status.set_status(status, {"nominal": "NOMINAL", "warning": "ATTENTION", "critical": "CRITICAL"}[status])
        self.activity.setText(sample.activity.upper())
        for key, w in self.values.items():
            w.setText(format_value(key, sample.values.get(key)))
            metric_status = next((a.severity for a in alerts if a.crew_id == self.crew["id"] and a.metric == key), "nominal")
            c = STATUS_COLORS[metric_status] if metric_status != "nominal" else COLORS["text"]
            w.setStyleSheet(f"font-size: 24px; font-weight: 600; color: {c};")
        online = sum(s == "online" for s in sample.sensor_status.values())
        self.sensor_hint.setText(f"{online} / {len(SENSORS)} sensors")
        if self.last_second != int(t):
            self.last_second = int(t)
            _, values = self.source.history(self.crew["id"], "heart_rate", int(t), seconds=60)
            self.spark.set_values(values, STATUS_COLORS[status])


class DashboardPage(QWidget):
    select_crew = Signal(str)
    select_sensors = Signal()
    select_companion = Signal(str)
    send_requested = Signal()

    def __init__(self, source, parent=None):
        super().__init__(parent)
        self.source = source
        self.alerts = []
        self.frame = {}
        self.watch_id = None
        self.dialog = None
        self.event_log = []
        self.previous_keys = set()
        self.last_t = -1
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 3, 0)
        layout.setSpacing(16)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.tiles = {}
        for name, title, unit, color in [
            ("crew", "CREW MONITORED", "aboard", COLORS["cyan"]),
            ("nominal", "WITHIN DEMO LIMITS", "crew", COLORS["green"]),
            ("attention", "NEED ATTENTION", "crew", COLORS["amber"]),
            ("sensors", "SENSOR STREAMS", "/ 42 online", COLORS["cyan"]),
        ]:
            tile = MetricTile(title, unit, color)
            self.tiles[name] = tile
            stats.addWidget(tile, 1)
        layout.addLayout(stats)

        main = QHBoxLayout()
        main.setSpacing(16)
        left = QVBoxLayout()
        left.setSpacing(12)
        section = QHBoxLayout()
        section.addWidget(label("CREW VITALS", "section"))
        section.addStretch()
        section.addWidget(label("●  1 Hz replay", "muted"))
        left.addLayout(section)
        grid = QGridLayout()
        grid.setSpacing(12)
        self.cards = {}
        for i, crew in enumerate(CREW):
            card = CrewCard(crew, source)
            card.selected.connect(self.select_crew.emit)
            card.actions_requested.connect(self.show_recommendations)
            self.cards[crew["id"]] = card
            grid.addWidget(card, i//3, i%3)
        left.addLayout(grid)
        context = Panel()
        context.body.setContentsMargins(16, 12, 16, 12)
        cabin = QHBoxLayout()
        cabin.addWidget(label("CABIN", "section"))
        cabin.addStretch()
        self.cabin_co2 = label("CO₂   — ppm")
        self.cabin_temp = label("AIR   — °C")
        self.elapsed = label("00:00 / 10:00", "muted")
        cabin.addWidget(self.cabin_co2)
        cabin.addSpacing(20)
        cabin.addWidget(self.cabin_temp)
        cabin.addStretch()
        cabin.addWidget(self.elapsed)
        context.body.addLayout(cabin)
        left.addWidget(context)
        left.addStretch()
        main.addLayout(left, 3)

        right = QVBoxLayout()
        right.setSpacing(12)
        watch = Panel("Priority watch")
        watch.setMinimumWidth(236)
        watch.setMaximumWidth(310)
        self.watch_panel = watch
        self.watch_tag = StatusChip("CREW STABLE", "nominal")
        watch.body.addWidget(self.watch_tag, 0, Qt.AlignmentFlag.AlignLeft)
        self.eye = HalEye(98)
        watch.body.addWidget(self.eye, 0, Qt.AlignmentFlag.AlignHCenter)
        self.watch_portraits = {}
        for crew in CREW:
            portrait = Portrait(crew, 104)
            portrait.hide()
            portrait.clicked.connect(lambda cid=crew["id"]: self.show_recommendations(cid))
            self.watch_portraits[crew["id"]] = portrait
            watch.body.addWidget(portrait, 0, Qt.AlignmentFlag.AlignHCenter)
        self.watch_name = label("All crew accounted for", "heading")
        self.watch_name.setWordWrap(True)
        self.watch_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        watch.body.addWidget(self.watch_name)
        self.watch_text = label("HAL2030 is monitoring the incoming telemetry.")
        self.watch_text.setWordWrap(True)
        self.watch_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        watch.body.addWidget(self.watch_text)
        self.action_button = button("No action required")
        self.action_button.clicked.connect(lambda: self.show_recommendations(self.watch_id) if self.watch_id else None)
        self.action_button.setEnabled(False)
        watch.body.addWidget(self.action_button)
        self.alert_selector = QVBoxLayout()
        self.alert_selector.setSpacing(5)
        watch.body.addLayout(self.alert_selector)
        right.addWidget(watch)

        events = Panel("Recent events")
        self.event_labels = []
        for _ in range(3):
            w = label("", "muted")
            w.setWordWrap(True)
            events.body.addWidget(w)
            self.event_labels.append(w)
        self.event_labels[0].setText("00:00  Telemetry replay initialized")
        right.addWidget(events)
        link = Panel()
        link.body.setContentsMargins(16, 13, 16, 13)
        link.body.addWidget(label("GROUND LINK", "section"))
        self.link_status = label("●  Simulated link available", "muted")
        self.link_status.setWordWrap(True)
        link.body.addWidget(self.link_status)
        send = button("Send health snapshot  ↗")
        send.clicked.connect(self.send_requested.emit)
        link.body.addWidget(send)
        right.addWidget(link)
        right.addStretch()
        main.addLayout(right, 1)
        layout.addLayout(main)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        self._alert_signature = None

    def update_link(self, service):
        pending = sum(p["status"] != "delivered" for p in service.queue)
        if service.connected:
            self.link_status.setText(f"●  Simulated link available\n{pending} packet(s) pending")
        else:
            self.link_status.setText(f"●  Link offline · buffering\n{pending} packet(s) pending")

    def update_frame(self, frame, alerts, t):
        self.frame, self.alerts = frame, alerts
        statuses = {c["id"]: crew_status(c["id"], alerts) for c in CREW}
        self.tiles["crew"].set_value(len(frame))
        self.tiles["nominal"].set_value(sum(s == "nominal" for s in statuses.values()))
        self.tiles["attention"].set_value(sum(s != "nominal" for s in statuses.values()))
        self.tiles["sensors"].set_value(sum(v == "online" for s in frame.values() for v in s.sensor_status.values()))
        for cid, card in self.cards.items():
            if cid in frame:
                card.update_sample(frame[cid], alerts, t)
        first = next(iter(frame.values()), None)
        if first:
            self.cabin_co2.setText(f"CO₂   {first.cabin_co2:.0f} ppm")
            self.cabin_temp.setText(f"AIR   {first.cabin_temp:.1f} °C")
        self.elapsed.setText(f"{int(t)//60:02d}:{int(t)%60:02d} / 10:00")
        self.eye.set_phase(float(t))
        self._update_watch(alerts, statuses, t)

    def _update_watch(self, alerts, statuses, t):
        ordered = sorted(alerts, key=lambda a: (a.severity != "critical"))
        highest = ordered[0] if ordered else None
        cid = highest.crew_id if highest else None
        self.watch_id = cid
        self.eye.setVisible(cid is None)
        for pid, portrait in self.watch_portraits.items():
            portrait.setVisible(pid == cid)
            portrait.set_status(statuses[pid])
            if pid in self.frame:
                portrait.set_activity(self.frame[pid].activity)
            portrait.set_phase(float(t))
        if highest:
            crew = next(c for c in CREW if c["id"] == cid)
            self.watch_tag.set_status(highest.severity, "ACTION REQUIRED" if highest.severity == "critical" else "CHECK REQUESTED")
            self.watch_name.setText(crew["name"])
            self.watch_text.setText(highest.title)
            self.action_button.setEnabled(True)
            self.action_button.setText("Review actions  →")
        else:
            self.watch_tag.set_status("nominal", "CREW STABLE")
            self.watch_name.setText("All crew accounted for")
            self.watch_text.setText("HAL2030 is monitoring the incoming telemetry.")
            self.action_button.setText("No action required")
            self.action_button.setEnabled(False)
        signature = tuple(a.key for a in ordered)
        if signature != self._alert_signature:
            self._alert_signature = signature
            while self.alert_selector.count():
                item = self.alert_selector.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            other_ids = list(dict.fromkeys(a.crew_id for a in ordered if a.crew_id != cid))
            for other_id in other_ids:
                name = next(c["name"] for c in CREW if c["id"] == other_id)
                b = button(f"Also review: {name}")
                b.clicked.connect(lambda checked=False, person=other_id: self.show_recommendations(person))
                self.alert_selector.addWidget(b)
        keys = set(signature)
        if int(t) < self.last_t:
            self.event_log.clear()
            self.previous_keys.clear()
        self.last_t = int(t)
        for alert in ordered:
            if alert.key not in self.previous_keys:
                name = next(c["name"] for c in CREW if c["id"] == alert.crew_id)
                self.event_log.append(f"{int(t)//60:02d}:{int(t)%60:02d}  {name}: {alert.title}")
        if self.previous_keys - keys:
            self.event_log.append(f"{int(t)//60:02d}:{int(t)%60:02d}  Earlier alert cleared by telemetry")
        self.previous_keys = keys
        self.event_log = self.event_log[-12:]
        for i, w in enumerate(self.event_labels):
            latest = self.event_log[-3:][::-1]
            w.setText(latest[i] if i < len(latest) else ("Monitoring all seven sensor types." if i == 0 else ""))

    def show_recommendations(self, crew_id):
        if not crew_id:
            return
        crew = next(c for c in CREW if c["id"] == crew_id)
        self.dialog = RecommendationDialog(crew, self.alerts, self)
        self.dialog.inspect_requested.connect(self.select_crew.emit)
        self.dialog.open()
