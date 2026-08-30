"""
main.py
--------
UAV Hedef / Hareket Takibi (Motion Tracking)
============================================

Kullanım:
    python main.py                              # Webcam (ID=0), MOG2
    python main.py --source video.mp4           # Video dosyası
    python main.py --source 0 --method absdiff  # Webcam, absdiff
    python main.py --source rtsp://...          # RTSP drone kamerası
    python main.py --source demo/test_video.mp4 --output cikti.mp4

Klavye Kısayolları:
    Q → Çıkış
    P → Duraklat / Devam
    R → Arkaplanı Sıfırla
    S → Ekran Görüntüsü Kaydet
    M → MOG2 ↔ absdiff Geçiş
    H → Yardım Ekranını Aç/Kapat
    + / - → Min Alan artır/azalt
"""

import cv2
import os
import sys
import argparse
import time
import numpy as np

# Proje modülleri
from tracker.background_subtractor import BackgroundSubtractor
from tracker.object_detector       import ObjectDetector
from tracker.tracker_core          import CentroidTracker
from ui.control_panel              import ControlPanel
from utils.fps_counter             import FPSCounter
from utils.drawing                 import (
    draw_detection, draw_hud,
    draw_help_screen, draw_mask_thumbnail
)
from utils import config as cfg


# ─── Argüman Ayrıştırıcı ────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="İHA Hedef / Hareket Takip Sistemi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--source", default="0",
        help="Kaynak: 0/1/.. (webcam ID) | video.mp4 | rtsp://... (varsayılan: 0)"
    )
    parser.add_argument(
        "--method", default=cfg.DEFAULT_METHOD,
        choices=["mog2", "absdiff"],
        help="Arkaplan çıkarma yöntemi (varsayılan: mog2)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Çıkış video dosyası yolu (isteğe bağlı, örn: output.mp4)"
    )
    parser.add_argument(
        "--no-panel", action="store_true",
        help="Kontrol panelini gizle (headless)"
    )
    parser.add_argument(
        "--no-mask", action="store_true",
        help="Maske önizlemesini gizle"
    )
    parser.add_argument(
        "--scale", type=float, default=1.0,
        help="Görüntü ölçeği (örn: 0.5 → yarı boyut, daha hızlı işlem)"
    )
    return parser.parse_args()


# ─── Video Kaynağı ──────────────────────────────────────────────────────────

def open_source(source_str: str) -> cv2.VideoCapture:
    """Kaynak stringinden VideoCapture oluştur."""
    src = int(source_str) if source_str.isdigit() else source_str
    cap = cv2.VideoCapture(src)

    if not cap.isOpened():
        print(f"[HATA] Kaynak açılamadı: {source_str}")
        print("       Lütfen webcam ID'sini veya video yolunu kontrol edin.")
        sys.exit(1)

    # Buffer boyutunu küçült (canlı kaynak için gecikmeyi azaltır)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def get_video_info(cap: cv2.VideoCapture) -> tuple:
    """Genişlik, yükseklik, FPS bilgisini döndür."""
    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or cfg.OUTPUT_FPS
    return w, h, fps


