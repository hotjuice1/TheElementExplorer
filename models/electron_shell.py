"""Strict configuration parsing, including noble-gas shorthand and ions."""
from dataclasses import dataclass
import re

CAPACITY = {"s": 2, "p": 6, "d": 10, "f": 14}
ORDER = tuple(sorted(((n, l) for n in range(1, 9) for l in CAPACITY
                      if "spdf".index(l) < n),
                     key=lambda pair: (pair[0] + "spdf".index(pair[1]), pair[0])))
CORES = {
    "He": "1s2", "Ne": "1s2 2s2 2p6", "Ar": "1s2 2s2 2p6 3s2 3p6",
    "Kr": "[Ar] 3d10 4s2 4p6", "Xe": "[Kr] 4d10 5s2 5p6",
    "Rn": "[Xe] 4f14 5d10 6s2 6p6", "Og": "[Rn] 5f14 6d10 7s2 7p6",
}
SUPERSCRIPT = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")

@dataclass(frozen=True)
class Subshell:
    n: int
    orbital: str
    electrons: int

    @property
    def label(self) -> str:
        return f"{self.n}{self.orbital}"

def parse_configuration(text: str) -> tuple[Subshell, ...]:
    """Parse the entire string; never silently accept partial or duplicate tokens."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Electron configuration must be a non-empty string")
    text = text.translate(str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789"))
    result: dict[tuple[int, str], int] = {}
    for i, token in enumerate(text.split()):
        if token.startswith("["):
            if i != 0 or token[1:-1] not in CORES or not token.endswith("]"):
                raise ValueError(f"Invalid noble-gas core: {token}")
            result.update({(s.n, s.orbital): s.electrons for s in parse_configuration(CORES[token[1:-1]])})
            continue
        match = re.fullmatch(r"([1-8])([spdf])(\d{1,2})", token)
        if not match:
            raise ValueError(f"Invalid electron configuration token: {token!r}")
        n, orbital, count = int(match[1]), match[2], int(match[3])
        if "spdf".index(orbital) >= n or not 0 <= count <= CAPACITY[orbital]:
            raise ValueError(f"Invalid occupancy: {token}")
        if (n, orbital) in result:
            raise ValueError(f"Duplicate subshell: {n}{orbital}")
        result[n, orbital] = count
    return tuple(Subshell(n, l, count) for (n, l), count in sorted(result.items(), key=lambda item: (item[0][0], "spdf".index(item[0][1]))) if count)

def shell_populations(subshells: tuple[Subshell, ...]) -> tuple[int, ...]:
    if not subshells:
        return ()
    shells = [0] * max(s.n for s in subshells)
    for s in subshells:
        shells[s.n - 1] += s.electrons
    return tuple(shells)

def format_configuration(subshells: tuple[Subshell, ...]) -> str:
    return " ".join(s.label + str(s.electrons).translate(SUPERSCRIPT) for s in subshells) or "No electrons"

def ionic_configuration(neutral: tuple[Subshell, ...], charge: int) -> tuple[Subshell, ...]:
    """Educational ion approximation: remove highest n/l first; add by Madelung order."""
    if type(charge) is not int or charge not in range(-3, 4):
        raise ValueError("Charge must be between −3 and +3")
    counts = {(s.n, s.orbital): s.electrons for s in neutral}
    if sum(counts.values()) < charge:
        raise ValueError("This charge would produce a negative electron count")
    for _ in range(max(0, charge)):
        key = max((k for k, v in counts.items() if v), key=lambda k: (k[0], "spdf".index(k[1])))
        counts[key] -= 1
    for _ in range(max(0, -charge)):
        key = next(k for k in ORDER if counts.get(k, 0) < CAPACITY[k[1]])
        counts[key] = counts.get(key, 0) + 1
    return tuple(Subshell(n, l, count) for (n, l), count in sorted(counts.items(), key=lambda item: (item[0][0], "spdf".index(item[0][1]))) if count)
