from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QListWidget, QFrame, QMessageBox, QDoubleSpinBox
)
import theme


class HomePage(QWidget):
    start_requested = Signal(list, float)
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

    def _selected_faces(self):
        """The faces to scan. 'all' becomes every side."""
        picked = [item.text() for item in self.face_list.selectedItems()]
        if "all" in picked:
            return ["side1", "side2", "side3", "side4", "side5"]
        return picked

    def _build_ui(self):
        home_layout = QVBoxLayout(self)
        home_layout.setContentsMargins(48, 55, 48, 44)

        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        content_row.addWidget(self._build_face_select_card())
        content_row.addLayout(self._build_button_col())
        content_row.addStretch()  # leaves the empty space on the right like the figma

        home_layout.addLayout(content_row)
        home_layout.addStretch()

    def _build_face_select_card(self):
        # light outer card
        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(315, 380)
        card.setStyleSheet(f"""
            #card {{
                background-color: {theme.CARD_BACKGROUND};
                border-radius: 6px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(40)

        # dark inner box holding the face list
        face_box = QFrame()
        face_box.setObjectName("faceBox")
        face_box.setFixedHeight(213)
        face_box.setStyleSheet(f"""
            #faceBox {{
                background-color: {theme.BACKGROUND};
                border-radius: 6px;
            }}
        """)

        face_layout = QVBoxLayout(face_box)
        face_layout.setContentsMargins(16, 14, 16, 14)
        face_layout.setSpacing(2)

        select_face_label = QLabel("select face")
        select_face_label.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
        """)
        face_layout.addWidget(select_face_label)

        ## REPLACE THIS LATER (3D)
        self.face_list = QListWidget()
        self.face_list.addItems(["side1", "side2", "side3", "side4", "side5", "all"])
        self.face_list.setCurrentRow(0)
        self.face_list.setFocusPolicy(Qt.NoFocus)  # gets rid of the blue macOS focus ring
        self.face_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: 0;
                color: {theme.TEXT_PRIMARY};
                font-family: {theme.FONT_FAMILY};
            }}
            QListWidget::item {{
                padding: 1px 2px;
                border-radius: 3px;
            }}
            QListWidget::item:hover {{
                background-color: rgba(255, 255, 255, 20);
            }}
            QListWidget::item:selected {{
                background-color: rgba(255, 255, 255, 45);
                color: {theme.TEXT_PRIMARY};
            }}
        """)
        face_layout.addWidget(self.face_list)

        card_layout.addWidget(face_box)

        # number-only box for the radiation threshold
        self.radiation_input = QDoubleSpinBox()
        self.radiation_input.setRange(0, 10000)             # min, max
        self.radiation_input.setDecimals(3)                 # up to 3 decimal places
        self.radiation_input.setValue(1.0)                  # TEMP default, ask Sean for the real one
        self.radiation_input.setPrefix("Radiation Level: ") # text before the number
        self.radiation_input.setSuffix(" μSv/h")            # units after the number
        self.radiation_input.setFixedHeight(42)
        self.radiation_input.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {theme.BACKGROUND};
                color: {theme.TEXT_PRIMARY};
                border: none;
                border-radius: 4px;
                padding: 0px 10px;
                font-family: {theme.FONT_FAMILY};
            }}
        """)

        card_layout.addWidget(self.radiation_input)
        card_layout.addStretch()

        return card

    def _build_button_col(self):
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
        self.start_btn.clicked.connect(self._on_start)      # START asks first
        self.jog_btn.clicked.connect(self.jog_requested)

        return right_col

    def _on_start(self):
        if self._confirm_scan() and self._final_confirm():
            faces = self._selected_faces()
            level = self.radiation_input.value()
            print("SENDING:", faces, level)   # TEMPORARY, to check it works
            self.start_requested.emit(faces, level)

    def _confirm_scan(self):
        """Ask the user to double check before scanning. Returns True if they hit Confirm."""
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
        """Second confirm/check"""
        popup = QMessageBox(self)
        popup.setWindowTitle("final confirmation")
        popup.setIcon(QMessageBox.Icon.Warning)   # warning icon so it looks serious
        popup.setText("Are you sure about this scan?")
        popup.setInformativeText("The machine WILL start moving once you confirm.")

        start_btn = popup.addButton("Start Scan", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = popup.addButton(QMessageBox.StandardButton.Cancel)
        popup.setDefaultButton(cancel_btn)        # Enter = Cancel, so you can't accidentally double-tap through

        popup.exec()
        return popup.clickedButton() == start_btn