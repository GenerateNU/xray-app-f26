from PySide6.QtCore import QTimer
from backend.base import Backend


class FakeBackend(Backend):
    """Pretend machine for testing without hardware. Same contract as SerialBackend."""

    def __init__(self):
        super().__init__()
        self._homed = False                  # starts not homed, just like a real board after power-on
        self._percent = 0
        self._scan_timer = QTimer(self)      # ticks while a fake scan is running
        self._scan_timer.setInterval(50)     # 100 ticks × 50 ms ≈ 5 second scan
        self._scan_timer.timeout.connect(self._tick)

    # ---------- connection ----------

    def open_connection(self):
        print("[fake] connected")
        self.connection_changed.emit(True)
        self.request_status()

    def close_connection(self):
        self._scan_timer.stop()
        self.connection_changed.emit(False)

    # ---------- app → machine ----------

    def request_status(self):
        QTimer.singleShot(100, lambda: self.status_received.emit("HOMED" if self._homed else "NOT_HOMED"))

    def home(self):
        print("[fake] HOME")
        QTimer.singleShot(1500, self._finish_homing)   # pretend homing takes 1.5 s

    def start_scan(self, faces, level):
        print(f"[fake] START {faces} {level}")
        self._percent = 0
        self._scan_timer.start()

    def pause(self):
        print("[fake] PAUSE")
        self._scan_timer.stop()

    def resume(self):
        print("[fake] RESUME")
        self._scan_timer.start()

    def abort(self):
        print("[fake] ABORT")
        self._scan_timer.stop()
        self._percent = 0

    def jog(self, axis, direction):
        print(f"[fake] JOG {axis.upper()}{'+' if direction > 0 else '-'}")

    def jog_stop(self):
        print("[fake] JOG STOP")

    # ---------- fake machine behavior ----------

    def _finish_homing(self):
        self._homed = True
        self.homed.emit()

    def _tick(self):
        self._percent += 1
        self.progress.emit(self._percent)
        if self._percent >= 100:
            self._scan_timer.stop()
            self.scan_finished.emit()

    def fake_error(self, message="E-stop pressed"):
        """Testing only: pretend something serious happened."""
        print(f"[fake] ERR {message}")
        self._scan_timer.stop()
        self._homed = False
        self.error.emit(message)