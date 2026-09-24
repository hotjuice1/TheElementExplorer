# Dataset provenance and license

`elements.json` is a transformed, offline educational dataset. It is distributed under **CC BY-SA 3.0**, following the upstream element descriptions and data snapshot. The software does not download data at runtime.

## Core properties and descriptions

- Author/project: **Bowserinator and Periodic-Table-JSON contributors**.
- Repository: https://github.com/Bowserinator/Periodic-Table-JSON
- Source file: https://github.com/Bowserinator/Periodic-Table-JSON/blob/master/PeriodicTableJSON.json
- Local original snapshot: `source_periodic_table.json`, retrieved 2026-09-24.
- License: https://creativecommons.org/licenses/by-sa/3.0/ ; upstream notice saved in `SOURCE_LICENSE.md`.
- Upstream descriptions derive from Wikipedia. Each transformed record retains its original article URL in `source`; no article text is fetched at runtime.

Transformations: exclude hypothetical Z=119; rename fields; normalize gas density from g/L to g/cm³; map categories; use separated 15-element lanthanide/actinide rows with group `null` and visual block `f` (La/Lu and Ac/Lr assignments are a table convention); recompute shell populations from configurations; suppress unmeasured thermodynamic/state fields for Z≥104. Source standard atomic masses are retained, including representative mass numbers for radioactive elements. The core file is a maintained community compilation, not an independently certified database; it can contain uncertainties or outdated values.

## Isotopes and covalent radii

- **Paul Kienzle and periodictable contributors**, `periodictable` Python package **2.1.0**.
- Repository: https://github.com/pkienzle/periodictable
- Isotope API: https://periodictable.readthedocs.io/en/latest/api/core.html
- Radius provenance: https://periodictable.readthedocs.io/en/latest/api/covalent_radius.html
- BSD license included in `PERIODICTABLE_LICENSE.txt`.

Use naturally occurring isotopes with positive abundance, and select the largest abundance as default. In the absence of reported natural abundances, use the integer representative mass from the core snapshot. Add educational examples H-1/2/3, C-12/13/14, U-234/235/238, Pu-238/239/240/244. Missing isotope abundances are `null`, not invented percentages or stability claims. Covalent radii are converted from Å to pm. Radius uncertainties are not included in this display dataset.

## Configuration cross-checks and corrections

- NIST periodic table / ground-state configurations: https://www.nist.gov/system/files/documents/2019/12/10/nist_periodictable_july2019.pdf
- Palladium: https://physics.nist.gov/cgi-bin/Elements/elInfo.pl?element=46
- Platinum: https://physics.nist.gov/PhysRefData/Handbook/Tables/platinumtable1.htm

Lr explicitly uses `[Rn] 5f14 7s2 7p1`. Neutral exceptions are stored, never reconstructed from an assumed universal filling rule. Unit tests pin the expected shell populations of Cr, Cu, Nb, Mo, Ru, Rh, Pd, Ag, Pt, Au, Lr and Og. Beyond measured ground states, upstream theoretical configurations are used as educational predictions.

Discovery years for a small subset of early elements are retained from the original project data; unavailable dates remain null. `tools/build_data.py` documents every transformation and reproduces the snapshot without network access when the developer dependency is installed.
