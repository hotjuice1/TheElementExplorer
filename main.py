"""ATOMIC entry point. Runtime never accesses the network."""
import argparse
import logging
from pathlib import Path
import sys
from PySide6.QtGui import QSurfaceFormat, QFont
from PySide6.QtWidgets import QApplication, QMessageBox
from app.theme import STYLESHEET
from app.settings import ANTIALIASING
from data.element_loader import ElementCatalog, load_elements

def create_application() -> QApplication:
    surface = QSurfaceFormat()
    surface.setVersion(3,3)
    surface.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    surface.setDepthBufferSize(24)
    surface.setSamples(4 if ANTIALIASING else 0)
    surface.setSwapInterval(1)
    QSurfaceFormat.setDefaultFormat(surface)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("ATOMIC")
    app.setOrganizationName("Atomic Explorer")
    app.setFont(QFont("Segoe UI",10))
    app.setStyleSheet(STYLESHEET)
    return app

def main() -> int:
    parser = argparse.ArgumentParser(description="Offline periodic table and 3D atom explorer")
    parser.add_argument("--software",action="store_true",help="Use the CPU compatibility renderer")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING,format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    application = create_application()
    try:
        catalog = ElementCatalog(load_elements())
    except ValueError as exc:
        QMessageBox.critical(None,"Element data could not be loaded",str(exc))
        return 2
    from app.main_window import MainWindow
    window = MainWindow(catalog,software=args.software)
    window.show()
    return application.exec()

if __name__ == "__main__":
    raise SystemExit(main())
