"""Reusable painted instruments and compact console components."""

import math
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import (QColor, QPainter, QPainterPath, QPen, QPixmap,
                          QRadialGradient, QLinearGradient, QFont)
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton,
                               QVBoxLayout, QHBoxLayout, QSizePolicy)

from .theme import COLORS, STATUS_COLORS


def label(text, style="body"):
    w = QLabel(str(text))
    styles = {
        "body": "font-size: 13px; color: #c0cfdf;",
        "muted": "font-size: 12px; color: #8496ad;",
        "small": "font-size: 10px; color: #8496ad; letter-spacing: 1px;",
        "title": "font-size: 29px; font-weight: 700; color: #edf5ff;",
        "heading": "font-size: 18px; font-weight: 600; color: #edf5ff;",
        "section": "font-size: 11px; font-weight: 700; color: #91a9c2; letter-spacing: 1.5px;",
        "value": "font-size: 30px; font-weight: 600; color: #edf5ff;",
    }
    w.setStyleSheet(styles.get(style, styles["body"]))
    return w


def button(text, accent=False):
    w = QPushButton(text)
    if accent:
        w.setObjectName("accent")
    w.setCursor(Qt.CursorShape.PointingHandCursor)
    return w


def format_value(key, value):
    if value is None:
        return "—"
    try:
        if not math.isfinite(float(value)):
            return "—"
        from hal2030.config import METRICS
        digits = METRICS.get(key, {}).get("decimals", 0)
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


