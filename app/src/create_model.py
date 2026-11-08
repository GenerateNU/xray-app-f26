from step_model import StepModel
from radeyeDriver import Radeye
from widgets.model_view import ModelView
import pyvista as pv
import numpy as np
from pathlib import Path

CACHE = Path(__file__).parent / "assets" / "heat_mesh_1000mm.vtp"

mesh = pv.merge(list(StepModel().meshes.values()))
heat_mesh = mesh.triangulate().subdivide_adaptive(max_edge_len=1000.0)
heat_mesh.save(CACHE)