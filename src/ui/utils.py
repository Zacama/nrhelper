from PyQt6.QtWidgets import QWidget
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