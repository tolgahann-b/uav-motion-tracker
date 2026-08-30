"""
utils/fps_counter.py
---------------------
Kayan ortalama (sliding window) FPS hesaplayıcı.
"""

import time
from collections import deque


class FPSCounter:
    """
    Son `window` kareyi kullanarak gerçek zamanlı FPS hesaplar.
    Ani değişimlerde daha kararlı sonuç verir.
    """

    def __init__(self, window: int = 30):
        self._window  = window
        self._times: deque = deque(maxlen=window)
        self._start   = time.perf_counter()
        self._fps     = 0.0

    def tick(self) -> float:
        """Her kare işlendikten sonra çağır. Anlık FPS'i döndürür."""
        now = time.perf_counter()
        self._times.append(now)

        if len(self._times) >= 2:
            elapsed = self._times[-1] - self._times[0]
            self._fps = (len(self._times) - 1) / elapsed if elapsed > 0 else 0.0

        return self._fps

    @property
    def fps(self) -> float:
        return round(self._fps, 1)

    def reset(self):
        self._times.clear()
        self._start = time.perf_counter()
        self._fps   = 0.0
