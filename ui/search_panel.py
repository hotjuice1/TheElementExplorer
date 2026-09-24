from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QLabel
from app.theme import CATEGORIES

class SearchPanel(QWidget):
    changed = Signal()
    submitted = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0,0,0,0)
        self.query = QLineEdit()
        self.query.setPlaceholderText("Find an element · name, symbol or atomic number")
        self.query.setClearButtonEnabled(True)
        self.query.setAccessibleName("Search elements")
        row.addWidget(self.query,2)
        self.category,self.period,self.block = QComboBox(),QComboBox(),QComboBox()
        self.category.addItem("All categories","")
        for category in CATEGORIES:
            self.category.addItem(category.title(),category)
        self.period.addItem("All periods",0)
        for period in range(1,8):
            self.period.addItem(f"Period {period}",period)
        self.block.addItem("All blocks","")
        for block in "spdf":
            self.block.addItem(f"{block} block",block)
        for label,combo in (("Category",self.category),("Period",self.period),("Block",self.block)):
            combo.setAccessibleName(label)
            row.addWidget(combo)
            combo.currentIndexChanged.connect(lambda _: self.changed.emit())
        clear = QPushButton("Clear filters")
        clear.clicked.connect(self.clear)
        row.addWidget(clear)
        self.count = QLabel("118 / 118")
        self.count.setObjectName("muted")
        row.addWidget(self.count)
        self.query.textChanged.connect(lambda _: self.changed.emit())
        self.query.returnPressed.connect(self.submitted.emit)

    def clear(self) -> None:
        for widget in (self.query,self.category,self.period,self.block):
            widget.blockSignals(True)
        self.query.clear()
        for combo in (self.category,self.period,self.block):
            combo.setCurrentIndex(0)
        for widget in (self.query,self.category,self.period,self.block):
            widget.blockSignals(False)
        self.changed.emit()
