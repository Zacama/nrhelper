import sys
from PyQt6.QtCore import QThread
from PyQt6.QtGui import QIcon, QAction, QCursor
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu
)

from src.input import InputWorker
from src.updater import Updater
from src.overlay import OverlayWidget, UIState
from src.settings import SettingsWindow
from src.common import APP_FULLNAME, APP_VERSION, get_asset_path
from src.logger import info, warning, error

if __name__ == "__main__":
    info("=" * 40)
    info(f"Starting app v{APP_VERSION}...")

    app = QApplication(sys.argv)
    
    # 防止因没有窗口而导致程序退出
    app.setQuitOnLastWindowClosed(False)

    # 创建对象
    input = InputWorker()
    overlay = OverlayWidget()
    updater = Updater(overlay)
    settings_window = SettingsWindow(overlay, updater, input)
    
    # 创建系统托盘图标和菜单
    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(QIcon(get_asset_path("icon.ico")))
    tray_icon.setToolTip(APP_FULLNAME)

    menu = QMenu()
    settings_action = QAction("设置")
    settings_action.triggered.connect(settings_window.show)
    quit_action = QAction("退出")
    quit_action.triggered.connect(app.quit)
    menu.addAction(settings_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray_icon.setContextMenu(menu)
    tray_icon.show()

    def show_and_set_menu_pos():
        cursor_pos = QCursor.pos()
        menu.move(cursor_pos)
        menu.show()
    overlay.right_click_signal.connect(show_and_set_menu_pos)

    # 启动输入监听
    input_thread = QThread()
    input.moveToThread(input_thread)
    input_thread.started.connect(input.run)
    input_thread.start()
    
    # 设置并启动后台检测器
    updater_thread = QThread()
    updater.moveToThread(updater_thread)
    updater_thread.started.connect(updater.run)
    
    # 清理：程序退出时，停止worker并等待线程结束
    def on_quit():
        info("Stopping worker thread...")
        updater.stop()
        updater_thread.quit()
        updater_thread.wait()
        input.stop()
        input_thread.quit()
        input_thread.wait()
        info("Thread stopped. Exiting.")
    app.aboutToQuit.connect(on_quit)
    
    updater_thread.start()
    overlay.show()
    app.exec()

    info("App exited.")
