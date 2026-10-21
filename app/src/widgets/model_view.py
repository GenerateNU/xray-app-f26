from pathlib import Path
import pyvista as pv
from pyvistaqt import QtInteractor
import theme

# widgets/ -> src/ -> src/assets/neptune.stl
MODEL_PATH = Path(__file__).parent.parent / "assets" / "neptune.stl"


class ModelView(QtInteractor):
    """The interactive 3D Neptune model. Drag to rotate, scroll to zoom."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_background(theme.CARD_BACKGROUND)

        self.mesh = pv.read(MODEL_PATH)
        self.add_mesh(self.mesh, color=theme.MODEL_COLOR, smooth_shading=True)
        self.reset_camera()