from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel


class ClickableLabel(QLabel):
    """A QLabel you can click. Used for the nav tabs and the reports link."""
    clicked = Signal()

    def __init__(self, text=""):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)   # hand cursor so it looks clickable

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mouseReleaseEvent(event)