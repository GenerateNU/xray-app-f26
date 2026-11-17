"""
Groups the STEP file's CAD faces into the scan sides.
Face numbers come from shape.Faces() on assets/neptune.step.

If Michael re-exports the STEP, these numbers can CHANGE.
Re-run view_sides.py to check the colors still line up.
"""

FACE_TABLE = {
    "side1": {                              # +Y side
        "normal": (0, 1, 0),
        "main": [12, 29],                   # big flat faces to sweep
        "details": [33, 36, 37, 38, 39, 40],   # recessed band + small box sticking out
    },
    "side2": {                              # -Y side
        "normal": (0, -1, 0),
        "main": [13, 28],
        "details": [32, 41, 42, 73, 74, 75, 76],   # recessed band + panel + knob
    },
    "side3": {                              # +X end
        "normal": (1, 0, 0),
        "main": [21, 19],
        "details": [15],                    # recessed band
    },
    "side4": {                              # -X end
        "normal": (-1, 0, 0),
        "main": [23, 25],
        "details": [16],                    # recessed band
    },
    "side5": {                              # top
        "normal": (0, 0, 1),
        "main": [22],
        "details": [71, 72],                # post sticking up
    },
}