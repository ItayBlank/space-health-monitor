"""Sensor inventory: ownership, availability, signal age and alert severity."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from hal2030.alerts import sensor_status
from hal2030.config import CREW, METRICS, SENSORS
from hal2030.ui.theme import COLORS, STATUS_COLORS
from hal2030.ui.widgets import MetricTile, label


class SensorsPage(QWidget):
    """Stable inventory rows; refreshing never recreates the table or its scroll."""

    select_crew = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._frame = {}
        self._alerts = []
        self._t = 0.0
        self._last_update = None
        self._last_seen = {}
        self._row_status = {}
        self._previous_t = -1
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(label("Sensor registry", "heading"))
        subtitle = label("42 wearable channels across six crew members. Double-click a row to inspect its astronaut.", "muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        counts = QHBoxLayout()
        self.streaming = MetricTile("Sensors streaming", "of 42", COLORS["green"])
        self.missing = MetricTile("No signal", "channels", COLORS["amber"])
        self.critical = MetricTile("Critical readings", "channels", COLORS["red"])
        for tile in (self.streaming, self.missing, self.critical):
            counts.addWidget(tile)
        layout.addLayout(counts)

        filters = QHBoxLayout()
        filters.addWidget(label("VIEW", "muted"))
        self.crew_filter = QComboBox()
        self.crew_filter.setMinimumWidth(185)
        self.crew_filter.addItem("All crew members", "all")
        for crew in CREW:
            self.crew_filter.addItem(crew["name"], crew["id"])
        self.state_filter = QComboBox()
        self.state_filter.setMinimumWidth(190)
        for title, key in [("All states", "all"), ("Online / nominal", "nominal"), ("Attention / no signal", "warning"), ("Critical readings", "critical")]:
            self.state_filter.addItem(title, key)
        self.crew_filter.currentIndexChanged.connect(self._filter)
        self.state_filter.currentIndexChanged.connect(self._filter)
        filters.addWidget(self.crew_filter)
        filters.addWidget(self.state_filter)
        filters.addStretch(1)
        self.time_label = label("T+00:00", "muted")
        filters.addWidget(self.time_label)
        layout.addLayout(filters)

        self.table = QTableWidget(len(CREW) * len(SENSORS), 7)
        self.table.setHorizontalHeaderLabels(["ASTRONAUT", "SENSOR / CHANNEL", "PLACEMENT", "LATEST READING", "STATE", "QUALITY", "SAMPLE AGE"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(49)
        self.table.horizontalHeader().setMinimumSectionSize(55)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for col, width in enumerate([135, 180, 130, 210, 115, 75, 90]):
            self.table.setColumnWidth(col, width)
        self._rows = []
        for crew in CREW:
            for sensor in SENSORS:
                row = len(self._rows)
                self._rows.append((crew, sensor))
                values = [crew["name"], sensor["name"], sensor["placement"], "—", "WAITING", "—", "—"]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.ItemDataRole.UserRole, crew["id"])
                    if column >= 4:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, column, item)
                self.table.item(row, 1).setToolTip(f"Acquisition specification: {sensor['sample_rate']}\nReplay summary rate: 1 Hz")
        self.table.cellDoubleClicked.connect(lambda row, _: self.select_crew.emit(self._rows[row][0]["id"]))
        layout.addWidget(self.table, 1)
        legend = label("● GREEN  streaming / nominal     ● AMBER  attention or missing signal     ● RED  critical parameter     • Missing readings remain blank.", "muted")
        legend.setWordWrap(True)
        layout.addWidget(legend)

    def _filter(self, *_):
        selected_crew = self.crew_filter.currentData()
        selected_state = self.state_filter.currentData()
        for row, (crew, _) in enumerate(self._rows):
            show = selected_crew in ("all", crew["id"]) and selected_state in ("all", self._row_status.get(row, "nominal"))
            self.table.setRowHidden(row, not show)

    def update_frame(self, frame, alerts, t):
        self._frame, self._alerts, self._t = frame, alerts, float(t)
        current = (int(t), tuple((a.key, a.severity) for a in alerts))
        if current == self._last_update:
            return
        self._last_update = current
        if t < self._previous_t:
            self._last_seen.clear()
        self._previous_t = t
        self.time_label.setText(f"T+{int(t) // 60:02d}:{int(t) % 60:02d} · 1 Hz summary")
        missing = critical = streaming = 0
        for row, (crew, sensor) in enumerate(self._rows):
            sample = frame.get(crew["id"])
            if sample is None:
                continue
            sensor_id = sensor["id"]
            connected = sample.sensor_status.get(sensor_id) == "online"
            state = sensor_status(crew["id"], sensor_id, frame, alerts)
            self._row_status[row] = state
            color = STATUS_COLORS.get(state, COLORS["muted"])
            if connected:
                streaming += 1
                self._last_seen[row] = int(t)
            else:
                missing += 1
            if state == "critical":
                critical += 1
            status_text = "NO SIGNAL" if not connected else {"nominal": "ONLINE", "warning": "ATTENTION", "critical": "CRITICAL"}.get(state, state.upper())
            self.table.item(row, 4).setText(f"● {status_text}")
            self.table.item(row, 4).setForeground(QColor(color))
            self.table.item(row, 0).setForeground(QColor(COLORS["text"]))
            self.table.item(row, 3).setForeground(QColor(color if state != "nominal" else COLORS["text"]))
            parts = []
            for key in sensor["metrics"]:
                value = sample.values.get(key) if connected else None
                if value is not None:
                    definition = METRICS.get(key, {})
                    decimals = definition.get("decimals", 0)
                    unit = definition.get("unit", "")
                    short = {"eeg_alpha": "α", "eeg_beta": "β", "hrv": "HRV", "systolic": "SYS", "diastolic": "DIA"}.get(key, "")
                    parts.append(f"{short + ' ' if short else ''}{float(value):.{decimals}f} {unit}".strip())
            self.table.item(row, 3).setText("  /  ".join(parts) if parts else "—")
            quality = float(sample.signal_quality)
            if quality <= 1:
                quality *= 100
            self.table.item(row, 5).setText(f"{quality:.0f}%" if connected else "—")
            self.table.item(row, 5).setToolTip("Scenario signal-quality estimate for this crew sample; not independently measured per sensor.")
            last_seen = self._last_seen.get(row)
            self.table.item(row, 6).setText("0 s" if connected else (f"{int(t) - last_seen} s" if last_seen is not None else "Unknown"))
            self.table.item(row, 6).setToolTip("Time since this application last observed a valid sample. Seeking may reset this estimate.")
        self.streaming.set_value(str(streaming))
        self.missing.set_value(str(missing))
        self.critical.set_value(str(critical))
        self._filter()
