"""Qt interaction regressions using the compatibility renderer (no GPU required)."""
import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from main import create_application
from app.main_window import MainWindow

@pytest.fixture(scope="module")
def qt_app():
    return create_application()

@pytest.fixture
def window(qt_app,catalog):
    w = MainWindow(catalog,software=True)
    w.show()
    qt_app.processEvents()
    yield w
    w.close()
    w.deleteLater()
    qt_app.processEvents()

def test_table_click_and_search(window,catalog):
    QTest.mouseClick(window.table,Qt.MouseButton.LeftButton,pos=window.table.cell_rect(catalog.lookup("Cu")).center().toPoint())
    assert window.atom.element.symbol == "Cu"
    window.search.query.setText("gold")
    assert window.atom.element.symbol == "Au"
    window.search.query.setText("79")
    assert window.table.matches == {79}
    window.search.query.setText("no-such-element")
    assert window.table.matches == set()
    window.search.clear()
    assert len(window.table.matches) == 118

def test_filters(window):
    window.search.category.setCurrentIndex(window.search.category.findData("noble gas"))
    window.search.period.setCurrentIndex(window.search.period.findData(3))
    window.search.block.setCurrentIndex(window.search.block.findData("p"))
    assert window.table.matches == {18}
    window.search.clear()
    assert len(window.table.matches) == 118

def test_controls(window):
    window.controls.pause.click()
    assert window.renderer.paused
    before = window.renderer.scene.time
    QTest.qWait(50)
    assert window.renderer.scene.time == before
    window.select_element(118)
    assert window.renderer.paused
    window.controls.pause.click()
    assert not window.renderer.paused
    for i,speed in enumerate((.25,.5,1,2,4)):
        window.controls.speed.setCurrentIndex(i)
        assert window.renderer.speed == speed
    window.controls.auto.click()
    assert not window.renderer.auto_rotate
    window.renderer.camera.target_pan[:] = (1,1)
    window.controls.center.click()
    assert not np.any(window.renderer.camera.target_pan)
    window.renderer.camera.zoom(4)
    window.controls.reset.click()
    assert window.renderer.camera.target_distance == window.renderer.camera.home_distance

def test_isotopes_ions_and_empty_cloud(window):
    window.select_element(6)
    window.details.isotope.setCurrentIndex(window.details.isotope.findData(14))
    assert window.atom.neutrons == 8
    assert window.renderer.scene.mass == 14
    window.details.charge.setCurrentIndex(window.details.charge.findData(-2))
    assert window.atom.electrons == 8
    window.select_element(1)
    assert window.details.charge.findData(2) == -1
    window.details.charge.setCurrentIndex(window.details.charge.findData(1))
    window.mode.setCurrentText("Orbital cloud")
    assert window.renderer.scene.cloud.shape == (0,3)
    assert not window.orbital.isEnabled()

def test_modes_and_particle_picking(window):
    for mode in ("Shell model","Orbital cloud","Bohr model"):
        window.mode.setCurrentText(mode)
        assert window.renderer.scene.mode == mode
    window.select_element(1)
    r = window.renderer
    r.paused = True
    r.camera.update(1)
    xy,_ = r.project(r.scene.vertices[:1,:3])
    r.pick(*xy[0])
    assert r.selection == 0
    assert "Proton" in window.details.particle.text()
    xy,_ = r.project(r.scene.vertices[1:,:3])
    r.pick(*xy[0])
    assert "Electron" in window.details.particle.text()
    window.details.isotope.setCurrentIndex(window.details.isotope.findData(2))
    r.camera.update(1)
    xy,_ = r.project(r.scene.vertices[1:2,:3])
    r.pick(*xy[0])
    assert "Neutron" in window.details.particle.text()

def test_export_image(window,tmp_path,monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    from PySide6.QtGui import QImage
    path = tmp_path/"atom.png"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args: (str(path),"PNG"))
    window.export_image()
    assert not QImage(str(path)).isNull()
