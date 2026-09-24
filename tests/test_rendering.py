import numpy as np
import pytest
from models.atom import Atom
from rendering.geometry import nucleus_positions, orbital_cloud
from rendering.scene import AtomScene
from rendering.camera import Camera

def test_stable_close_packing():
    positions = nucleus_positions(118,294)
    assert positions.shape == (294,3)
    assert positions is nucleus_positions(118,294)
    distances = np.linalg.norm(positions[:,None]-positions[None,:],axis=2)
    np.fill_diagonal(distances,np.inf)
    assert distances.min() > .22
    assert np.linalg.norm(positions.mean(axis=0)) < 1e-6
    assert np.linalg.norm(positions,axis=1).max() < 1.4

def test_particle_counts_and_animation(catalog):
    scene = AtomScene(Atom(catalog.lookup("Og")))
    assert len(scene.vertices) == 294+118
    nucleus = scene.vertices[:294].copy()
    electrons = scene.vertices[294:].copy()
    scene.animate(.5)
    assert np.array_equal(nucleus,scene.vertices[:294])
    assert not np.allclose(electrons,scene.vertices[294:])
    assert np.allclose(np.linalg.norm(scene.vertices[294:,:3],axis=1),scene.radii)

def test_delta_time_independence(catalog):
    a,b = AtomScene(Atom(catalog.lookup("Cu"))),AtomScene(Atom(catalog.lookup("Cu")))
    for _ in range(60): a.animate(1/60)
    for _ in range(30): b.animate(1/30)
    np.testing.assert_allclose(a.vertices,b.vertices,atol=1e-6)
    first,second = Camera(),Camera()
    first.target_distance = second.target_distance = 8
    for _ in range(60): first.update(1/60)
    for _ in range(30): second.update(1/30)
    assert first.distance == pytest.approx(second.distance)

@pytest.mark.parametrize("orbital",list("spdf"))
def test_clouds_are_finite_cached_and_three_dimensional(orbital):
    points = orbital_cloud(4,orbital)
    assert points is orbital_cloud(4,orbital)
    assert np.isfinite(points).all()
    assert points.std(axis=0).min() > .2

def test_camera_limits():
    camera = Camera()
    camera.zoom(1000)
    assert camera.target_distance == 2
    camera.zoom(-1000)
    assert camera.target_distance == 70
    camera.rotate(1,1000)
    assert camera.target_pitch == 89
