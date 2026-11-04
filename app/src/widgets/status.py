from PySide6.QtWidgets import QLabel
import theme


class StatusLabel(QLabel):
    """The SYSTEM IDLE.... / SYSTEM SCANNING... text at the top of the viz-x pages."""

    def __init__(self, text=""):
        super().__init__(text)
        self.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_NORMAL};
        """)