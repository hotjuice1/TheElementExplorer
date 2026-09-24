"""Scrollable element facts and atom-state controls."""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QScrollArea, QWidget, QGridLayout
from models.atom import Atom
from models.electron_shell import format_configuration
from app.theme import CATEGORIES

def label(text: str, name: str = "", wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(wrap)
    widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return widget

class ElementDetails(QFrame):
    state_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setMinimumWidth(278)
        self.setMaximumWidth(365)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16,12,16,10)
        outer.addWidget(label("ELEMENT PROFILE","eyebrow"))
        head = QHBoxLayout()
        self.symbol,self.name = label("","symbol"),label("","title")
        head.addWidget(self.symbol)
        head.addWidget(self.name,1)
        outer.addLayout(head)
        self.category = label("","muted")
        outer.addWidget(self.category)
        self.counts = label("",wrap=True)
        outer.addWidget(self.counts)
        isotope_row = QHBoxLayout()
        self.isotope,self.charge = QComboBox(),QComboBox()
        self.isotope.setAccessibleName("Isotope")
        self.charge.setAccessibleName("Ion charge")
        isotope_row.addWidget(self.isotope,2)
        isotope_row.addWidget(self.charge,1)
        outer.addLayout(isotope_row)
        self.isotope.currentIndexChanged.connect(lambda _: self.state_changed.emit())
        self.charge.currentIndexChanged.connect(lambda _: self.state_changed.emit())
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0,7,7,0)
        layout.addWidget(label("ELECTRON STRUCTURE","eyebrow"))
        self.config = label("",wrap=True)
        self.shells = label("",wrap=True)
        self.ion_note = label("Ion occupancy is approximate; not all charges form bound atoms.","muted",True)
        self.ion_note.setStyleSheet("font-size:10px")
        for w in (self.config,self.shells,self.ion_note):
            layout.addWidget(w)
        layout.addWidget(label("PHYSICAL PROPERTIES","eyebrow"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        self.values = {}
        for i,key in enumerate(("Atomic number","Atomic mass","Period / group / block","Covalent radius","Electronegativity","Melting point","Boiling point","Density","Room-temperature state","Discovery year")):
            field = label(key,"muted")
            field.setStyleSheet("font-size:10px")
            value = label("",wrap=True)
            value.setStyleSheet("font-size:11px")
            grid.addWidget(field,i,0)
            grid.addWidget(value,i,1)
            self.values[key] = value
        layout.addLayout(grid)
        self.description = label("",wrap=True)
        layout.addWidget(self.description)
        layout.addWidget(label("— = unavailable / unmeasured. Covalent radius is a bonding estimate. Thermodynamic values depend on conditions; helium melts only under pressure. Superheavy configurations are predictions.","muted",True))
        layout.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll,1)
        self.particle = label("Click a visible particle to inspect it.","muted",True)
        self.particle.setMinimumHeight(42)
        self.particle.setStyleSheet("font-size:11px; border-top:1px solid #2b3e50; padding-top:6px")
        outer.addWidget(self.particle)

    def show_atom(self, atom: Atom, new_element: bool = False) -> None:
        e = atom.element
        self.symbol.setText(atom.notation)
        self.symbol.setStyleSheet(f"color:{CATEGORIES[e.category]}")
        self.name.setText(e.name)
        self.name.setStyleSheet("font-size:21px" if len(e.name) > 10 else "font-size:25px")
        self.category.setText(f"{e.category.upper()}  ·  {e.symbol}-{atom.mass_number}")
        self.counts.setText(f"{atom.protons} protons    {atom.neutrons} neutrons    {atom.electrons} electrons")
        self.isotope.blockSignals(True)
        self.charge.blockSignals(True)
        if new_element:
            self.isotope.clear()
            for iso in e.isotopes:
                abundance = f" · {iso.abundance:g}%" if iso.abundance is not None else ""
                self.isotope.addItem(f"{e.symbol}-{iso.mass_number}{abundance}",iso.mass_number)
            self.charge.clear()
            for charge in range(-3,min(3,e.atomic_number)+1):
                self.charge.addItem("Neutral" if charge == 0 else f"Charge {charge:+}",charge)
        self.isotope.setCurrentIndex(self.isotope.findData(atom.mass_number))
        self.charge.setCurrentIndex(self.charge.findData(atom.charge))
        self.isotope.blockSignals(False)
        self.charge.blockSignals(False)
        self.config.setText(format_configuration(atom.subshells))
        self.shells.setText("Shells: " + (" / ".join(str(n) for n in atom.shells) or "empty"))
        self.ion_note.setVisible(atom.charge != 0)
        def value(number,unit="") -> str:
            return "—" if number is None else f"{number:g}{unit}"
        values = {
            "Atomic number":str(e.atomic_number), "Atomic mass":value(e.atomic_mass," u"),
            "Period / group / block":f"{e.period} / {e.group if e.group else '—'} / {e.block}",
            "Covalent radius":value(e.atomic_radius," pm"), "Electronegativity":value(e.electronegativity),
            "Melting point":value(e.melting_point," K"), "Boiling point":value(e.boiling_point," K"),
            "Density":value(e.density," g/cm³"), "Room-temperature state":e.state.capitalize(),
            "Discovery year":str(e.discovery_year) if e.discovery_year else "—",
        }
        for key,text in values.items():
            self.values[key].setText(text)
        self.description.setText(e.description)
        self.particle.setText("Click a visible particle to inspect it.")
