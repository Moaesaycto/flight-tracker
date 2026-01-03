from PySide6.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QWidget
from PySide6.QtCore import QThread

from src.widgets.radar import RadarScopeGL
from src.widgets.radar.ADSBSocketWorker import ADSBSocketWorker

from src.widgets.plane_list.PlaneList import PlaneList
from src.utils.gps import get_gps_location


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.container = QWidget()
        self.setCentralWidget(self.container)
        layout = QHBoxLayout(self.container)

        lat, lon = get_gps_location()
        print(f"GPS position locked: {lat}, {lon}")

        self.radar = RadarScopeGL(lat, lon)
        self.plane_list = PlaneList()
        layout.addWidget(self.radar)
        layout.addWidget(self.plane_list)

        self.worker = ADSBSocketWorker()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.planes_updated.connect(self.radar.handle_socket_update)
        self.worker.planes_updated.connect(
            self.plane_list.handle_socket_update)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def closeEvent(self, event):
        self.worker.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication([])
    main = MainWindow()
    main.show()
    app.exec()
