from typing import Dict, Tuple
from PySide6.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QWidget
from PySide6.QtCore import QThread

from src.widgets.radar.Plane import Plane
from src.widgets.radar import RadarScopeGL
from src.widgets.radar.ADSBSocketWorker import ADSBSocketWorker

import serial
import pynmea2
import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def get_gps_location() -> Tuple[float, float]:
    if config.get('GPS', 'type') == "auto":
        port = config.get('GPS', 'port')
        baud = config.getint('GPS', 'baud')
        try:
            with serial.Serial(port, baud, timeout=1) as ser:
                print("Connected to GPS. Waiting for lock...")

                while True:
                    line = ser.readline().decode('ascii', errors='replace')

                    if line.startswith('$GPGGA'):
                        try:
                            msg = pynmea2.parse(line)
                            if msg.gps_qual and int(msg.gps_qual) > 0 and msg.latitude and msg.longitude:
                                return float(msg.latitude), float(msg.longitude)
                            else:
                                print(
                                    f"Waiting for fix... (Sats visible: {msg.num_sats})", end='\r')
                        except pynmea2.ParseError:
                            continue

        except Exception as e:
            print(f"Serial Error: {e}")
            return config.getfloat('GPS', 'lat'), config.getfloat('GPS', 'lon')

    return config.getfloat('GPS', 'lat'), config.getfloat('GPS', 'lon')


class MainWindow(QMainWindow):
    planes: Dict[str, Plane]

    def __init__(self):
        super().__init__()
        self.container = QWidget()
        self.setCentralWidget(self.container)
        layout = QHBoxLayout(self.container)
        lat, lon = get_gps_location()
        print(f"GPS position locked: {lat}, {lon}")
        self.radar = RadarScopeGL(lat, lon)

        layout.addWidget(self.radar)

        self.worker = ADSBSocketWorker()
        self.worker_thread = QThread()

        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.planes_updated.connect(self.radar.handle_socket_update)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

        self.resize(800, 800)

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
