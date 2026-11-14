"""Individual crew telemetry, illustrative waveforms and reviewable guidance."""
from __future__ import annotations

from html import escape
from typing import Any

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QHBoxLayout, QLabel, QScrollArea,
    QTextBrowser, QVBoxLayout, QWidget,
)

from hal2030.alerts import crew_status
from hal2030.config import CREW, METRICS
from hal2030.ui.theme import COLORS, STATUS_COLORS
from hal2030.ui.widgets import MetricTile, Panel, Portrait, button, label


def _number(key: str, value: Any) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{METRICS.get(key, {}).get('decimals', 0)}f}"


def _plot(title: str, unit: str, color: str, height: int = 155):
    plot = pg.PlotWidget(background=COLORS["panel"])
    plot.setMinimumHeight(height)
    plot.setMaximumHeight(height + 35)
    plot.setTitle(title, color=COLORS["muted"], size="10pt")
    plot.showGrid(x=True, y=True, alpha=0.15)
    plot.setLabel("left", unit, color=COLORS["muted"])
    plot.setLabel("bottom", "Mission time", units="s", color=COLORS["muted"])
    plot.setMenuEnabled(False)
    plot.setMouseEnabled(x=True, y=False)
    for position in ("left", "bottom"):
        plot.getAxis(position).setPen(pg.mkPen(COLORS["border"]))
        plot.getAxis(position).setTextPen(pg.mkPen(COLORS["muted"]))
    curve = plot.plot(pen=pg.mkPen(color, width=1.6), connect="finite")
    return plot, curve


