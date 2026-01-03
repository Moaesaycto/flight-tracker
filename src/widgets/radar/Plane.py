from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from PySide6.QtGui import QMatrix4x4
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from src.gl.GLGeometry import GLGeometry
from src.gl.BaseOpenGLWidget import BaseOpenGLWidget, Drawable


def safe_float(val):
    try:
        return float(val)
    except ValueError:
        return None


def safe_int(val):
    try:
        return int(val)
    except ValueError:
        return None


@dataclass
class Plane:
    hexIdent: str

    _widget: QWidget | None = None
    _callsign_label: QLabel | None = None

    lastGenUpdate: datetime = field(default_factory=datetime.now)
    lastLogUpdate: datetime = field(default_factory=datetime.now)

    callsign: str | None = None
    x: float = 0.0  # Normalized position (-1 to 1)
    y: float = 0.0
    heading: float = 0.0  # Degrees
    altitude: int | None = None
    groundSpeed: int | None = None
    track: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    verticalRate: int | None = None
    squawk: str | None = None

    # Flags
    alert: bool = False
    emergency: bool = False
    spi: bool = False
    onGround: bool = True

    staMessage: str | None = None

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
        transmissionType = data[0]

        if transmissionType == "MSG":
            messageType = data[1]
            # ES Identification and Category
            if messageType == "1":
                self.callsign = data[10]

            # ES Surface Position Message
            elif messageType == "2":
                self.altitude, self.groundSpeed, self.track = [
                    safe_int(d) for d in data[11:14]]

                self.latitude = safe_float(data[14]) or self.latitude
                self.longitude = safe_float(data[15]) or self.longitude

                self.onGround = data[21] != "0"

            # ES Airborne Position Message
            elif messageType == "3":
                self.altitude = safe_int(data[11]) or self.altitude
                self.latitude = safe_float(data[14]) or self.latitude
                self.longitude = safe_float(data[15]) or self.longitude
                self.alert, self.emergency, self.spi, self.onGround = [
                    d != "0" for d in data[18:22]]

            # ES Airborne Velocity Message
            elif messageType == "4":
                self.groundSpeed, self.track = [
                    safe_int(d) for d in data[12:14]]
                self.verticalRate = safe_int(data[16])

            # Surveillance Alt Message
            elif messageType == "5":
                self.altitude = safe_int(data[11]) or self.altitude
                self.alert, self.spi, self.onGround = data[18] != "0", data[20] != "0", data[21] != "0"

            # Surveillance ID Message
            elif messageType == "6":
                self.altitude = safe_int(data[11]) or self.altitude
                self.squawk = data[18]
                self.alert, self.emergency, self.spi, self.onGround = [
                    d != "0" for d in data[18:22]]

            # Air To Air Message
            elif messageType == "7":
                self.altitude = safe_int(data[11]) or self.altitude
                self.onGround = data[21] != "0"

            # All Call Reply
            elif messageType == "8":
                self.onGround = data[21] != "0"

        # New ID and Aircraft Message
        elif transmissionType in {"SEL", "ID"}:
            self.callsign = data[10]

        # Status Change Message
        elif transmissionType in {"STA"}:
            self.staMessage = data[10]

        # Not a useful message otherwise
        else:
            return

        genDate, genTime, logDate, logTime = data[6:10]
        self.lastGenUpdate = datetime.strptime(
            f"{genDate} {genTime}000", "%Y/%m/%d %H:%M:%S.%f")
        self.lastLogUpdate = datetime.strptime(
            f"{logDate} {logTime}000", "%Y/%m/%d %H:%M:%S.%f")

    def generate_widget(self) -> QWidget:
        small_text_style = "font-size: 8px;"
        card = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # Info area (callsign, alt, heading, lat/lon, heading, squawk(?))
        info = QFrame()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Top info area:
        # Callsign            alt   GS
        top_info = QFrame()
        top_info_layout = QHBoxLayout()
        top_info_layout.setSpacing(0)
        top_info_layout.setContentsMargins(0, 0, 0, 0)

        callsign_label = QLabel(self.callsign)
        alt_label = QLabel(str(self.altitude) + "ft")
        alt_label.setStyleSheet(small_text_style)
        gs_label = QLabel(str(self.groundSpeed) + "kt")
        gs_label.setStyleSheet(small_text_style)

        top_info_layout.addWidget(callsign_label)
        top_info_layout.addStretch()
        top_info_layout.addWidget(alt_label)
        top_info_layout.addWidget(gs_label)
        top_info.setLayout(top_info_layout)

        # Bottom info area:
        # lat,lon   heading   alert   squawk
        latlon_label = QLabel(f"{self.latitude:.3f}°,{self.longitude:.3f}°")
        latlon_label.setStyleSheet(small_text_style)
        heading_label = QLabel(f"{self.heading}°")
        heading_label.setStyleSheet(small_text_style)
        squawk_label = QLabel(f"{self.squawk}")
        squawk_label.setStyleSheet(small_text_style)

        bottom_info = QFrame()
        bottom_info_layout = QHBoxLayout()
        bottom_info_layout.setContentsMargins(0, 0, 0, 0)
        bottom_info_layout.addWidget(latlon_label)
        bottom_info_layout.addStretch()
        bottom_info_layout.addWidget(heading_label)
        bottom_info_layout.addWidget(squawk_label)
        bottom_info.setLayout(bottom_info_layout)

        # Final sprint
        info_layout.addWidget(top_info)
        info_layout.addWidget(bottom_info)
        info.setLayout(info_layout)

        layout.addWidget(info)
        card.setLayout(layout)

        return card

    def __str__(self):
        return f"{self.callsign}: {self.latitude}, {self.longitude}"
