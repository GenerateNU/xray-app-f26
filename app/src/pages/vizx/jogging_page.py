from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QFrame
)
import theme
from widgets.status import StatusLabel



class JoggingPage(QWidget):
    stop_requested = Signal()
    scan_requested = Signal()

    def __init__(self):
        super().__init__()

        self.button_style = f"""
            QPushButton {{
                background-color: {theme.BUTTON_PRIMARY};
                color: {theme.BUTTON_TEXT};
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

        self.status_label = StatusLabel("SYSTEM JOGGING....")
        home_layout.addWidget(self.status_label, 0, Qt.AlignHCenter)
        home_layout.addSpacing(14)

        
        content_row = QHBoxLayout()
        content_row.setSpacing(40)

        content_row.addStretch()  # leaves the empty space on the right like the figma

        content_row.addLayout(self._build_button_col())

        home_layout.addLayout(content_row, 1)  # the 1 = take up all the extra height


    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(18)

        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setFixedSize(196, 45)
        self.stop_btn.setStyleSheet(self.button_style)
        self.stop_btn.clicked.connect(self.stop_requested)
        right_col.addWidget(self.stop_btn)

        self.scan_btn = QPushButton("SCAN")
        self.scan_btn.setFixedSize(196, 45)
        self.scan_btn.setStyleSheet(self.button_style)
        self.scan_btn.clicked.connect(self.scan_requested)
        right_col.addWidget(self.scan_btn)

        right_col.addStretch()  # keeps the buttons at the top
        return right_col