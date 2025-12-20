
from PySide6.QtWidgets import QApplication

from src.widgets.radar import Plane, RadarScopeGL

if __name__ == "__main__":
    app = QApplication([])
    radar = RadarScopeGL()

    test_planes = [
        Plane("QFA123", 0.3, 0.4, 45),
        Plane("UAL456", -0.5, 0.2, 180),
        Plane("BAW789", 0.1, -0.6, 270),
        Plane("SIA321", -0.3, -0.3, 90),
        Plane("DLH654", 0.6, 0.1, 315),
    ]
    radar.update_planes(test_planes)
    radar.show()
    app.exec()