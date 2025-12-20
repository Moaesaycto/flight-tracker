import configparser
from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QElapsedTimer, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QMatrix4x4, QPainter
from PySide6.QtOpenGL import QOpenGLShader, QOpenGLShaderProgram
from PySide6.QtOpenGLWidgets import QOpenGLWidget

import numpy as np

from OpenGL.GL import (glEnable, glBlendFunc, glViewport,
                       glUniform4f, glUniformMatrix4fv, glClear, glDisable)
from OpenGL.GL import (GL_BLEND, GL_LINE_SMOOTH, GL_COLOR_BUFFER_BIT,
                       GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_FALSE)


VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec2 position;

uniform mat4 projection;
uniform mat4 model;

void main() {
    gl_Position = projection * model * vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
uniform vec4 color;
out vec4 fragColor;

void main() {
    fragColor = color;
}
"""

config = configparser.ConfigParser()
config.read('config.ini')


@dataclass
class Drawable:
    draw_func: Callable[..., None]
    z_order: int = 0


class Layer:
    """Manages a list of drawable items"""

    def __init__(self):
        self.items: list[Drawable] = []

    def add(self, draw_func: Callable[..., None], z_order=0):
        item = Drawable(draw_func, z_order)
        self.items.append(item)
        self.items.sort(key=lambda x: x.z_order)

    def remove(self, item: Drawable):
        self.items.remove(item)

    def clear(self):
        self.items.clear()

    def draw_all(self, widget):
        for item in self.items:
            item.draw_func(widget)


class BaseOpenGLWidget(QOpenGLWidget):
    shader: QOpenGLShaderProgram | None = None
    loc_projection: int
    loc_model: int
    loc_color: int

    projection: QMatrix4x4

    elapsed: QElapsedTimer | None = None
    timer: QTimer | None = None
    last_time: int

    def __init__(self, min_width=400, min_height=400, animated=False):
        super().__init__()
        self.setMinimumSize(min_width, min_height)
        self.projection = QMatrix4x4()

        self.static_layer = Layer()
        self.dynamic_layer = Layer()

        self._model_matrix = QMatrix4x4()
        self._model_data = np.zeros(16, dtype=np.float32)

        # Text rendering
        self._font = QFont("Monospace", 12)
        self.texts: list[dict] = []

        # Timer for animations if needed
        if animated:
            self.elapsed = QElapsedTimer()
            self.elapsed.start()
            self.last_time = 0
            self.timer = QTimer()
            self.timer.timeout.connect(self._tick)
            self.timer.start(1000 // config.getint('GUI', 'fps'))

    def initializeGL(self) -> None:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)

        self.shader = QOpenGLShaderProgram(self)
        self.shader.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Vertex, VERTEX_SHADER)
        self.shader.addShaderFromSourceCode(
            QOpenGLShader.ShaderTypeBit.Fragment, FRAGMENT_SHADER)
        self.shader.link()

        self.loc_projection = self.shader.uniformLocation("projection")
        self.loc_model = self.shader.uniformLocation("model")
        self.loc_color = self.shader.uniformLocation("color")

        self.init_geometry()
        self.init_static_layer()

        return super().initializeGL()

    def resizeGL(self, w: int, h: int) -> None:
        glViewport(0, 0, w, h)
        self.projection = QMatrix4x4()
        aspect = w / h if h > 0 else 1.0
        self.projection.ortho(-aspect, aspect, -1.0, 1.0, -1.0, 1.0)

    def paintGL(self) -> None:
        if not self.shader:
            return

        glClear(GL_COLOR_BUFFER_BIT)
        self.shader.bind()
        self.set_projection(self.projection)

        self.static_layer.draw_all(self)
        self.dynamic_layer.draw_all(self)

        self.shader.release()
        
        # Reset OpenGL state for QPainter
        glDisable(GL_BLEND)
        glDisable(GL_LINE_SMOOTH)
        
        self._draw_texts()
        
        # Restore OpenGL state
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)

    def set_color(self, r: float, g: float, b: float, a: float):
        glUniform4f(self.loc_color, r, g, b, a)

    def set_model(self, matrix: QMatrix4x4):
        glUniformMatrix4fv(self.loc_model, 1, GL_FALSE,
                           np.array(matrix.data(), dtype=np.float32))

    def set_projection(self, matrix: QMatrix4x4):
        glUniformMatrix4fv(self.loc_projection, 1, GL_FALSE,
                           np.array(matrix.data(), dtype=np.float32))

    def draw_at(self, geometry, x: float = 0, y: float = 0,
                scale: float = 1.0, rotation: float = 0.0):
        self._model_matrix.setToIdentity()
        self._model_matrix.translate(x, y, 0.0)
        self._model_matrix.rotate(rotation, 0.0, 0.0, 1.0)
        self._model_matrix.scale(scale)

        self._model_data[:] = self._model_matrix.data()

        glUniformMatrix4fv(self.loc_model, 1, GL_FALSE, self._model_data)
        geometry.draw()

    def _tick(self):
        if not self.elapsed:
            raise AttributeError("Animation not enabled.")

        now = self.elapsed.elapsed()
        delta = (now - self.last_time) / 1000.0
        self.last_time = now

        self.tick(delta)
        self.update()

    def _draw_texts(self):
        painter = QPainter(self)
        painter.setFont(self._font)
        metrics = painter.fontMetrics()

        for t in self.texts:
            painter.setPen(QColor(*t["color"]))
            px, py = self._gl_to_pixel(t["x"], t["y"])
            
            # Get text bounds
            text_rect = metrics.boundingRect(
                QRectF(0, 0, 1000, 1000).toRect(),
                t["align"],
                t["text"]
            )
            
            # Horizontal anchor
            if t["align"] & Qt.AlignmentFlag.AlignHCenter:
                px -= text_rect.width() // 2
            elif t["align"] & Qt.AlignmentFlag.AlignRight:
                px -= text_rect.width()
            
            # Vertical anchor
            if t["align"] & Qt.AlignmentFlag.AlignVCenter:
                py -= text_rect.height() // 2
            elif t["align"] & Qt.AlignmentFlag.AlignBottom:
                py -= text_rect.height()
            
            text_rect.moveLeft(int(px))
            text_rect.moveTop(int(py))
            
            painter.drawText(text_rect, t["align"], t["text"])

        painter.end()

    def _gl_to_pixel(self, x: float, y: float) -> tuple[int, int]:
        w, h = self.width(), self.height()
        aspect = w/h if h > 0 else 1.0

        return int((x / aspect + 1) / 2 * w), int((1 - y) / 2 * h)

    def add_text(self, text: str, x: float, y: float,
                 color: tuple = (0, 230, 230),
                 align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop):
        self.texts.append({
            "text": text,
            "x": x,
            "y": y,
            "color": color,
            "align": align
        })

    def clear_texts(self): self.texts.clear()

    def init_geometry(self): raise NotImplementedError
    def init_static_layer(self): pass
    def tick(self, delta: float): pass
