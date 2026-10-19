import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedWidget
)
import theme
from pages.home_page import HomePage


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("luX-Ray")
        self.resize(870, 540)

        # give the root an id so its background doesn't cascade into every child
        self.setObjectName("root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"#root {{ background-color: {theme.BACKGROUND}; }}")

        # the stack holds every page, but only shows one at a time
        self.pages = QStackedWidget()
        self.pages.addWidget(HomePage())  # index 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._build_nav_row())
        layout.addWidget(self.pages)

    def _build_nav_row(self):
        nav_row = QHBoxLayout()
        nav_row.setContentsMargins(48, 24, 48, 0)
        nav_row.addStretch()  # stretch on both sides = centered

        home_label = QLabel("Home")
        home_label.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_HEADER};
            text-decoration: underline;
        """)
        nav_row.addWidget(home_label)

        nav_row.addSpacing(120)

        vizx_label = QLabel("viz-x")
        vizx_label.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_HEADER};
        """)
        nav_row.addWidget(vizx_label)

        nav_row.addStretch()
        return nav_row


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())