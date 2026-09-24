"""Responsive, keyboard-accessible periodic table drawn in a single widget."""
from PySide6.QtCore import Qt, QRectF, Signal, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget, QToolTip
from app.theme import CATEGORIES, ACCENT, MUTED
from models.element import Element

class PeriodicTable(QWidget):
    element_selected = Signal(int)

    def __init__(self, elements: tuple[Element, ...], parent=None) -> None:
        super().__init__(parent)
        self.elements = elements
        self.selected = 79
        self.matches = {e.atomic_number for e in elements}
        self.hovered = None
        self.hover_alpha = 0.0
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(130)
        self.animation.valueChanged.connect(self._animate_hover)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(940, 326)
        self.setAccessibleName("Periodic table, 118 elements. Left and right arrows browse; Enter selects.")

    def _animate_hover(self, value: float) -> None:
        self.hover_alpha = value
        self.update()

    def cell_rect(self, element: Element) -> QRectF:
        z = element.atomic_number
        if 57 <= z <= 71:
            row,col = 7.55,z-54
        elif 89 <= z <= 103:
            row,col = 8.55,z-86
        else:
            row,col = element.period-1,element.group-1
        cell_w = self.width()/18
        cell_h = (self.height()-20)/9.55
        return QRectF(col*cell_w+2,20+row*cell_h+2,cell_w-4,cell_h-4)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont("Segoe UI",7))
        p.setPen(QColor(MUTED))
        for group in range(1,19):
            p.drawText(QRectF((group-1)*self.width()/18,0,self.width()/18,18),Qt.AlignmentFlag.AlignCenter,str(group))
        for e in self.elements:
            rect = self.cell_rect(e)
            active = e.atomic_number in self.matches
            selected = e.atomic_number == self.selected
            color = QColor(CATEGORIES[e.category])
            p.setOpacity(1 if active else .18)
            fill = QColor(color)
            fill.setAlpha(45 if selected else int(22+35*self.hover_alpha) if e.atomic_number == self.hovered else 18)
            p.setBrush(fill)
            border = QColor(ACCENT) if selected else QColor(color)
            if not selected:
                border.setAlpha(160 if e.atomic_number == self.hovered else 65)
            p.setPen(QPen(border,1.8 if selected else .8))
            p.drawRoundedRect(rect,4,4)
            p.setFont(QFont("Segoe UI",6))
            p.setPen(color)
            p.drawText(rect.adjusted(4,1,-3,-1),Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,str(e.atomic_number))
            p.setFont(QFont("Segoe UI",12 if rect.height() > 36 else 10,QFont.Weight.DemiBold))
            p.drawText(rect.adjusted(0,0,0,-5),Qt.AlignmentFlag.AlignCenter,e.symbol)
            p.setFont(QFont("Segoe UI",6))
            name = p.fontMetrics().elidedText(e.name,Qt.TextElideMode.ElideRight,int(rect.width()-5))
            p.drawText(rect.adjusted(2,0,-2,-1),Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,name)
        p.setOpacity(1)
        p.setPen(QColor(MUTED))
        p.setFont(QFont("Segoe UI",8))
        cell_w,cell_h = self.width()/18,(self.height()-20)/9.55
        for row,text in ((5,"57–71"),(6,"89–103")):
            p.drawText(QRectF(cell_w*2,20+row*cell_h,cell_w,cell_h),Qt.AlignmentFlag.AlignCenter,text)
        for row,text in ((7.55,"LANTHANIDES"),(8.55,"ACTINIDES")):
            p.drawText(QRectF(0,20+row*cell_h,cell_w*3-12,cell_h),Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,text)
        p.end()

    def hit(self, point) -> Element | None:
        return next((e for e in self.elements if self.cell_rect(e).contains(point)),None)

    def mouseMoveEvent(self, event) -> None:
        e = self.hit(event.position())
        hovered = e.atomic_number if e else None
        if hovered != self.hovered:
            self.hovered = hovered
            self.animation.stop()
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()
            self.setCursor(Qt.CursorShape.PointingHandCursor if e and e.atomic_number in self.matches else Qt.CursorShape.ArrowCursor)
            if e:
                QToolTip.showText(event.globalPosition().toPoint(),f"{e.atomic_number} · {e.name} ({e.symbol})\n{e.category.title()} · {e.atomic_mass:g} u",self)

    def leaveEvent(self, event) -> None:
        self.hovered = None
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            e = self.hit(event.position())
            if e and e.atomic_number in self.matches:
                self.element_selected.emit(e.atomic_number)

    def keyPressEvent(self, event) -> None:
        keys = {Qt.Key.Key_Left:-1,Qt.Key.Key_Right:1}
        if event.key() in keys:
            available = sorted(self.matches)
            if available:
                pos = available.index(self.selected) if self.selected in available else 0
                self.element_selected.emit(available[(pos+keys[event.key()]) % len(available)])
        elif event.key() in (Qt.Key.Key_Enter,Qt.Key.Key_Return) and self.selected in self.matches:
            self.element_selected.emit(self.selected)
        else:
            super().keyPressEvent(event)
