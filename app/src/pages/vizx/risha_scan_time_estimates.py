"""
Scan time estimates for the picked sides.

as discussed, i Assumed the square wave path where  the sensor sweeps straight across the x axis side, stops,
steps down one line gap via y axis motor, stops, and sweeps back the other way.

"""
import math
from face_table import FACE_TABLE

SCAN_SPEED_MM_S = 50.0   # speed of the x motor in (mm/s)
LINE_GAP_MM = 50.0       # distance between sweeps in mm (this is basically how much the rad eye can see)
STOP_TIME_S = 1.0        # extra time at each corner to slow down and speed up again


def side_size_mm(step_model, side):
    """sweep the width and height of one side in mm, measured from the STEP file."""
    # put the side's main faces in one box by combining their bounds
    xs, ys, zs = [], [], []
    for face_id in FACE_TABLE[side]["main"]:
        xmin, xmax, ymin, ymax, zmin, zmax = step_model.meshes[face_id].bounds
        xs += [xmin, xmax]
        ys += [ymin, ymax]
        zs += [zmin, zmax]

    size_x = max(xs) - min(xs)
    size_y = max(ys) - min(ys)
    size_z = max(zs) - min(zs)

    # which two sizes matter depends on which way the side faces
    nx, ny, nz = FACE_TABLE[side]["normal"]
    if nz != 0:                  # top: sweep along X, step along Y
        return size_x, size_y
    if nx != 0:                  # +X / -X sides: sweep along Y, step down Z
        return size_y, size_z
    return size_x, size_z        # +Y / -Y sides: sweep along X, step down Z


def side_sizes(step_model):
    """{side: (sweep width, height)} for every side. Call once, the STEP doesn't change."""
    return {side: side_size_mm(step_model, side) for side in FACE_TABLE}


def side_time_s(width_mm, height_mm):
    """Seconds to scan one side with the square wave path."""
    sweeps = math.ceil(height_mm / LINE_GAP_MM)                 # rows across the side
    sweep_time = width_mm / SCAN_SPEED_MM_S + STOP_TIME_S        # one row across
    step_time = LINE_GAP_MM / SCAN_SPEED_MM_S + STOP_TIME_S      # move down to the next row
    return sweeps * sweep_time + (sweeps - 1) * step_time


def scan_time_s(sides, sizes):
    """Total seconds for the picked sides (one side = that side acc to amy's code rn T-T, more = the sum)."""
    total = 0.0
    for side in sides:
        width, height = sizes[side]
        total += side_time_s(width, height)
    return total


def format_time(seconds):
    """Turns seconds into text like '24 min' or '1 h 27 min' to be displayed in the home_page.py file."""
    minutes = round(seconds / 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours} h {minutes} min"
    return f"{minutes} min"