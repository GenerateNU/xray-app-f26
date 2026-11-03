from PySide6.QtCore import QObject, Signal


class Backend(QObject):
    """WHAT THE BACKEND IS CAPABLE OF AHAHAHA MAIN TALKS TO DIS ONLY>"""

    # ---------- machine → app (signals) ----------
    connection_changed = Signal(bool)        # True = talking to the MCU, False = not
    status_received = Signal(str)            # answer to STATUS?: "HOMED", "NOT_HOMED", or "ERROR"
    homed = Signal()                         # homing finished
    progress = Signal(int)                   # scan progress, 0-100
    scan_finished = Signal()                 # the MCU finished the scan
    position = Signal(float, float, float)   # where the gantry is right now (x, y, z in mm)
    error = Signal(str)                      # something serious happened (e-stop, fault, ...)

    # ---------- app → machine (each backend fills these in) ----------
    def open_connection(self):
        raise NotImplementedError

    def close_connection(self):
        raise NotImplementedError

    def request_status(self):
        """Send STATUS? (the handshake when the app connects)."""
        raise NotImplementedError

    def home(self):
        raise NotImplementedError

    def start_scan(self, faces, level):
        raise NotImplementedError

    def pause(self):
        raise NotImplementedError

    def resume(self):
        raise NotImplementedError

    def abort(self):
        raise NotImplementedError

    def jog(self, axis, direction):
        raise NotImplementedError

    def jog_stop(self):
        raise NotImplementedError