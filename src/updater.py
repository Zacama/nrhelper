from PyQt6.QtCore import QObject, pyqtSignal
import time
from enum import Enum

from src.config import Config
from src.detector import Detector
from src.overlay import OverlayWidget, UIState
from src.input import InputWorker, InputSetting
from src.logger import info, warning, error


class Phase(Enum):
    FIRST_CIRCLE_STABLE = 0
    FIRST_CIRCLE_SHRINK = 1
    SECOND_CIRCLE_STABLE = 2
    SECOND_CIRCLE_SHRINK = 3
    NIGHT_BOSS = 4


def format_period(seconds: int) -> str:
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


class Updater(QObject):
    update_ui_state_signal = pyqtSignal(UIState)

    def __init__(self, overlay: OverlayWidget):
        super().__init__()
        self.overlay = overlay
        self.update_ui_state_signal.connect(self.overlay.update_ui_state)

        self.detector = Detector()
        self._running = False

        self.auto_detect_enabled: bool = True

        self.day: int = None
        self.current_phase: Phase = None
        self.phase_start_time: float = None

        self.in_rain_start_time: float = None

        self.day1_detect_region = None
        self.hp_bar_detect_region = None


    def get_time(self) -> float:
        return time.time() * Config.get().time_scale

    def start_day1(self):
        self.day = 1
        self.current_phase = Phase.FIRST_CIRCLE_STABLE
        self.phase_start_time = self.get_time()
        info("Day 1 started.")

    def start_day2(self):
        self.day = 2
        self.current_phase = Phase.FIRST_CIRCLE_STABLE
        self.phase_start_time = self.get_time()
        info("Day 2 started.")

    def start_day3(self):
        self.day = 3
        self.current_phase = Phase.NIGHT_BOSS
        self.phase_start_time = self.get_time()
        info("Day 3 started.")

    def start_day_by_shortcut(self):
        if self.day is None:
            self.start_day1()
            info("Day 1 started by shortcut.")
        elif self.day == 1:
            self.start_day2()
            info("Day 2 started by shortcut.")
        elif self.day == 2:
            self.start_day1()
            info("Day 1 started by shortcut.")

    def foward_day_by_shortcut(self):
        if self.phase_start_time is not None:
            self.phase_start_time -= Config.get().foward_day_seconds

    def back_day_by_shortcut(self):
        if self.phase_start_time is not None:
            self.phase_start_time += Config.get().back_day_seconds

    def get_phase_progress_text(self) -> tuple[float, str]:
        if self.day is None:
            progress = 0.0
            text = None
        elif self.day == 3:
            progress = 4.0
            t = self.get_time() - self.phase_start_time
            text = f"{format_period(int(t))}"
        elif self.current_phase == Phase.NIGHT_BOSS:
            progress = 4.0
            t = self.get_time() - self.phase_start_time
            text = f"夜晚BOSS战 {format_period(int(t))}"
        else:
            index = self.current_phase.value
            t = self.get_time() - self.phase_start_time
            total = Config.get().day_period_seconds[index]
            progress = t / total + index
            circle_no = "一" if index < 2 else "二"
            action_text = "开始缩圈" if index % 2 == 0 else "缩圈结束"
            text = f"{format_period(int(total - t))} 后第{circle_no}圈{action_text}"
        if self.day is not None:
            text = f"DAY {'I' * self.day} - " + text
        return progress, text
    
    def update_phase(self):
        config = Config.get()
        if self.current_phase is not None:
            index = self.current_phase.value
            phase_length = None if index >= 4 else config.day_period_seconds[index]
            if phase_length is not None and self.get_time() - self.phase_start_time > phase_length:
                self.current_phase = Phase(self.current_phase.value + 1)
                self.phase_start_time += phase_length
                info(f"Phase progress to {self.current_phase.name}.")
            if self.get_time() < self.phase_start_time:
                if self.current_phase.value >= 1:
                    self.current_phase = Phase(self.current_phase.value - 1)
                    self.phase_start_time -= config.day_period_seconds[self.current_phase.value]
                    info(f"Phase back to {self.current_phase.name}.")
                else:
                    self.phase_start_time = self.get_time()

    def start_in_rain(self):
        self.in_rain_start_time = self.get_time()
        info("Started in rain.")

    def stop_in_rain(self):
        self.in_rain_start_time = None
        info("Stopped in rain.")

    def start_in_rain_by_shortcut(self):
        if self.in_rain_start_time is None:
            self.start_in_rain()
            info("Started in rain by shortcut.")
        else:
            self.stop_in_rain()
            info("Stopped in rain by shortcut.")

    def get_in_rain_progress_text(self) -> tuple[float, str]:
        if self.in_rain_start_time is None:
            return 0, ""
        t = self.get_time() - self.in_rain_start_time
        total = Config.get().deadly_nightrain_seconds
        progress = 1.0 - min(t / total, 1.0)
        percent = int(100 * (1.0 - progress))
        text = f"雨中冒险倒计时 {format_period(int(max(total - t, 0)))} - {percent}%"
        return progress, text

    
    def detect_and_update(self):
        result = self.detector.detect(
            self.day1_detect_region,
            self.hp_bar_detect_region
        )
        if result.start_day1:
            self.start_day1()
        elif result.start_day2:
            self.start_day2()
        elif result.start_day3:
            self.start_day3()

        if result.is_in_rain is not None:
            if result.is_in_rain and self.in_rain_start_time is None:
                self.start_in_rain()
            if not result.is_in_rain and self.in_rain_start_time is not None:
                self.stop_in_rain()

    def run(self):
        self._running = True
        info("Updater started.")

        last_detect_time = 0
        while self._running:
            start_time = self.get_time()

            if self.get_time() - last_detect_time > Config.get().detect_interval and self.auto_detect_enabled:
                self.detect_and_update()
                last_detect_time = self.get_time()

            self.update_phase()
            progress, text = self.get_phase_progress_text()
            progress2, text2 = self.get_in_rain_progress_text()

            self.update_ui_state_signal.emit(UIState(
                progress=progress,
                text=text,
                progress2=progress2,
                text2=text2,
                progress2_visible=progress2 > 0.0,
            ))

            elapsed = self.get_time() - start_time
            sleep_time = Config.get().update_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def stop(self):
        self._running = False


