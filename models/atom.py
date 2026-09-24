"""Validated atom state; failed mutations leave the old atom intact."""
from dataclasses import dataclass, field
from models.element import Element
from models.electron_shell import Subshell, parse_configuration, ionic_configuration, shell_populations, SUPERSCRIPT

@dataclass
class Atom:
    element: Element
    mass_number: int | None = None
    charge: int = 0
    subshells: tuple[Subshell, ...] = field(init=False)

    def __post_init__(self) -> None:
        mass = self.element.representative_isotope if self.mass_number is None else self.mass_number
        self.set_state(mass, self.charge)

    def set_state(self, mass_number: int, charge: int) -> None:
        if type(mass_number) is not int or mass_number not in {i.mass_number for i in self.element.isotopes}:
            raise ValueError(f"No bundled isotope {self.element.symbol}-{mass_number}")
        subshells = ionic_configuration(parse_configuration(self.element.electron_configuration), charge)
        self.mass_number, self.charge, self.subshells = mass_number, charge, subshells

    @property
    def protons(self) -> int:
        return self.element.atomic_number

    @property
    def neutrons(self) -> int:
        return int(self.mass_number) - self.protons

    @property
    def electrons(self) -> int:
        return self.protons - self.charge

    @property
    def shells(self) -> tuple[int, ...]:
        return shell_populations(self.subshells)

    @property
    def notation(self) -> str:
        charge = "" if not self.charge else ((str(abs(self.charge)) if abs(self.charge) != 1 else "") + ("+" if self.charge > 0 else "-"))
        return self.element.symbol + charge.translate(SUPERSCRIPT)
