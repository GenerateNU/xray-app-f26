from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QInputDialog
)
import theme
from widgets.status import StatusLabel
from widgets.clickable_label import ClickableLabel


class ScanDonePage(QWidget):
    new_scan_requested = Signal()   # START → back Home to set up a new scan
    jog_requested = Signal()        # JOG → jogging page

    def __init__(self) -> None:
        super().__init__()

        self.faces = []
        self.reports = []   # reports from the scan (the backend fills this in later)                # faces that were scanned
        self.radiation_level = None    # threshold that was used

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

    def _build_ui(self)-> None:
        home_layout = QVBoxLayout(self)
        home_layout.setContentsMargins(48, 55, 48, 44)

        self.status_label = StatusLabel("SCAN COMPLETE!")
        home_layout.addWidget(self.status_label, 0, Qt.AlignHCenter)
        home_layout.addSpacing(14)

        self.scan_info = StatusLabel("")
        home_layout.addWidget(self.scan_info, 0, Qt.AlignHCenter)

        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        content_row.addStretch()                         # space on the left (scan view goes here later)
        content_row.addLayout(self._build_button_col())

        home_layout.addLayout(content_row, 1)

    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(18)

        self.start_btn = QPushButton("START")
        self.start_btn.setFixedSize(196, 45)
        self.start_btn.setStyleSheet(self.button_style)
        self.start_btn.clicked.connect(self.new_scan_requested)
        right_col.addWidget(self.start_btn)

        self.jog_btn = QPushButton("JOG")
        self.jog_btn.setFixedSize(196, 45)
        self.jog_btn.setStyleSheet(self.button_style)
        self.jog_btn.clicked.connect(self.jog_requested)
        right_col.addWidget(self.jog_btn)

        right_col.addStretch()   # pushes DOWNLOAD to the bottom, like the figma

                # "3 reports" link (opens the reports popup)
        self.reports_link = ClickableLabel("0 reports")
        self.reports_link.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_SMALL};
            text-decoration: underline;
        """)
        self.reports_link.clicked.connect(self._show_reports)
        right_col.addWidget(self.reports_link)


        self.download_btn = QPushButton("DOWNLOAD")
        self.download_btn.setFixedSize(196, 45)
        self.download_btn.setStyleSheet(self.button_style)
        self.download_btn.clicked.connect(self._on_download)
        right_col.addWidget(self.download_btn)

        return right_col

    

    # ---------- called from outside (main.py) ----------

    def show_results(self, faces, level)-> None:
        """Main calls this when a scan finishes, with what was scanned."""
        self.faces = faces
        self.radiation_level = level
        self.scan_info.setText(f"Faces: {', '.join(faces)}  |  Threshold: {level} μSv/h")

        self.set_reports([])

    # ---------- download flow ----------

    def _on_download(self)-> None:
        """name → save → success, or fail with retry. Loops until it works or they cancel."""
        name = f"luXRay Scan {datetime.now():%Y-%m-%d %H-%M}"   # starting default name
        while True:
            name = self._name_scan(name)          # ask for a name (pre-filled with the last one)
            if name is None:                      # they hit Cancel
                return
            ok, reason = self._save_scan(name)
            if ok:
                self._download_successful(name)
                return
            if not self._download_bad(reason):    # failed, and they hit Cancel
                return
            # they hit Retry, so loop back to the name popup with the same name

    def _name_scan(self, default):
        """Text box to name the scan. Returns the name, or None if they hit Cancel."""
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Download Scan")
        dialog.setLabelText("Name this scan:")
        dialog.setTextValue(default)
        dialog.setOkButtonText("Confirm && Download")    # && shows as a single &
        dialog.setCancelButtonText("Cancel")
        if not dialog.exec():
            return None
        return dialog.textValue().strip()

    def _save_scan(self, name):
        """Try to save the file. Returns (True, None) if it worked, or (False, reason) if not."""
        if not name:
            return False, "The scan name can't be empty."
        try:
            path = Path.home() / "Downloads" / f"{name}.csv"
            with open(path, "w") as f:
                f.write("faces,radiation_level\n")
                f.write(f"{' '.join(self.faces)},{self.radiation_level}\n")
                # TODO: write the real sensor readings once the backend sends them
            return True, None
        except Exception as e:
            return False, str(e)

    def _download_successful(self, name):
        QMessageBox.information(self, "Download Successful", f"Saved {name}.csv to your Downloads folder.")

    def _download_bad(self, reason):
        """Says why it failed. Returns True if they hit Retry."""
        popup = QMessageBox(self)
        popup.setIcon(QMessageBox.Icon.Warning)
        popup.setWindowTitle("Download Failed")
        popup.setText("The scan couldn't be saved.")
        popup.setInformativeText(f"Reason: {reason}")

        retry_btn = popup.addButton("Retry", QMessageBox.ButtonRole.AcceptRole)
        popup.addButton(QMessageBox.StandardButton.Cancel)

        popup.exec()
        return popup.clickedButton() == retry_btn

    def set_reports(self, reports):
        """The backend calls this with the reports from the scan."""
        self.reports = reports
        n = len(reports)
        self.reports_link.setText(f"{n} report" if n == 1 else f"{n} reports")

    def _show_reports(self):
        """The reports popup (Desktop 5)."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Reports")
        dialog.resize(420, 300)

        layout = QVBoxLayout(dialog)
        report_list = QListWidget()
        if self.reports:
            report_list.addItems(self.reports)
        else:
            report_list.addItem("No reports for this scan yet.")
        layout.addWidget(report_list)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)   # accept = close the dialog
        layout.addWidget(close_btn, 0, Qt.AlignRight)

        dialog.exec()