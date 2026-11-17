from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QFrame
)
import theme
from widgets.status import StatusLabel
from widgets.jog_pad import JogPad



class JoggingPage(QWidget):
    stop_requested = Signal()
    scan_requested = Signal()
    jog_pressed = Signal(str, int)   # axis, direction (passed up from the jog pad)
    jog_released = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.button_style = f"""
            QPushButton {{
                background-color: {theme.BUTTON_PRIMARY};
                color: {theme.TEXT_SECONDARY};
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
        left_col = QVBoxLayout(self)
        left_col.setContentsMargins(48, 55, 48, 44)

        self.status_label = StatusLabel("SYSTEM JOGGING....")
        left_col.addWidget(self.status_label, 0, Qt.AlignHCenter)
        left_col.addSpacing(14)

        self.jog_pad = JogPad()
        self.jog_pad.jog_pressed.connect(self.jog_pressed)     # pass it up
        self.jog_pad.jog_released.connect(self.jog_released)

        
        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        content_row.addStretch()                # space on the left
        content_row.addWidget(self.jog_pad)     # pad in the middle of the left area
        content_row.addStretch()                # space on the right of the pad        
        content_row.addLayout(self._build_button_col())

        left_col.addLayout(content_row)
        left_col.addStretch()

        return left_col


    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(18)

        self.scan_btn = QPushButton("SCAN")
        self.scan_btn.setFixedSize(196, 45)
        self.scan_btn.setStyleSheet(self.button_style)
        self.scan_btn.clicked.connect(self.scan_requested)
        right_col.addWidget(self.scan_btn)

        right_col.addStretch()  # keeps the buttons at the top
        return right_col