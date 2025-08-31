import cv2
import numpy as np
from dataclasses import dataclass
from PIL import Image
import time
from mss import mss
from PyQt6.QtGui import QPixmap

from src.config import Config
from src.logger import info, warning, error
from src.common import get_asset_path


def hls_to_rgb(hls: tuple[int, int, int]) -> tuple[int, int, int]:
    img = np.uint8([[hls]]) 
    img = cv2.cvtColor(img, cv2.COLOR_HLS2RGB)
    return tuple(int(c) for c in img[0][0]) 
    

def get_size_by_height(size: tuple[int], target_height: int) -> tuple[int]:
    width, height = size
    aspect_ratio = width / height
    target_width = int(target_height * aspect_ratio)
    return (target_width, target_height)

def resize_by_height_keep_aspect_ratio(image: Image.Image, target_height: int) -> Image.Image:
    target_size = get_size_by_height(image.size, target_height)
    return image.resize(target_size, Image.Resampling.LANCZOS)


def get_image_mask(image: Image.Image) -> np.ndarray:
    config = Config.get()
    image_np = np.array(image)

    # 1. 转换为 HSV 颜色空间
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    # 2. 定义白色范围
    lower_white = np.array(config.mask_lower_white)
    upper_white = np.array(config.mask_upper_white)

    # 3. 创建掩膜 (mask)
    mask = cv2.inRange(hsv, lower_white, upper_white)

    # 4. 可选：形态学操作（去除噪声，连接区域）
    # kernel = np.ones((3,3), np.uint8)
    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) # 开运算去除小白点噪声
    # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # 闭运算连接断裂区域

    cv2.imwrite(f"sandbox/debug_hsv_mask.png", mask)
    return mask

