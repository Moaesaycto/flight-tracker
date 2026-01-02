from dataclasses import dataclass
from datetime import datetime
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QMatrix4x4
from src.gl.GLGeometry import GLGeometry, GLPrimitives
from src.gl.BaseOpenGLWidget import BaseOpenGLWidget, Drawable

from OpenGL.GL import glDisable, glEnable, GL_LINE_SMOOTH


@dataclass
class Plane:
    """Represents a tracked aircraft."""
    hexIdent: str
    lastGenUpdate: datetime
    lastLogUpdate: datetime

    callsign: str
    x: float  # Normalized position (-1 to 1)
    y: float
    heading: float  # Degrees
    altitude: int = 0
    groundSpeed: int = 0
    track: int = 0
    latitude: float = 0
    longitude: float = 0
    verticalRate: int = 0
    squark: str | None = None

    # Flags
    alert: bool = False
    emergency: bool = False
    spi: bool = False
    onGround: bool = True

    def create_drawable(self, icon: GLGeometry) -> Drawable:
        def draw(widget: BaseOpenGLWidget):
            # Draw plane icon
            widget.set_color(0.0, 0.9, 0.9, 1.0)
            model = QMatrix4x4()
            model.translate(self.x, self.y, 0.0)
            model.rotate(self.heading, 0.0, 0.0, 1.0)
            model.scale(0.03)
            widget.set_model(model)
            icon.draw()

        return Drawable(draw_func=draw, z_order=10)

    def update(self, data: List[str]) -> None:
        transmissionType, messageType = data[0:2]

        genDate, genTime, logDate, logTime = data[6:11]
        self.lastGenUpdate = datetime.strptime(
            f"{genDate} {genTime}000", "%m/%d/%y %H:%M:%S.%f")
        self.lastLogUpdate = datetime.strptime(
            f"{logDate} {logTime}000", "%m/%d/%y %H:%M:%S.%f")

        if transmissionType == "MSG":
            # ES Identification and Category
            if messageType == "1":
                self.callsign = data[10]

            # ES Surface Position Message
            elif messageType == "2":
                self.altitude, self.groundSpeed, self.track = [
                    int(d) for d in data[11:14]]

                self.latitude, self.longitude = [float(d) for d in data[14:16]]
                self.onGround = data[21] != "0"

            # ES Airborne Position Message
            elif messageType == "3":
                self.altitude = int(data[11])
                self.latitude, self.longitude = [float(d) for d in data[14:17]]
                self.alert, self.emergency, self.spi, self.onGround = [
                    d != "0" for d in data[18:22]]

            # ES Airborne Velocity Message
            elif messageType == "4":
                self.groundSpeed, self.track = [int(d) for d in data[12:14]]
                self.verticalRate = int(data[16])

            # Surveillance Alt Message
            elif messageType == "5":
                self.altitude = int(data[11])
                self.alert, self.spi, self.onGround = data[18] != "0", data[20] != "0", data[21] != "0"

            # Surveillance ID Message
            elif messageType == "6":
                self.altitude = int(data[11])
                self.squark = data[18]
                self.alert, self.emergency, self.spi, self.onGround = [
                    d != "0" for d in data[18:22]]

            # Air To Air Message
            elif messageType == "7":
                self.altitude = int(data[11])
                self.onGround = data[21] != "0"

            # All Call Reply
            elif messageType == "8":
                self.onGround = data[21] != "0"


class RadarScopeGL(BaseOpenGLWidget):
    def __init__(self):
        super().__init__(animated=True)
        self.sweep_angle = 0.0
        self.circle = None
        self.line = None

        self.plane_icon = None

    def init_geometry(self):
        self.circle = GLPrimitives.circle()
        self.plane_icon = GLPrimitives.circle(disc=True)
        self.line = GLPrimitives.line(0, 0, 1, 0)

    def init_static_layer(self):
        # Range rings
        for r in [0.2, 0.4, 0.6, 0.8]:
            def draw_ring(w, radius=r):
                glDisable(GL_LINE_SMOOTH)
                w.set_color(0.1, 0.24, 0.1, 1.0)
                w.draw_at(self.circle, scale=radius)
                glEnable(GL_LINE_SMOOTH)
            self.static_layer.add(draw_ring, z_order=0)

        # Sweep line (animated, but part of static visual structure)
        def draw_sweep(w):
            w.set_color(0.29, 0.87, 0.5, 1.0)
            w.draw_at(self.line, scale=0.85, rotation=self.sweep_angle)
        self.static_layer.add(draw_sweep, z_order=1)

    def tick(self, delta: float):
        self.sweep_angle = (self.sweep_angle + 90.0 * delta) % 360

    def update_planes(self, planes: list):
        """Called when new ADS-B data arrives."""
        if not self.plane_icon:
            return

        self.dynamic_layer.clear()
        self.clear_texts()

        for plane in planes:
            def draw_plane(w, p=plane):
                w.set_color(0.0, 0.9, 0.9, 1.0)
                w.draw_at(self.plane_icon, x=p.x, y=p.y, scale=0.02)
            self.dynamic_layer.add(draw_plane, z_order=10)

            self.add_text(
                f"{plane.callsign}",
                x=plane.x + 0.04,
                y=plane.y + 0.02,
                color=(0, 230, 230),
                align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                z_order=-1,
            )
