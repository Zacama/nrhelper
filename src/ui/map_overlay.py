from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout, QSizePolicy
)
from PyQt6.QtGui import QMouseEvent, QKeySequence, QKeyEvent
from dataclasses import dataclass, field
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor, QPixmap, QImage
from PIL import Image

from src.common import APP_FULLNAME, APP_AUTHER
from src.config import Config
from src.logger import info, warning, error
from src.ui.utils import set_widget_always_on_top


@dataclass
class MapOverlayUIState:
    x: int | None = None
    y: int | None = None
    w: int | None = None
    h: int | None = None
    opacity: float | None = None
    visible: bool | None = None
    overlay_image: Image.Image | None = None


class MapOverlayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool 
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        set_widget_always_on_top(self)

        self.layout: QVBoxLayout = QVBoxLayout(self)
        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.label)

        self.target_opacity = 1.0
        self.real_opacity = 1.0

        self.startTimer(20)

        self.update_ui_state(MapOverlayUIState(
            w=100,
            h=100,
            opacity=0.0,
            visible=True,
        ))

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_image(self, img: Image.Image):
        img = img.convert("RGBA").resize((self.width(), self.height()), Image.Resampling.BICUBIC)
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap)
        
    def update_ui_state(self, state: MapOverlayUIState):
        if state.x is not None and state.y is not None:
            self.move(state.x, state.y)
        if state.w is not None and state.h is not None:
            self.resize(state.w, state.h)
        if state.opacity is not None:
            self.target_opacity = state.opacity
        if state.visible is not None:
            if state.visible:
                self.show()
            else:
                self.hide()
        if state.overlay_image is not None:
            self.set_image(state.overlay_image)
        self.update()


    def timerEvent(self, event):
        threshold = 0.01
        step = 0.2
        dlt = self.target_opacity - self.real_opacity
        if abs(dlt) > threshold:
            self.real_opacity += dlt * step
            self.setWindowOpacity(self.real_opacity)
        elif 0 < abs(dlt) <= threshold:
            self.real_opacity = self.target_opacity
            self.setWindowOpacity(self.real_opacity)