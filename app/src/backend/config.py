# Serial connection to the MCU.
# Find your board's port with:  python -m serial.tools.list_ports -v
SERIAL_PORT = "/dev/cu.usbmodem1103"   # TODO: replace with your board's port
SERIAL_BAUD = 115200                   # TODO: must match the firmware's baud rate