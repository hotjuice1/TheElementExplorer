from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox, QCheckBox, QLabel
from app.settings import AUTO_ROTATE

class Controls(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(4,4,4,4)
        self.pause = QPushButton("Pause")
        self.pause.setCheckable(True)
        self.pause.setToolTip("Pause animation · Space")
        self.speed = QComboBox()
        for value in (.25,.5,1,2,4):
            self.speed.addItem(f"{value:g}×",value)
        self.speed.setCurrentIndex(2)
        self.speed.setAccessibleName("Animation speed")
        self.auto = QCheckBox("Auto rotate")
        self.auto.setChecked(AUTO_ROTATE)
        self.reset = QPushButton("Reset view")
        self.reset.setToolTip("Reset camera · R")
        self.center = QPushButton("Center nucleus")
        for widget in (self.pause,QLabel("Speed"),self.speed,self.auto):
            row.addWidget(widget)
        row.addStretch()
        row.addWidget(self.center)
        row.addWidget(self.reset)
