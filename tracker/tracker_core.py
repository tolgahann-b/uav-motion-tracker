"""
tracker/tracker_core.py
------------------------
Centroid Tracking algoritması:
  • Her tespit edilen nesneye kalıcı bir ID atar
  • Kareler arası mesafe karşılaştırmasıyla nesne eşleştirir
  • Belirli sayıda kayıptan sonra nesneyi siler
  • Hız (piksel/kare) hesaplar
"""

import numpy as np
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from tracker.object_detector import Detection
from utils import config as cfg


@dataclass
class TrackedObject:
    """İzlenen bir nesnenin tam durumu."""
    obj_id:     int
    cx:         int
    cy:         int
    x:          int
    y:          int
    w:          int
    h:          int
    area:       float
    speed:      float   = 0.0
    disappeared: int    = 0
    history:    list    = field(default_factory=list)   # son N merkez noktası


class CentroidTracker:
    """
    Basit ama etkili centroid tabanlı çok-nesne takipçi.

    Parameters
    ----------
    max_disappeared : Nesnenin silinmeden önce kaybolabileceği maksimum kare sayısı
    max_distance    : İki nesnenin eşleşebileceği maksimum piksel mesafesi
    history_len     : Hız hesabı için tutulan geçmiş uzunluğu
    """

    def __init__(self,
                 max_disappeared: int = cfg.MAX_DISAPPEARED,
                 max_distance:    int = cfg.MAX_DISTANCE,
                 history_len:     int = 8):
        self.next_id         = 0
        self.max_disappeared = max_disappeared
        self.max_distance    = max_distance
        self.history_len     = history_len
        self.objects: OrderedDict[int, TrackedObject] = OrderedDict()

    # ── Yardımcı ────────────────────────────────────────────────────────────

    def _euclidean(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def _calc_speed(self, obj: TrackedObject) -> float:
        """Geçmiş noktalar üzerinden ortalama hız hesapla (px/kare)."""
        if len(obj.history) < 2:
            return 0.0
        pts = np.array(obj.history[-min(self.history_len, len(obj.history)):])
        dists = np.sqrt(np.sum(np.diff(pts, axis=0) ** 2, axis=1))
        return float(np.mean(dists))

    def _register(self, det: Detection):
        obj = TrackedObject(
            obj_id=self.next_id,
            cx=det.cx, cy=det.cy,
            x=det.x,   y=det.y,
            w=det.w,   h=det.h,
            area=det.area,
            history=[(det.cx, det.cy)]
        )
        self.objects[self.next_id] = obj
        self.next_id += 1

    def _deregister(self, obj_id: int):
        del self.objects[obj_id]

    # ── Ana Güncelleme ──────────────────────────────────────────────────────

    def update(self, detections: List[Detection]) -> Dict[int, TrackedObject]:
        """
        Yeni karedeki tespitleri alır, nesne sözlüğünü günceller.

        Returns
        -------
        Aktif izlenen nesneler {id: TrackedObject}
        """
        # Tespit yoksa tüm nesnelerin kaybolma sayacını artır
        if not detections:
            for obj_id in list(self.objects.keys()):
                self.objects[obj_id].disappeared += 1
                if self.objects[obj_id].disappeared > self.max_disappeared:
                    self._deregister(obj_id)
            return self.objects

        # İlk kare — hepsini kaydet
        if not self.objects:
            for det in detections:
                self._register(det)
            return self.objects

        # Mevcut centroidler
        obj_ids      = list(self.objects.keys())
        obj_centroids = [(self.objects[i].cx, self.objects[i].cy) for i in obj_ids]
        det_centroids = [(d.cx, d.cy) for d in detections]

        # Mesafe matrisi [mevcut_nesne x yeni_tespit]
        dist_matrix = np.array([
            [self._euclidean(oc, dc) for dc in det_centroids]
            for oc in obj_centroids
        ])

        # Her satırın minimum değerine göre sırala (en yakın eşleştirme)
        rows = dist_matrix.min(axis=1).argsort()
        cols = dist_matrix.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
            if dist_matrix[row, col] > self.max_distance:
                continue

            obj_id = obj_ids[row]
            det    = detections[col]
            obj    = self.objects[obj_id]

            # Güncelle
            obj.cx          = det.cx
            obj.cy          = det.cy
            obj.x, obj.y    = det.x, det.y
            obj.w, obj.h    = det.w, det.h
            obj.area        = det.area
            obj.disappeared = 0
            obj.history.append((det.cx, det.cy))
            if len(obj.history) > self.history_len:
                obj.history.pop(0)
            obj.speed = self._calc_speed(obj)

            used_rows.add(row)
            used_cols.add(col)

        # Eşleşmeyen mevcut nesneler — kaybolma sayacı artır
        unused_rows = set(range(len(obj_ids))) - used_rows
        for row in unused_rows:
            obj_id = obj_ids[row]
            self.objects[obj_id].disappeared += 1
            if self.objects[obj_id].disappeared > self.max_disappeared:
                self._deregister(obj_id)

        # Eşleşmeyen yeni tespitler — yeni nesne olarak kaydet
        unused_cols = set(range(len(detections))) - used_cols
        for col in unused_cols:
            self._register(detections[col])

        return self.objects

    def reset(self):
        """Tüm izleme geçmişini sıfırla."""
        self.objects.clear()
        self.next_id = 0
