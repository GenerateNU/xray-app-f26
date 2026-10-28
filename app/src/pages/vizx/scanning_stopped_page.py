from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout
import theme
from widgets.status import StatusLabel



class ScanStoppedPage(QWidget):
    resume_requested = Signal()   # RESUME → keep scanning where it left off
    cancel_requested = Signal()   # CANCEL → end the scan, go Home

    def __init__(self):
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
        home_layout = QVBoxLayout(self)
        home_layout.setContentsMargins(48, 55, 48, 44)

        self.status_label = StatusLabel("SYSTEM STOPPED.")
        home_layout.addWidget(self.status_label, 0, Qt.AlignHCenter)
        home_layout.addSpacing(14)

        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        content_row.addStretch()                         # space on the left (scan view goes here later)
        content_row.addLayout(self._build_button_col())

        home_layout.addLayout(content_row, 1)

    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(18)

        self.resume_btn = QPushButton("RESUME")
        self.resume_btn.setFixedSize(196, 45)
        self.resume_btn.setStyleSheet(self.button_style)
        self.resume_btn.clicked.connect(self.resume_requested)
        right_col.addWidget(self.resume_btn)

        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setFixedSize(196, 45)
        self.cancel_btn.setStyleSheet(self.button_style)
        self.cancel_btn.clicked.connect(self.cancel_requested)
        right_col.addWidget(self.cancel_btn)

        right_col.addStretch()   # keeps the buttons at the top
        return right_col