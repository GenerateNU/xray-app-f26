import serial

ser = serial.Serial('/dev/tty.usbserial-AQ002K50', baudrate=9600, timeout=1)

# Read response
rawData = line = ser.read_all()
rawData1 = line = ser.read()

print(rawData)
print(rawData1)

if ser.in_waiting > 0:
    incoming_data = ser.read(ser.in_waiting)
    print(incoming_data)

# possible
#line = ser.readline().decode("utf-8").strip()
#print(line)

def send_and_read(ser, command, timeout=2):
    """Send a command string and return the response line."""
    ser.reset_input_buffer()
    ser.write(command.encode() + b'\r\n')

    old_timeout = ser.timeout
    ser.timeout = timeout
    try:
        return ser.readline().decode('utf-8').strip()
    finally:
        ser.timeout = old_timeout

# response = send_and_read(ser, "AT+GMR")
# print(f"Firmware: {response}")

ser.close()
