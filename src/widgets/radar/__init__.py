from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QMatrix4x4
from src.gl.GLGeometry import GLGeometry, GLPrimitives
from src.gl.BaseOpenGLWidget import BaseOpenGLWidget, Drawable


@dataclass
class Plane:
    """Represents a tracked aircraft."""
    callsign: str
    x: float  # Normalized position (-1 to 1)
    y: float
    heading: float  # Degrees
    altitude: int | None = None

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


class RadarScopeGL(BaseOpenGLWidget):
    def __init__(self):
        super().__init__(animated=True)
        self.sweep_angle = 0.0
        self.circle = None
        self.line = None

    def init_geometry(self):
        self.circle = GLPrimitives.circle()
        self.plane_icon = GLPrimitives.circle(disc=True)
        self.line = GLPrimitives.line(0, 0, 1, 0)

    def init_static_layer(self):
        # Range rings
        for r in [0.2, 0.4, 0.6, 0.8]:
            def draw_ring(w, radius=r):
                w.set_color(0.1, 0.24, 0.1, 1.0)
                w.draw_at(self.circle, scale=radius)
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
            )
