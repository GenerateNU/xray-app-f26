from pathlib import Path

import numpy as np
import cadquery as cq
import pyvista as pv

from face_table import FACE_TABLE

STEP_PATH = Path(__file__).parent / "assets" / "neptune.step"
SIDE_COLORS = {"side1": "red", "side2": "blue", "side3": "green", "side4": "orange", "side5": "purple"}

faces = cq.importers.importStep(str(STEP_PATH)).val().Faces()

# flip the table around: face number → which side it belongs to
side_of = {}
for side, info in FACE_TABLE.items():
    for face_id in info["main"] + info["details"]:
        side_of[face_id] = side

plotter = pv.Plotter()
for i, face in enumerate(faces):
    verts, tris = face.tessellate(0.5)
    points = np.array([(v.x, v.y, v.z) for v in verts])
    cells = np.hstack([[3, a, b, c] for a, b, c in tris])
    color = SIDE_COLORS.get(side_of.get(i), "lightgray")   # not in a side = gray
    plotter.add_mesh(pv.PolyData(points, cells), color=color)

plotter.add_legend([[side, color] for side, color in SIDE_COLORS.items()])
plotter.show()