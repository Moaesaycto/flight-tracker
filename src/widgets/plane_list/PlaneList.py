from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class PlaneList(QScrollArea):
    _list: QWidget | None = None

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(200)
        self.count_label = QLabel()

        self._layout = QVBoxLayout()
        self._layout.setSpacing(5)
        self.setLayout(self._layout)
        self.setContentsMargins(0, 0, 0, 0)

    def clear(self):
        while self._layout and self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    @Slot(dict)
    def handle_socket_update(self, updated_planes):
        self.clear()
        self.planes = updated_planes

        count = 0
        for p in self.planes.values():
            if p.callsign and p.longitude and p.latitude:
                self._layout.addWidget(p.generate_widget())
            else:
                count += 1

        self._layout.addStretch()

        unaccounted_label = QLabel(f"{count} detected with no position")
        self._layout.addWidget(unaccounted_label)
