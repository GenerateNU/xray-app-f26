"""code to read data from radeye when AutoSend is on
more info can be found in my workbook on notion"""

from typing import Optional
import serial
import time

class Radeye():
    STX = b"\x02"
    ETX =  b"\x03"
    BEL = b"\x07"

    def __init__(self, port):
        self.buf = b''
        self.serial = serial.Serial(port, baudrate=9600, bytesize=serial.SEVENBITS,
                            parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_TWO, timeout=1)

    def _checksum(self, value: str) -> str:
        total = 0x02 + sum(value.encode("ascii"))
        return f"{total & 0xFF:02X}"

    def parseToGetData(self, frame: bytes) -> Optional[float]:
        if (frame is None):
            return None
        
        start = frame.find(self.STX)
        end = frame.find(self.ETX, start + 1)

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

    def getFrame(self) -> Optional[bytes]:
        """returns a complete frame if one is ready, otherwise None right away."""

        waiting = self.serial.in_waiting
        if waiting:
            self.buf += self.serial.read(waiting)       # only what's already arrived, never waits
            if len(self.buf) > 4096:
                self.buf = self.buf[-512:]

        start = self.buf.find(self.STX)
        end = self.buf.find(self.ETX, start + 1)

        if start < 0 or end < start:
            return None                                  # no complete frame yet

        frame = self.buf[start : end + 1]
        self.buf = self.buf[end + 1:]
        return frame

    def init(self):
        self.serial.reset_input_buffer()
        self.serial.write(b"@")

        if self.serial.read(1) == b">":
            self.serial.write(b"*C1\r\n")
            print(self.serial.read_until(b"\n"))   # expect b'#\r\n'
            self.serial.write(b"@")
            print(self.serial.read(1))             # expect b'\x07'

    def close(self):
        self.serial.close()

if __name__ == "__main__":
    print("MAKE SURE AUTOSEND IS TURNED ON IN RADEYE or else you won't get anything")
    
    usb = input("Enter the usb name: ") # '/dev/tty.usbserial-AQ002K50' for me
        
    ser = serial.Serial(usb, baudrate=9600, bytesize=serial.SEVENBITS,
                    parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_TWO, timeout=1)
    radeye = Radeye('/dev/tty.usbserial-AQ002K50')
    #init(ser)
    
    try:
        while True:
            frame = radeye.getFrame()
            radiation = radeye.parseToGetData(frame)

            if radiation is not None:
                print(f"{radiation:.2f} uSv/h")

            time.sleep(0.05)
    except KeyboardInterrupt:
        ser.close()


# still need to add timeouts, 
# check to see if response is correct, 
# figure out to turn on AutoSend through software. 