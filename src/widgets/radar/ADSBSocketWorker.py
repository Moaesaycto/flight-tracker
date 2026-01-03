from datetime import datetime
import socket
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QCoreApplication

from src.widgets.radar.Plane import Plane


class ADSBSocketWorker(QObject):
    planes_updated = Signal(dict)

    def __init__(self, host="localhost", port=30003):
        super().__init__()
        self.host = host
        self.port = port
        self._running = True
        self.planes = {}

    @Slot()
    def run(self):
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.purge_stale_planes)
        self.cleanup_timer.start(1000)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)

        try:
            sock.connect((self.host, self.port))
            buffer = ""

            while self._running:
                QCoreApplication.processEvents()
                try:
                    data = sock.recv(1024).decode('utf-8')
                    if not data:
                        break

                    buffer += data

                except socket.timeout:
                    continue

                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    message = line.split(',')
                    if len(message) < 5:
                        continue

                    hex_id = message[4]
                    if hex_id not in self.planes:
                        self.planes[hex_id] = Plane(hexIdent=hex_id)

                    try:
                        self.planes[hex_id].update(message)
                        now = datetime.now()
                        stale_ids = [
                            hid for hid, p in self.planes.items()
                            if (now - p.lastLogUpdate)
                        ]
                        self.planes_updated.emit(self.planes.copy())
                    except Exception as e:
                        print("Failed to update: ", line, {e},  "END")
        except Exception as e:
            print(f"Socket Error: {e}")
        finally:
            sock.close()

    def stop(self):
        self._running = False

    @Slot()
    def purge_stale_planes(self):
        now = datetime.now()
        to_remove = [hid for hid, p in self.planes.items()
                     if (now - p.lastLogUpdate).total_seconds() > 60]

        if to_remove:
            for hid in to_remove:
                del self.planes[hid]
            self.planes_updated.emit(self.planes)
