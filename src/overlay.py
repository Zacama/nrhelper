from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout, QSizePolicy
)
from PyQt6.QtGui import QMouseEvent, QKeySequence, QKeyEvent
from dataclasses import dataclass, field
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

from src.common import APP_FULLNAME, APP_AUTHER
from src.config import Config
from src.logger import info, warning, error


@dataclass
class UIState:
    x: int | None = None
    y: int | None = None
    scale: float | None = None
    opacity: float | None = None
    draggable: bool | None = None
    progress: float | None = None
    text: str | None = None
    visible: bool | None = None
    progress2: float | None = None
    text2: str | None = None
    progress2_visible: bool | None = None


class OverlayWidget(QWidget):
    double_click_signal = pyqtSignal()
    right_click_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool 
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 获取窗口句柄并设置系统层面的置顶
        self.set_system_always_on_top()
        
        self.layout: QVBoxLayout = QVBoxLayout(self)

        self.progress_bar_layout = QHBoxLayout()
        self.progress_bar_layout.setSpacing(1)
        self.progress_bars: list[QProgressBar] = []
        for i in range(4):
            length = Config.get().day_period_seconds[i]
            progress_bar = QProgressBar()
            progress_bar.setTextVisible(False)
            progress_bar.setRange(0, 10000)
            progress_bar.setMinimumWidth(10)
            self.progress_bars.append(progress_bar)
            self.progress_bar_layout.addWidget(progress_bar)
            self.progress_bar_layout.setStretchFactor(progress_bar, length)
        self.layout.addLayout(self.progress_bar_layout)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setColor(QColor(0, 0, 0, 150)) 
        shadow_effect.setOffset(0, 0) 
        self.label.setGraphicsEffect(shadow_effect)
        self.layout.addWidget(self.label)

        self.progress_bar2 = QProgressBar()
        self.progress_bar2.setTextVisible(False)
        self.progress_bar2.setRange(0, 10000)
        self.layout.addWidget(self.progress_bar2)

        self.label2 = QLabel()
        self.label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setColor(QColor(0, 0, 0, 150)) 
        shadow_effect.setOffset(0, 0) 
        self.label2.setGraphicsEffect(shadow_effect)
        self.layout.addWidget(self.label2)

        self.layout.addStretch()
        
        self.drag_position = QPoint()
        self.draggable = False

        self.progress_css = Config.get().day_progress_css
        self.text_css = Config.get().day_text_css
        self.progress2_css = Config.get().in_rain_progress_css
        self.text2_css = Config.get().in_rain_text_css
       
        self.update_ui_state(UIState(
            scale=1.0,
            opacity=0.6,
            draggable=False,
            progress=0,
            text=f"{APP_FULLNAME} by {APP_AUTHER} (右键打开菜单)",
            visible=True,
            progress2=0,
            text2="",
            progress2_visible=False,
        ))


    def set_system_always_on_top(self):
        try:
            import win32gui
            import win32con
            hwnd = self.winId().__int__()
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 
                                  0, 0, 0, 0, 
                                  win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
            info(f"Window HWND: {hwnd} set to TOPMOST.")
        except Exception as e:
            error(f"Error setting system always on top: {e}")

    def mousePressEvent(self, event: QMouseEvent):
        if self.draggable and event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        if event.button() == Qt.MouseButton.RightButton:
            self.right_click_signal.emit()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.draggable and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_click_signal.emit()
            event.accept()
    
    def _set_draggable(self, draggable: bool):
        self.draggable = draggable
        if draggable:
            self.setStyleSheet("background: #333;")
            info("Overlay: Draggable mode ON")
        else:
            self.setStyleSheet("")
            info("Overlay: Draggable mode OFF")

    def _apply_scale(self, scale: float):
        width = int(400 * scale)
        height = int(140 * scale)
        self.setFixedSize(width, height)

        font_size = int(14 * scale)
        self.label.setStyleSheet(self.text_css.replace("{font_size}", str(font_size)))
        self.label2.setStyleSheet(self.text2_css.replace("{font_size}", str(font_size)))

        pb_height = int(16 * scale)
        pb_border_radius = int(pb_height / 5)

        for i in range(4):
            self.progress_bars[i].setFixedHeight(pb_height)
            self.progress_bars[i].setStyleSheet(self.progress_css.replace("{border_radius}", str(pb_border_radius)))

        self.progress_bar2.setFixedHeight(pb_height)
        self.progress_bar2.setStyleSheet(self.progress2_css.replace("{border_radius}", str(pb_border_radius)))

    def update_ui_state(self, state: UIState):
        if state.x is not None and state.y is not None:
            self.move(state.x, state.y)
        if state.scale is not None:
            self._apply_scale(state.scale)
        if state.opacity is not None:
            self.setWindowOpacity(state.opacity)
        if state.progress is not None:
            for i in range(4):
                progress = min(1, max(0, (state.progress - i)))
                self.progress_bars[i].setValue(int(progress * self.progress_bars[i].maximum()))
        if state.text is not None:
            self.label.setText(state.text)
        if state.draggable is not None:
            self._set_draggable(state.draggable)
        if state.visible is not None:
            if state.visible:
                self.show()
            else:
                self.hide()
        if state.progress2 is not None:
            self.progress_bar2.setValue(int(state.progress2 * self.progress_bar2.maximum()))
        if state.text2 is not None:
            self.label2.setText(state.text2)
        if state.progress2_visible is not None:
            if state.progress2_visible:
                self.progress_bar2.show()
                self.label2.show()
            else:
                self.progress_bar2.hide()
                self.label2.hide()
        self.update()