# People Counter - Enhanced Edition 🏢

**Real-time People Counting System with Advanced Analytics & Web Dashboard**

Sistem penghitung orang berbasis computer vision yang dilengkapi dengan fitur analytics real-time, web dashboard interaktif, dan berbagai fitur monitoring canggih.

## 🌟 Fitur Utama

### ✨ Core Features
- **Real-time People Detection**: Menggunakan MediaPipe untuk deteksi wajah dan pose
- **Stabilized Counting**: Algoritma stabilisasi untuk mengurangi fluktuasi counting
- **Dual Camera Support**: Mendukung webcam lokal dan IP camera
- **Capacity Monitoring**: Alert otomatis saat mencapai kapasitas maksimum

### 📊 Analytics & Monitoring
- **Session Analytics**: Tracking durasi session, FPS, dan statistik real-time
- **Data Logging**: Otomatis menyimpan data setiap 2 detik
- **Historical Data**: Melacak count maksimum harian dan trend
- **Visual Indicators**: UI informatif dengan status dan controls

### 🌐 Web Dashboard
- **Interactive Dashboard**: Dashboard web dengan grafik real-time
- **Auto-refresh**: Update otomatis setiap 5 detik
- **Responsive Design**: Mobile-friendly interface
- **Chart Visualization**: Grafik Chart.js untuk visualisasi data
- **Export Data**: Session data tersimpan dalam format JSON

## 🔧 Persyaratan Sistem

### Dependencies
```bash
pip install opencv-python
pip install mediapipe
pip install numpy
```

### Sistem Requirements
- **Python**: 3.7+
- **OpenCV**: 4.5+
- **MediaPipe**: 0.8+
- **RAM**: Minimum 4GB (8GB recommended)
- **Camera**: Webcam atau IP Camera

## 🚀 Instalasi

### 1. Clone Repository
```bash
git clone https://github.com/rasyidfirdaus482/camera-people-counter.git
cd camera-people-counter
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

atau manual:
```bash
pip install opencv-python mediapipe numpy
```

### 3. Jalankan Program
```bash
python people_counter.py
```

## 📖 Cara Penggunaan

### 1. Pemilihan Sumber Video
Saat program dijalankan, Anda akan diminta memilih sumber video:
- **[1] Webcam Lokal**: Menggunakan kamera bawaan komputer
- **[2] IP Camera**: Menggunakan IP camera dengan URL stream

### 2. Kontrol Program
Gunakan keyboard shortcuts berikut saat program berjalan:

| Key | Fungsi |
|-----|--------|
| `Q` | Keluar dan simpan data session |
| `R` | Reset counter ke 0 |
| `S` | Simpan data session saat ini |
| `C` | Ubah kapasitas maksimum |
| `W` | Buka web dashboard |
| `ESC` | Keluar tanpa menyimpan |

### 3. Web Dashboard
- Tekan `W` untuk membuka dashboard web
- Dashboard akan terbuka di `http://localhost:8080`
- Auto-refresh setiap 5 detik
- Menampilkan grafik, statistik, dan data log

## 🎛️ Konfigurasi

### Pengaturan Default
```python
# Dalam class PeopleCounter.__init__()
self.max_capacity = 10          # Kapasitas maksimum
self.log_interval = 2           # Interval logging (detik)
self.buffer_size = 3            # Buffer stabilisasi
self.web_port = 8080           # Port web server
self.web_update_interval = 2    # Update interval web (detik)
```

### MediaPipe Settings
```python
# Face Detection
min_detection_confidence = 0.4
model_selection = 0

# Pose Detection
min_detection_confidence = 0.5
min_tracking_confidence = 0.5
model_complexity = 1
```

## 📊 Output Data

### 1. Session JSON
Program otomatis menyimpan data session:
```json
{
  "session_start": "2025-06-25 10:30:00",
  "session_end": "2025-06-25 11:00:00",
  "max_count": 8,
  "current_count": 3,
  "total_frames": 1800,
  "average_fps": 30.5,
  "data_points": [...]
}
```

