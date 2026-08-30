"""
tracker/object_detector.py
---------------------------
Hareket maskesinden konturları bulur, filtreler ve
bounding box listesi döndürür.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List
from utils import config as cfg


@dataclass
class Detection:
    """Tek bir tespit edilen nesnenin ham verisi."""
    x: int          # Bounding box sol üst X
    y: int          # Bounding box sol üst Y
    w: int          # Genişlik
    h: int          # Yükseklik
    cx: int         # Merkez X
    cy: int         # Merkez Y
    area: float     # Kontur alanı (piksel²)


class ObjectDetector:
    """
    İkili maskeden nesne tespiti yapar.

    Adımlar:
      1. Konturları bul (RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
      2. Alan filtresi (MIN / MAX)
      3. En/Boy oranı filtresi
      4. Detection listesi döndür
    """

    def __init__(self,
                 min_area: int  = cfg.MIN_CONTOUR_AREA,
                 max_area: int  = cfg.MAX_CONTOUR_AREA,
                 min_ar: float  = cfg.MIN_ASPECT_RATIO,
                 max_ar: float  = cfg.MAX_ASPECT_RATIO):
        self.min_area = min_area
        self.max_area = max_area
        self.min_ar   = min_ar
        self.max_ar   = max_ar

    def detect(self, mask: np.ndarray) -> List[Detection]:
        """
        Maskeyi alır, Detection listesi döndürür.
        """
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        detections: List[Detection] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)

            # Alan filtresi
            if not (self.min_area <= area <= self.max_area):
                continue

            x, y, w, h = cv2.boundingRect(cnt)

            # En/boy oranı filtresi
            if h == 0:
                continue
            ar = w / h
            if not (self.min_ar <= ar <= self.max_ar):
                continue

            cx = x + w // 2
            cy = y + h // 2

            detections.append(Detection(x, y, w, h, cx, cy, area))

        # Büyükten küçüğe sırala
        detections.sort(key=lambda d: d.area, reverse=True)
        return detections
