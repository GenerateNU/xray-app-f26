from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
import theme
from widgets.status import StatusLabel


class ErrorPage(QWidget):
    """Serious error (e-stop, radiation over threshold, etc). The system has stopped and must re-home."""

    rehome_requested = Signal()   # REHOME → reset the machine, then go Home

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

    # ---------- layout ----------

    def _build_ui(self):
        home_layout = QVBoxLayout(self)
        home_layout.setContentsMargins(48, 55, 48, 44)

        self.status_label = StatusLabel("SYSTEM HALTED.")
        home_layout.addWidget(self.status_label, 0, Qt.AlignHCenter)
        home_layout.addSpacing(14)

        content_row = QHBoxLayout()
        content_row.setSpacing(40)

        # big red box with what went wrong (Desktop 6)
        self.error_box = QLabel()
        self.error_box.setAlignment(Qt.AlignCenter)
        self.error_box.setWordWrap(True)            # long messages wrap instead of running off
        self.error_box.setStyleSheet(f"""
            background-color: {theme.ERROR};
            color: {theme.TEXT_SECONDARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_NORMAL};
            border-radius: 6px;
            padding: 16px;
        """)
        content_row.addWidget(self.error_box, 1)     # the 1 = red box takes the extra width

        content_row.addLayout(self._build_button_col())
        home_layout.addLayout(content_row, 1)

    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(18)

        self.rehome_btn = QPushButton("REHOME")
        self.rehome_btn.setFixedSize(196, 45)
        self.rehome_btn.setStyleSheet(self.button_style)
        self.rehome_btn.clicked.connect(self.rehome_requested)
        right_col.addWidget(self.rehome_btn)

        right_col.addStretch()   # keeps the button at the top
        return right_col

    # ---------- called from outside (main.py now, backend later) ----------

    def show_error(self, message):
        """Fill in the red box with what went wrong."""
        self.error_box.setText(f"ERROR\n\n{message}\n\nThe system has stopped. Rehome before continuing.")