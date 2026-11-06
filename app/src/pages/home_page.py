from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QGridLayout, QMessageBox, QDoubleSpinBox, QHBoxLayout
)
import theme
from widgets.model_view import ModelView
from widgets.clickable_label import ClickableLabel
from face_table import FACE_TABLE


class HomePage(QWidget):
    start_requested = Signal(list, float)   # faces, radiation level
    jog_requested = Signal()

    def __init__(self, step_model):
        super().__init__()
        self.step_model = step_model    

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

    # ---------- layout (Desktop 12) ----------

    def _build_ui(self):
        #           col 0                 col 1
        #   row 0   3D model        |
        #   row 1   radiation input |   START / JOG
        grid = QGridLayout(self)
        grid.setContentsMargins(52, 40, 72, 54)
        grid.setHorizontalSpacing(80)
        grid.setVerticalSpacing(30)

        # 3D model (top left): this is where you pick faces now
        self.model_view = ModelView(self.step_model)
        grid.addWidget(self.model_view, 0, 0)

        # radiation input (under the model)
        # radiation input + select all / clear (under the model)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(24)
        bottom_row.addWidget(self._build_radiation_input())
        bottom_row.addWidget(self._make_link("select all", lambda: self.model_view.set_selected(FACE_TABLE.keys())))
        bottom_row.addWidget(self._make_link("clear", lambda: self.model_view.set_selected([])))
        bottom_row.addStretch()
        grid.addLayout(bottom_row, 1, 0)
        # buttons (right side), spanning both rows so they sit at the bottom
        grid.addLayout(self._build_button_col(), 0, 1, 2, 1)

        grid.setColumnStretch(0, 1)   
        grid.setRowStretch(0, 1)      

    def _build_radiation_input(self):
        # number-only box for the radiation threshold
        self.radiation_input = QDoubleSpinBox()
        self.radiation_input.setRange(0, 10000)             # min, max
        self.radiation_input.setDecimals(3)                 # up to 3 decimal places
        self.radiation_input.setValue(1.0)                  # TEMP default, ask Sean for the real one
        self.radiation_input.setPrefix("Radiation Level: ") # text before the number
        self.radiation_input.setSuffix(" μSv/h")            # units after the number
        self.radiation_input.setFixedSize(300, 48)
        self.radiation_input.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {theme.BUTTON_PRIMARY};
                color: {theme.BUTTON_TEXT};
                border: none;
                border-radius: 6px;
                padding: 0px 12px;
                font-family: {theme.FONT_FAMILY};
            }}
        """)
        return self.radiation_input

    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(18)
        right_col.addStretch()   

        self.start_btn = QPushButton("START")
        self.start_btn.setFixedSize(195, 48)
        self.start_btn.setStyleSheet(self.button_style)
        self.start_btn.clicked.connect(self._on_start)      
        right_col.addWidget(self.start_btn)

        self.jog_btn = QPushButton("JOG")
        self.jog_btn.setFixedSize(195, 48)
        self.jog_btn.setStyleSheet(self.button_style)
        self.jog_btn.clicked.connect(self.jog_requested)
        right_col.addWidget(self.jog_btn)

        return right_col

    # ---------- starting a scan ----------

    def _selected_faces(self):
        """The sides picked on the 3D model, like ["side1", "side3"]."""
        return self.model_view.selected_sides()

    def _on_start(self):
        if self._confirm_scan() and self._final_confirm():
            self.start_requested.emit(self._selected_faces(), self.radiation_input.value())

    def _confirm_scan(self):
        """First check: shows the level + faces. Returns True if they hit Confirm."""
        level = self.radiation_input.value()
        faces = ", ".join(self._selected_faces()) or "(none selected)"

        popup = QMessageBox(self)
        popup.setWindowTitle("Confirm Scan")
        popup.setText("Are you sure you want to start this scan?")
        popup.setInformativeText(f"Radiation level: {level} μSv/h\nSelected faces: {faces}")

        confirm_btn = popup.addButton("Confirm", QMessageBox.ButtonRole.AcceptRole)
        popup.addButton(QMessageBox.StandardButton.Cancel)

        popup.exec()
        return popup.clickedButton() == confirm_btn

    def _final_confirm(self):
        """Second check so nobody starts it by accident. Returns True if they hit Start Scan."""
        popup = QMessageBox(self)
        popup.setWindowTitle("Final Check")
        popup.setIcon(QMessageBox.Icon.Warning)
        popup.setText("Are you REALLY sure?")
        popup.setInformativeText("The machine will start moving once you continue.")

        start_btn = popup.addButton("Start Scan", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = popup.addButton(QMessageBox.StandardButton.Cancel)
        popup.setDefaultButton(cancel_btn)        # Enter = Cancel

        popup.exec()
        return popup.clickedButton() == start_btn

    def _make_link(self, text, on_click):
        """Small underlined clickable text, used for select all / clear."""
        link = ClickableLabel(text)
        link.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_NORMAL};
            text-decoration: underline;
        """)
        link.clicked.connect(on_click)
        return link