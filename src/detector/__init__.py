from src.detector.rain_detector import RainDetector, RainDetectResult, RainDetectParam
from src.detector.day_detector import DayDetector, DayDetectResult, DayDetectParam
from src.detector.map_detector import MapDetector, MapDetectResult, MapDetectParam
from src.detector.hp_detector import HpDetector, HpDetectResult, HpDetectParam
from dataclasses import dataclass
from mss import mss


@dataclass
class DetectParam:
    day_detect_param: DayDetectParam = None
    rain_detect_param: RainDetectParam = None
    map_detect_param: MapDetectParam = None
    hp_detect_param: HpDetectParam = None

@dataclass
class DetectResult:
    day_detect_result: DayDetectResult = None
    rain_detect_result: RainDetectResult = None
    map_detect_result: MapDetectResult = None
    hp_detect_result: HpDetectResult = None


class DetectorManager:
    def __init__(self):
        self.rain_detector = RainDetector()
        self.day_detector = DayDetector()
        self.map_detector = MapDetector()
        self.hp_detector = HpDetector()

    def detect(self, params: DetectParam) -> DetectResult:
        result = DetectResult()
        with mss() as sct:
            result.day_detect_result = self.day_detector.detect(sct, params.day_detect_param)
            result.rain_detect_result = self.rain_detector.detect(sct, params.rain_detect_param)
            result.map_detect_result = self.map_detector.detect(sct, params.map_detect_param)
            result.hp_detect_result = self.hp_detector.detect(sct, params.hp_detect_param)
        return result
        