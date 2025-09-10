from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt
from src.logger import info, warning, error


def set_widget_always_on_top(widget: QWidget):
    try:
        import win32gui
        import win32con
        hwnd = widget.winId().__int__()
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 
                                0, 0, 0, 0, 
                                win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
        info(f"Window HWND: {hwnd} set to TOPMOST.")
    except Exception as e:
        warning(f"Error setting system always on top: {e}")


def is_window_in_foreground(window_title: str) -> bool:
    """
    检查包含特定标题的窗口是否在 Windows 的最前面。
    """
    try:
        import win32gui
        import time
        active_window_handle = win32gui.GetForegroundWindow()
        active_window_title = win32gui.GetWindowText(active_window_handle)
        if window_title.lower() in active_window_title.lower():
            return True
        return False
    except Exception as e:
        return False
    

def mss_region_to_qt_region(region: tuple[int]):
    x, y, w, h = region
    app: QApplication = QApplication.instance()
    screens = app.screens()
    for screen in screens:
        sx = screen.geometry().x()
        sy = screen.geometry().y()
        sw = screen.geometry().width()
        sh = screen.geometry().height()
        ratio = screen.devicePixelRatio()
        mss_sw = int(sw * ratio)
        mss_sh = int(sh * ratio)
        if sx <= x <= sx + mss_sw and sy <= y <= sy + mss_sh:
            qx = sx + int((x - sx) / ratio)
            qy = sy + int((y - sy) / ratio)
            qw = int(w / ratio)
            qh = int(h / ratio)
            return (qx, qy, qw, qh)
    raise ValueError(f"Region {region} is out of all screen bounds")
    