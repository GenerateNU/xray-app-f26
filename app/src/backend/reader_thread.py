import serial
from PySide6.QtCore import QThread, Signal


class ReaderThread(QThread):
    """Waits for lines from the MCU on its own thread, so the app never freezes."""

    line_received = Signal(str)     # one full line from the MCU (without the \n)
    connection_lost = Signal()      # the port broke (cable pulled, board reset)

    def __init__(self, ser):
        super().__init__()
        self.ser = ser              # the open serial port (from SerialBackend)
        self.running = True

    def run(self):
        """Everything in here runs on the separate thread. Started with .start()."""
        buffer = b""
        while self.running:
            try:
                chunk = self.ser.readline()     # waits up to the port's timeout, returns b"" if nothing came
            except (serial.SerialException, OSError):
                self.connection_lost.emit()
                break
            if not chunk:
                continue                        # nothing yet, loop again
            buffer += chunk
            if buffer.endswith(b"\n"):          # only pass along FULL lines (a timeout can cut one in half)
                self.line_received.emit(buffer.decode(errors="replace").strip())
                buffer = b""

    def stop(self):
        """Tell the loop to end, then wait until it actually has."""
        self.running = False
        self.wait()