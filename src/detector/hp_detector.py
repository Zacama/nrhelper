import cv2
import numpy as np
from dataclasses import dataclass
from PIL import Image
import time
from PyQt6.QtGui import QPixmap
from mss.base import MSSBase

from src.config import Config
from src.logger import info, warning, error
from src.detector.utils import grab_region, resize_by_height_keep_aspect_ratio


@dataclass
class HpDetectParam:
    hpbar_region: tuple[int] | None = None

@dataclass
class HpDetectResult:
    hpbar_length: int | None = None


class HpDetector:
    def __init__(self):
        pass

    def detect(self, sct: MSSBase, params: HpDetectParam | None) -> HpDetectResult:
        if params is None or params.hpbar_region is None:
            return HpDetectResult()
        config = Config.get()
        ret = HpDetectResult()

        t = time.time()
        x, y, w, h = params.hpbar_region
        w = h * config.hpbar_region_aspect_ratio
        img = grab_region(sct, (x, y, w, h))
        img = resize_by_height_keep_aspect_ratio(img, config.hpbar_detect_std_height)
        hsv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HSV)

        # 截取中线的亮度
        mid_y = hsv.shape[0] // 2
        vals = hsv[mid_y, :, 2].astype(int)

        peak_num = 0
        start = config.hpbar_border_v_peak_start
        threshold = config.hpbar_border_v_peak_threshold
        interval = config.hpbar_border_v_peak_interval
        last_is_peak = False

        # 检测亮度快速提升的尖峰
        for i in range(start, len(vals)):
            cur_is_peak = False
            for j in range(0, interval):
                if vals[i] - vals[i - j] > threshold:
                    cur_is_peak = True
                    break   
            if cur_is_peak and not last_is_peak:
                peak_num += 1
                ret.hpbar_length = i
                if peak_num == 2:
                    break
        
        print(f"HpDetector: hpbar_length={ret.hpbar_length}, time={time.time() - t:.3f}s")
        return ret
    