# ─── Ana Döngü ───────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # ── Kaynak Aç ──
    cap           = open_source(args.source)
    src_w, src_h, src_fps = get_video_info(cap)
    scale         = args.scale
    out_w         = int(src_w * scale)
    out_h         = int(src_h * scale)

    print(f"\n{'='*55}")
    print(f"  İHA Hareket Takip Sistemi")
    print(f"{'='*55}")
    print(f"  Kaynak  : {args.source}")
    print(f"  Boyut   : {src_w}x{src_h}  →  {out_w}x{out_h} (ölçek: {scale})")
    print(f"  Yöntem  : {args.method.upper()}")
    print(f"  Çıkış   : {args.output or 'Kayıt Yok'}")
    print(f"{'='*55}\n")

    # ── Bileşenler ──
    subtractor = BackgroundSubtractor(method=args.method)
    detector   = ObjectDetector()
    tracker    = CentroidTracker()
    fps_ctr    = FPSCounter(window=30)
    panel      = ControlPanel()

    if not args.no_panel:
        panel.create()

    # ── Video Yazıcı ──
    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*cfg.OUTPUT_CODEC)
        writer = cv2.VideoWriter(args.output, fourcc, cfg.OUTPUT_FPS, (out_w, out_h))
        print(f"[Kayıt] → {args.output}")

    # ── Pencere ──
    cv2.namedWindow(cfg.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(cfg.WINDOW_NAME, min(out_w, 1280), min(out_h, 720))

    paused         = False
    show_help      = True
    show_mask      = not args.no_mask
    frame_count    = 0
    last_frame     = None
    screenshot_n   = 0
    # NOT: playback_speed artık _speed[0] olarak yönetiliyor (aşağıda)

    os.makedirs(cfg.SCREENSHOT_DIR, exist_ok=True)

    # ── FPS Bazlı Gecikme ──────────────────────────────────────────────────────
    is_file_source = not str(args.source).isdigit()
    # Liste kullanarak closure scope sorununu önle
    _speed = [1.0]   # _speed[0] = mevcut oynatma hızı

    def get_delay_ms():
        if not is_file_source:
            return 1
        return max(1, int(1000.0 / src_fps / _speed[0]))


    # ══════════════════════════════════════════════════════════════════════════════
    while True:
        # ── Klavye İşle ──────────────────────────────────────────────────────
        key = cv2.waitKey(get_delay_ms()) & 0xFF

        if key == ord('q') or key == 27:          # Q veya ESC → Çıkış
            break
        elif key == ord('p') or key == ord(' '):  # P / Space → Duraklat
            paused = not paused
            print(f"[{'DURAKLADI' if paused else 'DEVAM'}]")
        elif key == ord('r'):                      # R → Sıfırla
            subtractor.reset()
            tracker.reset()
            print("[Arkaplan sıfırlandı]")
        elif key == ord('s'):                      # S → Ekran görüntüsü
            if last_frame is not None:
                ts   = time.strftime("%Y%m%d_%H%M%S")
                path = os.path.join(cfg.SCREENSHOT_DIR, f"screenshot_{ts}_{screenshot_n}.png")
                cv2.imwrite(path, last_frame)
                screenshot_n += 1
                print(f"[Ekran Görüntüsü] → {path}")
        elif key == ord('m'):                      # M → Yöntem Değiştir
            new_method = "absdiff" if subtractor.method == "mog2" else "mog2"
            subtractor.switch_method(new_method)
            tracker.reset()
            print(f"[Yöntem] → {new_method.upper()}")
        elif key == ord('h'):                      # H → Yardim
            show_help = not show_help
        elif key == ord('v'):                      # V → Maske onizleme
            show_mask = not show_mask
        elif key == ord('['):                      # [ → Yavaslat
            _speed[0] = max(0.1, round(_speed[0] - 0.25, 2))
            print(f"[Hiz] {_speed[0]:.2f}x  ({get_delay_ms()}ms/kare)")
        elif key == ord(']'):                      # ] → Hizlandir
            _speed[0] = min(8.0, round(_speed[0] + 0.25, 2))
            print(f"[Hiz] {_speed[0]:.2f}x  ({get_delay_ms()}ms/kare)")
        elif key == ord('0'):                      # 0 → Normal hiz
            _speed[0] = 1.0
            print("[Hiz] Normal (1.0x)")

        # ── Duraklama ────────────────────────────────────────────────────────
        if paused:
            if last_frame is not None:
                cv2.imshow(cfg.WINDOW_NAME, last_frame)
            continue

        # ── Kare Oku ─────────────────────────────────────────────────────────
        ret, frame = cap.read()
        if not ret:
            print("[Bitti] Video sona erdi veya kare okunamadı.")
            # Video döngüsü (sadece dosya kaynağı için)
            if not str(args.source).isdigit():
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                subtractor.reset()
                tracker.reset()
                continue
            break

        frame_count += 1

        # ── Yeniden Boyutlandır ───────────────────────────────────────────────
        if scale != 1.0:
            frame = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_LINEAR)

        # ── Kontrol Paneli Parametreleri ──────────────────────────────────────
        if panel.is_open():
            params = panel.get_params()
            subtractor.blur_k       = params.get("blur_k",      subtractor.blur_k)
            subtractor.morph_k      = params.get("morph_k",     subtractor.morph_k)
            subtractor.dilate_iter  = params.get("dilate_iter", subtractor.dilate_iter)
            subtractor.erode_iter   = params.get("erode_iter",  subtractor.erode_iter)
            subtractor.threshold    = params.get("threshold",   subtractor.threshold)
            detector.min_area       = params.get("min_area",    detector.min_area)
            detector.max_area       = params.get("max_area",    detector.max_area)
            tracker.max_disappeared = params.get("max_disappeared", tracker.max_disappeared)

            # MOG2 varThreshold canlı güncelle
            if subtractor.method == "mog2" and subtractor._mog2 is not None:
                subtractor._mog2.setVarThreshold(params.get("mog2_var_thr", 16))

        # ── Arkaplan Çıkarma ──────────────────────────────────────────────────
        mask = subtractor.apply(frame)

        # ── Nesne Tespiti ─────────────────────────────────────────────────────
        detections = detector.detect(mask)

        # ── Centroid Tracking ─────────────────────────────────────────────────
        tracked = tracker.update(detections)

        # ── Görselleştirme ───────────────────────────────────────────────────
        display = frame.copy()

        # Tespit kutularını çiz
        for obj_id, obj in tracked.items():
            if obj.disappeared == 0:   # Sadece bu karede görünen nesneler
                draw_detection(
                    display,
                    obj_id,
                    obj.x, obj.y, obj.w, obj.h,
                    obj.cx, obj.cy,
                    speed=obj.speed,
                    area=obj.area
                )

        # Aktif nesne iz çizgileri (son 8 nokta)
        for obj_id, obj in tracked.items():
            if len(obj.history) > 1 and obj.disappeared == 0:
                pts = obj.history[-8:]
                for i in range(1, len(pts)):
                    alpha = i / len(pts)
                    color = tuple(int(c * alpha) for c in cfg.COLOR_GREEN)
                    cv2.line(display, pts[i-1], pts[i], color, 1)

        # Maske önizleme (sağ üst köşe)
        if show_mask:
            draw_mask_thumbnail(display, mask)

        # HUD
        fps_val = fps_ctr.tick()
        draw_hud(display, fps_val, len([o for o in tracked.values() if o.disappeared == 0]),
                 subtractor.method, paused, _speed[0])


        # Yardım ekranı
        if show_help:
            draw_help_screen(display)

        # ── Göster / Kaydet ──────────────────────────────────────────────────
        cv2.imshow(cfg.WINDOW_NAME, display)
        last_frame = display

        if writer is not None:
            writer.write(display)

    # ── Temizlik ─────────────────────────────────────────────────────────────
    cap.release()
    if writer is not None:
        writer.release()
    panel.destroy()
    cv2.destroyAllWindows()

    print(f"\n✅ Toplam işlenen kare: {frame_count}")
    if args.output and writer:
        print(f"   Kayıt tamamlandı: {args.output}")
    print("   İyi uçuşlar! 🚁")


# ─── Giriş Noktası ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
