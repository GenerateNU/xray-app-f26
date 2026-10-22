"code to read data from radeye when AutoSend is on"
"more info can be found in my workbook on notion"


from typing import Optional

import serial

STX = b"\x02"
ETX =  b"\x03"
BEL = b"\x07"

buf = b''

def checksum(value: str) -> str:
    total = 0x02 + sum(value.encode("ascii"))
    return f"{total & 0xFF:02X}"

def parseToGetData(buf: bytes) -> Optional[float]:
    start = buf.find(STX)
    end = buf.find(ETX, start + 1)

    if start < 0:
        return None
    if end < 0:
        return None

    body = buf[start + 1 : end].decode("ascii", errors="replace")

    data = body[:-2]
    checksumValue = body[-2:]

    if checksumValue.upper() != checksum(data):
        return None

    try:
        return float(data.split()[0]) * 0.01
    except (ValueError, IndexError):
        return None

def getFrame(ser) -> bytes:
    global buf

    while True:
        incoming = ser.read(ser.in_waiting or 1)
        
        if incoming:
            buf += incoming
            if len(buf) > 4096:
                buf = buf[-512:]

        start = buf.find(STX)
        end = buf.find(ETX, start + 1)

        if end > start and start >= 0:
            break

    frame = buf[start:end + 1]
    buf = buf[end + 1:]
    return frame

def init(ser):
    ser.reset_input_buffer()
    ser.write(b"@")

    if ser.read(1) == b">":
        ser.write(b"*C1\r\n")
        print(ser.read_until(b"\n"))   # expect b'#\r\n'
        ser.write(b"@")
        print(ser.read(1))             # expect b'\x07'


def main():
    print("MAKE SURE AUTOSEND IS TURNED ON IN RADEYE or else you won't get anything")

    usb = input("Enter the usb name: ") # '/dev/tty.usbserial-AQ002K50' for me
    
    ser = serial.Serial(usb, baudrate=9600, bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_TWO, timeout=1)

    #init(ser)

    try:
        while True:
            frame = getFrame(ser)
            radiation = parseToGetData(frame)
            if radiation is not None:
                print(f"{radiation:.2f} uSv/h")
    except KeyboardInterrupt:
        ser.close()

if __name__ == "__main__":
    main()


# still need to add timeouts, 
# check to see if response is correct, 
# figure out to turn on AutoSend through software. 