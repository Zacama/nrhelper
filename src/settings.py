from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QSlider, QGroupBox, QCheckBox, QPushButton,
    QMessageBox, QApplication, QFrame
)
from PyQt6.QtGui import QPixmap, QIcon
import yaml
from dataclasses import dataclass, asdict
import os

from src.overlay import UIState, OverlayWidget
from src.updater import Updater
from src.input import InputWorker, InputSettingWidget, InputSetting
from src.common import APP_FULLNAME, get_appdata_path, get_asset_path, ICON_PATH
from src.logger import info, warning, error
from src.screenshot import ScreenShotWindow
from src.config import Config
from src.detector import Detector, hls_to_rgb


SETTINGS_SAVE_PATH = get_appdata_path("settings.yaml")
DETECT_REGION_TUTORIAL_IMG_PATH = get_asset_path("detect_region_tutorial/{i}.jpg")
COLOR_ALIGN_TUTORIAL_IMG_PATH = get_asset_path("color_align_tutorial/{i}.jpg")

class SettingsWindow(QWidget):
    update_ui_state_signal = pyqtSignal(UIState)

    def __init__(self, overlay: OverlayWidget, updater: Updater, input: InputWorker):
        super().__init__()
        config = Config.get()
        self.overlay = overlay
        self.update_ui_state_signal.connect(self.overlay.update_ui_state)
        self.updater = updater
        self.input = input

        self.setWindowIcon(QIcon(ICON_PATH))
        self.setWindowTitle(f"{APP_FULLNAME} - 设置")
        self.setMinimumSize(350, 200)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        self.layout: QHBoxLayout = QHBoxLayout(self)
        self.left_layout = QVBoxLayout()
        self.layout.addLayout(self.left_layout)

        # 外观设置
        self.appearance_group = QGroupBox("外观")
        self.appearance_layout = QVBoxLayout(self.appearance_group)
        self.left_layout.addWidget(self.appearance_group)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("大小"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(10, 500)
        self.size_slider.setValue(self.overlay.width())
        self.size_slider.valueChanged.connect(self.change_overlay_size)
        size_layout.addWidget(self.size_slider)
        self.appearance_layout.addLayout(size_layout)
        
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("透明度"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.overlay.windowOpacity() * 100))
        self.opacity_slider.valueChanged.connect(self.change_overlay_opacity)
        opacity_layout.addWidget(self.opacity_slider)
        self.appearance_layout.addLayout(opacity_layout)

        self.appearance_layout.addWidget(QLabel("提示：现在可以用鼠标左键拖动调整位置"))
        self.appearance_layout.addWidget(QLabel("推荐使用无边框窗口模式启动游戏\n真全屏模式下可能无法使用"))

        # 输入设置
        self.input_group = QGroupBox("快捷键")
        self.input_layout = QVBoxLayout(self.input_group)
        self.left_layout.addWidget(self.input_group)

        day_input_layout = QHBoxLayout()
        day_input_layout.addWidget(QLabel("重置缩圈"))
        self.day_input_setting_widget = InputSettingWidget(self.input)
        self.day_input_setting_widget.input_triggered.connect(self.updater.start_day_by_shortcut)
        day_input_layout.addWidget(self.day_input_setting_widget)
        self.input_layout.addLayout(day_input_layout)

        forward_day_input_layout = QHBoxLayout()
        forward_day_input_layout.addWidget(QLabel(f"快进缩圈{config.foward_day_seconds}秒"))
        self.forward_day_input_setting_widget = InputSettingWidget(self.input)
        self.forward_day_input_setting_widget.input_triggered.connect(self.updater.foward_day_by_shortcut)
        forward_day_input_layout.addWidget(self.forward_day_input_setting_widget)
        self.input_layout.addLayout(forward_day_input_layout)

        back_day_input_layout = QHBoxLayout()
        back_day_input_layout.addWidget(QLabel(f"倒退缩圈{config.back_day_seconds}秒"))
        self.back_day_input_setting_widget = InputSettingWidget(self.input)
        self.back_day_input_setting_widget.input_triggered.connect(self.updater.back_day_by_shortcut)
        back_day_input_layout.addWidget(self.back_day_input_setting_widget)
        self.input_layout.addLayout(back_day_input_layout)

        in_rain_input_layout = QHBoxLayout()
        in_rain_input_layout.addWidget(QLabel("开始雨中冒险"))
        self.in_rain_input_setting_widget = InputSettingWidget(self.input)
        self.in_rain_input_setting_widget.input_triggered.connect(self.updater.start_in_rain_by_shortcut)
        in_rain_input_layout.addWidget(self.in_rain_input_setting_widget)
        self.input_layout.addLayout(in_rain_input_layout)

        self.input_layout.addWidget(QLabel("点击按钮修改，支持键盘或手柄组合键"))


        self.right_layout = QVBoxLayout()
        self.layout.addLayout(self.right_layout)

        # 自动检测设置
        self.auto_detect_group = QGroupBox("自动检测")
        self.auto_detect_layout = QVBoxLayout(self.auto_detect_group)
        self.right_layout.addWidget(self.auto_detect_group)

        screenshot_region_help_layout = QHBoxLayout()
        help_button = QPushButton("查看帮助")
        help_button.setStyleSheet("padding: 6px;")
        help_button.clicked.connect(self.show_detect_tutorial)
        screenshot_region_help_layout.addWidget(help_button)
        self.auto_detect_layout.addLayout(screenshot_region_help_layout)

        dayx_detect_enable_layout = QHBoxLayout()
        self.dayx_detect_enable_checkbox = QCheckBox("启用缩圈检测")
        self.dayx_detect_enable_checkbox.stateChanged.connect(self.update_dayx_detect_enable)
        dayx_detect_enable_layout.addWidget(self.dayx_detect_enable_checkbox)
        dayx_detect_enable_layout.addStretch()
        self.auto_detect_layout.addLayout(dayx_detect_enable_layout)

        in_rain_detect_enable_layout = QHBoxLayout()
        self.in_rain_detect_enable_checkbox = QCheckBox("启用雨中冒险检测")
        self.in_rain_detect_enable_checkbox.stateChanged.connect(self.update_in_rain_detect_enable)
        in_rain_detect_enable_layout.addWidget(self.in_rain_detect_enable_checkbox)
        in_rain_detect_enable_layout.addStretch()
        self.auto_detect_layout.addLayout(in_rain_detect_enable_layout)

        screenshot_region_layout = QHBoxLayout()
        screenshot_region_layout.addWidget(QLabel("设置检测区域快捷键"))
        self.screenshot_region_setting_widget = InputSettingWidget(self.input)
        self.screenshot_region_setting_widget.input_triggered.connect(self.start_screenshot_region)
        screenshot_region_layout.addWidget(self.screenshot_region_setting_widget)
        self.auto_detect_layout.addLayout(screenshot_region_layout)

        self.day1_detect_region = None
        self.day1_detect_region_label = QLabel("缩圈检测区域：未设置")
        self.auto_detect_layout.addWidget(self.day1_detect_region_label)

        self.hp_bar_detect_region = None
        self.hp_bar_detect_region_label = QLabel("雨中冒险检测区域：未设置")
        self.auto_detect_layout.addWidget(self.hp_bar_detect_region_label)

        clear_button_layout = QHBoxLayout()
        clear_button = QPushButton("清空检测区域")
        clear_button.setStyleSheet("padding: 6px;")
        clear_button.clicked.connect(self.clear_screenshot_region)
        clear_button_layout.addWidget(clear_button)
        clear_button_layout.addStretch()
        self.auto_detect_layout.addLayout(clear_button_layout)

        hp_color_help_layout = QHBoxLayout()
        hp_color_help_button = QPushButton("查看校准血条颜色帮助")
        hp_color_help_button.setStyleSheet("padding: 6px;")
        hp_color_help_button.clicked.connect(self.show_align_hp_color_help)
        hp_color_help_layout.addWidget(hp_color_help_button)
        self.auto_detect_layout.addLayout(hp_color_help_layout)

        align_to_detect_hp_color_layout = QHBoxLayout()
        align_to_detect_hp_color_layout.addWidget(QLabel("校准血条颜色快捷键"))
        self.align_to_detect_hp_color_input_widget = InputSettingWidget(self.input)
        self.align_to_detect_hp_color_input_widget.input_triggered.connect(self.start_to_align_hp_color)
        align_to_detect_hp_color_layout.addWidget(self.align_to_detect_hp_color_input_widget)
        self.auto_detect_layout.addLayout(align_to_detect_hp_color_layout)
        
        self.not_in_rain_hls = None
        self.in_rain_hls = None
        hp_color_layout = QHBoxLayout()
        hp_color_layout.addWidget(QLabel("正常血条颜色:"))
        self.not_in_rain_label = QLabel("默认")
        hp_color_layout.addWidget(self.not_in_rain_label)
        hp_color_layout.addStretch()
        hp_color_layout.addWidget(QLabel("雨中血条颜色:"))
        self.in_rain_label = QLabel("默认")
        hp_color_layout.addWidget(self.in_rain_label)
        self.auto_detect_layout.addLayout(hp_color_layout)

        clear_to_detect_hp_layout = QHBoxLayout()
        clear_to_detect_hp_color = QPushButton("重置血条颜色设置")
        clear_to_detect_hp_color.setStyleSheet("padding: 6px;")
        clear_to_detect_hp_color.clicked.connect(self.clear_hp_color)
        clear_to_detect_hp_layout.addWidget(clear_to_detect_hp_color)
        clear_to_detect_hp_layout.addStretch()
        self.auto_detect_layout.addLayout(clear_to_detect_hp_layout)

        # 打开日志位置按钮
        open_log_button = QPushButton("打开日志位置")
        open_log_button.setStyleSheet("padding: 6px;")
        open_log_button.clicked.connect(self.open_log_directory)
        self.right_layout.addWidget(open_log_button)

        self.left_layout.addStretch()
        self.right_layout.addStretch()

        # 加载设置
        self.load_settings()


    def change_overlay_size(self, value):
        self.update_ui_state_signal.emit(UIState(scale=value / 100.0))
        info(f"Overlay size changed to {value}")

    def change_overlay_opacity(self, value):
        self.update_ui_state_signal.emit(UIState(opacity=value / 100.0))
        info(f"Overlay opacity changed to {value}")
    

    def showEvent(self, event):
        self.update_ui_state_signal.emit(UIState(draggable=True))
        self.load_settings()
        super().showEvent(event)

    def closeEvent(self, event):
        self.update_ui_state_signal.emit(UIState(draggable=False))
        self.save_settings()
        super().closeEvent(event)


    def start_screenshot_region(self):
        screen_size = QApplication.primaryScreen().geometry().size()
        sw, sh = screen_size.width(), screen_size.height()
        COLOR_HP_BAR = "#a84747"
        COLOR_DAY_I = "#686435"
        SCREENSHOT_WINDOW_CONFIG = {
            'annotation_buttons': [
                {'pos': (int(sw * 0.8), int(sh * 0.1)), 'size': 32, 'color': COLOR_HP_BAR, 'text': '点我并框出 血条 的区域'},
                {'pos': (int(sw * 0.8), int(sh * 0.2)), 'size': 32, 'color': COLOR_DAY_I, 'text': '点我并框出 DAY I 图标 的区域'},
            ],
            'control_buttons': {
                'cancel':   {'pos': (int(sw * 0.8), int(sh * 0.5)), 'size': 50, 'color': "#b3b3b3", 'text': '取消'},
                'save':     {'pos': (int(sw * 0.8), int(sh * 0.6)), 'size': 50, 'color': "#ffffff", 'text': '保存'},
            }
        }
        window = ScreenShotWindow(SCREENSHOT_WINDOW_CONFIG, self.input)
        region_result = window.capture_and_show()
        if region_result is None:
            warning("Screenshot region setting canceled")
            return
        else:
            if screenshot := window.screenshot_at_saving:
                save_path = get_appdata_path("detect_region_screenshot.png")
                screenshot.save(save_path)
            for item in region_result:
                if item['color'] == COLOR_HP_BAR:
                    self.hp_bar_detect_region = item['rect']
                elif item['color'] == COLOR_DAY_I:
                    self.day1_detect_region = item['rect']
            self.update_detect_regions()
            self.save_settings()

    def clear_screenshot_region(self):
        reply = QMessageBox.question(self, '确认', '确定要清空已设置的检测区域吗？',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.day1_detect_region = None
            self.hp_bar_detect_region = None
            self.update_detect_regions()

    def show_detect_tutorial(self):
        tutorial_imgs = [QPixmap(str(DETECT_REGION_TUTORIAL_IMG_PATH).format(i=i)) for i in range(1, 7)]
        img_widgets: list[QLabel] = []
        for img in tutorial_imgs:
            img_widget = QLabel()
            img = img.scaledToHeight(min(100, img.height()), Qt.TransformationMode.SmoothTransformation)
            img_widget.setPixmap(img)
            img_widget.setStyleSheet("border: 1px solid #ccc;")
            img_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_widgets.append(img_widget)
        msg = QMessageBox(self)
        msg.setMaximumWidth(400)
        msg.setWindowTitle("自动检测帮助")
        layout: QVBoxLayout = QVBoxLayout()
        layout.addWidget(QLabel("自动检测功能原理为通过定时截图分析画面内容，因此需要先框选检测区域，请按照以下步骤操作："))
        layout.addWidget(QLabel("1. 首先在设置界面调整\"设置检测区域快捷键\""))
        layout.addWidget(img_widgets[0])
        layout.addWidget(QLabel("2. 开始一局单人游戏，在游戏第一天开始，出现\"DAY I\"图标时，按下刚才设置的快捷键\n"
                                "画面会定格，并出现几个按钮"))
        hlayout = QHBoxLayout()
        hlayout.addWidget(img_widgets[1])
        hlayout.addWidget(img_widgets[2])
        layout.addLayout(hlayout)
        layout.addWidget(QLabel("3. 点击\"点我并框出 血条 的区域\"按钮，然后用鼠标框选屏幕上的血条区域\n"
                                "框选的区域如下图所示，需要把血条的纯色内部框进去，只需要框最前面一小段，尽量不要框到边框"))
        layout.addWidget(img_widgets[3])
        layout.addWidget(QLabel("4. 点击\"点我并框出 DAY I 图标 的区域\"按钮，然后用鼠标框选屏幕上的 DAY I 图标\n"
                                "框选的区域如下图所示，需要把最左边的D和最右边的I的突出部分也要框进去，并且尽量严丝合缝"))
        layout.addWidget(img_widgets[4])
        layout.addWidget(QLabel("5. 最后点击\"保存\"按钮完成设置，在设置界面查看是否显示\"已设置\""))
        layout.addWidget(img_widgets[5])
        layout.addWidget(QLabel("6. 之后正常游玩即可自动计时缩圈和雨中冒险，若修改游戏分辨率则需要重新框选"))
        layout.addWidget(QLabel("缩圈自动检测可能失效的场景：DAY X图标出现时正在浏览背包和地图 / 使用简体中文以外的游戏语言\n"
                                "雨中冒险检测可能失效的场景：丝血 / 开启HDR / 开启画面滤镜"))
        layout.addWidget(QLabel("即使开启了自动检测，仍然推荐设置快捷键作为备用"))
        layout.addWidget(QLabel("7. 如果雨中冒险检测失效，可能是因为色差，可以尝试设置里的\"校准血条颜色\""))
        msg.layout().addLayout(layout, 0, 0)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def update_detect_regions(self):
        self.updater.day1_detect_region = self.day1_detect_region
        self.updater.hp_bar_detect_region = self.hp_bar_detect_region
        info(f"Updated detect regions: day1={self.day1_detect_region}, hp_bar={self.hp_bar_detect_region}")
        if self.day1_detect_region is None:
            self.day1_detect_region_label.setText("缩圈检测区域：未设置")
        else:
            self.day1_detect_region_label.setText(f"缩圈检测区域：已设置 {self.day1_detect_region}")
        if self.hp_bar_detect_region is None:
            self.hp_bar_detect_region_label.setText("雨中冒险检测区域：未设置")
        else:
            self.hp_bar_detect_region_label.setText(f"雨中冒险检测区域：已设置 {self.hp_bar_detect_region}")


    def start_to_align_hp_color(self):
        screen_size = QApplication.primaryScreen().geometry().size()
        sw, sh = screen_size.width(), screen_size.height()
        COLOR_NOT_IN_RAIN = "#b83232"
        COLOR_IN_RAIN = "#c03184"
        SCREENSHOT_WINDOW_CONFIG = {
            'annotation_buttons': [
                {'pos': (int(sw * 0.8), int(sh * 0.1)), 'size': 32, 'color': COLOR_NOT_IN_RAIN, 'text': '点我并框出 正常颜色血条 的区域'},
                {'pos': (int(sw * 0.8), int(sh * 0.2)), 'size': 32, 'color': COLOR_IN_RAIN,     'text': '点我并框出 雨中颜色血条 的区域'},
            ],
            'control_buttons': {
                'cancel':   {'pos': (int(sw * 0.8), int(sh * 0.5)), 'size': 50, 'color': "#b3b3b3", 'text': '取消'},
                'save':     {'pos': (int(sw * 0.8), int(sh * 0.6)), 'size': 50, 'color': "#ffffff", 'text': '保存'},
            }
        }
        window = ScreenShotWindow(SCREENSHOT_WINDOW_CONFIG, self.input)
        region_result = window.capture_and_show()
        if region_result is None:
            warning("align hp color setting canceled")
            return
        else:
            for item in region_result:
                if item['color'] == COLOR_NOT_IN_RAIN:
                    self.not_in_rain_hls = Detector.get_to_detect_hp_hls(window.screenshot_pixmap, item['rect'])
                elif item['color'] == COLOR_IN_RAIN:
                    self.in_rain_hls = Detector.get_to_detect_hp_hls(window.screenshot_pixmap, item['rect'])
            self.update_hp_color()
            self.save_settings()

    def clear_hp_color(self):
        reply = QMessageBox.question(self, '确认', '确定要重置血条颜色设置为默认吗？', 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.not_in_rain_hls = None
            self.in_rain_hls = None
            self.update_hp_color()

    def update_hp_color(self):
        self.updater.not_in_rain_hls = self.not_in_rain_hls
        self.updater.in_rain_hls = self.in_rain_hls
        info(f"Updated hp color: not_in_rain_hls={self.not_in_rain_hls}, in_rain_hls={self.in_rain_hls}")
        if self.not_in_rain_hls is None:
            self.not_in_rain_label.setText(f"默认")
            self.not_in_rain_label.setStyleSheet(f"background-color: #fff")
        else:
            self.not_in_rain_label.setText(f"已设置")
            self.not_in_rain_label.setStyleSheet(f"background-color: rgb{hls_to_rgb(self.not_in_rain_hls)}; color: white")
        if self.in_rain_hls is None:
            self.in_rain_label.setText(f"默认")
            self.in_rain_label.setStyleSheet(f"background-color: #fff")
        else:
            self.in_rain_label.setText(f"已设置")
            self.in_rain_label.setStyleSheet(f"background-color: rgb{hls_to_rgb(self.in_rain_hls)}; color: white")

    def show_align_hp_color_help(self):
        tutorial_imgs = [QPixmap(str(COLOR_ALIGN_TUTORIAL_IMG_PATH).format(i=i)) for i in range(1, 4)]
        img_widgets: list[QLabel] = []
        for img in tutorial_imgs:
            img_widget = QLabel()
            img = img.scaledToHeight(min(100, img.height()), Qt.TransformationMode.SmoothTransformation)
            img_widget.setPixmap(img)
            img_widget.setStyleSheet("border: 1px solid #ccc;")
            img_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_widgets.append(img_widget)
        msg = QMessageBox(self)
        msg.setMaximumWidth(400)
        msg.setWindowTitle("校准血条颜色帮助")
        layout: QVBoxLayout = QVBoxLayout()
        layout.addWidget(QLabel("雨中冒险自动检测原理为检测血条颜色，有可能因为色差而失效，则需要使用校准步骤："))
        layout.addWidget(QLabel("1. 首先在设置界面调整\"校准血条颜色快捷键\""))
        layout.addWidget(QLabel("2. 开始一局单人游戏，在画面中有血条时按下之前设置的快捷键\n"
                                "画面定格并显示出按钮"))
        layout.addWidget(img_widgets[0])
        layout.addWidget(QLabel("3. 如果画面中有正常血条，则点击\"点我框选 正常颜色血条 的区域\"按钮\n"
                                "然后拖动鼠标框出血条中的纯色部分，点击保存按钮"))
        layout.addWidget(img_widgets[1])
        layout.addWidget(QLabel("4. 以相同的步骤对在雨里的血条也框选一次"))
        layout.addWidget(QLabel("5. 设置界面看到两个颜色显示已设置即可，重置按钮可以退回到程序内置的默认颜色"))
        layout.addWidget(img_widgets[2])

        msg.layout().addLayout(layout, 0, 0)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()


    def update_dayx_detect_enable(self, state):
        enabled = self.dayx_detect_enable_checkbox.isChecked()
        self.updater.dayx_detect_enabled = enabled
        info(f"DayX detect enabled: {enabled}")

    def update_in_rain_detect_enable(self, state):
        enabled = self.in_rain_detect_enable_checkbox.isChecked()
        self.updater.in_rain_detect_enabled = enabled
        info(f"In Rain detect enabled: {enabled}")


    def open_log_directory(self):
        log_dir = get_appdata_path("")
        os.startfile(log_dir)

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_SAVE_PATH):
                with open(SETTINGS_SAVE_PATH, "r") as f:
                    data: dict = yaml.safe_load(f)
                info(f"Loaded settings from {SETTINGS_SAVE_PATH}")
            else:
                data = {}
                warning(f"Settings file not found: {SETTINGS_SAVE_PATH}, using defaults")
            self.size_slider.setValue(data.get("size", 200))
            self.opacity_slider.setValue(data.get("opacity", 60))
            self.update_ui_state_signal.emit(UIState(
                x=data.get("x"),
                y=data.get("y"),
            ))
            self.day_input_setting_widget.set_setting(InputSetting.load_from_dict(data.get("day_input_setting")))
            self.in_rain_input_setting_widget.set_setting(InputSetting.load_from_dict(data.get("in_rain_input_setting")))
            self.screenshot_region_setting_widget.set_setting(InputSetting.load_from_dict(data.get("screenshot_region_input_setting")))
            self.forward_day_input_setting_widget.set_setting(InputSetting.load_from_dict(data.get("forward_day_input_setting")))
            self.back_day_input_setting_widget.set_setting(InputSetting.load_from_dict(data.get("back_day_input_setting")))
            self.align_to_detect_hp_color_input_widget.set_setting(InputSetting.load_from_dict(data.get("align_to_detect_hp_color_input_setting")))
            self.day1_detect_region = data.get("day1_detect_region", None)
            self.hp_bar_detect_region = data.get("hp_bar_detect_region", None)
            self.dayx_detect_enable_checkbox.setChecked(data.get("dayx_detect_enabled", True))
            self.in_rain_detect_enable_checkbox.setChecked(data.get("in_rain_detect_enabled", True))
            self.not_in_rain_hls = data.get("not_in_rain_hls", None)
            self.in_rain_hls = data.get("in_rain_hls", None)
            self.update_detect_regions()
            self.update_hp_color()
        except Exception as e:
            error(f"Failed to load settings: {e}")

    def save_settings(self):
        try:
            with open(SETTINGS_SAVE_PATH, "w") as f:
                yaml.safe_dump({
                    "size": self.size_slider.value(),
                    "opacity": self.opacity_slider.value(),
                    "x": self.overlay.x(),
                    "y": self.overlay.y(),
                    "day_input_setting": asdict(self.day_input_setting_widget.get_setting()),
                    "in_rain_input_setting": asdict(self.in_rain_input_setting_widget.get_setting()),
                    "screenshot_region_input_setting": asdict(self.screenshot_region_setting_widget.get_setting()),
                    "forward_day_input_setting": asdict(self.forward_day_input_setting_widget.get_setting()),
                    "back_day_input_setting": asdict(self.back_day_input_setting_widget.get_setting()),
                    "align_to_detect_hp_color_input_setting": asdict(self.align_to_detect_hp_color_input_widget.get_setting()),
                    "day1_detect_region": self.day1_detect_region,
                    "hp_bar_detect_region": self.hp_bar_detect_region,
                    "dayx_detect_enabled": self.dayx_detect_enable_checkbox.isChecked(),
                    "in_rain_detect_enabled": self.in_rain_detect_enable_checkbox.isChecked(),
                    "not_in_rain_hls": self.not_in_rain_hls,
                    "in_rain_hls": self.in_rain_hls,
                }, f)
        except Exception as e:
            error(f"Failed to save settings: {e}")

