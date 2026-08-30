# 🚁 UAV Motion Tracker — İHA Hedef ve Hareket Takip Sistemi

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green?style=for-the-badge&logo=opencv)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)

**Sabit kamera veya drone videosu üzerinden hareket eden nesneleri (araba, insan vb.) gerçek zamanlı olarak tespit edip takip eden Python + OpenCV uygulaması.**

</div>

---

## 📸 Özellikler

- 🎯 **İki Arkaplan Çıkarma Modu**
  - `MOG2` — Drone / dış mekan / değişen ışık için ideal
  - `absdiff` — Sabit kamera / iç mekan için ideal
- 🆔 **Centroid Tracking** — Her nesneye kalıcı ID atar, kareler arası takip eder
- ⚡ **Hız Tahmini** — Nesnenin piksel/kare cinsinden anlık hızını hesaplar
- 🟢🔴 **Dinamik Renk** — Yavaş nesne yeşil, hızlı/büyük nesne kırmızı kutu
- 🎛️ **Canlı Kontrol Paneli** — OpenCV Trackbar ile parametreleri anlık ayarla
- 📹 **Video Kaydı** — İşlenmiş videoyu `.mp4` olarak kaydet
- 🖼️ **Ekran Görüntüsü** — `S` tuşuyla anlık kaydeder
- 🎬 **Oynatma Hız Kontrolü** — `[` yavaşlat / `]` hızlandır
- 📡 **RTSP Desteği** — Gerçek drone kamerasına doğrudan bağlan

---

## 📁 Proje Yapısı

```
uav_motion_tracker/
│
├── main.py                        # Ana program — buradan başlat
├── requirements.txt
│
├── tracker/
│   ├── background_subtractor.py   # MOG2 + absdiff arkaplan çıkarma
│   ├── object_detector.py         # Kontur bulma ve filtreleme
│   └── tracker_core.py            # Centroid tabanlı çok-nesne takibi
│
├── utils/
│   ├── config.py                  # Tüm parametreler (merkezi ayar dosyası)
│   ├── drawing.py                 # Bounding box, HUD, maske önizleme
│   └── fps_counter.py             # FPS hesaplayıcı
│
├── ui/
│   └── control_panel.py           # OpenCV Trackbar kontrol paneli
│
└── demo/
    └── generate_test_video.py     # Gerçek video olmadan test için
```

---

## 🚀 Kurulum

### 1. Repoyu klonla
```bash
git clone https://github.com/KULLANICI_ADIN/uav-motion-tracker.git
cd uav-motion-tracker
```

### 2. Sanal ortam oluştur (önerilir)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Bağımlılıkları yükle
```bash
pip install -r requirements.txt
```

---

## ▶️ Kullanım

### Demo video oluştur (gerçek video yoksa)
```bash
python demo/generate_test_video.py
```

### MOG2 ile çalıştır (drone / dış mekan)
```bash
python main.py --source demo/test_video.mp4 --method mog2
```

### absdiff ile çalıştır (sabit kamera)
```bash
python main.py --source demo/test_video.mp4 --method absdiff
```

### Webcam ile canlı test
```bash
python main.py --source 0
```

### Gerçek video dosyası
```bash
python main.py --source "C:\Videolar\trafik.mp4"
```

### RTSP (drone kamerası)
```bash
python main.py --source rtsp://192.168.1.1:554/stream
```

### Çıktıyı kaydet
```bash
python main.py --source demo/test_video.mp4 --output sonuc.mp4
```

### Tüm seçenekler
```
python main.py --help

  --source     Kaynak: 0 (webcam) | video.mp4 | rtsp://...
  --method     mog2 | absdiff (varsayılan: mog2)
  --output     Çıkış video dosyası (isteğe bağlı)
  --scale      Görüntü ölçeği, örn: 0.5 → yarı boyut (varsayılan: 1.0)
  --no-panel   Kontrol panelini gizle
  --no-mask    Maske önizlemesini gizle
```

---

## ⌨️ Klavye Kısayolları

| Tuş | İşlev |
|-----|-------|
| `Q` veya `ESC` | Çıkış |
| `P` veya `Space` | Duraklat / Devam |
| `R` | Arkaplan modelini sıfırla |
| `S` | Ekran görüntüsü kaydet (`screenshots/`) |
| `M` | MOG2 ↔ absdiff geçiş (anında) |
| `[` | Oynatma hızını düşür (−0.25x) |
| `]` | Oynatma hızını artır (+0.25x) |
| `0` | Normal hıza dön (1.0x) |
| `H` | Yardım ekranını aç/kapat |
| `V` | Maske önizlemesini aç/kapat |

---

## 🎛️ Parametre Ayarlama

### Yöntem 1: Canlı (program açıkken)
**"Kontrol Paneli"** penceresindeki trackbar'ları sürükle — anında etki eder.

| Parametre | Açıklama |
|-----------|----------|
| Min Area | Küçük gürültü → artır / küçük nesne kaçıyor → azalt |
| MOG2 Var Threshold | Hassasiyet — düşük=hassas, yüksek=gürültüsüz |
| Blur Kernel | Görüntü yumuşatma |
| Dilate Iter | Parçalı tespitleri birleştir |

### Yöntem 2: Kalıcı (`utils/config.py`)

```python
# Drone videosu için önerilen
DEFAULT_METHOD       = "mog2"
MOG2_VAR_THRESHOLD   = 25
MIN_CONTOUR_AREA     = 1500

# Sabit kamera için önerilen
DEFAULT_METHOD       = "absdiff"
MIN_CONTOUR_AREA     = 800
```

---

## 🧠 Sistem Mimarisi

```
Video Kaynağı
     │
     ▼
BackgroundSubtractor ──── MOG2 / absdiff
     │
     ▼
ObjectDetector ─────────── Kontur + Alan/AR Filtresi
     │
     ▼
CentroidTracker ────────── ID Atama + Hız Hesabı
     │
     ▼
Drawing ────────────────── Kutu + HUD + İz + Maske
     │
     ▼
OpenCV Pencere / Video Kayıt
```

---

## 🔧 Bağımlılıklar

| Paket | Sürüm | Amaç |
|-------|-------|------|
| `opencv-python` | ≥ 4.8 | Görüntü işleme |
| `opencv-contrib-python` | ≥ 4.8 | Ek algoritmalar |
| `numpy` | ≥ 1.24 | Dizi işlemleri |
| `imutils` | ≥ 0.5.4 | OpenCV yardımcıları |

---

## 📜 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

---

## 🤝 Katkı

Pull request ve issue'lar memnuniyetle karşılanır!

1. Fork'la
2. Feature branch oluştur (`git checkout -b feature/yeni-ozellik`)
3. Commit'le (`git commit -m 'feat: yeni özellik eklendi'`)
4. Push'la (`git push origin feature/yeni-ozellik`)
5. Pull Request aç
