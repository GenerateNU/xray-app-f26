import math

from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPolygonF, QFont
from PySide6.QtWidgets import QWidget
import theme

# what each part of the pad moves: (axis, direction)
# ring = X/Y, triangles = Z. Change this if the real machine's axes are different.
MOVES = {
    "right":  ("x", +1),
    "left":   ("x", -1),
    "top":    ("y", +1),
    "bottom": ("y", -1),
    "up":     ("z", +1),   # top triangle
    "down":   ("z", -1),   # bottom triangle
}

# where each arrow sits on the ring, in degrees (0 = right, 90 = top, like a clock going backwards)
RING_ANGLES = {"right": 0, "top": 90, "left": 180, "bottom": 270}

# how wide each arrow's clickable slice on the ring is, in degrees
# (90 = no gaps, smaller = bigger dead zones between arrows)
ARROW_SPREAD = 60


class JogPad(QWidget):
    """The round jog controller from the figma (Desktop 3). Hold to move, let go to stop."""

    jog_pressed = Signal(str, int)   # axis ("x"/"y"/"z"), direction (+1/-1)
    jog_released = Signal()

    def __init__(self, size=284):
        super().__init__()
        self.setFixedSize(size, size)                       # perfect square so the circle stays round
        self.setCursor(Qt.CursorShape.PointingHandCursor)   # hand cursor so it feels clickable
        self.pressed = None                                  # which part is being held right now

    # ---------- shapes (used by BOTH drawing and clicking, so they always match) ----------

    def _geometry(self):
        """Center + sizes of the circle."""
        cx = self.width() / 2
        cy = self.height() / 2
        outer = min(self.width(), self.height()) / 2   # radius of the whole pad
        inner = outer * 0.68                            # radius of the darker middle circle
        return cx, cy, outer, inner

    def _triangles(self):
        """The up and down triangle shapes."""
        cx, cy, outer, inner = self._geometry()
        gap = inner * 0.06       # space between the two triangles
        height = inner * 0.7     # how tall each triangle is
        half_w = inner * 0.55    # half of each triangle's width
        up = QPolygonF([
            QPointF(cx, cy - gap - height),     # tip
            QPointF(cx - half_w, cy - gap),     # bottom left
            QPointF(cx + half_w, cy - gap),     # bottom right
        ])
        down = QPolygonF([
            QPointF(cx, cy + gap + height),     # tip
            QPointF(cx - half_w, cy + gap),     # top left
            QPointF(cx + half_w, cy + gap),     # top right
        ])
        return up, down

    # ---------- clicking ----------

    def _region_at(self, pos):
        """Figure out which part of the pad a click landed on (or None)."""
        cx, cy, outer, inner = self._geometry()
        dx = pos.x() - cx            # how far right of center (negative = left)
        dy = pos.y() - cy            # how far below center (negative = above)
        dist = math.hypot(dx, dy)    # straight-line distance from center

        if dist > outer:
            return None              # outside the circle

        if dist <= inner:
            # in the middle: only the triangles themselves count
            up, down = self._triangles()
            if up.containsPoint(pos, Qt.FillRule.OddEvenFill):
                return "up"
            if down.containsPoint(pos, Qt.FillRule.OddEvenFill):
                return "down"
            return None              # dark space around the triangles

        # on the ring: which arrow is the click closest to, by angle?
        angle = math.degrees(math.atan2(-dy, dx)) % 360    # 0 = right, 90 = top, 180 = left, 270 = bottom
        for name, arrow_angle in RING_ANGLES.items():
            off_by = abs((angle - arrow_angle + 180) % 360 - 180)   # how many degrees away from this arrow
            if off_by <= ARROW_SPREAD / 2:
                return name
        return None                  # in a gap between arrows

    def mousePressEvent(self, event):
        region = self._region_at(event.position())
        if region:
            self.pressed = region
            axis, direction = MOVES[region]
            print("JOG PRESSED:", axis, direction)   # TEMPORARY, to check it works
            self.jog_pressed.emit(axis, direction)
            self.update()                             # redraw so the pressed part lights up

    def mouseReleaseEvent(self, event):
        if self.pressed:
            self.pressed = None
            print("JOG RELEASED")                    # TEMPORARY
            self.jog_released.emit()
            self.update()                             # redraw so it goes back to normal

    # ---------- drawing ----------

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            self._draw(p)
        finally:
            p.end()   # ALWAYS close the painter, even if drawing errors

    def _draw(self, p):
        cx, cy, outer, inner = self._geometry()
        center = QPointF(cx, cy)

        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        # 1. outer ring
        p.setBrush(QColor(theme.BUTTON_PRIMARY))
        p.drawEllipse(center, outer, outer)

        # 2. if a ring arrow is held, darken just its slice
        if self.pressed in RING_ANGLES:
            start = RING_ANGLES[self.pressed] - ARROW_SPREAD / 2
            p.setBrush(QColor(theme.BUTTON_PRESSED))
            p.drawPie(QRectF(cx - outer, cy - outer, outer * 2, outer * 2),
                      int(start * 16), int(ARROW_SPREAD * 16))   # Qt measures pie angles in 1/16ths of a degree

        # 3. inner circle (drawn on top, so it covers the middle of the pie slice)
        p.setBrush(QColor(theme.JOG_INNER))
        p.drawEllipse(center, inner, inner)

        # 4. triangles (the held one turns white)
        up, down = self._triangles()
        for name, triangle in (("up", up), ("down", down)):
            color = theme.TEXT_PRIMARY if self.pressed == name else theme.BUTTON_PRIMARY
            p.setBrush(QColor(color))
            p.drawPolygon(triangle)

        # 5. little arrows on the ring
        p.setPen(QColor(theme.BACKGROUND))
        p.setFont(QFont(theme.FONT_FAMILY, 13))
        mid = (outer + inner) / 2
        box = 24
        arrows = {"^": (0, -1), "v": (0, 1), "<": (-1, 0), ">": (1, 0)}
        for arrow, (ax, ay) in arrows.items():
            x = cx + ax * mid
            y = cy + ay * mid
            p.drawText(QRectF(x - box / 2, y - box / 2, box, box), Qt.AlignmentFlag.AlignCenter, arrow)