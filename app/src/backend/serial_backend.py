import serial
from PySide6.QtCore import QTimer

from backend.base import Backend
from backend.reader_thread import ReaderThread


class SerialBackend(Backend):
    """Talks to the MCU over a serial port, one text line per message."""

    HEARTBEAT_MS = 1000     # send PING this often so the firmware knows the app is alive

    def __init__(self, port, baud=115200):
        super().__init__()
        self.port = port          # e.g. "/dev/cu.usbmodem1103"
        self.baud = baud          # has to match the firmware's baud rate
        self._serial = None       # the open port (None = not connected)
        self._reader = None       # the reader thread (made when we connect)

        # heartbeat: send PING every second so the firmware knows we're alive
        self._heartbeat = QTimer(self)
        self._heartbeat.setInterval(self.HEARTBEAT_MS)
        self._heartbeat.timeout.connect(lambda: self._send("PING"))

    # ---------- connection ----------

    def open_connection(self):
        try:
            self._serial = serial.Serial(self.port, self.baud, timeout=0.1)
        except serial.SerialException as e:
            print(f"[serial] couldn't open {self.port}: {e}")
            self._serial = None
            self.connection_changed.emit(False)
            return

        # start listening on a separate thread
        self._reader = ReaderThread(self._serial)
        self._reader.line_received.connect(self._handle_line)          # runs back on the main thread
        self._reader.connection_lost.connect(self._on_connection_lost)
        self._reader.start()                                           # start() runs run() on the new thread

        self._heartbeat.start()
        print(f"[serial] connected to {self.port} @ {self.baud}")
        self.connection_changed.emit(True)
        self.request_status()                                          # the handshake: "are you homed?"

    def close_connection(self):
        self._heartbeat.stop()
        if self._reader is not None:
            self._reader.stop()          # stop listening BEFORE closing the port
            self._reader = None
        if self._serial is not None:
            self._serial.close()
            self._serial = None
        self.connection_changed.emit(False)

    def _on_connection_lost(self):
        print("[serial] connection lost")
        self.close_connection()

    # ---------- sending ----------

    def _send(self, line):
        """Send one line to the MCU."""
        if self._serial is None:
            return                                       # not connected, nowhere to send it
        try:
            self._serial.write((line + "\n").encode())   # text → add the line ending → bytes
        except (serial.SerialException, OSError):
            self._on_connection_lost()                   # cable got pulled mid-send

    # ---------- app → machine (the contract) ----------

    def request_status(self):
        self._send("STATUS?")

    def home(self):
        self._send("HOME")

    def start_scan(self, faces, level):
        # placeholder: later the scan planner sends MOVE lines instead
        self._send(f"START {','.join(faces)} {level}")

    def pause(self):
        self._send("PAUSE")

    def resume(self):
        self._send("RESUME")

    def abort(self):
        self._send("ABORT")

    def jog(self, axis, direction):
        sign = "+" if direction > 0 else "-"
        self._send(f"JOG {axis.upper()}{sign}")

    def jog_stop(self):
        self._send("JOG STOP")

    # ---------- machine → app (turn lines into signals) ----------

    def _handle_line(self, line):
        """One line from the MCU → the matching signal. Runs on the main thread."""
        parts = line.split(maxsplit=1)       # split off just the first word
        if not parts:
            return                           # empty line, ignore it
        word = parts[0]                      # e.g. "PROGRESS"
        rest = parts[1] if len(parts) > 1 else ""   # e.g. "40" (or "" if nothing after)

        try:
            if word == "STATUS":                         # STATUS HOMED / NOT_HOMED / ERROR
                self.status_received.emit(rest)
            elif word == "HOMED":
                self.homed.emit()
            elif word == "PROGRESS":                     # PROGRESS 40
                self.progress.emit(int(rest))
            elif word == "POS":                          # POS 100.0 200.0 50.0
                x, y, z = (float(v) for v in rest.split())
                self.position.emit(x, y, z)
            elif word == "DONE":
                self.scan_finished.emit()
            elif word == "ERR":                          # ERR limit switch hit
                self.error.emit(rest or "unknown error")
            elif word in ("OK", "PONG"):
                pass                                     # just acknowledgements, nothing to do
            else:
                print(f"[serial] unknown message: {line!r}")
        except ValueError:
            print(f"[serial] couldn't read message: {line!r}")