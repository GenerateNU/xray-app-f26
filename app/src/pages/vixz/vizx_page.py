from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QFrame
)
import theme
from widgets.status import StatusLabel



class VizXPage(QWidget):
    start_requested = Signal()
    jog_requested = Signal()

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

        self.status_label = StatusLabel("SYSTEM IDLE...")
        home_layout.addWidget(self.status_label, 0, Qt.AlignHCenter)
        home_layout.addSpacing(14)

        
        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        content_row.addStretch()  # leaves the empty space on the right like the figma
        content_row.addLayout(self._build_button_col())

        home_layout.addLayout(content_row)
        home_layout.addStretch()



    def _build_button_col(self) :
        right_col = QVBoxLayout()
        right_col.setSpacing(18)
        right_col.addStretch()  # pushes the buttons down to the bottom of the card

        self.start_btn = QPushButton("START")
        self.start_btn.setFixedSize(195, 48)
        self.start_btn.setStyleSheet(self.button_style)
        right_col.addWidget(self.start_btn)

        self.jog_btn = QPushButton("JOG")
        self.jog_btn.setFixedSize(195, 48)
        self.jog_btn.setStyleSheet(self.button_style)
        right_col.addWidget(self.jog_btn)

        right_col.addSpacing(6)
        self.start_btn.clicked.connect(self.start_requested)
        self.jog_btn.clicked.connect(self.jog_requested)

        return right_col