import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedWidget
)
import theme
from pages.home_page import HomePage
from pages.vizx.vizx_page import VizXPage
from pages.vizx.scanning_page import ScanPage
from pages.vizx.jogging_page import JoggingPage
from widgets.model_view import ModelView


class ClickableLabel(QLabel):
    """A QLabel you can click, used for the nav tabs."""
    clicked = Signal()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mouseReleaseEvent(event)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("luX-Ray")
        self.resize(870, 540)

        # give the root an id so its background doesn't cascade into every child
        self.setObjectName("root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"#root {{ background-color: {theme.BACKGROUND}; }}")

        # make the pages
        self.home_page = HomePage()
        self.vizx_page = VizXPage()
        self.scan_page = ScanPage()
        self.jogging_page = JoggingPage()

        # the stack holds every page, but only shows one at a time
        self.pages = QStackedWidget()
        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.vizx_page)
        self.pages.addWidget(self.scan_page)
        self.pages.addWidget(self.jogging_page)


        # link pages together
        self.home_page.start_requested.connect(self._open_scan)
        self.home_page.jog_requested.connect(self._open_jogging)
        self.jogging_page.stop_requested.connect(self._open_home)
        self.jogging_page.scan_requested.connect(self._open_home)
        self.scan_page.stop_requested.connect(self._open_home)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._build_nav_row())
        layout.addWidget(self.pages)

    def _build_nav_row(self):
        nav_row = QHBoxLayout()
        nav_row.setContentsMargins(48, 24, 48, 0)
        nav_row.addStretch()  # stretch on both sides = centered

        self.home_label = ClickableLabel("Home")
        self.home_label.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_HEADER};
        """)
        self.home_label.clicked.connect(self._open_home)
        nav_row.addWidget(self.home_label)

        nav_row.addSpacing(120)

        self.vizx_label = ClickableLabel("viz-x")
        self.vizx_label.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_HEADER};
        """)
        self.vizx_label.clicked.connect(self._open_vizx)
        nav_row.addWidget(self.vizx_label)

        nav_row.addStretch()
        return nav_row

    def _open_home(self):
        self.pages.setCurrentWidget(self.home_page)

    def _open_vizx(self):
        self.pages.setCurrentWidget(self.vizx_page)

    def _open_scan(self):
        self.pages.setCurrentWidget(self.scan_page)

    def _open_jogging(self):
        self.pages.setCurrentWidget(self.jogging_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())