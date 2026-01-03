import configparser
import socket
from typing import Dict

from PySide6.QtCore import Qt, QThread, Slot
from src.gl.GLGeometry import GLPrimitives
from src.gl.BaseOpenGLWidget import BaseOpenGLWidget
from OpenGL.GL import glDisable, glEnable, GL_LINE_SMOOTH

from src.widgets.radar.Plane import Plane
from src.widgets.radar.ADSBSocketWorker import ADSBSocketWorker

config = configparser.ConfigParser()
config.read('config.ini')


class RadarScopeGL(BaseOpenGLWidget):
    def __init__(self, lat: float, lon: float):
        super().__init__(animated=True)
        self.lat = lat
        self.lon = lon

        self.setMinimumSize(600, 600)
        self.planes = {}

        self.sweep_angle = 0.0
        self.circle = None
        self.line = None

        self.plane_icon = None

    @Slot(dict)
    def handle_socket_update(self, updated_planes):
        self.planes = updated_planes
        self.update_planes(list(self.planes.values()))

    def init_geometry(self):
        self.circle = GLPrimitives.circle()
        self.plane_icon = GLPrimitives.circle(disc=True)
        self.line = GLPrimitives.line(0, 0, 1, 0)

    def init_static_layer(self):
        r, h = 0, 1/(config.getint('RADAR', 'ring_count') + 1)
        while r < 1:
            def draw_ring(w, radius=r):
                glDisable(GL_LINE_SMOOTH)
                w.set_color(0.1, 0.24, 0.1, 1.0)
                w.draw_at(self.circle, scale=radius)
                glEnable(GL_LINE_SMOOTH)
            self.static_layer.add(draw_ring, z_order=0)
            r += h

        # Sweep line (animated, but part of static visual structure)
        def draw_sweep(w):
            w.set_color(0.29, 0.87, 0.5, 1.0)
            w.draw_at(self.line, scale=0.85, rotation=self.sweep_angle)
        self.static_layer.add(draw_sweep, z_order=1)

    def tick(self, delta: float):
        self.sweep_angle = (self.sweep_angle + 90.0 * delta) % 360

    def update_planes(self, planes: list):
        if not self.plane_icon: return

        r = config.getfloat('RADAR', 'radius')
        origin_lat, origin_lon = self.lat, self.lon
        self.dynamic_layer.clear()
        self.clear_texts()

        for plane in planes:
            if plane.latitude is None or plane.longitude is None: continue

            gl_x = (plane.longitude - origin_lon) / r
            gl_y = (plane.latitude - origin_lat) / r

            def draw_plane(w, x=gl_x, y=gl_y):
                w.set_color(0.0, 0.9, 0.9, 1.0)
                w.draw_at(self.plane_icon, x=x, y=y, scale=0.02)
            
            self.dynamic_layer.add(draw_plane, z_order=10)

            callsign = plane.callsign.strip() if plane.callsign else ""
            self.add_text(
                callsign,
                x=gl_x + 0.03,
                y=gl_y + 0.02,
                color=(0, 230, 230),
                align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                z_order=-1,
            )