class DetailPage(QWidget):
    """Scroll-friendly detail page with a persistent crew selector."""

    open_companion = Signal(str)
    open_vision = Signal(str)

    def __init__(self, source, parent=None):
        super().__init__(parent)
        self.source = source
        self.crew_id = CREW[0]["id"]
        self._frame = {}
        self._alerts = []
        self._t = 0.0
        self._last_discrete = None
        self._last_guidance = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(16)

        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("Crew health", "heading"))
        titles.addWidget(label("An individual view of every signal.", "muted"))
        top.addLayout(titles, 1)
        self.selector = QComboBox()
        self.selector.setMinimumWidth(205)
        self.selector.setMinimumHeight(38)
        for crew in CREW:
            self.selector.addItem(crew["name"], crew["id"])
        self.selector.currentIndexChanged.connect(self._select_index)
        top.addWidget(self.selector)
        outer.addLayout(top)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll, 1)
        content = QWidget()
        content.setObjectName("detailContent")
        body = QVBoxLayout(content)
        body.setContentsMargins(0, 0, 8, 8)
        body.setSpacing(14)
        scroll.setWidget(content)

        identity = Panel()
        header = QHBoxLayout()
        self.portrait_holder = QVBoxLayout()
        self.portrait = Portrait(CREW[0], size=78)
        self.portrait_holder.addWidget(self.portrait)
        header.addLayout(self.portrait_holder)
        identity_text = QVBoxLayout()
        self.name_label = label(CREW[0]["name"], "heading")
        self.name_label.setStyleSheet(f"font-size: 23px; font-weight: 700; color: {COLORS['text']};")
        self.role_label = label("", "muted")
        self.activity_label = label("ACTIVE", "body")
        identity_text.addWidget(self.name_label)
        identity_text.addWidget(self.role_label)
        identity_text.addWidget(self.activity_label)
        header.addLayout(identity_text, 1)
        right = QVBoxLayout()
        self.status_label = label("NOMINAL", "body")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.sample_label = label("T+00:00 • 1 Hz telemetry", "muted")
        self.sample_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        companion = button("Open personal HAL2030", accent=True)
        companion.clicked.connect(lambda: self.open_companion.emit(self.crew_id))
        right.addWidget(self.status_label)
        right.addWidget(self.sample_label)
        right.addWidget(companion)
        vision = button("Start vision check")
        vision.clicked.connect(lambda: self.open_vision.emit(self.crew_id))
        right.addWidget(vision)
        header.addLayout(right)
        identity.body.addLayout(header)
        body.addWidget(identity)

        grid = QGridLayout()
        grid.setSpacing(10)
        self.metric_tiles = {}
        self.metric_accents = {}
        definitions = [
            ("heart_rate", "Heart rate", "bpm", "green"),
            ("spo2", "Blood oxygen", "%", "cyan"),
            ("resp_rate", "Respiration", "breaths/min", "purple"),
            ("skin_temp", "Skin temperature", "°C", "amber"),
            ("bp", "Blood pressure", "mmHg", "cyan"),
            ("hrv", "HRV · RMSSD", "ms", "green"),
            ("eeg_alpha", "EEG alpha power", "%", "purple"),
            ("eeg_beta", "EEG beta power", "%", "purple"),
        ]
        for index, (key, title, unit, color) in enumerate(definitions):
            tile = MetricTile(title, unit, COLORS[color])
            tile.setMinimumHeight(88)
            self.metric_tiles[key] = tile
            self.metric_accents[key] = COLORS[color]
            grid.addWidget(tile, index // 4, index % 4)
        body.addLayout(grid)

        waveform_panel = Panel("SIGNAL STRIP")
        note = label("Illustrative synthetic waveforms • rendered from the demonstration scenario, not raw sensor recordings", "muted")
        note.setWordWrap(True)
        waveform_panel.body.addWidget(note)
        wave_grid = QGridLayout()
        wave_grid.setHorizontalSpacing(12)
        self.waveforms = {}
        for index, (kind, title, unit, color) in enumerate([
            ("ecg", "ECG · illustrative", "mV", "green"),
            ("respiration", "Respiration · illustrative", "a.u.", "cyan"),
            ("eeg", "EEG · illustrative", "µV", "purple"),
        ]):
            plot, curve = _plot(title, unit, COLORS[color])
            self.waveforms[kind] = (plot, curve)
            wave_grid.addWidget(plot, 0, index)
        waveform_panel.body.addLayout(wave_grid)
        body.addWidget(waveform_panel)

        lower = QHBoxLayout()
        lower.setSpacing(14)
        trends = Panel("RECENT TRENDS · 60 SECONDS")
        self.trends = {}
        for metric, title, unit, color in [
            ("heart_rate", "Heart rate", "bpm", "green"),
            ("spo2", "Blood oxygen saturation", "%", "cyan"),
        ]:
            plot, curve = _plot(title, unit, COLORS[color], height=125)
            self.trends[metric] = (plot, curve)
            trends.body.addWidget(plot)
        lower.addWidget(trends, 3)

        guidance = Panel("ONBOARD GUIDANCE")
        self.guidance = QTextBrowser()
        self.guidance.setMinimumHeight(270)
        self.guidance.setFrameShape(QTextBrowser.Shape.NoFrame)
        self.guidance.setStyleSheet(f"QTextBrowser {{ background: transparent; border: none; color: {COLORS['text']}; font-size: 12px; }}")
        guidance.body.addWidget(self.guidance, 1)
        disclaimer = label("Demonstration rules • crew medical officer review required before clinical action.", "muted")
        disclaimer.setWordWrap(True)
        guidance.body.addWidget(disclaimer)
        lower.addWidget(guidance, 2)
        body.addLayout(lower)
        body.addStretch(1)
        self._update_identity()

    def _select_index(self, index):
        self.set_crew(self.selector.itemData(index))

    def _update_identity(self):
        crew = next(person for person in CREW if person["id"] == self.crew_id)
        old = self.portrait
        self.portrait = Portrait(crew, size=78)
        self.portrait_holder.replaceWidget(old, self.portrait)
        old.hide()
        old.deleteLater()
        self.name_label.setText(crew["name"])
        self.role_label.setText(f"{crew['role']}  ·  {crew['nationality']}")

    def set_crew(self, crew_id):
        if crew_id not in {crew["id"] for crew in CREW}:
            return
        changed = crew_id != self.crew_id
        self.crew_id = crew_id
        index = self.selector.findData(crew_id)
        self.selector.blockSignals(True)
        self.selector.setCurrentIndex(index)
        self.selector.blockSignals(False)
        if changed:
            self._update_identity()
        self._last_discrete = None
        self._last_guidance = None
        if self._frame:
            self.update_frame(self._frame, self._alerts, self._t)

    def update_frame(self, frame, alerts, t):
        self._frame, self._alerts, self._t = frame, alerts, float(t)
        sample = frame.get(self.crew_id)
        if sample is None:
            return
        discrete = (self.crew_id, int(t), tuple(a.key for a in alerts))
        if discrete != self._last_discrete:
            self._last_discrete = discrete
            status = crew_status(self.crew_id, alerts)
            color = STATUS_COLORS.get(status, COLORS["green"])
            self.portrait.set_status(status)
            self.portrait.set_activity(sample.activity)
            self.status_label.setText({"nominal": "●  NOMINAL", "warning": "●  ATTENTION", "critical": "●  CRITICAL"}.get(status, status.upper()))
            self.status_label.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 13px;")
            self.activity_label.setText(f"{sample.activity.upper()}  ·  CREW {self.crew_id.upper()}")
            self.activity_label.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 11px; font-weight: 600;")
            self.sample_label.setText(f"T+{int(t) // 60:02d}:{int(t) % 60:02d} • 1 Hz telemetry")
            own_alerts = [alert for alert in alerts if alert.crew_id == self.crew_id]
            for metric, tile in self.metric_tiles.items():
                if metric == "bp":
                    sys = sample.values.get("systolic")
                    dia = sample.values.get("diastolic")
                    value = "—" if sys is None or dia is None else f"{sys:.0f}/{dia:.0f}"
                else:
                    value = _number(metric, sample.values.get(metric))
                tile.set_value(value)
                linked = [a for a in own_alerts if a.metric == metric or (metric == "bp" and a.metric in ("systolic", "diastolic"))]
                tile_color = COLORS["red"] if any(a.severity == "critical" for a in linked) else (
                    COLORS["amber"] if linked or value == "—" else self.metric_accents[metric]
                )
                tile.value.setStyleSheet(f"font-size: 27px; font-weight: 600; color: {tile_color};")
            guidance_key = tuple((a.key, a.severity, a.title, a.recommendation) for a in own_alerts)
            if guidance_key != self._last_guidance:
                self._last_guidance = guidance_key
                if not own_alerts:
                    self.guidance.setHtml(
                        f"<h3 style='color:{COLORS['green']}'>All available signals are within demo limits.</h3>"
                        "<p>Continue the scheduled activity. HAL2030 will highlight a change in vital signs or signal availability.</p>"
                        "<p>Activity context is used by the demonstration rules: an increased heart rate during exercise is evaluated differently from a resting reading.</p>"
                        "<p style='color:#8494aa'>EEG powers are relative scenario features; they do not diagnose cognitive or emotional state.</p>"
                    )
                else:
                    sections = []
                    for alert in own_alerts:
                        tone = COLORS["red"] if alert.severity == "critical" else COLORS["amber"]
                        steps = "".join(f"<li>{escape(str(step))}</li>" for step in alert.steps)
                        sections.append(
                            f"<h3 style='color:{tone}'>{escape(alert.title)}</h3>"
                            f"<p>{escape(alert.recommendation)}</p><ol>{steps}</ol>"
                        )
                    self.guidance.setHtml("".join(sections))
            for metric, (plot, curve) in self.trends.items():
                xs, ys = self.source.history(self.crew_id, metric, int(t), seconds=60)
                curve.setData(xs, ys)
                plot.setXRange(max(0, float(t) - 60), max(60, float(t)), padding=0)

        for kind, (plot, curve) in self.waveforms.items():
            xs, ys = self.source.waveform(self.crew_id, kind, float(t), seconds=8, fs=100)
            curve.setData(xs, ys)
            plot.setXRange(max(0, float(t) - 8), max(8, float(t)), padding=0)
