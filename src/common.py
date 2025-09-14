from pathlib import Path
import os
from datetime import timedelta
from platformdirs import user_data_dir, user_desktop_dir


APP_NAME = "nightreign-overlay-helper"
APP_NAME_CHS = "黑夜君临悬浮助手"
APP_VERSION = "0.7.1"
APP_FULLNAME = f"{APP_NAME_CHS}v{APP_VERSION}"
APP_AUTHOR = "NeuraXmy"

GAME_WINDOW_TITLE = "ELDEN RING NIGHTREIGN"


def get_asset_path(path: str) -> str:
    return str(Path("assets") / path)

def get_data_path(path: str) -> str:
    return str(Path("data") / path)

def get_appdata_path(filename: str) -> str:
    if appdata := os.getenv("APPDATA"):
        app_data_dir = Path(appdata) / APP_NAME
    else:
        app_data_dir = Path(user_data_dir(appname=APP_NAME, appauthor=APP_AUTHOR))
    app_data_dir.mkdir(parents=True, exist_ok=True)
    return str(app_data_dir / filename)

def get_desktop_path(filename: str = "") -> str:
    desktop = Path(user_desktop_dir())
    desktop.mkdir(exist_ok=True)
    return str(desktop / filename) if filename else str(desktop)


ICON_PATH = get_asset_path("icon.ico")


def get_readable_timedelta(t: timedelta) -> str:
    seconds = int(t.total_seconds())
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}小时{minutes}分钟{seconds}秒"
    elif minutes > 0:
        return f"{minutes}分钟{seconds}秒"
    else:
        return f"{seconds}秒"
    

