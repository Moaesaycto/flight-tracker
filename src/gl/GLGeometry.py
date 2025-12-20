from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLVertexArrayObject
import numpy as np
import mapbox_earcut as earcut

from OpenGL.GL import (glEnableVertexAttribArray,
                       glVertexAttribPointer, glDrawArrays)
from OpenGL.GL import (GL_FLOAT, GL_FALSE, GL_LINES,
                       GL_LINE_LOOP, GL_TRIANGLE_FAN, GL_LINE_STRIP, GL_TRIANGLES)


class GLGeometry:
    def __init__(self, vertices: np.ndarray, draw_mode: int):
        """Custom GLGeometry parent class

        Args:
            vertices (np.ndarray): flat array of points, [x, y, x, y, ...]
            draw_mode (int): GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP, GL_TRIANGLES, GL_TRIANGLE_FAN
        """
        self.draw_mode = draw_mode
        self.vertex_count = len(vertices) // 2

        self.vao = QOpenGLVertexArrayObject()
        self.vao.create()
        self.vao.bind()

        self.vbo = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self.vbo.create()
        self.vbo.bind()
        self.vbo.allocate(vertices.tobytes(), vertices.nbytes)

        # See VERTEX_SHADER's layout location in BaseOpenGLWidget
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

        self.vbo.release()
        self.vao.release()

    def draw(self):
        self.vao.bind()
        glDrawArrays(self.draw_mode, 0, self.vertex_count)
        self.vao.release()

    def destroy(self):
        self.vbo.destroy()
        self.vao.destroy()


class GLPrimitives:
    @staticmethod
    def line(x1: float | int, y1: float | int, x2: float | int, y2: float | int) -> GLGeometry:
        """Generate a Euclidean line from (x1, y1) to (x2, y2)

        Args:
            x1 (float | int): x coordinate of first point
            y1 (float | int): y coordinate of first point
            x2 (float | int): x coordinate of second point
            y2 (float | int): y coordinate of second point

        Returns:
            GLGeometry: Structure for OpenGL to render
        """
        vertices = np.array([x1, y1, x2, y2], dtype=np.float32)
        return GLGeometry(vertices, GL_LINES)

    @staticmethod
    def circle(cx: float = 0, cy: float = 0, r: float = 1, segments: int = 64, disc=False) -> GLGeometry:
        """Generate a circle centered at (cx, cy) with a radius of r.

        Args:
            cx (float, optional): x coordinate of center. Defaults to 0.
            cy (float, optional): y coordinate of center. Defaults to 0.
            r (float, optional): Radius of circle. Defaults to 1.
            segments (int, optional): Line count creating the circle. Defaults to 64.
            disc (bool, optional): Fill the circle to make it a disc. Defaults to False.

        Returns:
            GLGeometry: Structure for OpenGL to render
        """
        theta = np.linspace(0, 2 * np.pi, segments + 1, dtype=np.float32)
        edge_x, edge_y = r * np.cos(theta) + cx, r * np.sin(theta) + cy

        if disc:
            vertices = np.empty((segments + 2) * 2, dtype=np.float32)
            vertices[0], vertices[1] = cx, cy
            vertices[2::2], vertices[3::2] = edge_x, edge_y
        else:
            vertices = np.empty((segments + 1) * 2, dtype=np.float32)
            vertices[0::2], vertices[1::2] = edge_x, edge_y

        return GLGeometry(vertices, GL_TRIANGLE_FAN if disc else GL_LINE_LOOP)

    @staticmethod
    def polygon(points: list[tuple[float, float]], closed=True, filled=False) -> GLGeometry:
        """Generate a polygon (and polyline) through the given vertices

        Args:
            points (list[tuple[float, float]]): Vertices for the polygon
            closed (bool, optional): Close the polyline to make a polygon. Defaults to True.
            filled (bool, optional): Fill the polygon. Defaults to False.

        Returns:
            GLGeometry: _description_
        """
        vertices = np.array(points, dtype=np.float32)

        if filled:
            rings = np.array([len(points)])
            indices = earcut.triangulate_float32(vertices, rings)
            return GLGeometry(vertices[indices].flatten(), GL_TRIANGLES)
        else:
            return GLGeometry(vertices.flatten(), GL_LINE_LOOP if closed else GL_LINE_STRIP)
