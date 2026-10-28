from pathlib import Path

import numpy as np
import cadquery as cq
import pyvista as pv

STEP_PATH = Path(__file__).parent / "assets" / "neptune.step"


class StepModel:
    """Loads the Neptune STEP file once. Keeps the exact CAD faces + a drawable mesh for each one."""

    def __init__(self, path=STEP_PATH, tolerance=0.5):
        shape = cq.importers.importStep(str(path)).val()
        self.faces = shape.Faces()          # exact CAD faces (for the planner later)
        self.meshes = {}                    # face number → PyVista mesh (for drawing)

        for i, face in enumerate(self.faces):
            mesh = self._to_mesh(face, tolerance)
            if mesh is not None:
                self.meshes[i] = mesh

    @staticmethod
    def _to_mesh(face, tolerance):
        """Turn one exact CAD face into triangles PyVista can draw."""
        verts, tris = face.tessellate(tolerance)
        if not tris:
            return None                                    # some tiny faces can come out empty, so skip those
        points = np.array([(v.x, v.y, v.z) for v in verts])
        cells = np.hstack([[3, a, b, c] for a, b, c in tris])
        return pv.PolyData(points, cells)