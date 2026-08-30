"""
demo/generate_test_video.py
----------------------------
Gercek video olmadan test edebilmek icin yapay bir video uretir:
  - Gri gradyan arka plan (kamera titremesi simulasyonu)
  - Birden fazla hareketli dikdortgen (araba / insan simulasyonu)
  - Farkli hiz, boyut, renk

Kullanim:
    python demo/generate_test_video.py
    -> demo/test_video.mp4 olusturur
"""

import cv2
import numpy as np
import os
import math
import random

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "test_video.mp4")
WIDTH, HEIGHT = 1280, 720
FPS           = 25
DURATION_SEC  = 30      # Saniye
TOTAL_FRAMES  = FPS * DURATION_SEC

# ─── Nesne Tanimlari ─────────────────────────────────────────────────────────

class FakeObject:
    """Yapay hareketli nesne."""

    def __init__(self, x, y, w, h, vx, vy, color, label=""):
        self.x     = float(x)
        self.y     = float(y)
        self.w     = w
        self.h     = h
        self.vx    = vx    # piksel/kare yatay hiz
        self.vy    = vy    # piksel/kare dikey hiz
        self.color = color
        self.label = label

    def update(self, width, height):
        self.x += self.vx
        self.y += self.vy

        # Kenara carpma -> yon degistir
        if self.x < 0 or self.x + self.w > width:
            self.vx *= -1
        if self.y < 0 or self.y + self.h > height:
            self.vy *= -1

        self.x = max(0, min(self.x, width  - self.w))
        self.y = max(0, min(self.y, height - self.h))

    def draw(self, frame):
        xi, yi = int(self.x), int(self.y)
        cv2.rectangle(frame, (xi, yi), (xi + self.w, yi + self.h), self.color, -1)
        cv2.rectangle(frame, (xi, yi), (xi + self.w, yi + self.h), (0, 0, 0), 1)
        if self.label:
            cv2.putText(frame, self.label, (xi + 2, yi - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)


def make_background(frame_idx: int) -> np.ndarray:
    """Hafif renk degisimi olan statik arka plan (yol/alan simulasyonu)."""
    bg = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # Gri zemin
    bg[:] = (55, 55, 55)

    # Yol seritleri
    for lane_y in [240, 480]:
        cv2.rectangle(bg, (0, lane_y - 4), (WIDTH, lane_y + 4), (80, 80, 80), -1)

    # Cizgili yol isaretleri
    for xi in range(0, WIDTH, 80):
        cv2.rectangle(bg, (xi, 350), (xi + 40, 360), (100, 100, 100), -1)

    # Hafif isik titremesi (sinus)
    flicker = int(math.sin(frame_idx * 0.05) * 5)
    bg = np.clip(bg.astype(np.int16) + flicker, 0, 255).astype(np.uint8)

    return bg


def main():
    random.seed(42)
    np.random.seed(42)

    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(OUTPUT_PATH, fourcc, FPS, (WIDTH, HEIGHT))

    # Hareketli nesneler
    objects = [
        # Arabalar (genis, hizli)
        FakeObject(100, 200, 90, 45, 4.5, 0.3,   (30,  80, 200), "Araba-1"),
        FakeObject(600, 420, 80, 40, -3.2, 0.5,  (200, 80,  30), "Araba-2"),
        FakeObject(900, 300, 100, 50, 5.0, -0.4, (50, 180,  50), "Araba-3"),
        FakeObject(200, 600, 85, 42, -4.0, -0.2, (180, 30, 180), "Araba-4"),

        # Insanlar (dar, yavas)
        FakeObject(300, 350, 25, 60, 1.2, 0.8,   (255, 200, 100), "Insan-1"),
        FakeObject(800, 500, 22, 55, -0.9, 1.0,  (100, 255, 200), "Insan-2"),
        FakeObject(500, 150, 20, 58,  1.5, -0.6, (200, 100, 255), "Insan-3"),

        # Yavas nesne (bisiklet)
        FakeObject(400, 300, 40, 30, 2.0, 0.2,   (255, 255, 100), "Bisiklet"),
    ]

    # Zaman zaman cerceve giren gecici nesne
    temp_obj = FakeObject(-120, 280, 90, 45, 6.0, 0.0, (100, 200, 255), "Hizli-Arac")

    print(f"[Demo] Video olusturuluyor -> {OUTPUT_PATH}")
    print(f"       Cozunurluk : {WIDTH}x{HEIGHT}  |  FPS : {FPS}  |  Sure : {DURATION_SEC}s")

    for fi in range(TOTAL_FRAMES):
        frame = make_background(fi)

        # Normal nesneleri guncelle + ciz
        for obj in objects:
            obj.update(WIDTH, HEIGHT)
            obj.draw(frame)

        # Gecici nesne (sadece ilk 8 saniyede)
        if fi < FPS * 8:
            temp_obj.update(WIDTH, HEIGHT)
            temp_obj.draw(frame)

        # Sahne bilgisi
        cv2.putText(frame, f"DEMO VIDEO - Kare: {fi}/{TOTAL_FRAMES}",
                    (10, HEIGHT - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (160, 160, 160), 1)

        writer.write(frame)

        if fi % (FPS * 5) == 0:
            print(f"  -> {fi // FPS}s / {DURATION_SEC}s")

    writer.release()
    print(f"\n[OK] Video hazir: {os.path.abspath(OUTPUT_PATH)}")
    print("   Simdi calistir:")
    print("   python main.py --source demo/test_video.mp4 --method mog2")


if __name__ == "__main__":
    main()
