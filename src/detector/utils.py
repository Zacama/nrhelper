import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from mss.base import MSSBase

from src.common import get_data_path
from src.logger import warning


def hls_to_rgb(hls: tuple[int, int, int]) -> tuple[int, int, int]:
    img = np.uint8([[hls]]) 
    img = cv2.cvtColor(img, cv2.COLOR_HLS2RGB)
    return tuple(int(c) for c in img[0][0]) 
    
def get_size_by_height(size: tuple[int], target_height: int) -> tuple[int]:
    width, height = size
    aspect_ratio = width / height
    target_width = int(target_height * aspect_ratio)
    return (target_width, target_height)

def get_size_by_width(size: tuple[int], target_width: int) -> tuple[int]:
    width, height = size
    aspect_ratio = width / height
    target_height = int(target_width / aspect_ratio)
    return (target_width, target_height)

def resize_by_height_keep_aspect_ratio(image: Image.Image, target_height: int) -> Image.Image:
    target_size = get_size_by_height(image.size, target_height)
    return image.resize(target_size, Image.Resampling.LANCZOS)

def resize_by_width_keep_aspect_ratio(image: Image.Image, target_width: int) -> Image.Image:
    target_size = get_size_by_width(image.size, target_width)
    return image.resize(target_size, Image.Resampling.LANCZOS)

def resize_by_scale(image: Image.Image, scale: float) -> Image.Image:
    target_size = (int(image.size[0] * scale), int(image.size[1] * scale))
    return image.resize(target_size, Image.Resampling.LANCZOS)

def paste_cv2(img1: np.ndarray, img2: np.ndarray, pos: tuple[int, int]):
    x, y = pos
    h, w = img2.shape[0], img2.shape[1]
    img1[y:y+h, x:x+w] = img2

def grab_region(sct: MSSBase, region: tuple[int]) -> Image.Image:

    x, y, w, h = region
    
    # 首先检查坐标是否已经是绝对坐标（包含屏幕偏移）
    # 如果坐标在任何屏幕的范围内，直接使用
    for monitor in sct.monitors[1:]:  # 跳过 monitors[0] (所有屏幕的汇总)
        if (monitor["left"] <= x < monitor["left"] + monitor["width"] and
                monitor["top"] <= y < monitor["top"] + monitor["height"]):
            # 坐标已经是绝对坐标，直接截图
            screenshot = sct.grab({
                "left": x,
                "top": y,
                "width": w,
                "height": h
            })
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra,
                                  "raw", "BGRX")
            return img
    
    # 如果没有找到匹配的屏幕，可能是相对坐标，尝试转换为绝对坐标
    # 默认使用主屏幕偏移（保持向后兼容）
    main_screen = sct.monitors[1]
    main_screen_offset = (main_screen["left"], main_screen["top"])
    absolute_region = (
        x + main_screen_offset[0],
        y + main_screen_offset[1],
        w,
        h,
    )
    
    # 验证转换后的坐标是否有效
    abs_x, abs_y, abs_w, abs_h = absolute_region
    for monitor in sct.monitors[1:]:
        if (monitor["left"] <= abs_x < monitor["left"] + monitor["width"] and
                monitor["top"] <= abs_y < monitor["top"] + monitor["height"]):
            screenshot = sct.grab({
                "left": abs_x,
                "top": abs_y,
                "width": abs_w,
                "height": abs_h
            })
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra,
                                  "raw", "BGRX")
            return img
    
    # 如果仍然找不到有效屏幕，使用原始逻辑作为最后的fallback
    warning(f"Region {region} could not be mapped to any screen. "
            f"Using fallback method.")
    screenshot = sct.grab({
        "left": abs_x,
        "top": abs_y,
        "width": abs_w,
        "height": abs_h
    })
    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    return img


DEFAULT_FONT_PATH = get_data_path("fonts/SourceHanSansSC-Normal.otf")

font_cache = {}


def get_font(size: int, path: str=DEFAULT_FONT_PATH) -> ImageFont.FreeTypeFont:
    key = f"{path}-{size}"
    if key not in font_cache:
        font_cache[key] = ImageFont.truetype(path, size)
    return font_cache[key]


def get_text_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    return font.getbbox(text)[2:4]


def draw_icon(img: Image.Image, pos: tuple[int, int], icon: Image.Image, size: tuple[int, int] | None = None):
    if size is None:
        size = icon.size
    icon = icon.resize(size, resample=Image.Resampling.BICUBIC)
    img.alpha_composite(icon, (pos[0] - size[0] // 2, pos[1] - size[1] // 2))


def draw_text(img: Image.Image, pos: tuple[int, int], text: str, size: int,
              color: tuple[int, int, int, int],
              outline_width: int = 0,
              outline_color: tuple[int, int, int, int] = (0, 0, 0, 255),
              align='c'):
    assert align in ('lb', 'c', 'lt')
    if text is None: text = "null"
    draw = ImageDraw.Draw(img)
    font = get_font(size)
    text_size = get_text_size(font, text)
    if align == 'lb':
        pos = (pos[0] + text_size[0] // 2, pos[1] - text_size[1] // 2)
    elif align == 'lt':
        pos = (pos[0] + text_size[0] // 2, pos[1] + text_size[1] // 2)
    if outline_width > 0:
        for dx in range(-outline_width, outline_width+1):
            for dy in range(-outline_width, outline_width+1):
                if dx*dx + dy*dy <= outline_width * outline_width:
                    draw.text((pos[0] - text_size[0] // 2 + dx,
                              pos[1] - text_size[1] // 2 + dy), text,
                              font=font, fill=outline_color)
    draw.text((pos[0] - text_size[0] // 2, pos[1] - text_size[1] // 2),
              text, font=font, fill=color)
