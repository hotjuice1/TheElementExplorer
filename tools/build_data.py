"""Rebuild the offline snapshot; developer-only dependency: periodictable 2.1.0."""
import json
from pathlib import Path
import sys
import periodictable as pt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from models.electron_shell import parse_configuration, shell_populations

def main() -> None:
    source = json.loads((ROOT / "data/source_periodic_table.json").read_text(encoding="utf-8"))
    extra_isotopes = {1: [1, 2, 3], 6: [12, 13, 14], 92: [234, 235, 238], 94: [238, 239, 240, 244]}
    years = {1: 1766, 2: 1868, 3: 1817, 4: 1798, 5: 1808, 7: 1772, 8: 1774,
             9: 1886, 10: 1898, 11: 1807, 12: 1755, 13: 1825, 14: 1824, 15: 1669}
    result = []
    for row in source["elements"]:
        z = row["number"]
        if z > 118:
            continue
        element = pt.elements[z]
        natural = {iso.isotope: float(iso.abundance) for iso in element if iso.abundance > 0}
        representative = max(natural, key=natural.get) if natural else round(row["atomic_mass"])
        isotopes = sorted(set(natural) | set(extra_isotopes.get(z, [])) | {representative})
        config = row["electron_configuration"]
        if z == 103:
            config = "[Rn] 5f14 7s2 7p1"  # NIST ground state, not legacy 6d1.
        category = row["category"]
        if category == "diatomic nonmetal":
            category = "halogen" if row["group"] == 17 else "nonmetal"
        elif category == "polyatomic nonmetal":
            category = "nonmetal"
        elif category.startswith("unknown"):
            category = "unknown"
        radius = getattr(element, "covalent_radius", None)
        # Unmeasured properties of short-lived superheavy atoms are not presented as observations.
        unmeasured = z >= 104
        result.append(dict(
            atomic_number=z, symbol=row["symbol"], name=row["name"], atomic_mass=row["atomic_mass"],
            period=row["period"], group=None if 57 <= z <= 71 or 89 <= z <= 103 else row["group"],
            category=category, block="f" if 57 <= z <= 71 or 89 <= z <= 103 else row["block"],
            protons=z, electrons=z, neutrons=representative-z,
            electron_configuration=config, shell_distribution=list(shell_populations(parse_configuration(config))),
            representative_isotope=representative,
            isotopes=[dict(mass_number=a, abundance=natural.get(a)) for a in isotopes],
            electronegativity=row["electronegativity_pauling"],
            atomic_radius=round(radius*100, 2) if radius is not None else None,
            melting_point=None if unmeasured else row["melt"], boiling_point=None if unmeasured else row["boil"],
            density=None if unmeasured or row["density"] is None else row["density"] / (1000 if row["phase"] == "Gas" else 1),
            state="unknown" if unmeasured else row["phase"].lower(),
            discovery_year=years.get(z), description=row["summary"], source=row["source"],
        ))
    (ROOT / "data/elements.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

if __name__ == "__main__":
    main()
