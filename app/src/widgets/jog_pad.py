from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPolygonF, QFont
from PySide6.QtWidgets import QWidget
import theme


class JogPad(QWidget):
    """The round jog controller from the figma (Desktop 3)."""

    def __init__(self, size=284):
        super().__init__()
        self.setFixedSize(size, size)   # always a perfect square, so the circle stays round

    def paintEvent(self, event):
        # sizes, measured from the center
        outer = self.width() / 2        # radius of the whole pad
        inner = outer * 0.68            # radius of the darker middle circle
        center = QPointF(outer, outer)  # middle of the widget

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)  # smooth edges instead of jagged
        p.setPen(Qt.PenStyle.NoPen)                         # no outlines on shapes

        # 1. outer ring (light)
        p.setBrush(QColor(theme.BUTTON_PRIMARY))
        p.drawEllipse(center, outer, outer)

        # 2. inner circle (darker), drawn on top of the ring
        p.setBrush(QColor(theme.JOG_INNER))
        p.drawEllipse(center, inner, inner)

        # 3. big up / down triangles in the middle
        gap = inner * 0.06       # little space between the two triangles
        height = inner * 0.7     # how tall each triangle is
        half_w = inner * 0.55    # half of each triangle's width
        up = QPolygonF([
            QPointF(outer, outer - gap - height),   # tip (top)
            QPointF(outer - half_w, outer - gap),   # bottom left
            QPointF(outer + half_w, outer - gap),   # bottom right
        ])
        down = QPolygonF([
            QPointF(outer, outer + gap + height),   # tip (bottom)
            QPointF(outer - half_w, outer + gap),   # top left
            QPointF(outer + half_w, outer + gap),   # top right
        ])
        p.setBrush(QColor(theme.BUTTON_PRIMARY))
        p.drawPolygon(up)
        p.drawPolygon(down)

        # 4. little arrows on the ring
        p.setPen(QColor(theme.BACKGROUND))
        p.setFont(QFont(theme.FONT_FAMILY, 13))
        mid = (outer + inner) / 2    # halfway across the ring
        box = 24                     # size of the box each arrow is centered in
        arrows = {"^": (0, -1), "v": (0, 1), "<": (-1, 0), ">": (1, 0)}
        for arrow, (dx, dy) in arrows.items():
            x = outer + dx * mid
            y = outer + dy * mid
            p.drawText(QRectF(x - box / 2, y - box / 2, box, box), Qt.AlignmentFlag.AlignCenter, arrow)

        p.end()   # done drawing