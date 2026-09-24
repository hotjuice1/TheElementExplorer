"""Immutable element and isotope records; unknown values remain None."""
from dataclasses import dataclass
import math

CATEGORY_NAMES = frozenset({"alkali metal", "alkaline earth metal", "transition metal",
    "post-transition metal", "metalloid", "nonmetal", "halogen", "noble gas",
    "lanthanide", "actinide", "unknown"})

@dataclass(frozen=True)
class Isotope:
    mass_number: int
    abundance: float | None = None

@dataclass(frozen=True)
class Element:
    atomic_number: int
    symbol: str
    name: str
    atomic_mass: float
    period: int
    group: int | None
    category: str
    block: str
    protons: int
    neutrons: int
    electrons: int
    electron_configuration: str
    shell_distribution: tuple[int, ...]
    representative_isotope: int
    isotopes: tuple[Isotope, ...]
    electronegativity: float | None
    atomic_radius: float | None
    melting_point: float | None
    boiling_point: float | None
    density: float | None
    state: str
    discovery_year: int | None
    description: str
    source: str

    @classmethod
    def from_record(cls, record: dict) -> "Element":
        values = dict(record)
        for key in ("atomic_number", "period", "protons", "neutrons", "electrons", "representative_isotope"):
            if type(values[key]) is not int:
                raise ValueError(f"{key} must be an integer")
        for key in ("group", "discovery_year"):
            if values[key] is not None and type(values[key]) is not int:
                raise ValueError(f"{key} must be an integer or null")
        for key in ("symbol", "name", "electron_configuration", "description", "source"):
            if not isinstance(values[key],str) or not values[key].strip():
                raise ValueError(f"{key} must be a non-empty string")
        for key in ("atomic_mass", "electronegativity", "atomic_radius", "melting_point", "boiling_point", "density"):
            value = values[key]
            if value is not None and (type(value) not in (int,float) or not math.isfinite(value) or value < 0):
                raise ValueError(f"{key} must be a finite nonnegative number or null")
        if values["category"] not in CATEGORY_NAMES:
            raise ValueError(f"Unknown category: {values['category']}")
        if values["state"] not in {"solid","liquid","gas","unknown"}:
            raise ValueError("Invalid physical state")
        if any(type(count) is not int or count < 0 for count in values["shell_distribution"]):
            raise ValueError("Shell populations must be nonnegative integers")
        values["shell_distribution"] = tuple(values["shell_distribution"])
        values["isotopes"] = tuple(Isotope(**item) for item in values["isotopes"])
        for iso in values["isotopes"]:
            if type(iso.mass_number) is not int:
                raise ValueError("Isotope mass numbers must be integers")
            if iso.abundance is not None and (type(iso.abundance) not in (int,float) or not math.isfinite(iso.abundance) or not 0 <= iso.abundance <= 100):
                raise ValueError("Isotope abundance must be a percentage or null")
        return cls(**values)
