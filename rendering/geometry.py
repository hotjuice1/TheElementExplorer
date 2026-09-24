"""Cached stable close-packed nuclei and approximate angular orbital clouds."""
from functools import lru_cache
import numpy as np
from app.settings import NUCLEON_RADIUS, CLOUD_POINTS, GUIDE_SEGMENTS

@lru_cache(maxsize=256)
def nucleus_positions(protons: int, mass: int) -> np.ndarray:
    """Cut a spherical FCC packing, rotate and gently jitter once (no force simulation)."""
    side = int(np.ceil((mass * 3 / (4*np.pi)*4)**(1/3))) + 2
    grid = np.indices((2*side+1,)*3).reshape(3,-1).T - side
    grid = grid[np.sum(grid, axis=1) % 2 == 0].astype(np.float32)
    rng = np.random.default_rng(protons * 1009 + mass)
    distances = np.sum(grid*grid, axis=1) + rng.uniform(0, .01, len(grid))
    points = grid[np.argsort(distances)[:mass]] * (NUCLEON_RADIUS*1.92/np.sqrt(2))
    rotation, _ = np.linalg.qr(rng.normal(size=(3,3)))
    points = points @ rotation + rng.normal(0, .008, points.shape)
    points -= points.mean(axis=0)
    rng.shuffle(points)  # Intermix proton and neutron colors throughout the nucleus.
    points = np.asarray(points, dtype=np.float32)
    points.setflags(write=False)
    return points

def shell_radius(n: int) -> float:
    return 1.35 + n * .64

def shell_basis(n: int) -> tuple[np.ndarray, np.ndarray]:
    angle = (n-1)*.47
    return np.array([np.cos(angle),0,np.sin(angle)]), np.array([0,1,0])

@lru_cache(maxsize=32)
def shell_guides(count: int, spherical: bool = False) -> np.ndarray:
    theta = np.linspace(0,2*np.pi,GUIDE_SEGMENTS,endpoint=False)
    lines = []
    for n in range(1, count+1):
        u,v = shell_basis(n)
        ring = shell_radius(n)*(np.cos(theta)[:,None]*u+np.sin(theta)[:,None]*v)
        lines.extend(np.stack([ring,np.roll(ring,-1,axis=0)],axis=1).reshape(-1,3))
        if spherical:
            for axis in range(1, 6):
                a = axis*np.pi/6
                u = np.array([np.cos(a),0,np.sin(a)])
                ring = shell_radius(n)*(np.cos(theta)[:,None]*u + np.sin(theta)[:,None]*v)
                lines.extend(np.stack([ring,np.roll(ring,-1,axis=0)],axis=1).reshape(-1,3))
            for latitude in (-.65, 0, .65):
                r = shell_radius(n)
                ring = np.column_stack([r*np.sqrt(1-latitude**2)*np.cos(theta), np.full_like(theta,r*latitude), r*np.sqrt(1-latitude**2)*np.sin(theta)])
                lines.extend(np.stack([ring,np.roll(ring,-1,axis=0)],axis=1).reshape(-1,3))
    return np.asarray(lines, dtype=np.float32).reshape(-1,3)

@lru_cache(maxsize=32)
def orbital_cloud(n: int, orbital: str) -> np.ndarray:
    """Stylized real angular harmonics (s, p_z, d_xz, f_xyz), no radial nodes or SCF."""
    rng = np.random.default_rng(n*101+ord(orbital))
    accepted = []
    total = 0
    while total < CLOUD_POINTS:
        direction = rng.normal(size=(CLOUD_POINTS,3))
        direction /= np.linalg.norm(direction,axis=1)[:,None]
        x,y,z = direction.T
        weight = {"s": np.ones_like(x), "p": z*z, "d": 4*x*x*z*z, "f": 27*x*x*y*y*z*z}[orbital]
        chosen = direction[rng.random(CLOUD_POINTS) < weight]
        radii = rng.gamma(5, .13, len(chosen)).clip(.05,1.7) * shell_radius(n)*.8
        accepted.append(chosen*radii[:,None])
        total += len(chosen)
    result = np.ascontiguousarray(np.concatenate(accepted)[:CLOUD_POINTS], dtype=np.float32)
    result.setflags(write=False)
    return result
