from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QFrame
)
import theme
from widgets.status import StatusLabel


class ScanPage(QWidget):
    stop_requested = Signal()

    def __init__(self):
        super().__init__()

        self.faces = [] #faces being scanned
        self.radiation_level = None

        self.button_style = f"""
            QPushButton {{
                background-color: {theme.BUTTON_PRIMARY};
                color: {theme.TEXT_PRIMARY};
                font-family: {theme.FONT_FAMILY};
                font-size: {theme.FONT_SIZE_BUTTON};
                border: none;
                border-radius: 14px;
            }}
            QPushButton:pressed {{
                background-color: {theme.BUTTON_PRESSED};
            }}
        """

        self._build_ui()

    def _build_ui(self):
        home_layout = QVBoxLayout(self)
        home_layout.setContentsMargins(48, 55, 48, 44)

        self.status_label = StatusLabel("SYSTEM SCANNING...")
        home_layout.addWidget(self.status_label, 0, Qt.AlignHCenter)
        home_layout.addSpacing(14)

        self.scan_info = StatusLabel("")
        home_layout.addWidget(self.scan_info, 0, Qt.AlignHCenter)

        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        content_row.addStretch()  # leaves the empty space on the right like the figma
        content_row.addLayout(self._build_button_col())

        home_layout.addLayout(content_row)
        home_layout.addStretch()



    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(18)

        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setFixedSize(196, 45)
        self.stop_btn.setStyleSheet(self.button_style)
        self.stop_btn.clicked.connect(self.stop_requested)
        right_col.addWidget(self.stop_btn)

        right_col.addStretch()  # pushes STOP to the top, like the figma
        return right_col

    def start_scan(self, faces, level):
        self.faces = faces
        self.level = level
        self.scan_info.setText(f"Faces: {', '.join(faces)}  |  Threshold: {level} μSv/h")