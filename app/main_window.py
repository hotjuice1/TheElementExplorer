"""Compose the table, atom scene and property panel without embedding science in UI."""
from pathlib import Path
import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSplitter, QScrollArea, QPushButton, QFileDialog, QMessageBox)
from app import settings
from app.theme import CATEGORIES
from data.element_loader import ElementCatalog
from models.atom import Atom
from rendering.atom_renderer import AtomRenderer, SoftwareRenderer
from ui.periodic_table import PeriodicTable
from ui.search_panel import SearchPanel
from ui.controls import Controls
from ui.element_details import ElementDetails

class MainWindow(QMainWindow):
    def __init__(self, catalog: ElementCatalog, software: bool = False) -> None:
        super().__init__()
        self.catalog = catalog
        self.atom = Atom(catalog.by_number[settings.DEFAULT_ATOM])
        self.setWindowTitle("ATOMIC · Periodic atom explorer")
        self.setMinimumSize(*settings.MIN_WINDOW)
        self.resize(*settings.DEFAULT_WINDOW)
        available = self.screen().availableGeometry()
        self.resize(min(self.width(),available.width()-30),min(self.height(),available.height()-60))
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18,12,18,4)
        layout.setSpacing(10)
        header = QHBoxLayout()
        brand = QLabel("ATOMIC")
        brand.setObjectName("brand")
        header.addWidget(brand)
        subtitle = QLabel("THE ELEMENT EXPLORER    /    118 ELEMENTS")
        subtitle.setObjectName("muted")
        header.addWidget(subtitle)
        header.addStretch()
        self.mode = QComboBox()
        self.mode.addItems(["Bohr model","Shell model","Orbital cloud"])
        self.mode.setAccessibleName("Visualization mode")
        self.orbital = QComboBox()
        self.orbital.setAccessibleName("Occupied subshell for the orbital cloud")
        header.addWidget(self.mode)
        header.addWidget(self.orbital)
        export = QPushButton("Save image")
        export.clicked.connect(self.export_image)
        header.addWidget(export)
        layout.addLayout(header)
        self.vertical = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self.vertical,1)
        self.middle = QSplitter(Qt.Orientation.Horizontal)
        self.vertical.addWidget(self.middle)
        center = QWidget()
        self.viewport_layout = QVBoxLayout(center)
        self.viewport_layout.setContentsMargins(0,0,10,0)
        self.renderer = SoftwareRenderer(self.atom) if software else AtomRenderer(self.atom)
        self.viewport_layout.addWidget(self.renderer,1)
        self.controls = Controls()
        self.viewport_layout.addWidget(self.controls)
        self.middle.addWidget(center)
        self.details = ElementDetails()
        self.middle.addWidget(self.details)
        self.middle.setSizes([1060,320])
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0,6,0,0)
        self.search = SearchPanel()
        bottom_layout.addWidget(self.search)
        self.table = PeriodicTable(catalog.elements)
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setWidget(self.table)
        bottom_layout.addWidget(table_scroll,1)
        legend = QLabel("  ·  ".join(f'<span style="color:{color}">{name.title()}</span>' for name,color in CATEGORIES.items()))
        legend.setWordWrap(True)
        legend.setStyleSheet("font-size:10px; padding:2px")
        bottom_layout.addWidget(legend)
        self.vertical.addWidget(bottom)
        self.vertical.setSizes([540,430])
        note = QLabel(settings.SCIENTIFIC_NOTE)
        note.setObjectName("muted")
        note.setWordWrap(True)
        note.setStyleSheet("font-size:10px")
        layout.addWidget(note)
        self.statusBar().showMessage("Offline dataset loaded · 118 elements · click any element to explore")
        self.connect_renderer()
        self.table.element_selected.connect(self.select_element)
        self.search.changed.connect(self.filter_elements)
        self.search.submitted.connect(self.submit_search)
        self.details.state_changed.connect(self.change_atom_state)
        self.mode.currentTextChanged.connect(self.change_mode)
        self.orbital.currentIndexChanged.connect(lambda index: self.renderer.set_orbital(index))
        self.controls.pause.toggled.connect(self.set_paused)
        self.controls.speed.currentIndexChanged.connect(lambda: setattr(self.renderer,"speed",self.controls.speed.currentData()))
        self.controls.auto.toggled.connect(lambda enabled: setattr(self.renderer,"auto_rotate",enabled))
        self.controls.reset.clicked.connect(lambda: self.renderer.reset_camera())
        self.controls.center.clicked.connect(lambda: self.renderer.center_nucleus())
        for sequence,callback in (("Space",self.controls.pause.click),("R",lambda: self.renderer.reset_camera()),
                                  ("Ctrl+F",self.search.query.setFocus),("Ctrl+Q",self.close)):
            shortcut = QShortcut(QKeySequence(sequence),self)
            shortcut.activated.connect(callback)
        self.select_element(settings.DEFAULT_ATOM)
        self.orbital.hide()
        if not software:
            QTimer.singleShot(900,self.check_context)

    def connect_renderer(self) -> None:
        self.renderer.particle_selected.connect(self.details.particle.setText)
        if isinstance(self.renderer,AtomRenderer):
            self.renderer.failed.connect(self.use_software)

    def check_context(self) -> None:
        if isinstance(self.renderer,AtomRenderer) and not self.renderer.isValid():
            self.use_software("An OpenGL 3.3 context could not be created")

    def use_software(self, reason: str) -> None:
        if isinstance(self.renderer,SoftwareRenderer):
            return
        logging.getLogger(__name__).warning("Using compatibility renderer: %s",reason)
        previous = self.renderer
        previous.timer.stop()
        renderer = SoftwareRenderer(self.atom)
        renderer.camera = previous.camera
        renderer.paused,renderer.speed,renderer.auto_rotate = previous.paused,previous.speed,previous.auto_rotate
        renderer.set_mode(self.mode.currentText())
        renderer.set_orbital(self.orbital.currentIndex())
        self.viewport_layout.replaceWidget(previous,renderer)
        self.renderer = renderer
        self.connect_renderer()
        previous.hide()
        previous.deleteLater()
        self.statusBar().showMessage(f"Compatibility renderer active · {reason}")

    def select_element(self, atomic_number: int) -> None:
        element = self.catalog.by_number.get(atomic_number)
        if element is None:
            self.statusBar().showMessage("Choose an atomic number between 1 and 118")
            return
        self.atom = Atom(element)
        self.table.selected = atomic_number
        self.table.update()
        self.details.show_atom(self.atom,new_element=True)
        self.renderer.set_atom(self.atom)
        self.refresh_orbitals()
        self.statusBar().showMessage(f"{element.name} · Z {atomic_number} · representative isotope {element.symbol}-{self.atom.mass_number}")

    def refresh_orbitals(self) -> None:
        self.orbital.blockSignals(True)
        self.orbital.clear()
        for sub in self.atom.subshells:
            self.orbital.addItem(f"{sub.label} · {sub.electrons} e⁻")
        current = self.renderer.scene.orbital
        if current:
            self.orbital.setCurrentIndex(self.atom.subshells.index(current))
        self.orbital.setEnabled(bool(current))
        self.orbital.blockSignals(False)

    def change_atom_state(self) -> None:
        try:
            self.atom.set_state(self.details.isotope.currentData(),self.details.charge.currentData())
        except ValueError as exc:
            self.statusBar().showMessage(str(exc))
            self.details.show_atom(self.atom)
            return
        self.details.show_atom(self.atom)
        self.renderer.set_atom(self.atom)
        self.refresh_orbitals()
        self.statusBar().showMessage(f"{self.atom.notation} · mass number {self.atom.mass_number} · {self.atom.neutrons} neutrons")

    def change_mode(self, mode: str) -> None:
        self.renderer.set_mode(mode)
        self.orbital.setVisible(mode == "Orbital cloud")
        self.details.particle.setText("Cloud shows a stylized occupied subshell; points are not individual electrons." if mode == "Orbital cloud" else "Click a visible particle to inspect it.")

    def set_paused(self, paused: bool) -> None:
        self.renderer.paused = paused
        self.controls.pause.setText("Resume" if paused else "Pause")

    def filter_elements(self) -> None:
        matches = self.catalog.search(self.search.query.text(),self.search.category.currentData(),self.search.period.currentData(),self.search.block.currentData())
        self.table.matches = {e.atomic_number for e in matches}
        self.table.update()
        self.search.count.setText(f"{len(matches)} / 118")
        exact = self.catalog.lookup(self.search.query.text())
        if exact and exact.atomic_number in self.table.matches:
            self.select_element(exact.atomic_number)
        elif self.search.query.text().strip() and len(matches) == 1:
            self.select_element(matches[0].atomic_number)
        if not matches:
            self.statusBar().showMessage("No matching elements · clear the search or filters")

    def submit_search(self) -> None:
        if self.table.matches:
            self.select_element(min(self.table.matches))

    def export_image(self) -> None:
        filename,_ = QFileDialog.getSaveFileName(self,"Save atom image",f"{self.atom.element.symbol}-{self.atom.mass_number}.png","PNG image (*.png)")
        if filename:
            image = self.renderer.grab().toImage()
            if image.save(filename):
                self.statusBar().showMessage(f"Image saved: {Path(filename).name}")
            else:
                QMessageBox.warning(self,"Image could not be saved","Choose a writable directory and try again.")

    def closeEvent(self, event) -> None:
        self.renderer.timer.stop()
        if isinstance(self.renderer,AtomRenderer) and self.renderer.ready:
            self.renderer.cleanup()
        super().closeEvent(event)
