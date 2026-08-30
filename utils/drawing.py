"""
utils/drawing.py
----------------
OpenCV çizim yardımcıları:
  - Bounding box (köşe vurgulu, renkli)
  - Nesne etiketi
  - HUD (FPS, nesne sayısı, mod, saat)
  - Yardım ekranı
"""

import cv2
import numpy as np
import time
from utils import config as cfg


# ─── Yardımcı ─────────────────────────────────────────────────────────────────

def _box_color(speed_px: float, area: float) -> tuple:
    """Hız ve alana göre renk seç: yeşil → sarı → kırmızı."""
    if speed_px > cfg.HIGH_SPEED_THRESHOLD or area > cfg.HIGH_AREA_THRESHOLD:
        return cfg.COLOR_RED
    elif speed_px > cfg.HIGH_SPEED_THRESHOLD * 0.5:
        return cfg.COLOR_YELLOW
    return cfg.COLOR_GREEN


def _draw_corner_marks(frame: np.ndarray, x: int, y: int, w: int, h: int,
                        color: tuple, length: int = cfg.CORNER_LENGTH,
                        thickness: int = cfg.CORNER_THICKNESS) -> None:
    """Kutunun dört köşesine ince 'L' şeklinde vurgu çiz."""
    corners = [
        # (başlangıç_x, başlangıç_y, bitiş_x, bitiş_y) — yatay
        # (başlangıç_x, başlangıç_y, bitiş_x, bitiş_y) — dikey
        ((x, y),           (x + length, y),      (x, y),           (x, y + length)),
        ((x + w, y),       (x + w - length, y),  (x + w, y),       (x + w, y + length)),
        ((x, y + h),       (x + length, y + h),  (x, y + h),       (x, y + h - length)),
        ((x + w, y + h),   (x + w - length, y + h), (x + w, y + h), (x + w, y + h - length)),
    ]
    for (h1, h2, v1, v2) in corners:
        cv2.line(frame, h1, h2, color, thickness)
        cv2.line(frame, v1, v2, color, thickness)


# ─── Ana Çizim Fonksiyonları ──────────────────────────────────────────────────

