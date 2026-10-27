from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QFrame
)
import theme
from widgets.status import StatusLabel
from widgets.progress_bar import ProgressBar



class ScanPage(QWidget):
    stop_requested = Signal()

    def __init__(self):
        super().__init__()

        self.faces = [] #faces being scanned
        self.radiation_level = None

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

        self.status_label = StatusLabel("SYSTEM SCANNING...")
        home_layout.addWidget(self.status_label, 0, Qt.AlignHCenter)
        home_layout.addSpacing(14)

        self.scan_info = StatusLabel("")
        home_layout.addWidget(self.scan_info, 0, Qt.AlignHCenter)

        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        self.progress = ProgressBar()
        content_row.addWidget(self.progress)        # progress bar on the far left
        content_row.addStretch()
        content_row.addLayout(self._build_button_col())

        home_layout.addLayout(content_row, 1)   # the 1 = row gets all the extra height

    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(18)

        self.start_btn = QPushButton("START")
        self.start_btn.setFixedSize(195, 48)
        self.start_btn.setStyleSheet(self.button_style)
        right_col.addWidget(self.start_btn)

        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setFixedSize(196, 45)
        self.stop_btn.setStyleSheet(self.button_style)
        self.stop_btn.clicked.connect(self.stop_requested)
        right_col.addWidget(self.stop_btn)

        self.stop_btn = QPushButton("DOWNLOAD")
        self.stop_btn.setFixedSize(196, 45)
        self.stop_btn.setStyleSheet(self.button_style)
        self.stop_btn.clicked.connect(self.stop_requested)
        right_col.addWidget(self.stop_btn)

        right_col.addStretch() 
        return right_col

    def _on_download(self):
        if self._name_scan():
            faces = self._selected_faces()
            level = self.radiation_input.value()
            print("SENDING:", faces, level)   # TEMPORARY, to check it works
            self.start_requested.emit(faces, level)

    def _name_scan(self):
        """Name the scan."""
        level = self.radiation_input.value()
        faces = ", ".join(self._selected_faces()) or "(none selected)"

        popup = QMessageBox(self)
        popup.setWindowTitle("Download Scan")
        popup.setText("Are you sure you want to download this scan?")
        popup.setInformativeText(f"Radiation level: {level} μSv/h\nSelected faces: {faces}")

        confirm_btn = popup.addButton("Confirm", QMessageBox.ButtonRole.AcceptRole)
        popup.addButton(QMessageBox.StandardButton.Cancel)

        popup.exec()
        return popup.clickedButton() == confirm_btn

    def _download_successful(self):
            """download was success"""
            level = self.radiation_input.value()
            faces = ", ".join(self._selected_faces()) or "(none selected)"
    
            popup = QMessageBox(self)
            popup.setWindowTitle("Download Scan")
            popup.setText("Are you sure you want to download this scan?")
            popup.setInformativeText(f"Radiation level: {level} μSv/h\nSelected faces: {faces}")
    
            confirm_btn = popup.addButton("Confirm", QMessageBox.ButtonRole.AcceptRole)
            popup.addButton(QMessageBox.StandardButton.Cancel)
    
            popup.exec()
            return popup.clickedButton() == confirm_btn

    def _download_bad(self):
                """download failed."""
                level = self.radiation_input.value()
                faces = ", ".join(self._selected_faces()) or "(none selected)"
        
                popup = QMessageBox(self)
                popup.setWindowTitle("Download Scan")
                popup.setText("Are you sure you want to download this scan?")
                popup.setInformativeText(f"Radiation level: {level} μSv/h\nSelected faces: {faces}")
        
                confirm_btn = popup.addButton("Confirm", QMessageBox.ButtonRole.AcceptRole)
                popup.addButton(QMessageBox.StandardButton.Cancel)
        
                popup.exec()
                return popup.clickedButton() == confirm_btn

    
    def start_scan(self, faces, level):
        self.faces = faces
        self.radiation_level = level
        self.scan_info.setText(f"Faces: {', '.join(faces)}  |  Threshold: {level} μSv/h")
        self.progress.set_progress(0)   # new scan starts empty

    def set_progress(self, percent):
        """The backend calls this with the real scan progress."""
        self.progress.set_progress(percent)