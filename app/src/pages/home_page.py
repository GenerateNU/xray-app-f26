from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QGridLayout,
    QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QFrame
)
import theme
from widgets.model_view import ModelView


class HomePage(QWidget):
    start_requested = Signal()
    jog_requested = Signal()

    def __init__(self) -> None:
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

    def _build_ui(self) -> None :
        # Home is a grid (rows + columns):
        #
        #           col 0                col 1
        #   row 0   3D model        |
        #   row 1   radiation input |   START / JOG
        #
        grid = QGridLayout(self)

        # empty space around the edges: left, top, right, bottom
        # (top is bigger because the nav bar sits above the page)
        grid.setContentsMargins(52, 76, 72, 54)

        # gap between the model and the buttons (side to side)
        grid.setHorizontalSpacing(106)
        # gap between the model and the radiation input (top to bottom)
        grid.setVerticalSpacing(43)

        # 3D model goes in the top left (row 0, col 0)
        self.model_view = ModelView()
        grid.addWidget(self.model_view, 0, 0)

        # radiation input goes under the model (row 1, col 0)
        # AlignLeft keeps it its own size and pushed left instead of centered
        grid.addWidget(self._build_radiation_input(), 1, 0, Qt.AlignLeft)

        # buttons go on the right (row 0, col 1) and span 2 rows, 1 column
        # spanning both rows gives them the full height, and the stretch inside
        # _build_button_col pushes them down to sit level with the radiation input
        grid.addLayout(self._build_button_col(), 0, 1, 2, 1)

        # when the window gets bigger, only the model grows
        # (it's in col 0 and row 0, everything else stays its fixed size)
        grid.setColumnStretch(0, 1)
        grid.setRowStretch(0, 1)

    def _build_radiation_input(self) -> QLineEdit:
        # one-line text box where the user types the radiation threshold
        self.radiation_input = QLineEdit()

        # hint text that shows when it's empty, disappears when you type
        self.radiation_input.setPlaceholderText("Radiation Level (μSv/h)")

        # fixed width 255, height 48 so the grid doesn't stretch it
        self.radiation_input.setFixedSize(255, 48)

        # light blue box (same as the buttons), dark text, rounded corners
        # padding keeps the text from touching the left edge
        self.radiation_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.BUTTON_PRIMARY};
                color: {theme.TEXT_DARK};
                border: none;
                border-radius: 6px;
                padding: 0px 12px;
                font-family: {theme.FONT_FAMILY};
            }}
        """)

        # stylesheets can't change placeholder color in Qt,
        # so we set it through the palette instead (dark so it shows on the light box)
        palette = self.radiation_input.palette()
        palette.setColor(QPalette.PlaceholderText, QColor(theme.TEXT_DARK))
        self.radiation_input.setPalette(palette)

        # hand it back so _build_ui can put it in the grid
        return self.radiation_input

    def _build_button_col(self) -> QVBoxLayout:
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