"""GPU viewport with a software compatibility viewport and shared interaction logic."""
from __future__ import annotations
import ctypes
import logging
from time import perf_counter
import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient, QFont, QPolygonF
from PySide6.QtWidgets import QWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from app import settings
from app.theme import BACKGROUND, MUTED, ACCENT, SHELL
from models.atom import Atom
from rendering.camera import Camera
from rendering.scene import AtomScene
from utils.performance import FrameMeter

logger = logging.getLogger(__name__)

class Interaction:
    """Shared state and mouse handling; all motion integrates elapsed seconds."""
    def setup(self, atom: Atom) -> None:
        self.scene = AtomScene(atom)
        self.camera = Camera()
        self.camera.reset(self.scene.radius)
        self.camera.distance = self.camera.target_distance
        self.paused = False
        self.speed = settings.ELECTRON_SPEED
        self.auto_rotate = settings.AUTO_ROTATE
        self.meter = FrameMeter()
        self.draw_calls = 0
        self.selection = None
        self.dragging = False
        self.last_mouse = None
        self.dirty = True
        self.setMinimumSize(340, 270)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.last_tick = perf_counter()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(max(1,int(1000/settings.TARGET_FPS)))

    def set_atom(self, atom: Atom) -> None:
        self.scene.set_atom(atom)
        self.selection = None
        self.camera.reset(self.scene.radius)
        self.dirty = True
        self.update()

    def set_mode(self, mode: str) -> None:
        self.scene.mode = mode
        self.scene.rebuild_guides()
        self.selection = None
        self.dirty = True
        self.update()

    def set_orbital(self, index: int) -> None:
        if 0 <= index < len(self.scene.atom.subshells):
            self.scene.orbital = self.scene.atom.subshells[index]
            self.scene.rebuild_guides()
            self.dirty = True
            self.update()

    def tick(self) -> None:
        now = perf_counter()
        dt = min(now-self.last_tick, settings.MAX_DELTA_TIME)
        self.last_tick = now
        if not self.isVisible():
            return
        if not self.paused:
            self.scene.animate(dt*self.speed)
            if self.auto_rotate and self.last_mouse is None:
                self.camera.target_yaw += dt*settings.AUTO_ROTATE_DEGREES
        self.camera.update(dt)
        self.update()

    def reset_camera(self) -> None:
        self.camera.reset(self.scene.radius)

    def center_nucleus(self) -> None:
        self.camera.target_pan[:] = 0

    def mousePressEvent(self, event) -> None:
        self.setFocus()
        self.last_mouse = event.position()
        self.press_mouse = event.position()
        self.dragging = False

    def mouseMoveEvent(self, event) -> None:
        if self.last_mouse is None:
            return
        delta = event.position()-self.last_mouse
        self.dragging |= (event.position()-self.press_mouse).manhattanLength() > 4
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.camera.rotate(delta.x(),delta.y())
        elif event.buttons() & (Qt.MouseButton.RightButton | Qt.MouseButton.MiddleButton):
            self.camera.translate(delta.x(),delta.y(),self.height())
        self.last_mouse = event.position()

    def mouseReleaseEvent(self, event) -> None:
        if not self.dragging and event.button() == Qt.MouseButton.LeftButton:
            self.pick(event.position().x(),event.position().y())
        self.last_mouse = None

    def wheelEvent(self, event) -> None:
        self.camera.zoom(event.angleDelta().y()/120)
        event.accept()

    def project(self, points: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
        view,projection = self.camera.matrices(self.width()/max(1,self.height()))
        homogeneous = np.column_stack([points,np.ones(len(points))])
        eye = homogeneous @ view.T
        clip = eye @ projection.T
        ndc = clip[:,:3]/np.maximum(clip[:,3:4],.001)
        xy = np.column_stack([(ndc[:,0]+1)*self.width()/2,(1-ndc[:,1])*self.height()/2])
        return xy,-eye[:,2]

    def pick(self, x: float, y: float) -> None:
        """World-space ray/sphere intersection, choosing the nearest visible surface."""
        view,projection = self.camera.matrices(self.width()/max(1,self.height()))
        inverse = np.linalg.inv(projection @ view)
        ndc = np.array([2*x/self.width()-1, 1-2*y/self.height(), -1, 1],dtype=np.float32)
        near = inverse @ ndc
        ndc[2] = 1
        far = inverse @ ndc
        origin = near[:3]/near[3]
        direction = far[:3]/far[3]-origin
        direction /= np.linalg.norm(direction)
        data = self.scene.vertices[:self.scene.visible_count]
        offset = origin-data[:,:3]
        b = offset @ direction
        discriminant = b*b-(np.sum(offset*offset,axis=1)-data[:,6]**2)
        distances = -b-np.sqrt(np.maximum(discriminant,0))
        distances[(discriminant < 0) | (distances <= 0)] = np.inf
        selected = int(np.argmin(distances))
        self.selection = selected if np.isfinite(distances[selected]) else None
        self.particle_selected.emit(self.scene.particle_text(selected) if self.selection is not None else "Click a visible particle to inspect it.")
        self.update()

    def overlay(self, painter: QPainter, backend: str) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(ACCENT))
        painter.setFont(QFont("Segoe UI",10,QFont.Weight.DemiBold))
        mode = self.scene.mode.upper()
        painter.drawText(22,29,mode)
        painter.setFont(QFont("Segoe UI",9))
        painter.setPen(QColor(MUTED))
        if self.scene.mode == "Orbital cloud":
            sub = self.scene.orbital.label if self.scene.orbital else "Empty ion"
            painter.drawText(22,49,f"{sub} · stylized angular density · one orientation · no radial nodes")
        else:
            painter.drawText(22,49,"Schematic paths · visual scale")
        painter.drawText(22,self.height()-19,"DRAG  Rotate    /    RIGHT DRAG  Pan    /    SCROLL  Zoom")
        if settings.SHOW_FPS:
            painter.drawText(self.width()-238,29,f"{self.meter.fps:4.0f} FPS  ·  {self.scene.visible_count} particles  ·  {backend}")
        if self.paused:
            painter.setPen(QColor(ACCENT))
            painter.drawText(self.width()-87,49,"PAUSED")
        if self.selection is not None:
            point = self.scene.vertices[self.selection:self.selection+1,:3]
            xy,depth = self.project(point)
            if depth[0] > .05:
                painter.setPen(QPen(QColor("#ffffff"),1.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(*xy[0]),10,10)

class ViewportOverlay(QWidget):
    """Qt overlay above the GL surface, avoiding driver-specific mixed paint state."""
    def __init__(self, viewport) -> None:
        super().__init__(viewport)
        self.viewport = viewport
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        self.viewport.overlay(painter,"GPU")
        painter.end()

class AtomRenderer(Interaction, QOpenGLWidget):
    particle_selected = Signal(str)
    failed = Signal(str)

    def __init__(self, atom: Atom, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ready = False
        self.failure = ""
        self.buffers = []
        self.vaos = []
        self.program = 0
        self.setup(atom)
        self.hud = ViewportOverlay(self)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.hud.setGeometry(self.rect())

    def initializeGL(self) -> None:
        try:
            from OpenGL import GL
            from OpenGL.GL.shaders import compileProgram, compileShader
            from rendering.shaders import VERTEX, FRAGMENT
            self.gl = GL
            self.program = compileProgram(compileShader(VERTEX,GL.GL_VERTEX_SHADER),compileShader(FRAGMENT,GL.GL_FRAGMENT_SHADER))
            self.uniforms = {name: GL.glGetUniformLocation(self.program,name) for name in ("view","projection","viewportHeight","style")}
            for _ in range(3):
                vao,buffer = int(GL.glGenVertexArrays(1)),int(GL.glGenBuffers(1))
                self.vaos.append(vao)
                self.buffers.append(buffer)
                GL.glBindVertexArray(vao)
                GL.glBindBuffer(GL.GL_ARRAY_BUFFER,buffer)
                for index,size,offset in ((0,3,0),(1,3,12),(2,1,24)):
                    GL.glEnableVertexAttribArray(index)
                    GL.glVertexAttribPointer(index,size,GL.GL_FLOAT,False,28,ctypes.c_void_p(offset))
            GL.glBindVertexArray(0)
            self.context().aboutToBeDestroyed.connect(self.cleanup)
            self.ready = True
        except Exception as exc:
            logger.exception("OpenGL initialization failed")
            self.failure = str(exc)
            QTimer.singleShot(0,lambda: self.failed.emit(self.failure))

    def upload(self) -> None:
        gl = self.gl
        guide = np.zeros((len(self.scene.guides),7),dtype=np.float32)
        guide[:,:3],guide[:,3:6] = self.scene.guides,SHELL
        cloud = np.zeros((len(self.scene.cloud),7),dtype=np.float32)
        cloud[:,:3],cloud[:,3:6],cloud[:,6] = self.scene.cloud,(.25,.74,.77),.024
        for buffer,data in zip(self.buffers,(self.scene.vertices,guide,cloud)):
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER,buffer)
            gl.glBufferData(gl.GL_ARRAY_BUFFER,data.nbytes,data,gl.GL_DYNAMIC_DRAW if buffer == self.buffers[0] else gl.GL_STATIC_DRAW)
        self.dirty = False

    def paintGL(self) -> None:
        if not self.ready:
            return
        try:
            gl = self.gl
            gl.glViewport(0,0,round(self.width()*self.devicePixelRatioF()),round(self.height()*self.devicePixelRatioF()))
            gl.glClearColor(.035,.055,.085,1)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA,gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glDepthMask(True)
            gl.glUseProgram(self.program)
            view,projection = self.camera.matrices(self.width()/max(1,self.height()))
            gl.glUniformMatrix4fv(self.uniforms["view"],1,True,view)
            gl.glUniformMatrix4fv(self.uniforms["projection"],1,True,projection)
            gl.glUniform1f(self.uniforms["viewportHeight"],self.height()*self.devicePixelRatioF())
            if self.dirty:
                self.upload()
            if self.scene.atom.electrons:
                electrons = self.scene.vertices[self.scene.mass:]
                gl.glBindBuffer(gl.GL_ARRAY_BUFFER,self.buffers[0])
                gl.glBufferSubData(gl.GL_ARRAY_BUFFER,self.scene.mass*28,electrons.nbytes,electrons)
            gl.glUniform1i(self.uniforms["style"],0)
            gl.glBindVertexArray(self.vaos[0])
            gl.glDrawArrays(gl.GL_POINTS,0,self.scene.visible_count)
            self.draw_calls = 1
            gl.glDepthMask(False)
            if self.scene.mode == "Orbital cloud":
                gl.glUniform1i(self.uniforms["style"],1)
                gl.glBindVertexArray(self.vaos[2])
                gl.glDrawArrays(gl.GL_POINTS,0,len(self.scene.cloud))
            else:
                gl.glUniform1i(self.uniforms["style"],2)
                gl.glBindVertexArray(self.vaos[1])
                gl.glDrawArrays(gl.GL_LINES,0,len(self.scene.guides))
            self.draw_calls += 1
            gl.glDepthMask(True)
            gl.glBindVertexArray(0)
            gl.glUseProgram(0)
            gl.glDisable(gl.GL_DEPTH_TEST)
            self.meter.frame()
            self.hud.update()
        except Exception as exc:
            self.ready = False
            self.failure = str(exc)
            logger.exception("OpenGL rendering failed")
            QTimer.singleShot(0,lambda: self.failed.emit(self.failure))

    def cleanup(self) -> None:
        if not self.program:
            return
        self.makeCurrent()
        self.gl.glDeleteBuffers(len(self.buffers),self.buffers)
        self.gl.glDeleteVertexArrays(len(self.vaos),self.vaos)
        self.gl.glDeleteProgram(self.program)
        self.program = 0
        self.ready = False
        self.doneCurrent()

class SoftwareRenderer(Interaction, QWidget):
    """Compatibility path: same 3D scene and camera, CPU projection and QPainter."""
    particle_selected = Signal(str)

    def __init__(self, atom: Atom, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setup(atom)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(),QColor(BACKGROUND))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.scene.mode == "Orbital cloud":
            xy,depth = self.project(self.scene.cloud[::3])
            painter.setPen(QPen(QColor(65,177,190,70),2))
            painter.drawPoints(QPolygonF([QPointF(*p) for p,d in zip(xy,depth) if d > .05]))
        else:
            xy,depth = self.project(self.scene.guides)
            painter.setPen(QPen(QColor(83,124,157,65),1))
            painter.drawLines([QPointF(*p) for p in xy])
        vertices = self.scene.vertices[:self.scene.visible_count]
        xy,depth = self.project(vertices[:,:3])
        focal = self.height()/(2*np.tan(np.radians(21)))
        painter.setPen(Qt.PenStyle.NoPen)
        for i in np.argsort(depth)[::-1]:
            if depth[i] < .05:
                continue
            x,y = xy[i]
            radius = max(1,vertices[i,6]*focal/depth[i])
            color = QColor.fromRgbF(*vertices[i,3:6])
            gradient = QRadialGradient(QPointF(x-radius*.3,y-radius*.3),radius*1.5)
            gradient.setColorAt(0,color.lighter(145))
            gradient.setColorAt(.5,color)
            gradient.setColorAt(1,color.darker(260))
            painter.setBrush(gradient)
            painter.drawEllipse(QPointF(x,y),radius,radius)
        self.meter.frame()
        self.overlay(painter,"CPU")
        painter.end()
