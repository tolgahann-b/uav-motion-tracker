"""
utils/config.py
---------------
UAV Motion Tracker - Merkezi Ayarlar Dosyası
Tüm eşik değerleri, renkler ve MOG2 parametreleri buradan yönetilir.
"""

# ─── Arkaplan Çıkarma Modu ──────────────────────────────────────────────────
# "mog2"   → cv2.createBackgroundSubtractorMOG2  (drone / dış mekan)
# "absdiff" → İlk kare referans farkı            (sabit kamera / iç mekan)
DEFAULT_METHOD = "mog2"

# ─── MOG2 Parametreleri ─────────────────────────────────────────────────────
MOG2_HISTORY          = 500    # Geçmiş kare sayısı
MOG2_VAR_THRESHOLD    = 16     # Piksel varyans eşiği (düşük=hassas, yüksek=gürültüsüz)
MOG2_DETECT_SHADOWS   = False  # Gölge tespiti (True → gri maske pikseller)
MOG2_LEARNING_RATE    = -1     # -1 = otomatik; 0.001-0.01 arası önerilir

# ─── Görüntü Ön-İşleme ──────────────────────────────────────────────────────
BLUR_KERNEL_SIZE      = 21     # Gaussian blur (tek sayı olmalı)
MORPH_KERNEL_SIZE     = 5      # Morfoloji işlemi çekirdek boyutu
DILATE_ITERATIONS     = 3      # Genişletme yineleme sayısı
ERODE_ITERATIONS      = 1      # Aşındırma yineleme sayısı
BINARY_THRESHOLD      = 25     # absdiff binary eşik değeri

# ─── Nesne Filtresi ──────────────────────────────────────────────────────────
MIN_CONTOUR_AREA      = 800    # Piksel² — daha küçük konturlar gürültü say
MAX_CONTOUR_AREA      = 80_000 # Piksel² — daha büyük konturlar çerçeve gürültüsü
MIN_ASPECT_RATIO      = 0.2    # En/Boy oranı alt sınır
MAX_ASPECT_RATIO      = 8.0    # En/Boy oranı üst sınır

# ─── Centroid Tracker ─────────────────────────────────────────────────────────
MAX_DISAPPEARED       = 30     # Nesne kaç kare görünmezse silinsin
MAX_DISTANCE          = 100    # Eşleştirme için maksimum piksel mesafesi

# ─── Hız / Renk Eşiği ───────────────────────────────────────────────────────
HIGH_SPEED_THRESHOLD  = 15     # Piksel/kare — bu değerin üstü "hızlı" (kırmızı)
HIGH_AREA_THRESHOLD   = 20_000 # Piksel² — bu değerin üstü "büyük nesne" (kırmızı)

# ─── Renkler (BGR formatı) ───────────────────────────────────────────────────
COLOR_GREEN           = (0,   220,  80)   # Yavaş / normal nesne
COLOR_RED             = (0,    40, 220)   # Hızlı / büyük nesne
COLOR_YELLOW          = (0,   200, 255)   # Orta hız
COLOR_WHITE           = (255, 255, 255)
COLOR_BLACK           = (0,     0,   0)
COLOR_CYAN            = (200, 200,   0)
COLOR_ORANGE          = (0,   140, 255)

# HUD Arka planı
HUD_BG_COLOR          = (20,  20,  20)
HUD_ALPHA             = 0.65              # Şeffaflık (0=tam şeffaf, 1=tam opak)

# ─── Çizim Ayarları ──────────────────────────────────────────────────────────
BOX_THICKNESS         = 2      # Bounding box çizgi kalınlığı
LABEL_FONT_SCALE      = 0.52
LABEL_THICKNESS       = 1
CORNER_LENGTH         = 15     # Köşe vurgusu uzunluğu (piksel)
CORNER_THICKNESS      = 3      # Köşe vurgusu kalınlığı

# ─── Video Çıktısı ───────────────────────────────────────────────────────────
OUTPUT_FPS            = 20
OUTPUT_CODEC          = "mp4v"   # fourcc kodu

# ─── Genel ──────────────────────────────────────────────────────────────────
SCREENSHOT_DIR        = "screenshots"
WINDOW_NAME           = "UAV Motion Tracker"
CONTROL_WINDOW_NAME   = "[ Kontrol Paneli ]"
