from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout
import theme
from widgets.status import StatusLabel
from widgets.progress_bar import ProgressBar
from widgets.model_view import ModelView


class ScanPage(QWidget):
    stop_requested = Signal()               # STOP clicked
    scan_finished = Signal(list, float)     # faces, level (main opens the done page + unlocks the nav)

    def __init__(self, step_model):
        super().__init__()
        self.step_model = step_model        # the loaded STEP, from main.py

        self.faces = []                     # faces being scanned
        self.radiation_level = None         # radiation threshold for this scan

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

        self.status_label = StatusLabel("SYSTEM SCANNING...")
        home_layout.addWidget(self.status_label, 0, Qt.AlignHCenter)
        home_layout.addSpacing(14)

        self.scan_info = StatusLabel("")
        home_layout.addWidget(self.scan_info, 0, Qt.AlignHCenter)

        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        self.progress = ProgressBar()
        content_row.addWidget(self.progress)                              # progress bar on the far left
        self.model_view = ModelView(self.step_model, selectable=False)   # view-only during a scan
        content_row.addWidget(self.model_view, 1)                         # model takes the middle
        content_row.addLayout(self._build_button_col())                   # STOP on the right

        home_layout.addLayout(content_row, 1)   # the 1 = row gets all the extra height

    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(18)

        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setFixedSize(196, 45)
        self.stop_btn.setStyleSheet(self.button_style)
        self.stop_btn.clicked.connect(self.stop_requested)
        right_col.addWidget(self.stop_btn)

        right_col.addStretch()   # keeps STOP at the top
        return right_col

    # ---------- called from outside (main.py now, backend later) ----------

    def start_scan(self, faces, level):
        """A new scan is starting: save what we're scanning, reset the bar, highlight the sides."""
        self.faces = faces
        self.radiation_level = level
        self.scan_info.setText(f"Faces: {', '.join(faces)}  |  Threshold: {level} μSv/h")
        self.progress.set_progress(0)          # new scan starts empty
        self.model_view.set_selected(faces)    # show which sides are being scanned

    def set_progress(self, percent):
        """The backend calls this with the real scan progress."""
        self.progress.set_progress(percent)
        if percent >= 100:
            self.finish_scan()

    def finish_scan(self):
        """Scan's done. Called at 100%, or later by the backend when the MCU says so."""
        self.scan_finished.emit(self.faces, self.radiation_level)