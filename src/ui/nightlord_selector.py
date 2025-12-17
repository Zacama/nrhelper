from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QApplication, QDialog, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout)

from src.logger import info

NIGHTLORD_NAMES = {
    0: "三头野兽",
    1: "碎身巨鳄",
    2: "慧心虫",
    3: "征兆",
    4: "平衡律法的魔物",
    5: "暗中飞驰的猎人",
    6: "雾中裂缝",
    7: "黑夜化形者",
}

# 地形ID到名称的映射
EARTH_SHIFTING_NAMES = {
    0: "默认",
    1: "雪山",
    2: "火山",
    3: "腐败森林",
    5: "隐城",
}


@dataclass
class NightlordSelection:
    """夜王选择结果"""
    nightlord: int  # 0-7
    earth_shifting: int  # 0:默认, 1:雪山, 2:火山, 3:腐败森林, 5:隐城


class NightlordSelectorDialog(QDialog):
    """
    夜王选择对话框
    用户选择夜王类型和地形类型
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_nightlord = None
        self.selected_earth_shifting = None

        self.setWindowTitle("选择夜王和地形")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(600, 500)

        # 主布局
        layout = QVBoxLayout(self)

        # 夜王标题
        nightlord_title_label = QLabel("请选择本局游戏的夜王类型")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        nightlord_title_label.setFont(title_font)
        nightlord_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(nightlord_title_label)

        layout.addSpacing(10)

        # 夜王选择网格（2行4列）
        nightlord_grid_layout = QGridLayout()
        nightlord_grid_layout.setSpacing(10)

        self.nightlord_buttons = {}
        for i in range(8):
            btn = QPushButton(NIGHTLORD_NAMES[i])
            btn.setMinimumHeight(60)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 13px;
                    padding: 10px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border-color: #999;
                }
                QPushButton:checked {
                    background-color: #4a90e2;
                    border-color: #357abd;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, nightlord_id=i: self.on_nightlord_selected(nightlord_id))
            self.nightlord_buttons[i] = btn

            row = i // 4
            col = i % 4
            nightlord_grid_layout.addWidget(btn, row, col)

        layout.addLayout(nightlord_grid_layout)

        layout.addSpacing(20)

        # 地形标题
        earth_shifting_title_label = QLabel("请选择本局游戏的地形")
        earth_shifting_title_label.setFont(title_font)
        earth_shifting_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(earth_shifting_title_label)

        layout.addSpacing(10)

        # 地形选择网格（1行5列）
        earth_shifting_layout = QHBoxLayout()
        earth_shifting_layout.addStretch()

        self.earth_shifting_buttons = {}
        for es_id in [0, 1, 2, 3, 5]:
            btn = QPushButton(EARTH_SHIFTING_NAMES[es_id])
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(100)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 13px;
                    padding: 10px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border-color: #999;
                }
                QPushButton:checked {
                    background-color: #4a90e2;
                    border-color: #357abd;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, earth_id=es_id: self.on_earth_shifting_selected(earth_id))
            self.earth_shifting_buttons[es_id] = btn
            earth_shifting_layout.addWidget(btn)

        earth_shifting_layout.addStretch()
        layout.addLayout(earth_shifting_layout)

        layout.addStretch()

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("取消")
        cancel_button.setMinimumWidth(100)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        confirm_button = QPushButton("确定")
        confirm_button.setMinimumWidth(100)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        confirm_button.clicked.connect(self.on_confirm)
        button_layout.addWidget(confirm_button)

        layout.addLayout(button_layout)

        # 设置窗口位置到屏幕左半边居中
        self._position_in_left_half()

    def _position_in_left_half(self):
        """将窗口定位到屏幕左半边的中心"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()

            # 计算左半边的中心位置
            # 左半边的中心X坐标为屏幕宽度的1/4
            left_half_center_x = screen_width // 4

            # 窗口的宽度和高度
            dialog_width = self.width()
            dialog_height = self.height()

            # 计算窗口左上角的位置，使窗口中心对齐到左半边中心
            x = left_half_center_x - dialog_width // 2
            y = (screen_height - dialog_height) // 2

            self.move(x, y)

    def on_nightlord_selected(self, nightlord_id: int):
        """用户选择了夜王"""
        # 取消其他夜王按钮的选中状态
        for nid, btn in self.nightlord_buttons.items():
            if nid != nightlord_id:
                btn.setChecked(False)

        self.selected_nightlord = nightlord_id
        nightlord_name = NIGHTLORD_NAMES[nightlord_id]
        info(f"User selected nightlord: {nightlord_name} ({nightlord_id})")

    def on_earth_shifting_selected(self, earth_shifting_id: int):
        """用户选择了地形"""
        # 取消其他地形按钮的选中状态
        for es_id, btn in self.earth_shifting_buttons.items():
            if es_id != earth_shifting_id:
                btn.setChecked(False)

        self.selected_earth_shifting = earth_shifting_id
        earth_shifting_name = EARTH_SHIFTING_NAMES[earth_shifting_id]
        info(f"User selected earth shifting: {earth_shifting_name} ({earth_shifting_id})")

    def on_confirm(self):
        """用户点击确定按钮"""
        if self.selected_nightlord is None:
            QMessageBox.warning(self, "未选择夜王", "请先选择夜王类型！")
            return

        if self.selected_earth_shifting is None:
            QMessageBox.warning(self, "未选择地形", "请先选择地形类型！")
            return

        info(f"User confirmed: Nightlord={self.selected_nightlord}, EarthShifting={self.selected_earth_shifting}")
        self.accept()

    def get_selection(self) -> NightlordSelection | None:
        """获取选择结果"""
        if self.selected_nightlord is not None and self.selected_earth_shifting is not None:
            return NightlordSelection(self.selected_nightlord, self.selected_earth_shifting)
        return None