def draw_detection(frame: np.ndarray, obj_id: int,
                   x: int, y: int, w: int, h: int,
                   cx: int, cy: int,
                   speed: float = 0.0,
                   area: float = 0.0) -> None:
    """
    Tespit edilen nesne etrafına kutu + köşe markaları + etiket çizer.

    Parameters
    ----------
    frame   : Çizilecek kare
    obj_id  : Nesne kimliği
    x,y,w,h : Bounding box koordinatları
    cx, cy  : Merkez noktası
    speed   : Piksel/kare hızı
    area    : Kontur alanı (piksel²)
    """
    color = _box_color(speed, area)

    # Ana bounding box (yarı şeffaf fill)
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
    cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)

    # Dış kenar
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, cfg.BOX_THICKNESS)

    # Köşe vurguları
    _draw_corner_marks(frame, x, y, w, h, color)

    # Merkez noktası
    cv2.circle(frame, (cx, cy), 3, color, -1)
    cv2.circle(frame, (cx, cy), 6, color, 1)

    # Etiket arka planı
    label = f"ID:{obj_id}  {speed:.1f}px/f"
    (lw, lh), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX,
        cfg.LABEL_FONT_SCALE, cfg.LABEL_THICKNESS
    )
    label_y = y - 6 if y - 6 > lh else y + h + lh + 4
    cv2.rectangle(
        frame,
        (x, label_y - lh - baseline),
        (x + lw + 4, label_y + baseline),
        color, -1
    )
    cv2.putText(
        frame, label,
        (x + 2, label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        cfg.LABEL_FONT_SCALE,
        cfg.COLOR_BLACK,
        cfg.LABEL_THICKNESS,
        cv2.LINE_AA
    )


def draw_hud(frame: np.ndarray, fps: float, obj_count: int,
             method: str, paused: bool = False,
             speed: float = 1.0) -> None:
    """
    Sol üst köşeye HUD (×××) çizer:
    FPS, nesne sayısı, çalışma modu, saat, oynatma hızı, duraklama durumu.
    """
    h_frame, w_frame = frame.shape[:2]
    speed_str = f"{speed:.2f}x" if speed != 1.0 else "1.00x (normal)"
    lines = [
        f"FPS  : {fps:.1f}",
        f"Nesne: {obj_count}",
        f"Mod  : {method.upper()}",
        f"Hiz  : {speed_str}",
        f"Saat : {time.strftime('%H:%M:%S')}",
    ]
    if paused:
        lines.append(">>> DURAKLADI <<<")

    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness  = 1
    pad        = 8
    line_h     = 22

    box_w = 200
    box_h = pad * 2 + line_h * len(lines)

    # Yarı şeffaf arka plan
    overlay = frame.copy()
    cv2.rectangle(overlay, (8, 8), (8 + box_w, 8 + box_h), cfg.HUD_BG_COLOR, -1)
    cv2.addWeighted(overlay, cfg.HUD_ALPHA, frame, 1 - cfg.HUD_ALPHA, 0, frame)

    # Kenarlık
    cv2.rectangle(frame, (8, 8), (8 + box_w, 8 + box_h), cfg.COLOR_CYAN, 1)

    for i, line in enumerate(lines):
        color = cfg.COLOR_RED if "DURAKLADI" in line else (
            cfg.COLOR_YELLOW if "Mod" in line else cfg.COLOR_WHITE
        )
        cv2.putText(
            frame, line,
            (8 + pad, 8 + pad + line_h * (i + 1) - 4),
            font, font_scale, color, thickness, cv2.LINE_AA
        )


def draw_help_screen(frame: np.ndarray) -> None:
    """Ekranın sağ alt köşesine klavye kısayollarını listeler."""
    shortcuts = [
        "[ Klavye Kisayollari ]",
        "  Q     → Cikis",
        "  P     → Duraklat / Devam",
        "  R     → Arkaplan Sifirla",
        "  S     → Ekran Goruntüsü",
        "  M     → MOG2 / absdiff",
        "  [  ]  → Yavastir / Hizlandir",
        "  0     → Normal Hiz (1x)",
        "  H     → Yardimi Kapat",
    ]
    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.50
    thickness  = 1
    line_h     = 22
    pad        = 8
    box_w      = 240
    box_h      = pad * 2 + line_h * len(shortcuts)

    h, w = frame.shape[:2]
    x0 = w - box_w - 12
    y0 = h - box_h - 12

    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + box_w, y0 + box_h), cfg.HUD_BG_COLOR, -1)
    cv2.addWeighted(overlay, cfg.HUD_ALPHA, frame, 1 - cfg.HUD_ALPHA, 0, frame)
    cv2.rectangle(frame, (x0, y0), (x0 + box_w, y0 + box_h), cfg.COLOR_ORANGE, 1)

    for i, line in enumerate(shortcuts):
        color = cfg.COLOR_ORANGE if i == 0 else cfg.COLOR_WHITE
        cv2.putText(
            frame, line,
            (x0 + pad, y0 + pad + line_h * (i + 1) - 4),
            font, font_scale, color, thickness, cv2.LINE_AA
        )


def draw_mask_thumbnail(frame: np.ndarray, mask: np.ndarray,
                         scale: float = 0.22) -> None:
    """
    Hareket maskesini sağ üst köşede küçük önizleme olarak gösterir.
    """
    h, w = frame.shape[:2]
    th = int(h * scale)
    tw = int(w * scale)

    mask_color = cv2.cvtColor(
        cv2.resize(mask, (tw, th)), cv2.COLOR_GRAY2BGR
    )

    # Yeşil tona boya
    green_tint = np.zeros_like(mask_color)
    green_tint[:, :, 1] = mask_color[:, :, 1]
    thumb = cv2.addWeighted(mask_color, 0.5, green_tint, 0.5, 0)

    x_off = w - tw - 12
    y_off = 12
    frame[y_off:y_off + th, x_off:x_off + tw] = thumb
    cv2.rectangle(frame, (x_off, y_off), (x_off + tw, y_off + th), cfg.COLOR_CYAN, 1)
    cv2.putText(
        frame, "MASK",
        (x_off + 4, y_off + th - 6),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, cfg.COLOR_CYAN, 1, cv2.LINE_AA
    )
