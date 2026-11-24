from typing import Optional

import serial
import time

STX = b"\x02"
ETX =  b"\x03"
END_SCAN = b"something"

class SerialManager():
    def __init__(self, port):
        self.buf = b''
        self.ser = serial.Serial(port, baudrate=115200, timeout=1)
        self.data = []

    def _confirm_ack(self, timeout=2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            b = self.ser.read(1)
            if b:
                print("got:", b.hex())
                if b[0] == 0x06:
                    print("ACK received")
                    return True
        print("timed out")
        return False

    def _confirm_wake(self):
        self.ser.write(b'@')
        self.ser.flush()
        print("sent @")
         
    def _confirm_scan_info(self, threshold, faces):
        """
        face1 = 0
        face2 = 0
        face3 = 0
        face4 = 0
        face5 = 0
        face6 = 0

        for face in faces:
            if 
        """

        frame = bytes([STX, threshold, faces, "checksum", ETX])

        self.ser.write(frame)

        return self._confirm_ack()

    def start_scan(self, threshold, faces):
        start_time = time.monotonic()
        while True:
            if time.monotonic() - start_time > 5:
                print("timed out")
                return False

            if self._confirm_wake():
                if self._confirm_scan_info(threshold, faces):
                    return True

    def _get_frame(self):
        """rewrite once we know what data we are sending"""

        waiting = self.ser.in_waiting
        if waiting:
            self.buf += self.ser.read(waiting)       # only what's already arrived, never waits
            if len(self.buf) > 4096:
                self.buf = self.buf[-512:]

        start = self.buf.find(STX)
        end = self.buf.find(ETX, start + 1)

        end_scan = self.buf.find(END_SCAN)

        if (end_scan):
            return 67

        if start < 0 or end < start:
            return None                                  # no complete frame yet

        frame = self.buf[start : end + 1]
        self.buf = self.buf[end + 1:]
        return frame

    def _checksum(self, value: str) -> str:
            total = 0x02 + sum(value.encode("ascii"))
            return f"{total & 0xFF:02X}"
    
    def _parse_get_data(self, frame: bytes) -> Optional[float]:
        """rewrite once we know what data we are sending"""
        if (frame is None):
            return None
        
        start = frame.find(STX)
        end = frame.find(ETX, start + 1)

        if start < 0:
            return None
        if end < 0:
            return None

        body = frame[start + 1 : end].decode("ascii", errors="replace")

        data = body[:-2]
        checksumValue = body[-2:]

        if checksumValue.upper() != self._checksum(data):
            return None

        try:
            return float(data.split()[0]) * 0.01
        except (ValueError, IndexError):
            return None
    
    def read_data(self):
        """rewrite once we know what data we are sending and how is this going to work"""
        while True:
            frame = self._get_frame()
            if frame == 67:
                return True
            data = self._parse_get_data(frame)
            self.data.append(data)
            


if __name__ == "__main__":
    ser = serial.Serial("/dev/tty.usbmodem101", baudrate=115200)

    try:
        while True:
            ser.write(STX)
            print("sent!")
            time.sleep(1)
    except KeyboardInterrupt:
        print("stopping")
    finally:
        ser.close()
        