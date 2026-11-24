import sys
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedWidget
)

import theme
from pages.home_page import HomePage
from pages.vizx.vizx_page import VizXPage
from pages.vizx.scanning_page import ScanPage
from pages.vizx.jogging_page import JoggingPage
from pages.vizx.scanning_done_page import ScanDonePage
from pages.vizx.scanning_stopped_page import ScanStoppedPage
from pages.vizx.error_page import ErrorPage
from widgets.clickable_label import ClickableLabel
from step_model import StepModel

# BACKEND ------------------------------------------------------------------------------
import config
from backend.serial_backend import SerialBackend

class MainWindow(QWidget) :
    def __init__(self):
        super().__init__()
        self.setWindowTitle("luX-Ray")
        self.resize(870, 540)

        # give the root an id so its background doesn't cascade into every child
        self.setObjectName("root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"#root {{ background-color: {theme.BACKGROUND}; }}")

        # make the pages
                # load the STEP once, and every 3D view shares it
        self.step_model = StepModel()

        # make the pages
        self.home_page = HomePage(self.step_model)
        self.vizx_page = VizXPage()
        self.scan_page = ScanPage(self.step_model)
        self.jogging_page = JoggingPage()
        self.done_page = ScanDonePage(self.step_model)
        self.stopped_page = ScanStoppedPage()
        self.error_page = ErrorPage()


        # the stack holds every page, but only shows one at a time
        self.pages = QStackedWidget()
        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.vizx_page)
        self.pages.addWidget(self.scan_page)
        self.pages.addWidget(self.jogging_page)
        self.pages.addWidget(self.done_page)
        self.pages.addWidget(self.stopped_page)
        self.pages.addWidget(self.error_page)


        self._set_homed(False)   # unknown position at startup (later: ask the firmware with STATUS?)

        # link pages together
        self.home_page.start_requested.connect(self._start_scan)
        self.home_page.jog_requested.connect(self._open_jogging)
        self.jogging_page.stop_requested.connect(self._open_home)
        self.jogging_page.scan_requested.connect(self._open_home)
        self.scan_page.stop_requested.connect(self._pause_scan)          # STOP → stopped screen
        self.stopped_page.resume_requested.connect(self._resume_scan)    # RESUME → back to scanning
        self.stopped_page.cancel_requested.connect(self._cancel_scan)        
        self.vizx_page.start_requested.connect(self._open_home)
        self.vizx_page.jog_requested.connect(self._open_jogging)
        self.scan_page.scan_finished.connect(self._finish_scan)
        self.done_page.new_scan_requested.connect(self._open_home)
        self.done_page.jog_requested.connect(self._open_jogging)
        self.jogging_page.jog_pressed.connect(self._jog_start)
        self.jogging_page.jog_released.connect(self._jog_stop)
        self.error_page.rehome_requested.connect(self._rehome)
        self.home_page.home_requested.connect(self._rehome)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._build_nav_row())
        layout.addWidget(self.pages)

        # update the underline every time the page changes, and once at startup
        self.pages.currentChanged.connect(self._update_nav)
        self._update_nav()

        # ---------- backend (talks to the MCU) ----------
        self.backend = SerialBackend(config.SERIAL_PORT, config.SERIAL_BAUD)
        self._connect_backend()          # hook up its signals FIRST...
        self.backend.open_connection()   # ...then connect

    def _set_nav_locked(self, locked):
        """Turn the nav tabs off during a scan so STOP is the only way out."""
        self.home_label.setEnabled(not locked)
        self.vizx_label.setEnabled(not locked)
        self._update_nav()   # restyle so they go gray (or back to white)

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
    def _open_done(self):
        self.pages.setCurrentWidget(self.done_page)

    def _start_scan(self, faces, level):
        self.scan_page.start_scan(faces, level)  # give the scan page the data
        self._open_scan()
        self._set_nav_locked(True)
        self.backend.start_scan(faces, level)    # tell the MCU to start


    def _pause_scan(self):
        self.backend.pause()
        self.pages.setCurrentWidget(self.stopped_page)   # nav stays locked, scan isn't over

    def _resume_scan(self):
        self.backend.resume()
        self._open_scan()                                 # progress is still there

    def _cancel_scan(self):
        self.backend.abort()
        self._set_nav_locked(False)                       # scan's over, unlock the nav
        self._open_home()

    def _jog_start(self, axis, direction):
        self.backend.jog(axis, direction)

    def _jog_stop(self):
        self.backend.jog_stop()

    def _system_error(self, message):
        """Something serious happened (e-stop, fault...). Works from any page."""
        self.backend.abort()                            # make sure the MCU stops everything
        self.error_page.show_error(message)
        self._set_nav_locked(True)                      # lock nav, REHOME is the only way out
        self.pages.setCurrentWidget(self.error_page)
        self._set_homed(False)                          # position can't be trusted after an error

    def _rehome(self):
        """HOME MACHINE (Home page) or REHOME (error page)."""
        self._set_nav_locked(True)          # the machine is moving, stay put
        self._open_home()
        self.home_page.set_homing(True)
        self.backend.home()                 # _homing_done runs when the MCU replies HOMED (step C)

    def _homing_done(self):
        """Homing finished (later: the firmware sent HOMED)."""
        self.home_page.set_homing(False)
        self._set_homed(True)
        self._set_nav_locked(False)

    def _style_tab(self, label, active):
        """Same style for both tabs: underlined if active, gray if locked."""
        underline = "underline" if active else "none"
        color = theme.TEXT_PRIMARY if label.isEnabled() else theme.NAV_DISABLED
        label.setStyleSheet(f"""
            color: {color};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_HEADER};
            text-decoration: {underline};
        """)

    def _set_homed(self, homed):
        """The app's copy of 'is the machine homed?' (later this mirrors what the firmware says)."""
        self.homed = homed
        self.home_page.set_homed(homed)

    def _connect_backend(self):
        """Machine → app: what happens when the backend reports something. (Step C adds the rest.)"""
        self.backend.connection_changed.connect(lambda ok: print("connected:", ok))

    def closeEvent(self, event):
        """The window is closing: stop the reader thread and close the port cleanly."""
        self.backend.close_connection()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())