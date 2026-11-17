from PySide6.QtCore import Signal
from pyvistaqt import QtInteractor

import theme
from face_table import FACE_TABLE


class ModelView(QtInteractor):
    """The interactive 3D Neptune model (from the STEP). Drag to rotate, scroll to zoom, click to pick sides."""

    selection_changed = Signal(list)   # fires with the picked sides every time the selection changes

    def __init__(self, step_model, selectable=True, parent=None):
        super().__init__(parent)
        self.step_model = step_model                # the loaded STEP (shared, only loaded once)
        self.set_background(theme.BACKGROUND)       # same color as the page, so it looks like it's floating

        # which side each CAD face belongs to, from the face table (e.g. face 42 → "side2")
        self.side_of = {}
        for side, info in FACE_TABLE.items():
            for face_id in info["main"] + info["details"]:
                self.side_of[face_id] = side

        # draw every CAD face as its own piece, and remember each one by face number
        self.face_actors = {}
        for face_id, mesh in step_model.meshes.items():
            mesh.field_data["face_id"] = [face_id]  # stamp the face number onto the mesh itself
            self.face_actors[face_id] = self.add_mesh(mesh, color=theme.MODEL_COLOR)

        self.reset_camera()                         # zoom so the whole model fits

        self.selected = set()                       # which sides are picked, like {"side2", "side5"}

        # clicking a face calls _on_pick (only on pages where you're allowed to pick, like Home)
        if selectable:
            self.enable_mesh_picking(
                self._on_pick,
                left_clicking=True,     # normal left click
                show=False,             # don't draw PyVista's pink outline, we do our own coloring
                show_message=False,     # don't show PyVista's help text
            )

    # ---------- clicking ----------

    def _on_pick(self, mesh):
        """A face got clicked: toggle its whole side on/off."""
        if mesh is None or "face_id" not in mesh.field_data:
            return                                  # clicked empty space
        face_id = int(mesh.field_data["face_id"][0])
        side = self.side_of.get(face_id)
        if side is None:
            return                                  # legs, bottom, etc. aren't part of any side

        if side in self.selected:
            self.selected.remove(side)              # already picked → unpick it
        else:
            self.selected.add(side)                 # not picked → pick it

        self._color_side(side)
        self.selection_changed.emit(self.selected_sides())

    def _color_side(self, side):
        """Paint every face of a side: highlighted if picked, normal if not."""
        color = theme.SELECTED_COLOR if side in self.selected else theme.MODEL_COLOR
        info = FACE_TABLE[side]
        for face_id in info["main"] + info["details"]:
            if face_id in self.face_actors:
                self.face_actors[face_id].prop.color = color
        self.render()                               # redraw so the color change shows

    # ---------- called from outside ----------

    def selected_sides(self):
        """The picked sides, in order, like ["side2", "side5"]."""
        return sorted(self.selected)

    def set_selected(self, sides):
        """Pick exactly these sides (used by select all / clear, and to show what's being scanned)."""
        self.selected = set(sides)
        for side in FACE_TABLE:
            self._color_side(side)                  # recolor every side to match
        self.selection_changed.emit(self.selected_sides())