def match_mask(image: np.ndarray, template: np.ndarray) -> float:
    t = time.time()
    scale_range = np.linspace(*Config.get().scale_range)
    score = float('inf')
    for scale in scale_range:
        w, h = template.shape[::-1]
        resized_template = cv2.resize(template, (int(w * scale), int(h * scale)))
        if resized_template.shape[0] > image.shape[0] or resized_template.shape[1] > image.shape[1]:
            continue
        res = cv2.matchTemplate(image, resized_template, cv2.TM_SQDIFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        score = min(score, min_val)
    # print("match mask score: ", score)
    # print("match mask time: ", time.time() - t)
    return score


@dataclass
class DetectResult:
    start_day1: bool = False
    start_day2: bool = False
    start_day3: bool = False
    
    score_day1: float = None
    score_day2: float = None
    score_day3: float = None
    
    is_in_rain: bool | None = None
    in_rain_area_ratio: float = None
    not_in_rain_area_ratio: float = None


class Detector:
    def __init__(self):
        config = Config.get()
        day1_image = Image.open(get_asset_path("day_template/1.png")).convert("RGB")
        day2_image = Image.open(get_asset_path("day_template/2.png")).convert("RGB")
        day3_image = Image.open(get_asset_path("day_template/3.png")).convert("RGB")
        self.day1_mask = get_image_mask(resize_by_height_keep_aspect_ratio(day1_image, config.template_standard_size[1]))
        self.day2_mask = get_image_mask(resize_by_height_keep_aspect_ratio(day2_image, config.template_standard_size[1]))
        self.day3_mask = get_image_mask(resize_by_height_keep_aspect_ratio(day3_image, config.template_standard_size[1]))
        self.day2_w_ratio = self.day2_mask.shape[1] / self.day1_mask.shape[1]
        self.day3_w_ratio = self.day3_mask.shape[1] / self.day1_mask.shape[1]

    def detect_dayx(self, sct, day1_region: tuple[int]) -> tuple[bool, float]:
        try:
            config = Config.get()
            t = time.time()
            x, y, w, h = day1_region
            cx, cy = x + w // 2, y + h // 2
            day2_w = int(w * self.day2_w_ratio)
            day2_region = (cx - day2_w // 2, cy - h // 2, day2_w, h)
            day3_w = int(w * self.day3_w_ratio)
            day3_region = (cx - day3_w // 2, cy - h // 2, day3_w, h)
            sc = sct.grab({
                "left":     day3_region[0],
                "top":      day3_region[1],
                "width":    day3_region[2],
                "height":   day3_region[3]
            })
            sc = Image.frombytes("RGB", sc.size, sc.bgra, "raw", "BGRX")
            def match_region(region: tuple[int], template_mask: np.ndarray) -> float:
                region = (
                    region[0] - day3_region[0], 
                    region[1] - day3_region[1], 
                    region[0] - day3_region[0] + region[2], 
                    region[1] - day3_region[1] + region[3]
                )
                img = sc.crop(region)
                img = resize_by_height_keep_aspect_ratio(img, config.template_standard_size[1])
                img_mask = get_image_mask(img)
                return match_mask(img_mask, template_mask)
            score_day1 = match_region(day1_region, self.day1_mask)
            score_day2 = match_region(day2_region, self.day2_mask)
            score_day3 = match_region(day3_region, self.day3_mask)
            # print("detect dayx time: ", time.time() - t)
            # print(f"{score_day1:.2f}, {score_day2:.2f}, {score_day3:.2f}")
            return score_day1, score_day2, score_day3
        except Exception as e:
            error(f"Detect dayx error")
            return float('inf'), float('inf'), float('inf')
        
    def detect_in_rain(
        self, sct, 
        hp_bar_region: tuple[int],
        in_rain_hls: tuple[int] | None,
        not_in_rain_hls: tuple[int] | None,
    ) -> tuple[float, float]:
        try:
            t = time.time()
            config = Config.get()
            screenshot = sct.grab({
                "left": hp_bar_region[0],
                "top": hp_bar_region[1],
                "width": hp_bar_region[2],
                "height": hp_bar_region[3]
            })
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            hls = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HLS)
            # print(hls[hls.shape[0]//2, hls.shape[1]//2])

            def calc_pixel_num(hls: np.ndarray, c1: list[int], c2: list[int]) -> int:
                lower = np.array([min(c1[i], c2[i]) for i in range(3)])
                upper = np.array([max(c1[i], c2[i]) for i in range(3)])
                tolerance = np.array([config.h_tolerance, config.l_tolerance, config.s_tolerance])
                lower = lower - tolerance
                upper = upper + tolerance
                mask = cv2.inRange(hls, lower, upper)
                return np.sum(mask > 0)
                
            total_pixel_num = hls.shape[0] * hls.shape[1]

            lower_hls_not_in_rain = not_in_rain_hls if not_in_rain_hls is not None else config.lower_hls_not_in_rain
            upper_hls_not_in_rain = not_in_rain_hls if not_in_rain_hls is not None else config.upper_hls_not_in_rain
            lower_hls_in_rain = in_rain_hls if in_rain_hls is not None else config.lower_hls_in_rain
            upper_hls_in_rain = in_rain_hls if in_rain_hls is not None else config.upper_hls_in_rain

            not_in_rain_ratio = calc_pixel_num(hls, lower_hls_not_in_rain, upper_hls_not_in_rain) / total_pixel_num
            in_rain_ratio     = calc_pixel_num(hls, lower_hls_in_rain,     upper_hls_in_rain)     / total_pixel_num

            # print(f"{not_in_rain_ratio:.2f}, {in_rain_ratio:.2f}")
            # print("detect in rain time: ", time.time() - t)
            return not_in_rain_ratio, in_rain_ratio
        except Exception as e:
            error(f"Detect in rain error")
            return 0.0, 0.0

    def detect(
        self, 
        day1_region: tuple[int] | None, 
        hp_bar_region: tuple[int] | None,
        in_rain_hls: tuple[int] | None,
        not_in_rain_hls: tuple[int] | None,
    ) -> DetectResult:
        ret = DetectResult()
        config = Config.get()
        with mss() as sct:
            if day1_region is not None:
                score_day1, score_day2, score_day3 = self.detect_dayx(sct, day1_region)
                ret.score_day1 = score_day1
                ret.score_day2 = score_day2
                ret.score_day3 = score_day3
                if score_day1 < config.dayx_score_threshold: ret.start_day1 = True
                if score_day2 < config.dayx_score_threshold: ret.start_day2 = True
                if score_day3 < config.dayx_score_threshold: ret.start_day3 = True
            if hp_bar_region is not None:
                not_in_rain_ratio, in_rain_ratio = self.detect_in_rain(sct, hp_bar_region, in_rain_hls, not_in_rain_hls)
                ret.not_in_rain_area_ratio = not_in_rain_ratio
                ret.in_rain_area_ratio = in_rain_ratio
                min_ratio = config.hp_color_min_area_ratio
                max_ratio = config.hp_color_max_area_ratio
                if in_rain_ratio >= max_ratio and not_in_rain_ratio <= min_ratio:
                    ret.is_in_rain = True
                elif not_in_rain_ratio >= max_ratio and in_rain_ratio <= min_ratio:
                    ret.is_in_rain = False
        return ret

    @staticmethod
    def get_to_detect_hp_hls(screenshot: QPixmap, region: tuple[int]) -> tuple[int]:
        img = Image.fromqpixmap(screenshot)
        hls = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2HLS)
        hp_bar_region = hls[region[1]:region[1]+region[3], region[0]:region[0]+region[2]]
        hist = cv2.calcHist([hp_bar_region], [0, 1, 2], None, [180, 256, 256], [0, 180, 0, 256, 0, 256])
        max_val = np.unravel_index(np.argmax(hist), hist.shape)
        return [int(x) for x in max_val]


if __name__ == "__main__":
    detector = Detector()
    while True:
        result = detector.detect((851, 589, 222, 60), None)
        result = detector.detect(None, (296, 157, 97, 7))
        time.sleep(0.2)
