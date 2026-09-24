"""Visible Qt/GPU acceptance run; saves screenshots and a reproducible QA report."""
from pathlib import Path
import argparse
import json
import sys
from time import perf_counter
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PySide6.QtCore import Qt, QEventLoop, QTimer, QPoint, QPointF
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from main import create_application
from app.main_window import MainWindow
from data.element_loader import load_elements, ElementCatalog
from rendering.atom_renderer import AtomRenderer

def wait(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds,loop.quit)
    loop.exec()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--software",action="store_true")
    args = parser.parse_args()
    errors = []
    def record_error(kind, value, tb):
        errors.append(f"{kind.__name__}: {value}")
        sys.__excepthook__(kind,value,tb)
    sys.excepthook = record_error
    app = create_application()
    catalog = ElementCatalog(load_elements())
    window = MainWindow(catalog,software=args.software)
    window.resize(1480,1040)
    window.show()
    wait(1200)
    renderer = window.renderer
    if not args.software:
        assert isinstance(renderer,AtomRenderer) and renderer.ready, "GPU initialization failed"
    checks = []
    symbols = ["H","He","C","Ne","Na","Fe","Cu","Kr","Ag","Xe","Au","U","Og"]
    for symbol in symbols:
        window.select_element(catalog.lookup(symbol).atomic_number)
        wait(50)
        assert renderer.scene.atom.electrons == catalog.lookup(symbol).atomic_number
        assert len(renderer.scene.vertices) == renderer.scene.mass+renderer.scene.atom.electrons
    checks.append("Required 13 elements selected and rendered")
    started = perf_counter()
    for e in catalog.elements:
        window.select_element(e.atomic_number)
        app.processEvents()
    rapid = perf_counter()-started
    checks.append("Rapid switch through all 118 elements")
    for query in ("gold","Au","79"):
        window.search.query.setText(query)
        assert window.atom.element.symbol == "Au"
    window.search.query.setText("invalid query 🥨")
    assert len(window.table.matches) == 0
    window.search.clear()
    window.search.category.setCurrentIndex(window.search.category.findData("noble gas"))
    window.search.period.setCurrentIndex(window.search.period.findData(3))
    window.search.block.setCurrentIndex(window.search.block.findData("p"))
    assert window.table.matches == {18}
    window.search.clear()
    QTest.mouseClick(window.table,Qt.MouseButton.LeftButton,pos=window.table.cell_rect(catalog.lookup("C")).center().toPoint())
    assert window.atom.element.symbol == "C"
    window.details.isotope.setCurrentIndex(window.details.isotope.findData(14))
    assert window.atom.neutrons == 8 and renderer.scene.mass == 14
    for charge in (-2,2):
        window.details.charge.setCurrentIndex(window.details.charge.findData(charge))
        assert window.atom.electrons == 6-charge
    checks.append("Tile click, name/symbol/number search, invalid search, combined filters, C-14, positive/negative ions")
    window.controls.pause.click()
    before = renderer.scene.time
    wait(100)
    assert renderer.scene.time == before
    window.controls.pause.click()
    wait(100)
    assert renderer.scene.time > before
    for i,speed in enumerate((.25,.5,1,2,4)):
        window.controls.speed.setCurrentIndex(i)
        assert renderer.speed == speed
    window.controls.speed.setCurrentIndex(2)
    window.controls.auto.setChecked(False)
    assert not renderer.auto_rotate
    before = renderer.camera.target_yaw
    center = renderer.rect().center()
    QTest.mousePress(renderer,Qt.MouseButton.LeftButton,pos=center)
    QTest.mouseMove(renderer,center+QPoint(65,25),delay=20)
    QTest.mouseRelease(renderer,Qt.MouseButton.LeftButton,pos=center+QPoint(65,25))
    assert renderer.camera.target_yaw != before
    QTest.mousePress(renderer,Qt.MouseButton.RightButton,pos=center)
    QTest.mouseMove(renderer,center+QPoint(40,20),delay=20)
    QTest.mouseRelease(renderer,Qt.MouseButton.RightButton,pos=center+QPoint(40,20))
    assert np.linalg.norm(renderer.camera.target_pan) > 0
    previous_distance = renderer.camera.target_distance
    wheel = QWheelEvent(QPointF(center),QPointF(renderer.mapToGlobal(center)),QPoint(),QPoint(0,120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.NoScrollPhase,False)
    app.sendEvent(renderer,wheel)
    assert renderer.camera.target_distance < previous_distance
    window.controls.center.click()
    assert np.linalg.norm(renderer.camera.target_pan) == 0
    window.controls.reset.click()
    assert renderer.camera.target_distance == renderer.camera.home_distance
    checks.append("Mouse rotate/pan/wheel, center/reset, auto-rotate, pause/resume, all speeds")
    window.select_element(1)
    renderer.paused = True
    wait(400)
    for index,name in ((0,"Proton"),(1,"Electron")):
        xy,_ = renderer.project(renderer.scene.vertices[index:index+1,:3])
        QTest.mouseClick(renderer,Qt.MouseButton.LeftButton,pos=QPoint(round(xy[0,0]),round(xy[0,1])))
        assert name in window.details.particle.text(), window.details.particle.text()
    checks.append("Ray picking: proton and electron")
    renderer.paused = False
    window.select_element(79)
    folder = ROOT/"docs"
    folder.mkdir(exist_ok=True)
    prefix = "software" if args.software else "gpu"
    for mode in ("Bohr model","Shell model","Orbital cloud"):
        window.mode.setCurrentText(mode)
        if mode == "Orbital cloud":
            window.orbital.setCurrentIndex(next(i for i,s in enumerate(window.atom.subshells) if s.label == "5d"))
        wait(450)
        assert window.grab().save(str(folder/f"{prefix}-{mode.split()[0].lower()}.png"))
        if not args.software:
            assert renderer.ready and renderer.draw_calls == 2
            image = renderer.grabFramebuffer()
            pixels = np.frombuffer(image.bits(),dtype=np.uint8).reshape(image.height(),image.bytesPerLine())
            assert pixels.std() > 8
    for orbital in "spdf":
        window.orbital.setCurrentIndex(next(i for i,s in enumerate(window.atom.subshells) if s.orbital == orbital))
        wait(60)
        assert renderer.scene.orbital.orbital == orbital
        assert len(renderer.scene.cloud) == 10000
    checks.append("All visualization modes rendered; screenshots saved")
    checks.append("All s/p/d/f cloud selectors rendered")
    window.resize(1000,720)
    wait(150)
    assert renderer.width() >= 340 and renderer.height() >= 270
    window.grab().save(str(folder/f"{prefix}-compact.png"))
    window.resize(1480,1040)
    wait(150)
    checks.append("Compact and large window resize")
    performance = {}
    window.mode.setCurrentText("Bohr model")
    for symbol in ("U","Pu","Og"):
        window.select_element(catalog.lookup(symbol).atomic_number)
        wait(300)
        renderer.meter.intervals.clear()
        wait(1800)
        performance[symbol] = {"fps":round(renderer.meter.fps,1),"frame_ms":round(1000/renderer.meter.fps,2),"particles":len(renderer.scene.vertices)}
    checks.append("Heavy-atom delivered-frame benchmarks")
    if not args.software:
        window.use_software("Acceptance test: simulated GPU failure")
        wait(100)
        assert window.renderer.__class__.__name__ == "SoftwareRenderer"
        assert window.renderer.scene.atom.element.symbol == "Og"
        checks.append("Automatic compatibility fallback preserves selected atom")
    window.select_element(79)
    wait(200)
    window.close()
    assert not errors, errors
    report = {"backend":type(renderer).__name__,"checks":checks,"rapid_switch_118_seconds":round(rapid,3),"performance":performance,"uncaught_exceptions":errors}
    (folder/f"qa-{prefix}.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__ == "__main__":
    main()
