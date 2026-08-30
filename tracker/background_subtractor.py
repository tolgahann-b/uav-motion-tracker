"""
tracker/background_subtractor.py
----------------------------------
İki arkaplan çıkarma stratejisini tek arayüzde sunar:

  1. MOG2  — cv2.createBackgroundSubtractorMOG2
     • Drone videosu, değişen ışık koşulları, dış mekan
     • Adaptif öğrenme oranı

  2. absdiff — İlk N kare ortalamasına göre fark
     • Sabit kamera, iç mekan, ışık değişimi az ise
     • Çok hızlı ve basit
"""

import cv2
import numpy as np
from utils import config as cfg


class BackgroundSubtractor:
    """
    Tek arayüz, iki mod.

    Parameters
    ----------
    method : "mog2" | "absdiff"
    """

    def __init__(self, method: str = cfg.DEFAULT_METHOD):
        self.method        = method.lower()
        self._mog2         = None
        self._bg_frame     = None         # absdiff referans karesi
        self._frame_count  = 0

        # Canlı ayarlanabilir parametreler (trackbar ile güncellenir)
        self.blur_k        = cfg.BLUR_KERNEL_SIZE
        self.morph_k       = cfg.MORPH_KERNEL_SIZE
        self.dilate_iter   = cfg.DILATE_ITERATIONS
        self.erode_iter    = cfg.ERODE_ITERATIONS
        self.threshold     = cfg.BINARY_THRESHOLD
        self.learning_rate = cfg.MOG2_LEARNING_RATE

        self._init_mog2()

    # ── Başlatma ────────────────────────────────────────────────────────────

    def _init_mog2(self):
        self._mog2 = cv2.createBackgroundSubtractorMOG2(
            history=cfg.MOG2_HISTORY,
            varThreshold=cfg.MOG2_VAR_THRESHOLD,
            detectShadows=cfg.MOG2_DETECT_SHADOWS
        )

    def reset(self):
        """Arkaplan modelini sıfırla (R tuşu)."""
        self._init_mog2()
        self._bg_frame    = None
        self._frame_count = 0

    def switch_method(self, method: str):
        """MOG2 ↔ absdiff geçiş."""
        self.method = method.lower()
        self.reset()

    # ── Ön-İşleme ────────────────────────────────────────────────────────────

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Gri + Gaussian blur uygula. blur_k tek sayı olmalı."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        k    = self.blur_k if self.blur_k % 2 == 1 else self.blur_k + 1
        return cv2.GaussianBlur(gray, (k, k), 0)

    def _postprocess(self, mask: np.ndarray) -> np.ndarray:
        """Binary eşik + morfoloji ile gürültüyü temizle."""
        _, binary = cv2.threshold(mask, self.threshold, 255, cv2.THRESH_BINARY)

        mk = self.morph_k if self.morph_k % 2 == 1 else self.morph_k + 1
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (mk, mk)
        )

        # Aşındır → küçük gürültüyü sil
        cleaned = cv2.erode(binary, kernel, iterations=self.erode_iter)
        # Genişlet → nesneleri doldur
        cleaned = cv2.dilate(cleaned, kernel, iterations=self.dilate_iter)
        return cleaned

    # ── Ana Çıkarma ──────────────────────────────────────────────────────────

    def apply(self, frame: np.ndarray) -> np.ndarray:
        """
        Kare uygular, ikili hareket maskesi döndürür (0/255).
        """
        self._frame_count += 1
        processed = self._preprocess(frame)

        if self.method == "mog2":
            raw_mask = self._apply_mog2(processed)
        else:
            raw_mask = self._apply_absdiff(processed)

        return self._postprocess(raw_mask)

    def _apply_mog2(self, gray: np.ndarray) -> np.ndarray:
        lr = self.learning_rate
        mask = self._mog2.apply(gray, learningRate=lr)
        # Gölge pikselleri (127) beyaza çevir
        mask[mask == 127] = 0
        return mask

    def _apply_absdiff(self, gray: np.ndarray) -> np.ndarray:
        """
        İlk 30 kareyi arkaplan ortalaması olarak kullanır.
        Sonraki karelerde bu referanstan farkı alır.
        """
        WARMUP = 30

        if self._frame_count <= WARMUP:
            # Isınma süresi — arkaplan kümüle et
            if self._bg_frame is None:
                self._bg_frame = gray.astype(np.float32)
            else:
                cv2.accumulateWeighted(gray, self._bg_frame, 0.5)
            # Isınma sırasında boş maske döndür
            return np.zeros_like(gray)

        # Referans kareden fark al
        ref   = cv2.convertScaleAbs(self._bg_frame)
        diff  = cv2.absdiff(gray, ref)

        # Yavaş öğrenme ile referansı güncelle (hareketleri izleme!)
        cv2.accumulateWeighted(gray, self._bg_frame, 0.002)

        return diff
