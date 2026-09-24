"""CPU scene arrays shared by GPU and compatibility renderers."""
import numpy as np
from app.theme import PROTON, NEUTRON, ELECTRON
from app.settings import NUCLEON_RADIUS, ELECTRON_RADIUS
from models.atom import Atom
from rendering.geometry import nucleus_positions, shell_radius, shell_basis, shell_guides, orbital_cloud

class AtomScene:
    def __init__(self, atom: Atom) -> None:
        self.mode = "Bohr model"
        self.time = 0.0
        self.set_atom(atom)

    def set_atom(self, atom: Atom) -> None:
        self.atom = atom
        self.mass = int(atom.mass_number)
        self.vertices = np.zeros((self.mass+atom.electrons,7), dtype=np.float32)
        self.vertices[:self.mass,:3] = nucleus_positions(atom.protons,self.mass)
        self.vertices[:atom.protons,3:6] = PROTON
        self.vertices[atom.protons:self.mass,3:6] = NEUTRON
        self.vertices[:self.mass,6] = NUCLEON_RADIUS
        self.vertices[self.mass:,3:6] = ELECTRON
        self.vertices[self.mass:,6] = ELECTRON_RADIUS
        self.labels = []
        for sub in atom.subshells:
            self.labels.extend([(sub.n,sub.label)]*sub.electrons)
        self.radii = np.array([shell_radius(n) for n,_ in self.labels])
        self.phase = np.zeros(atom.electrons)
        self.basis_u = np.zeros((atom.electrons,3))
        self.basis_v = np.zeros((atom.electrons,3))
        for n,count in enumerate(atom.shells,1):
            ids = [i for i,(shell,_) in enumerate(self.labels) if shell == n]
            self.phase[ids] = np.linspace(0,2*np.pi,count,endpoint=False) + n*.43
            self.basis_u[ids],self.basis_v[ids] = shell_basis(n)
        self.orbital = max(atom.subshells, key=lambda s: (s.n,"spdf".index(s.orbital))) if atom.subshells else None
        self.rebuild_guides()
        self.animate(0)

    @property
    def radius(self) -> float:
        return shell_radius(max(1,len(self.atom.shells)))

    @property
    def visible_count(self) -> int:
        return self.mass if self.mode == "Orbital cloud" else len(self.vertices)

    def rebuild_guides(self) -> None:
        self.guides = shell_guides(len(self.atom.shells), self.mode == "Shell model")
        self.cloud = orbital_cloud(self.orbital.n,self.orbital.orbital) if self.orbital else np.empty((0,3),dtype=np.float32)

    def animate(self, dt: float) -> None:
        self.time += dt
        phase = self.phase + self.time*.9 / np.maximum(self.radii,.1)**.65
        self.vertices[self.mass:,:3] = self.radii[:,None]*(np.cos(phase)[:,None]*self.basis_u + np.sin(phase)[:,None]*self.basis_v)

    def particle_text(self, index: int) -> str:
        if index < self.atom.protons:
            return "Proton  ·  charge +1e\nLocation: nucleus"
        if index < self.mass:
            return "Neutron  ·  charge 0\nLocation: nucleus"
        n,sub = self.labels[index-self.mass]
        shell = "KLMNOPQ"[n-1] if n <= 7 else f"n={n}"
        return f"Electron  ·  charge −1e\nShell {shell} (n={n}) · occupancy label {sub}\nPath is schematic, not a physical trajectory."
