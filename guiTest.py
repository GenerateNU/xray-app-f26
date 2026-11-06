import tkinter as tk
import serial
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from radeye_testing.radeyeDriver import parseToGetData, getFrame

ser = serial.Serial("/dev/tty.usbserial-AQ002K50", baudrate=9600, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_TWO, timeout=1)

root = tk.Tk()
label = tk.Label(root, text="Waiting...", font=("Arial", 24))
label.pack()

def display_radiation():
    try:
        frame = getFrame(ser)
        radiation = parseToGetData(frame)
        if radiation is not None:
            label.config(text=f"{radiation:.2f} uSv/h")
        else:
            label.config(text="waiting")

        root.after(50, display_radiation)
    except KeyboardInterrupt:
            ser.close()

display_radiation()
root.mainloop()