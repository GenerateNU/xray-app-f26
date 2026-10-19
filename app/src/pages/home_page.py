from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QFrame
)
import theme


class HomePage(QWidget):
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

        # dark radiation input (label lives inside as placeholder, like the figma)
        self.radiation_input = QLineEdit()
        self.radiation_input.setPlaceholderText("Radiation Level")
        self.radiation_input.setFixedHeight(42)
        self.radiation_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.BACKGROUND};
                color: {theme.TEXT_PRIMARY};
                border: none;
                border-radius: 4px;
                padding: 0px 10px;
                font-family: {theme.FONT_FAMILY};
            }}
        """)
        # make the placeholder text light instead of the default gray
        palette = self.radiation_input.palette()
        palette.setColor(QPalette.PlaceholderText, QColor(theme.TEXT_PRIMARY))
        self.radiation_input.setPalette(palette)

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
        return right_col