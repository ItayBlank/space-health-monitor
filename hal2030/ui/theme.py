"""Central visual tokens for the HAL2030 flight console."""

from PySide6.QtGui import QFont

COLORS = {
    "bg": "#080d15", "panel": "#101824", "card": "#131e2c",
    "border": "#233246", "text": "#edf5ff", "muted": "#8496ad",
    "cyan": "#6be4e8", "green": "#55dfad", "amber": "#f7c469",
    "red": "#ff6a76", "purple": "#b6a0ff",
}
STATUS_COLORS = {
    "nominal": COLORS["green"], "online": COLORS["green"],
    "warning": COLORS["amber"], "no_signal": COLORS["amber"],
    "critical": COLORS["red"], "offline": COLORS["muted"],
}


def apply_theme(app):
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet("""
        QWidget { background: transparent; color: #edf5ff; font-size: 13px; }
        QMainWindow, QDialog { background: #080d15; }
        QLabel { background: transparent; }
        QWidget#Sidebar { background: #0e1520; border-right: 1px solid #233246; }
        QFrame#Panel { background: #101824; border: 1px solid #233246; border-radius: 14px; }
        QFrame#Card { background: #131e2c; border: 1px solid #233246; border-radius: 14px; }
        QPushButton { color: #b7c8dc; background: #172434; border: 1px solid #2a3c51;
            border-radius: 8px; padding: 9px 13px; font-weight: 600; }
        QPushButton:hover { background: #213347; color: #ffffff; border-color: #537083; }
        QPushButton:pressed { background: #2a4054; }
        QPushButton:disabled { color: #60748a; background: #111b28; border-color: #1d2c3e; }
        QPushButton#accent { background: #6be4e8; color: #08232b; border-color: #6be4e8; }
        QPushButton#accent:hover { background: #9bedef; }
        QPushButton#NavButton { text-align: left; padding: 13px 15px; background: transparent;
            border: 1px solid transparent; color: #8f9eb2; font-size: 14px; }
        QPushButton#NavButton:checked { color: #8cebf0; background: #162b39; border: 1px solid #274958; }
        QPushButton#NavButton:hover { color: #edf5ff; background: #162231; }
        QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox { background: #101b29; color: #dbe8f7;
            border: 1px solid #2a3c51; border-radius: 7px; padding: 7px 10px;
            selection-background-color: #28505e; min-height: 19px; }
        QComboBox::drop-down { border: none; width: 24px; }
        QComboBox QAbstractItemView { background: #162231; color: #edf5ff;
            selection-background-color: #28505e; outline: 0; border: 1px solid #31455c; }
        QTextEdit, QPlainTextEdit, QTextBrowser { background: #0d1521; border: 1px solid #233246;
            border-radius: 9px; padding: 10px; selection-background-color: #28505e; }
        QTabWidget::pane { border: 1px solid #233246; border-radius: 8px; background: #101824; }
        QTabBar::tab { padding: 11px 18px; background: #101824; color: #8496ad;
            border-bottom: 2px solid transparent; }
        QTabBar::tab:selected { color: #6be4e8; border-bottom: 2px solid #6be4e8; background: #162535; }
        QTabBar::tab:hover { background: #1b2c3e; }
        QTableWidget, QTableView { background: #101824; alternate-background-color: #131f2d;
            gridline-color: #233246; border: 1px solid #233246; border-radius: 9px;
            selection-background-color: #203d4d; selection-color: #edf5ff; outline: 0; }
        QTableWidget::item, QTableView::item { padding: 7px; border-bottom: 1px solid #1c293b; }
        QHeaderView::section { background: #172333; color: #92a8bf; border: none;
            border-bottom: 1px solid #2c3e53; padding: 10px 7px; font-size: 11px; font-weight: 600; }
        QScrollArea { background: transparent; border: none; }
        QScrollBar:vertical { background: transparent; width: 7px; margin: 3px; }
        QScrollBar::handle:vertical { background: #35485e; border-radius: 3px; min-height: 36px; }
        QScrollBar:horizontal { background: transparent; height: 7px; }
        QScrollBar::handle:horizontal { background: #35485e; border-radius: 3px; min-width: 36px; }
        QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
        QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
        QSlider::groove:horizontal { border: none; height: 4px; background: #233246; border-radius: 2px; }
        QSlider::sub-page:horizontal { background: #6be4e8; border-radius: 2px; }
        QSlider::handle:horizontal { background: #b9f5f5; border: none; width: 12px;
            margin: -4px 0; border-radius: 6px; }
        QCheckBox { spacing: 7px; color: #9cb0c7; }
        QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid #3c566b;
            background: #111d2b; border-radius: 4px; }
        QCheckBox::indicator:checked { background: #6be4e8; border-color: #6be4e8; }
        QProgressBar { border: none; border-radius: 3px; background: #1f3042; text-align: center; }
        QProgressBar::chunk { border-radius: 3px; background: #6be4e8; }
        QToolTip { background: #1a2b3b; color: #edf5ff; border: 1px solid #39566a; padding: 6px; }
        QSplitter::handle { background: #1e2e41; }
        QGroupBox { border: 1px solid #233246; border-radius: 10px; margin-top: 18px; padding: 12px; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 7px; color: #97b3ca; }
        QMessageBox { background: #101824; }
    """)
