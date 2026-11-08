import pyvista as pv
import numpy as np
from pathlib import Path

from step_model import StepModel
from radeyeDriver import Radeye
from widgets.model_view import ModelView

MODEL = Path(__file__).parent / "assets" / "heat_mesh_1000mm.vtp"

class Heatmap(ModelView):
    def __init__(self, step_model, threshold):
        super().__init__(step_model, False)

        self.threshold = threshold

        self.heat_mesh = pv.read(MODEL).clean()
        
        self.xyz_mm = np.empty((0, 3))
        self.dose = np.empty(0)

    def set_data(self):
        self.xyz_mm = np.array([
            [ -700, -375.8, 1200],   # row 0
            [ 100, -375.8, 1200],   # row 1
            [ 700,  -375.8, 1200],   # row 2
        ])

        self.dose = np.array([0.8, 1.4, 3])

    def simulate_data(self, amount):
        rng = np.random.default_rng()

        self.dose = rng.uniform(0.1, 1, amount)

    def simulate_coords(self, amount):
        rng = np.random.default_rng()

        x = rng.uniform(-900.0, 900.0, amount)
        z = rng.uniform(862.0, 1790.0, amount)
        y = np.where(x > 347.4, -443.7, -375.8)    # panel sticks out on the right
                
        self.xyz_mm = np.column_stack([x, y, z])

    def generate_position(self):
        """Placeholder until real positions exist."""
        rng = np.random.default_rng()

        x = rng.uniform(-900.0, 900.0)
        z = rng.uniform(862.0, 1790.0)
        y = -443.7 if x > 347.4 else -375.8     # panel sticks out on the right
        return [x, y, z]

    def add_reading(self, xyz, doses):
        """Add one or many readings and repaint once.
        xyz: [x, y, z] array in mm. 
        doses: values in µSv/h."""
        xyz = np.atleast_2d(np.array(xyz, dtype=float))
        doses = np.atleast_1d(np.array(doses, dtype=float))
        
        if len(xyz) != len(doses):
            raise ValueError(f"{len(xyz)} positions but {len(doses)} doses")

        self.xyz_mm = np.vstack([self.xyz_mm, xyz])
        self.dose = np.append(self.dose, doses)
        self._draw_heatmap()        

    def clear_readings(self):
        """Wipe the heatmap and go back to the plain model."""
        self.xyz_mm = np.empty((0, 3))
        self.dose = np.empty(0)
        self.remove_actor("heat")
        self.remove_actor("dots")
        for actor in self.face_actors.values():
            actor.visibility = True
        self.render()

    def _draw_heatmap(self):
        readings = pv.PolyData(np.asarray(self.xyz_mm, dtype=float))
        readings["dose"] = self.dose

        painted = self.heat_mesh.interpolate(
            readings, radius=50, sharpness=4,
            strategy="null_value", null_value=np.nan,
        )

        style = dict(scalars="dose", cmap="RdYlGn_r",
                        clim=[0, self.threshold], above_color="darkred")
        self.add_mesh(painted, nan_color="lightgray", name="heat", **style)
        self.add_points(readings, render_points_as_spheres=True, point_size=12,
                        show_scalar_bar=False, name="dots", **style)

        for actor in self.face_actors.values():   # hide the plain faces underneath
            actor.visibility = False
        self.render()

if __name__ == "__main__":
    import sys
    import numpy as np
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QMainWindow

    from step_model import StepModel
    from widgets.model_view import ModelView

    SIMULATE = True                      # False = read the real RadEye
    PORT = "/dev/tty.usbserial-AQ002K50"

    rng = np.random.default_rng()
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Radiation Heatmap")
    view = Heatmap(StepModel(), 1)
    window.setCentralWidget(view)
    window.resize(1000, 750)
    view.view_xz()
    view.setEnabled(False)  # never rotates
    window.show()
    
    timer = QTimer()

    def simulate_reading(dose):
        view.add_reading(view.generate_position(), dose)
        window.statusBar().showMessage(f"Latest: {dose:.2f} µSv/h   |   Readings: {len(view.dose)}")

    def actual_reading(radeye):
        frame = radeye.getFrame()
        radiation = radeye.parseToGetData(frame)
        if radiation is not None:
            view.add_reading(view.generate_position(), radiation)
            window.statusBar().showMessage(f"Latest: {radiation:.2f} µSv/h   |   Readings: {len(view.dose)}")

    if SIMULATE:
        timer.timeout.connect(lambda: simulate_reading(rng.uniform(0.1, 1.2)))
        timer.start(100)                 # a fake reading every 100ms
    else:
        radeye = Radeye(PORT)
        timer.timeout.connect(lambda: actual_reading(radeye))
        timer.start(50)
        app.aboutToQuit.connect(timer.stop)
        app.aboutToQuit.connect(radeye.close)
        
    app.aboutToQuit.connect(view.close)
    sys.exit(app.exec())