class Panel(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(12)
        if title:
            self.body.addWidget(label(title.upper(), "section"))


class StatusChip(QLabel):
    def __init__(self, text="NOMINAL", status="nominal", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.set_status(status, text)

    def set_status(self, status, text=None):
        if text is not None:
            self.setText(text)
        c = STATUS_COLORS.get(status, COLORS["muted"])
        self.setStyleSheet(f"color: {c}; background: {QColor(c).darker(480).name()};"
                          f"border: 1px solid {QColor(c).darker(280).name()};"
                          "border-radius: 6px; padding: 4px 8px; font-size: 10px; font-weight: 700;")


class Portrait(QWidget):
    clicked = Signal()

    def __init__(self, crew, size=64, parent=None):
        super().__init__(parent)
        self.crew = crew
        self.status = "nominal"
        self.activity = ""
        self.phase = 0.0
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Open {crew.get('name', 'crew member')}'s profile")
        self.setAccessibleName(f"{crew.get('name', '')} portrait")
        from hal2030.config import ROOT
        raw = Path(crew.get("portrait", ""))
        candidates = [ROOT / raw, ROOT / "assets" / "portraits" / raw,
                      ROOT / "assets" / "portraits" / f"{crew['id']}.png"]
        self.pixmap = QPixmap()
        for candidate in candidates:
            if candidate.is_file():
                self.pixmap = QPixmap(str(candidate))
                break

    def set_status(self, status):
        if self.status != status:
            self.status = status
            self.update()

    def set_phase(self, phase):
        self.phase = phase
        if self.status == "critical":
            self.update()

    def set_activity(self, activity):
        """Show a small activity badge in the portrait's upper corner."""
        if self.activity != activity:
            self.activity = str(activity)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = min(self.width(), self.height())
        ring = QColor(STATUS_COLORS.get(self.status, COLORS["muted"]))
        p.setPen(QPen(QColor(ring.red(), ring.green(), ring.blue(), 35), 8))
        p.drawEllipse(QRectF(5, 5, s-10, s-10))
        p.setPen(QPen(ring, 2.4 if self.status != "critical" else 3.3))
        p.drawEllipse(QRectF(5, 5, s-10, s-10))
        inner = QRectF(10, 10, s-20, s-20)
        path = QPainterPath()
        path.addEllipse(inner)
        p.save()
        p.setClipPath(path)
        if not self.pixmap.isNull():
            # Center crop at draw time; the original generated asset is unchanged.
            w, h = self.pixmap.width(), self.pixmap.height()
            side = min(w, h)
            p.drawPixmap(inner, self.pixmap, QRectF((w-side)/2, (h-side)/2, side, side))
        else:
            g = QLinearGradient(0, 0, s, s)
            g.setColorAt(0, QColor("#254458"))
            g.setColorAt(1, QColor("#111c2a"))
            p.fillRect(inner, g)
            p.setPen(QColor("#cce7ef"))
            font = QFont("Segoe UI", max(10, int(s*.22)))
            font.setWeight(QFont.Weight.DemiBold)
            p.setFont(font)
            initials = "".join(x[0] for x in self.crew.get("name", "?").split()[:2])
            p.drawText(inner, Qt.AlignmentFlag.AlignCenter, initials)
        p.restore()
        if self.activity:
            short = {"Working": "WORK", "Sleeping": "SLEEP", "Moving": "MOVE",
                     "Resting": "REST", "Exercise": "EXER.", "Maintenance": "MAINT."}.get(self.activity, self.activity[:5].upper())
            badge_width = min(s-10, 38 if s < 80 else 48)
            badge = QRectF(s-badge_width, 0, badge_width, 13 if s < 80 else 17)
            p.setPen(QPen(QColor("#39516b"), .8))
            p.setBrush(QColor("#182839"))
            p.drawRoundedRect(badge, 3, 3)
            f = QFont("Segoe UI")
            f.setPixelSize(7 if s < 80 else 9)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor("#c2d8e8"))
            p.drawText(badge, Qt.AlignmentFlag.AlignCenter, short)
        p.end()


class HalEye(QWidget):
    """Original code-drawn optical lens, inspired by retro spacecraft consoles."""

    def __init__(self, size=100, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.phase = 0.0
        self.active = True
        self.setAccessibleName("HAL2030 red optical lens")

    def set_phase(self, phase):
        self.phase = phase
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = min(self.width(), self.height())
        p.translate(self.width()/2, self.height()/2)
        r = s*.44
        glow = QRadialGradient(0, 0, s*.51)
        glow.setColorAt(0, QColor(255, 62, 35, 90))
        glow.setColorAt(.65, QColor(200, 40, 22, 35))
        glow.setColorAt(1, QColor(100, 10, 5, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QPointF(0, 0), s*.51, s*.51)
        p.setBrush(QColor("#04070b"))
        p.setPen(QPen(QColor("#526071"), s*.022))
        p.drawEllipse(QPointF(0, 0), r, r)
        p.setPen(QPen(QColor("#182534"), s*.043))
        p.drawEllipse(QPointF(0, 0), r*.87, r*.87)
        lens = QRadialGradient(-r*.15, -r*.15, r*.85)
        lens.setColorAt(0, QColor("#fd9b62"))
        lens.setColorAt(.14, QColor("#ff4c34"))
        lens.setColorAt(.3, QColor("#b21c18"))
        lens.setColorAt(.5, QColor("#3b1014"))
        lens.setColorAt(.72, QColor("#090e17"))
        lens.setColorAt(1, QColor("#751c23"))
        p.setBrush(lens)
        p.setPen(QPen(QColor("#b14542"), 1.2))
        p.drawEllipse(QPointF(0, 0), r*.75, r*.75)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for factor, alpha in [(.62, 45), (.49, 60), (.32, 90)]:
            p.setPen(QPen(QColor(255, 92, 64, alpha), 1))
            p.drawEllipse(QPointF(0, 0), r*factor, r*factor)
        core = QRadialGradient(0, 0, r*.27)
        core.setColorAt(0, QColor("#fff6ca"))
        core.setColorAt(.35, QColor("#ffcca1"))
        core.setColorAt(.65, QColor("#ff6142"))
        core.setColorAt(1, QColor(255, 45, 30, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(core)
        pulse = .97 + .035*math.sin(self.phase*1.8)
        p.drawEllipse(QPointF(0, 0), r*.27*pulse, r*.27*pulse)
        p.setPen(QPen(QColor(208, 234, 255, 75), max(1, s*.018)))
        p.drawArc(QRectF(-r*.64, -r*.64, r*1.28, r*1.28), 40*16, 56*16)
        p.end()


class MetricTile(QFrame):
    def __init__(self, title, unit="", accent=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.unit = unit
        self.accent = accent or COLORS["text"]
        box = QVBoxLayout(self)
        box.setContentsMargins(16, 12, 16, 12)
        box.setSpacing(5)
        box.addWidget(label(title.upper(), "small"))
        row = QHBoxLayout()
        self.value = label("—", "value")
        self.value.setStyleSheet(f"font-size: 27px; font-weight: 600; color: {self.accent};")
        row.addWidget(self.value)
        self.unit_label = label(unit, "muted")
        row.addWidget(self.unit_label, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch()
        box.addLayout(row)

    def set_value(self, value, suffix=""):
        self.value.setText("—" if value is None else str(value))
        self.unit_label.setText(suffix or self.unit)


class Sparkline(QWidget):
    def __init__(self, color=None, parent=None):
        super().__init__(parent)
        self.color = color or COLORS["green"]
        self.values = []
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(40)

    def set_values(self, values, color=None):
        self.values = list(values)
        if color:
            self.color = color
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        p.setPen(QPen(QColor("#223348"), 1))
        p.drawLine(0, height-4, width, height-4)
        valid = [float(v) for v in self.values if v is not None and math.isfinite(float(v))]
        if not valid:
            p.setPen(QColor(COLORS["muted"]))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No signal")
            p.end()
            return
        lo, hi = min(valid)-3, max(valid)+3
        path = QPainterPath()
        connected = False
        n = len(self.values)
        for i, v in enumerate(self.values):
            if v is None or not math.isfinite(float(v)):
                connected = False
                continue
            x = 2+(width-4)*i/max(1, n-1)
            y = height-6-(height-12)*(float(v)-lo)/(hi-lo)
            if connected:
                path.lineTo(x, y)
            else:
                path.moveTo(x, y)
            connected = True
        p.setPen(QPen(QColor(self.color), 1.8))
        p.drawPath(path)
        p.end()
