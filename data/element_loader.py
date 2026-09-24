"""Transactional loading and scientific invariants for the offline dataset."""
import json
import math
from pathlib import Path
from models.element import Element
from models.electron_shell import parse_configuration, shell_populations

DATA_PATH = Path(__file__).with_name("elements.json")

def load_elements(path: Path = DATA_PATH) -> tuple[Element, ...]:
    try:
        records = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(records, list) or len(records) != 118:
            raise ValueError("Dataset must contain exactly 118 element records")
        elements = tuple(Element.from_record(row) for row in records)
        if {e.atomic_number for e in elements} != set(range(1, 119)):
            raise ValueError("Atomic numbers must be unique and cover 1–118")
        if len({e.symbol.casefold() for e in elements}) != 118:
            raise ValueError("Element symbols must be unique")
        for e in elements:
            try:
                shells = shell_populations(parse_configuration(e.electron_configuration))
                if not e.protons == e.electrons == sum(shells) == e.atomic_number:
                    raise ValueError("proton/electron/configuration totals disagree")
                if shells != e.shell_distribution:
                    raise ValueError("stored shell totals disagree with the configuration")
                if e.neutrons < 0 or e.neutrons != e.representative_isotope - e.protons:
                    raise ValueError("invalid representative neutron count")
                if e.representative_isotope not in {i.mass_number for i in e.isotopes}:
                    raise ValueError("representative isotope is missing")
                if len({i.mass_number for i in e.isotopes}) != len(e.isotopes):
                    raise ValueError("duplicate isotope")
                if any(i.mass_number < e.protons for i in e.isotopes):
                    raise ValueError("isotope has a negative neutron count")
                if e.block not in "spdf" or not 1 <= e.period <= 7:
                    raise ValueError("invalid periodic table position")
                if e.group is not None and not 1 <= e.group <= 18:
                    raise ValueError("group must be 1–18 or null")
                if not math.isfinite(e.atomic_mass) or e.atomic_mass <= 0:
                    raise ValueError("invalid atomic mass")
            except ValueError as exc:
                raise ValueError(f"{e.symbol} (Z={e.atomic_number}): {exc}") from exc
        return tuple(sorted(elements, key=lambda e: e.atomic_number))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Cannot load element data from {path}: {exc}") from exc

class ElementCatalog:
    def __init__(self, elements: tuple[Element, ...]) -> None:
        self.elements = elements
        self.by_number = {e.atomic_number: e for e in elements}

    def lookup(self, query: str) -> Element | None:
        query = query.strip().casefold()
        return next((e for e in self.elements if query in (str(e.atomic_number), e.symbol.casefold(), e.name.casefold())), None)

    def search(self, query: str = "", category: str = "", period: int = 0, block: str = "") -> list[Element]:
        query = query.strip().casefold()
        return [e for e in self.elements if (not query or query in e.name.casefold()
                or query == e.symbol.casefold() or query == str(e.atomic_number))
                and (not category or e.category == category)
                and (not period or e.period == period) and (not block or e.block == block)]
