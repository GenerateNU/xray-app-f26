"""THIS IS FAKE BACKEND CONFIG. POLLY WILL ADD THER READL ONES HERE TOO BUT YEA"""

# Flip this to False once the real board + firmware are ready.
USE_FAKE_BACKEND = True

# Only used when USE_FAKE_BACKEND = False
SERIAL_PORT = "/dev/cu.usbmodem1103"   # your board's port (find it with: python -m serial.tools.list_ports)
SERIAL_BAUD = 115200