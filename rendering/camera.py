"""Frame-rate-independent smoothed perspective camera."""
from dataclasses import dataclass, field
import math
import numpy as np
from app.settings import CAMERA_SMOOTHING

@dataclass
class Camera:
    yaw: float = -18.0
    pitch: float = 27.0
    distance: float = 14.0
    target_yaw: float = -18.0
    target_pitch: float = 27.0
    target_distance: float = 14.0
    pan: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.float32))
    target_pan: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.float32))
    home_distance: float = 14.0

    def reset(self, radius: float | None = None) -> None:
        if radius is not None:
            self.home_distance = max(6.0, radius * 3.4)
        self.target_yaw, self.target_pitch = -18.0, 27.0
        self.target_distance = self.home_distance
        self.target_pan[:] = 0

    def rotate(self, dx: float, dy: float) -> None:
        self.target_yaw += dx * 0.4
        self.target_pitch = float(np.clip(self.target_pitch + dy * 0.4, -89, 89))

    def translate(self, dx: float, dy: float, height: int) -> None:
        self.target_pan += np.array([dx, -dy]) * self.distance * 0.8 / max(height, 1)

    def zoom(self, steps: float) -> None:
        self.target_distance = float(np.clip(self.target_distance * math.exp(-steps * .12), 2, 70))

    def update(self, dt: float) -> None:
        alpha = -math.expm1(-CAMERA_SMOOTHING * dt)
        self.yaw += (self.target_yaw-self.yaw)*alpha
        self.pitch += (self.target_pitch-self.pitch)*alpha
        self.distance += (self.target_distance-self.distance)*alpha
        self.pan += (self.target_pan-self.pan)*alpha

    def matrices(self, aspect: float) -> tuple[np.ndarray, np.ndarray]:
        x, y = math.radians(self.pitch), math.radians(self.yaw)
        rx = np.array([[1,0,0,0], [0,math.cos(x),-math.sin(x),0], [0,math.sin(x),math.cos(x),0], [0,0,0,1]], dtype=np.float32)
        ry = np.array([[math.cos(y),0,math.sin(y),0], [0,1,0,0], [-math.sin(y),0,math.cos(y),0], [0,0,0,1]], dtype=np.float32)
        view = rx @ ry
        view[:3,3] = (self.pan[0], self.pan[1], -self.distance)
        f, near, far = 1/math.tan(math.radians(42)/2), .05, 150.0
        projection = np.array([[f/max(aspect,.1),0,0,0], [0,f,0,0],
                              [0,0,(far+near)/(near-far),2*far*near/(near-far)], [0,0,-1,0]], dtype=np.float32)
        return view, projection
