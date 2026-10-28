from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel
import theme


class ProgressBar(QWidget):
    """Thin vertical progress bar with the % under it (Desktop 7)."""

    def __init__(self):
        super().__init__()
        self.setFixedWidth(40)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # the bar itself
        self.bar = QProgressBar()
        self.bar.setOrientation(Qt.Vertical)    # standing up, like the figma
        self.bar.setInvertedAppearance(True)    # fills top to bottom
        self.bar.setTextVisible(False)          # we show the % in our own label
        self.bar.setRange(0, 100)
        self.bar.setFixedWidth(10)              # thin
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {theme.PROGRESS_CLR};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {theme.PROGRESS_BGND};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.bar, 1, Qt.AlignHCenter)

        # the % under it
        self.label = QLabel()
        self.label.setStyleSheet(f"""
            color: {theme.TEXT_PRIMARY};
            font-family: {theme.FONT_FAMILY};
            font-size: {theme.FONT_SIZE_NORMAL};
        """)
        layout.addWidget(self.label, 0, Qt.AlignHCenter)

        self.set_progress(0)   # start empty

    def set_progress(self, percent):
        """Update the bar and the % label."""
        percent = max(0, min(100, int(percent)))   # keep it between 0 and 100
        self.bar.setValue(percent)
        self.label.setText(f"{percent}%")