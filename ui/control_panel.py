"""
ui/control_panel.py
--------------------
OpenCV Trackbar tabanlı canlı kontrol paneli.
Parametre değişiklikleri BackgroundSubtractor ve ObjectDetector'a
doğrudan yansır — yeniden başlatma gerekmez.
"""

import cv2
import numpy as np
from utils import config as cfg

# Pencere adı
WIN = cfg.CONTROL_WINDOW_NAME


def _nothing(_):
    """Trackbar callback — boş."""
    pass


class ControlPanel:
    """
    Trackbar tabanlı parametre kontrol paneli.

    Kullanım:
        panel = ControlPanel()
        panel.create()
        ...
        params = panel.get_params()
        subtractor.blur_k      = params["blur_k"]
        detector.min_area      = params["min_area"]
        ...
    """

    TRACKBARS = [
        # (etiket, min, max, başlangıç)
        ("Blur Kernel (tek sayi)",    1, 51, cfg.BLUR_KERNEL_SIZE),
        ("Morph Kernel",              1, 31, cfg.MORPH_KERNEL_SIZE),
        ("Dilate Iter",               0, 10, cfg.DILATE_ITERATIONS),
        ("Erode Iter",                0, 10, cfg.ERODE_ITERATIONS),
        ("Binary Threshold",          0, 255, cfg.BINARY_THRESHOLD),
        ("Min Area (x100)",           1, 200, cfg.MIN_CONTOUR_AREA // 100),
        ("Max Area (x1000)",          1, 200, cfg.MAX_CONTOUR_AREA // 1000),
        ("MOG2 Var Threshold",        1, 100, cfg.MOG2_VAR_THRESHOLD),
        ("Hiz Esigi (px/f)",          1, 100, cfg.HIGH_SPEED_THRESHOLD),
        ("Max Disappear (kare)",      1, 100, cfg.MAX_DISAPPEARED),
    ]

    def __init__(self):
        self._created = False

    def create(self):
        """Kontrol penceresi ve trackbar'ları oluştur."""
        # Siyah canvas — pencere boyutlandırma için
        canvas = np.zeros((10, 400, 3), dtype=np.uint8)
        cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WIN, 400, len(self.TRACKBARS) * 40 + 20)
        cv2.imshow(WIN, canvas)

        for label, mn, mx, init in self.TRACKBARS:
            cv2.createTrackbar(label, WIN, init, mx, _nothing)
            # Alt sınırı koru (OpenCV trackbar min=0'dan başlar, istediğimiz min ≥ 1)
            cv2.setTrackbarMin(label, WIN, mn)

        self._created = True

    def get_params(self) -> dict:
        """Mevcut trackbar değerlerini dict olarak döndür."""
        if not self._created:
            return {}

        def tb(label):
            return cv2.getTrackbarPos(label, WIN)

        blur_k = tb("Blur Kernel (tek sayi)")
        blur_k = blur_k if blur_k % 2 == 1 else blur_k + 1  # tek sayıya zorla

        return {
            "blur_k":         blur_k,
            "morph_k":        tb("Morph Kernel"),
            "dilate_iter":    tb("Dilate Iter"),
            "erode_iter":     tb("Erode Iter"),
            "threshold":      tb("Binary Threshold"),
            "min_area":       tb("Min Area (x100)") * 100,
            "max_area":       tb("Max Area (x1000)") * 1000,
            "mog2_var_thr":   tb("MOG2 Var Threshold"),
            "speed_thr":      tb("Hiz Esigi (px/f)"),
            "max_disappeared": tb("Max Disappear (kare)"),
        }

    def is_open(self) -> bool:
        return self._created

    def destroy(self):
        if self._created:
            cv2.destroyWindow(WIN)
            self._created = False
