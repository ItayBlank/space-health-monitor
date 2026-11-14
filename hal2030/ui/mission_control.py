"""Explicitly simulated store-and-forward telemetry interface."""
from __future__ import annotations

import json
import math
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QHBoxLayout, QHeaderView, QPlainTextEdit, QScrollArea, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from hal2030.ui.theme import COLORS
from hal2030.ui.widgets import MetricTile, Panel, button, label


class MissionControlPage(QWidget):
    """Transport controls remain operable while the replay is paused."""

    send_requested = Signal()
    export_requested = Signal()

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self._last_queue_signature = None
        self._display_packets = []
        self._frame = {}
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(16)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("Ground communications", "heading"))
        subtitle = label("A local outbox, a delayed link, and a simulated ground acknowledgement.", "muted")
        subtitle.setWordWrap(True)
        titles.addWidget(subtitle)
        header.addLayout(titles, 1)
        self.link_badge = label("● SIMULATED LINK AVAILABLE", "body")
        self.link_badge.setStyleSheet(f"color: {COLORS['green']}; font-size: 11px; font-weight: 700;")
        header.addWidget(self.link_badge)
        layout.addLayout(header)

        controls = Panel("GROUND LINK · SIMULATION")
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(14)
        self.connected = QCheckBox("Ground link available")
        self.connected.setChecked(bool(service.connected))
        self.connected.toggled.connect(self._connection_changed)
        self.auto_send = QCheckBox("Auto-send every 30 seconds")
        self.auto_send.setToolTip("Uses elapsed wall-clock time while telemetry replay is running. Manual snapshots also work when paused.")
        self.auto_send.setChecked(bool(service.auto_send))
        self.auto_send.toggled.connect(self._auto_changed)
        self.delay = QComboBox()
        self.delay.setMinimumWidth(190)
        self.delay.addItem("Local demonstration · 3 s", 3)
        self.delay.addItem("Delayed link · 30 s", 30)
        self.delay.addItem("Mars scenario · 22 min", 1320)
        current = self.delay.findData(int(service.latency_s))
        if current >= 0:
            self.delay.setCurrentIndex(current)
        self.delay.currentIndexChanged.connect(self._delay_changed)
        grid.addWidget(self.connected, 0, 0)
        grid.addWidget(self.auto_send, 1, 0)
        grid.addWidget(label("ONE-WAY DELAY", "muted"), 0, 1)
        grid.addWidget(self.delay, 1, 1)
        send = button("Send current telemetry", accent=True)
        send.setMinimumHeight(42)
        send.clicked.connect(self.send_requested.emit)
        export = button("Export snapshot")
        export.clicked.connect(self.export_requested.emit)
        grid.addWidget(send, 0, 2)
        grid.addWidget(export, 1, 2)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 2)
        controls.body.addLayout(grid)
        explanation = label(
            "Packets are saved as JSON on this computer. Link loss keeps them queued. "
            "Acknowledgements are simulated; no NASA service is contacted. The selected delay is a scenario setting, not a fixed Earth–Mars delay.",
            "muted",
        )
        explanation.setWordWrap(True)
        controls.body.addWidget(explanation)
        layout.addWidget(controls)

        stats = QHBoxLayout()
        self.queued = MetricTile("Queued", "packets", COLORS["amber"])
        self.in_transit = MetricTile("In transit", "packets", COLORS["cyan"])
        self.delivered = MetricTile("Simulated received", "packets", COLORS["green"])
        for tile in (self.queued, self.in_transit, self.delivered):
            stats.addWidget(tile)
        layout.addLayout(stats)

        queue_header = QHBoxLayout()
        queue_header.addWidget(label("TELEMETRY OUTBOX", "heading"), 1)
        self.queue_hint = label("No packets sent yet", "muted")
        queue_header.addWidget(self.queue_hint)
        inspect = button("Inspect selected packet")
        inspect.clicked.connect(self._inspect_packet)
        queue_header.addWidget(inspect)
        layout.addLayout(queue_header)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["PACKET", "MISSION TIME", "CREW", "STATUS", "DELIVERY ETA"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellDoubleClicked.connect(lambda *_: self._inspect_packet())
        layout.addWidget(self.table, 1)

        footer = QHBoxLayout()
        included = label("INCLUDED  •  sensor readings, activity, signal state and current alerts", "muted")
        included.setWordWrap(True)
        excluded = label("PRIVATE  •  companion conversations are excluded", "muted")
        excluded.setWordWrap(True)
        footer.addWidget(included, 3)
        footer.addWidget(excluded, 2)
        layout.addLayout(footer)

    def _connection_changed(self, checked):
        if hasattr(self.service, "set_connected"):
            self.service.set_connected(checked)
        else:
            self.service.connected = checked
        self._last_queue_signature = None

    def _auto_changed(self, checked):
        self.service.auto_send = checked

    def _delay_changed(self, *_):
        self.service.latency_s = float(self.delay.currentData())

    def _inspect_packet(self):
        row = self.table.currentRow()
        if row < 0 and self._display_packets:
            row = 0
        if row < 0 or row >= len(self._display_packets):
            dialog = QDialog(self)
            dialog.setWindowTitle("Telemetry outbox")
            box = QVBoxLayout(dialog)
            box.addWidget(label("Send a telemetry snapshot to create the first packet.", "body"))
            close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            close.rejected.connect(dialog.reject)
            box.addWidget(close)
            dialog.exec()
            return
        packet = self._display_packets[row]
        filename = Path(str(packet.get("filename", "")))
        if not filename.is_absolute():
            filename = Path(getattr(self.service, "output_dir", ".")) / filename
        try:
            payload = json.loads(filename.read_text(encoding="utf-8"))
            content = json.dumps(payload, indent=2, ensure_ascii=False)
        except (OSError, ValueError):
            content = json.dumps(packet, indent=2, ensure_ascii=False)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Local packet · {packet['id']}")
        dialog.resize(780, 580)
        body = QVBoxLayout(dialog)
        body.addWidget(label("LOCAL TELEMETRY PACKET · SIMULATED DOWNLINK", "heading"))
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(content)
        text.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        body.addWidget(text, 1)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(dialog.reject)
        body.addWidget(close)
        dialog.exec()

    def update_frame(self, frame, alerts, t):
        self._frame = frame
        available = bool(self.service.connected)
        self.link_badge.setText("● SIMULATED LINK AVAILABLE" if available else "● LINK UNAVAILABLE · QUEUING")
        self.link_badge.setStyleSheet(f"color: {COLORS['green'] if available else COLORS['amber']}; font-size: 11px; font-weight: 700;")
        self.connected.blockSignals(True)
        self.connected.setChecked(available)
        self.connected.blockSignals(False)
        self.auto_send.blockSignals(True)
        self.auto_send.setChecked(bool(self.service.auto_send))
        self.auto_send.blockSignals(False)

        packets = self.service.queue
        self.queued.set_value(str(sum(p.get("status") == "queued" for p in packets)))
        self.in_transit.set_value(str(sum(p.get("status") == "in_transit" for p in packets)))
        self.delivered.set_value(str(sum(p.get("status") == "delivered" for p in packets)))
        self.queue_hint.setText(str(self.service.status_text))
        signature = tuple((p["id"], p.get("status"), math.ceil(float(p.get("eta_s") or 0))) for p in packets)
        if signature == self._last_queue_signature:
            return
        self._last_queue_signature = signature
        selected_id = None
        row = self.table.currentRow()
        if 0 <= row < len(self._display_packets):
            selected_id = self._display_packets[row]["id"]
        self._display_packets = list(reversed(packets[-200:]))
        self.table.setRowCount(len(self._display_packets))
        for row, packet in enumerate(self._display_packets):
            status = packet.get("status", "queued")
            mission = int(packet.get("mission_time", 0))
            eta = math.ceil(max(0, float(packet.get("eta_s") or 0)))
            eta_text = "Received (sim.)" if status == "delivered" else (f"{eta // 60:02d}:{eta % 60:02d}" if status == "in_transit" else "Awaiting link")
            values = [
                str(packet["id"]), f"T+{mission // 60:02d}:{mission % 60:02d}",
                str(packet.get("crew_count", len(frame))),
                {"queued": "QUEUED", "in_transit": "IN TRANSIT · SIM.", "delivered": "RECEIVED · SIM."}.get(status, status),
                eta_text,
            ]
            color = {"queued": COLORS["amber"], "in_transit": COLORS["cyan"], "delivered": COLORS["green"]}.get(status, COLORS["text"])
            for column, value in enumerate(values):
                item = self.table.item(row, column)
                if item is None:
                    item = QTableWidgetItem()
                    self.table.setItem(row, column, item)
                item.setText(value)
                item.setToolTip(str(packet.get("filename", "")))
                if column >= 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QColor(color if column == 3 else COLORS["text"]))
            if packet["id"] == selected_id:
                self.table.selectRow(row)