### 2. Web Dashboard
- **Real-time Stats**: Count saat ini, maksimum, rata-rata, durasi
- **Interactive Chart**: Grafik 20 data point terakhir
- **Data Table**: Log 10 entries terbaru
- **Auto-refresh**: Update otomatis setiap 5 detik

## 🔍 Algoritma Detection

### Face Detection (Primary)
- Menggunakan MediaPipe Face Detection
- Model: BlazeFace (lightweight)
- Confidence threshold: 0.4
- Mendeteksi multiple faces dalam satu frame

### Pose Detection (Fallback)
- Menggunakan MediaPipe Pose
- Aktivasi saat tidak ada wajah terdeteksi
- Full body landmark detection
- Model complexity: 1 (balanced)

### Stabilization Algorithm
```python
def stabilize_count(self, current_count):
    self.stability_buffer.append(current_count)
    if len(self.stability_buffer) > self.buffer_size:
        self.stability_buffer.pop(0)
    
    # Gunakan nilai maksimum untuk menghindari false negative
    stable_count = max(self.stability_buffer)
    return stable_count
```

## 🌐 Web Server Architecture

### Built-in HTTP Server
- **Framework**: Python `http.server`
- **Port**: 8080 (configurable)
- **Auto-generation**: HTML report setiap 2 detik
- **Static Files**: Serve HTML, CSS, JS

### Dashboard Features
- **Chart.js**: Interactive line charts
- **Responsive CSS**: Mobile-friendly design
- **Real-time Updates**: Auto-refresh mechanism
- **Modern UI**: Gradient backgrounds, animations

## 🔧 Troubleshooting

### Camera Issues
```python
# Jika webcam tidak terdeteksi
video_source = 1  # Coba index kamera lain
# atau
video_source = "http://your-ip-camera-url:your-port/video"
```

### Performance Issues
```python
# Kurangi resolusi untuk performa lebih baik
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Atau adjust detection confidence
min_detection_confidence = 0.3  # Lebih sensitif
```

### Web Dashboard Issues
- **Port conflict**: Ubah `self.web_port = 8081`
- **Browser cache**: Hard refresh (Ctrl+F5)
- **Firewall**: Allow port 8080 pada firewall

## 📈 Performance Optimization

### Recommended Settings
- **Resolution**: 640x480 untuk balance performance/accuracy
- **Buffer Size**: 3-5 frames untuk stabilitas optimal
- **Log Interval**: 2-5 detik untuk storage efficiency
- **Detection Confidence**: 0.4-0.6 untuk accuracy

### Hardware Recommendations
- **CPU**: Intel i5 atau AMD Ryzen 5+
- **RAM**: 8GB minimum
- **Camera**: 720p webcam atau IP camera
- **Storage**: SSD untuk data logging

## 🛡️ Security Considerations

### IP Camera
- Gunakan credentials yang kuat
- Pastikan network security
- Monitor bandwidth usage

### Data Privacy
- Data hanya disimpan lokal
- Tidak ada cloud upload
- Session data dapat dihapus manual

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 Changelog

### v1.0.0 (Current)
- ✅ Real-time people counting
- ✅ Face + Pose detection
- ✅ Stabilized counting algorithm
- ✅ Web dashboard with charts
- ✅ Session data logging
- ✅ IP camera support
- ✅ Capacity monitoring
- ✅ Auto-refresh web interface

### Planned Features
- 🔄 Database integration
- 🔄 Multiple camera zones
- 🔄 Email/SMS alerts
- 🔄 API endpoints
- 🔄 Machine learning improvements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/rasyidfirdaus482)

## 🙏 Acknowledgments

- **MediaPipe** - Google's ML framework
- **OpenCV** - Computer vision library
- **Chart.js** - JavaScript charting library
- **Python Community** - Amazing ecosystem

## 📞 Support

Jika mengalami masalah atau memiliki pertanyaan:

1. **Issues**: Buka issue di GitHub repository
2. **Email**: rasyidfirdaus53@gmail.com
3. **Documentation**: Baca README ini dengan teliti

---

**⭐ Jika project ini membantu Anda, jangan lupa untuk memberikan star di GitHub!**
