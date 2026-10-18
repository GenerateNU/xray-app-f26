import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QFrame
)
import theme


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("luX-Ray")
        self.resize(500, 400)
        self.setStyleSheet(f"background-color: {theme.BACKGROUND};")

        self.button_style = f"""
            background-color: {theme.BUTTON_PRIMARY};
            color: {theme.BUTTON_TEXT};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_BUTTON};
            border-radius: 6px;
            padding: 10px;
        """

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        main_layout.addLayout(self._build_nav_row())

        content_row = QHBoxLayout()
        content_row.setSpacing(20)
        content_row.addLayout(self._build_face_select_col())
        content_row.addLayout(self._build_button_col())
        main_layout.addLayout(content_row)

        self.setLayout(main_layout)

    def _build_nav_row(self):
        nav_row = QHBoxLayout()

        home_label = QLabel("Home")
        home_label.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_HEADER};
        """)
        nav_row.addWidget(home_label)

        vizx_label = QLabel("viz-x")
        vizx_label.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_HEADER};
            text-decoration: underline;
        """)
        nav_row.addWidget(vizx_label)

        return nav_row

    def _build_face_select_col(self):
        card = QFrame()
        card.setStyleSheet(f"background-color: {theme.CARD_BACKGROUND}; border-radius: 6px;")

        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(12, 12, 12, 12)
        inner_layout.setSpacing(8)

        select_face_label = QLabel("select face")
        select_face_label.setStyleSheet(f"color: {theme.TEXT_DARK}; font-family: {theme.FONT_FAMILY};")
        inner_layout.addWidget(select_face_label)

        self.face_dropdown = QComboBox()
        self.face_dropdown.addItems(["side1", "side2", "side3", "side4", "side5", "all"])
        self.face_dropdown.setStyleSheet(f"""
            QComboBox {{
                background-color: white;
                color: {theme.TEXT_DARK};
                padding: 6px;
                border-radius: 4px;
                font-family: {theme.FONT_FAMILY};
            }}
        """)
        inner_layout.addWidget(self.face_dropdown)

        radiation_label = QLabel("Radiation Level")
        radiation_label.setStyleSheet(f"color: {theme.TEXT_DARK}; font-family: {theme.FONT_FAMILY};")
        inner_layout.addWidget(radiation_label)

        self.radiation_input = QLineEdit()
        self.radiation_input.setPlaceholderText("threshold")
        self.radiation_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: white;
                color: {theme.TEXT_DARK};
                padding: 6px;
                border-radius: 4px;
                font-family: {theme.FONT_FAMILY};
            }}
        """)
        inner_layout.addWidget(self.radiation_input)

        card.setLayout(inner_layout)

        outer = QVBoxLayout()
        outer.addWidget(card)
        return outer

    def _build_button_col(self):
        right_col = QVBoxLayout()
        right_col.setSpacing(8)

        self.start_btn = QPushButton("START")
        self.start_btn.setStyleSheet(self.button_style)
        right_col.addWidget(self.start_btn)

        self.jog_btn = QPushButton("JOG")
        self.jog_btn.setStyleSheet(self.button_style)
        right_col.addWidget(self.jog_btn)

        return right_col


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())