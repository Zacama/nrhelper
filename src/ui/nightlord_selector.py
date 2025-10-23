from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout)

from src.logger import info


@dataclass
class NightlordSelection:
    """夜王选择结果"""
    nightlord: int  # 0-7


class NightlordSelectorDialog(QDialog):
    """
    夜王选择对话框
    用户选择夜王类型
    """

    # 夜王ID到名称的映射
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_nightlord = None

        self.setWindowTitle("选择夜王类型")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumSize(500, 400)

        # 主布局
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("请选择本局游戏的夜王类型")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(10)

        # 夜王选择网格（2行4列）
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        self.nightlord_buttons = {}
        for i in range(8):
            btn = QPushButton(self.NIGHTLORD_NAMES[i])
            btn.setMinimumHeight(60)
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
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            btn.clicked.connect(lambda checked, nightlord_id=i: self.on_nightlord_selected(nightlord_id))
            self.nightlord_buttons[i] = btn

            row = i // 4
            col = i % 4
            grid_layout.addWidget(btn, row, col)

        layout.addLayout(grid_layout)

        layout.addStretch()

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("取消")
        cancel_button.setMinimumWidth(100)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def on_nightlord_selected(self, nightlord_id: int):
        """用户选择了夜王"""
        self.selected_nightlord = nightlord_id
        nightlord_name = self.NIGHTLORD_NAMES[nightlord_id]

        info(f"User selected: Nightlord={nightlord_name} ({nightlord_id})")
        self.accept()

    def get_selection(self) -> NightlordSelection | None:
        """获取选择结果"""
        if self.selected_nightlord is not None:
            return NightlordSelection(self.selected_nightlord)
        return None
