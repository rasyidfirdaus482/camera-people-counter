import cv2
import mediapipe as mp
import numpy as np
import time
import json
from datetime import datetime
import os
import webbrowser
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

class PeopleCounter:
    def __init__(self):
        """
        Enhanced People Counter dengan fitur-fitur ringan tambahan
        """
        # MediaPipe initialization
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.4
        )
        
        self.pose_detector = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # ====== FITUR BARU: TRACKING & ANALYTICS ======
        self.detection_history = []  # Untuk smoothing
        self.max_count_today = 0
        self.session_start_time = time.time()
        self.frame_count = 0
        self.fps = 0
        
        # Counting zones (virtual lines)
        self.entry_line_y = None
        self.exit_line_y = None
        self.people_crossed_in = 0
        self.people_crossed_out = 0
        
        # Data logging
        self.data_log = []
        self.log_interval = 2  # DIPERKECIL: Log setiap 2 detik untuk update lebih cepat
        self.last_log_time = time.time()
        self.current_count = 0  # TAMBAHAN: Track current count
        
        # Alert system
        self.max_capacity = 10  # Bisa disesuaikan
        self.alert_triggered = False
        
        # Stabilization - DIPERBAIKI
        self.stability_buffer = []  # Buffer untuk stabilisasi counting
        self.buffer_size = 3  # DIPERKECIL untuk response lebih cepat
        
        # Web server
        self.web_server = None
        self.web_port = 8080
        self.web_running = False

        self.web_update_interval = 2  # Update file HTML setiap 2 detik
        self.last_web_update_time = 0
        
    def setup_counting_zones(self, frame_height):
        """Setup virtual entry/exit lines"""
        if self.entry_line_y is None:
            self.entry_line_y = frame_height // 2  # 1/3 dari atas
            self.exit_line_y = (frame_height * 9) // 10  # 2/3 dari atas

    def _get_video_source(self):
        """Menampilkan menu untuk memilih sumber video (Webcam atau IP Camera)."""
        while True:
            print("\nSilakan pilih sumber video:")
            print("[1] Webcam Lokal (Bawaan)")
            print("[2] IP Camera (example: http://244.178.44.111:8080/video)")
            choice = input("Masukkan pilihan (1 atau 2): ")

            if choice == '1':
                # Menggunakan webcam default (indeks 0)
                # Anda bisa meminta input indeks jika punya lebih dari 1 webcam
                return 0
            
            elif choice == '2':
                # Meminta URL dari IP Camera
                url = input("Masukkan URL stream dari IP Camera: ")
                if not url:
                    print("URL tidak boleh kosong. Silakan coba lagi.")
                    continue
                return url
            
            else:
                print("Pilihan tidak valid. Silakan masukkan 1 atau 2.")
    
    def stabilize_count(self, current_count):
        """Stabilisasi counting untuk mengurangi fluktuasi - DIPERBAIKI"""
        self.stability_buffer.append(current_count)
        
        if len(self.stability_buffer) > self.buffer_size:
            self.stability_buffer.pop(0)
        
        # Gunakan nilai maksimum dari buffer untuk menghindari false negative
        if len(self.stability_buffer) >= 2:
            stable_count = max(self.stability_buffer)
            self.current_count = stable_count  # Update current count
            return stable_count
        
        self.current_count = current_count
        return current_count
    
    def calculate_fps(self):
        """Hitung FPS secara real-time"""
        self.frame_count += 1
        current_time = time.time()
        
        if self.frame_count % 30 == 0:  # Update setiap 30 frame
            elapsed = current_time - self.session_start_time
            self.fps = self.frame_count / elapsed if elapsed > 0 else 0
    
    def log_data(self, count):
        """Log data untuk analytics - DIPERBAIKI"""
        current_time = time.time()
        
        if current_time - self.last_log_time >= self.log_interval:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update max count SEBELUM logging
            if count > self.max_count_today:
                self.max_count_today = count
                print(f"🔥 New max count: {self.max_count_today}")  # Debug info
            
            data_point = {
                "timestamp": timestamp,
                "count": count,
                "max_today": self.max_count_today,
                "session_duration": int(current_time - self.session_start_time)
            }
            self.data_log.append(data_point)
            self.last_log_time = current_time
            
            # Debug output
            print(f"📊 Logged: Count={count}, Max={self.max_count_today}, Time={timestamp}")
    
    def save_session_data(self):
        """Simpan data session ke file JSON - METHOD DIPERBAIKI"""
        try:
            filename = f"people_counter_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            session_summary = {
                "session_start": datetime.fromtimestamp(self.session_start_time).strftime("%Y-%m-%d %H:%M:%S"),
                "session_end": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "max_count": self.max_count_today,
                "current_count": self.current_count,
                "total_frames": self.frame_count,
                "average_fps": round(self.fps, 2),
                "data_points": self.data_log
            }
            
            with open(filename, 'w') as f:
                json.dump(session_summary, f, indent=2)
            
            print(f"✓ Data session disimpan ke: {filename}")
            return filename
        except Exception as e:
            print(f"Error menyimpan data: {e}")
            return None
    
    def generate_web_report(self):
        """Generate HTML report untuk web view - DIPERBAIKI"""
        try:
            # Pastikan ada data
            if not self.data_log:
                # Buat dummy data jika belum ada
                dummy_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "count": self.current_count,
                    "max_today": self.max_count_today,
                    "session_duration": int(time.time() - self.session_start_time)
                }
                self.data_log.append(dummy_data)
            
            # Hitung statistik
            total_data_points = len(self.data_log)
            session_duration = int(time.time() - self.session_start_time)
            avg_count = sum([d['count'] for d in self.data_log]) / total_data_points if total_data_points > 0 else 0
            
            # PERBAIKAN: Ambil count terbaru dengan benar
            latest_count = self.current_count if hasattr(self, 'current_count') else (self.data_log[-1]['count'] if self.data_log else 0)
            
            # Prepare data untuk chart
            timestamps = [d['timestamp'].split(' ')[1][:5] for d in self.data_log[-20:]]  # Last 20 points, time only
            counts = [d['count'] for d in self.data_log[-20:]]
            
            html_content = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>People Counter Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(45deg, #2196F3, #21CBF3);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-number {{
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 1.1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .current-count {{ color: #4CAF50; }}
        .max-count {{ color: #FF9800; }}
        .avg-count {{ color: #2196F3; }}
        .duration {{ color: #9C27B0; }}
        
        .chart-section {{
            padding: 30px;
            background: white;
        }}
        
        .chart-title {{
            text-align: center;
            font-size: 1.8em;
            margin-bottom: 30px;
            color: #333;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 30px;
        }}
        
        .data-table {{
            margin-top: 30px;
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
        }}
        
        .refresh-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 50px;
            padding: 15px 25px;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
            transition: all 0.3s ease;
        }}
        
        .refresh-btn:hover {{
            background: #45a049;
            transform: scale(1.05);
        }}
        
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }}
        
        .status-active {{ background: #4CAF50; }}
        .status-waiting {{ background: #FFC107; }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .debug-info {{
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .stat-number {{
                font-size: 2.5em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 People Counter Dashboard</h1>
            <p>Real-time Analytics & Monitoring</p>
            <p><span class="status-indicator status-active"></span>Live Session Active</p>
        </div>
        
        <!-- DEBUG INFO -->
        <div class="debug-info">
            <strong>Debug Info:</strong><br>
            Current Count: {latest_count} | Max Today: {self.max_count_today} | 
            Data Points: {len(self.data_log)} | Last Update: {datetime.now().strftime('%H:%M:%S')}
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number current-count">{latest_count}</div>
                <div class="stat-label">Saat Ini</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-number max-count">{self.max_count_today}</div>
                <div class="stat-label">Maksimum</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-number avg-count">{avg_count:.1f}</div>
                <div class="stat-label">Rata-rata</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-number duration">{session_duration//60}:{session_duration%60:02d}</div>
                <div class="stat-label">Durasi</div>
            </div>
        </div>
        
        <div class="chart-section">
            <h2 class="chart-title">📈 Grafik Real-time (20 Data Terakhir)</h2>
            <div class="chart-container">
                <canvas id="peopleChart"></canvas>
            </div>
            
            <div class="data-table">
                <h3 style="margin-bottom: 20px;">📊 Data Log Terbaru</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Waktu</th>
                            <th>Jumlah Orang</th>
                            <th>Max Hari Ini</th>
                            <th>Durasi Session</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            
            # Add last 10 data points to table
            for data_point in self.data_log[-10:][::-1]:  # Reverse untuk yang terbaru di atas
                duration_formatted = f"{data_point['session_duration']//60}:{data_point['session_duration']%60:02d}"
                html_content += f"""
                        <tr>
                            <td>{data_point['timestamp']}</td>
                            <td>{data_point['count']}</td>
                            <td>{data_point['max_today']}</td>
                            <td>{duration_formatted}</td>
                        </tr>
"""
            
            html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>People Counter Dashboard © 2025 | Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>Session Started: {datetime.fromtimestamp(self.session_start_time).strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
    
    <script>
        // Chart.js configuration
        const ctx = document.getElementById('peopleChart').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {timestamps},
                datasets: [{{
                    label: 'Jumlah Orang',
                    data: {counts},
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#4CAF50',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        labels: {{
                            font: {{
                                size: 14
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: 'rgba(0,0,0,0.1)'
                        }},
                        ticks: {{
                            font: {{
                                size: 12
                            }}
                        }}
                    }},
                    x: {{
                        grid: {{
                            color: 'rgba(0,0,0,0.1)'
                        }},
                        ticks: {{
                            font: {{
                                size: 12
                            }}
                        }}
                    }}
                }},
                animation: {{
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }}
            }}
        }});
        
        // Auto refresh setiap 5 detik (diperkecil dari 10 detik)
        setTimeout(function() {{
            location.reload();
        }}, 5000);
        
        // Add some interactivity
        document.addEventListener('DOMContentLoaded', function() {{
            // Animate stat cards on load
            const statCards = document.querySelectorAll('.stat-card');
            statCards.forEach((card, index) => {{
                setTimeout(() => {{
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    card.style.transition = 'all 0.6s ease';
                    
                    setTimeout(() => {{
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }}, 100);
                }}, index * 150);
            }});
        }});
    </script>
</body>
</html>
"""
            
            # Save HTML file
            html_filename = "people_counter_dashboard.html"
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Web report generated: {html_filename}")
            print(f"📊 Latest count in report: {latest_count}")
            
            return html_filename
            
        except Exception as e:
            print(f"Error generating web report: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def start_web_server(self):
        """Start simple HTTP server untuk web dashboard"""
        try:
            class CustomHandler(SimpleHTTPRequestHandler):
                def log_message(self, format, *args):
                    pass  # Suppress server logs
            
            self.web_server = HTTPServer(('localhost', self.web_port), CustomHandler)
            self.web_running = True
            
            def serve_forever():
                print(f"🌐 Web server started at http://localhost:{self.web_port}")
                self.web_server.serve_forever()
            
            server_thread = threading.Thread(target=serve_forever, daemon=True)
            server_thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting web server: {e}")
            return False
    
    def stop_web_server(self):
        """Stop web server"""
        if self.web_server and self.web_running:
            self.web_server.shutdown()
            self.web_running = False
            print("🌐 Web server stopped")
    
    def open_web_dashboard(self):
        """Generate and open web dashboard"""
        print("🔄 Generating fresh web report...")
        html_file = self.generate_web_report()
        if html_file:
            try:
                # Start web server if not running
                if not self.web_running:
                    self.start_web_server()
                    time.sleep(1)  # Wait for server to start
                
                # Open browser
                webbrowser.open(f'http://localhost:{self.web_port}/{html_file}')
                print(f"🌐 Dashboard dibuka di browser: http://localhost:{self.web_port}/{html_file}")
                return True
            except Exception as e:
                print(f"Error opening web dashboard: {e}")
                return False
        return False
    
    def check_capacity_alert(self, count):
        """Cek dan trigger alert jika melebihi kapasitas"""
        if count >= self.max_capacity and not self.alert_triggered:
            self.alert_triggered = True
            return True
        elif count < self.max_capacity:
            self.alert_triggered = False
        return False
    
    def draw_enhanced_ui(self, frame, person_count, detected_faces):
        """Gambar UI yang lebih informatif"""
        height, width = frame.shape[:2]
        
        # Setup counting zones
        self.setup_counting_zones(height)
        
        # ====== MAIN COUNTER PANEL ======
        panel_height = 180  # Diperbesar sedikit
        cv2.rectangle(frame, (10, 10), (450, panel_height), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (450, panel_height), (255, 255, 255), 2)
        
        # Stabilized count
        stable_count = self.stabilize_count(person_count)
        
        # Main counter dengan warna dinamis
        color = (0, 255, 0) if stable_count < self.max_capacity else (0, 0, 255)
        counter_text = f"Jumlah Orang: {stable_count}"
        cv2.putText(frame, counter_text, (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.3, color, 3)
        
        # Raw vs Stable count (debugging)
        debug_text = f"Raw: {person_count} | Stable: {stable_count}"
        cv2.putText(frame, debug_text, (20, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Capacity indicator
        capacity_text = f"Kapasitas: {stable_count}/{self.max_capacity}"
        capacity_color = (0, 255, 0) if stable_count < self.max_capacity else (0, 165, 255)
        cv2.putText(frame, capacity_text, (20, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, capacity_color, 2)
        
        # Session info
        session_duration = int(time.time() - self.session_start_time)
        duration_text = f"Durasi: {session_duration//60:02d}:{session_duration%60:02d}"
        cv2.putText(frame, duration_text, (20, 125), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Max count today
        max_text = f"Max Hari Ini: {self.max_count_today}"
        cv2.putText(frame, max_text, (20, 145), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # FPS info
        fps_text = f"FPS: {self.fps:.1f} | Logged: {len(self.data_log)}"
        cv2.putText(frame, fps_text, (20, 165), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # ====== VIRTUAL COUNTING ZONES ======
        # Entry line (hijau)
        # cv2.line(frame, (0, self.entry_line_y), (width, self.entry_line_y), (0, 255, 0), 2)
        # cv2.putText(frame, "ENTRY ZONE", (width - 150, self.entry_line_y - 10), 
        #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # # Exit line (merah)
        # cv2.line(frame, (0, self.exit_line_y), (width, self.exit_line_y), (0, 0, 255), 2)
        # cv2.putText(frame, "EXIT ZONE", (width - 150, self.exit_line_y + 20), 
        #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # ====== ALERTS ======
        if self.check_capacity_alert(stable_count):
            # Alert visual
            cv2.rectangle(frame, (0, 0), (width, 60), (0, 0, 255), -1)
            cv2.putText(frame, "⚠️ KAPASITAS PENUH!", (width//2 - 150, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        # ====== STATUS & CONTROLS ======
        # Status di pojok kanan bawah
        status_text = f"AKTIF ({stable_count})" if stable_count > 0 else "MENUNGGU"
        status_color = (0, 255, 0) if stable_count > 0 else (0, 255, 255)
        cv2.putText(frame, f"Status: {status_text}", (width - 200, height - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Controls info
        controls = [
            "Q: Keluar & Simpan",
            "R: Reset Counter", 
            "S: Simpan Data",
            "C: Set Kapasitas",
            "W: Web Dashboard"
        ]
        
        for i, control in enumerate(controls):
            cv2.putText(frame, control, (width - 200, height - 140 + i*20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        return stable_count
    
    def run(self):
        """Main loop aplikasi"""
        # ====== PERUBAHAN DIMULAI DI SINI ======

        # Panggil fungsi untuk memilih sumber video
        video_source = self._get_video_source()

        print(f"\nMenginisialisasi sumber video dari: '{'Webcam Lokal' if video_source == 0 else video_source}'...")
        cap = cv2.VideoCapture(video_source)
        
        # Beri sedikit waktu untuk kamera (terutama IP camera) untuk terhubung
        time.sleep(2.0)

        if not cap.isOpened():
            print(f"Error: Tidak dapat membuka sumber video! Pastikan webcam terhubung atau URL IP Camera sudah benar.")
            return
        
        # ====== AKHIR DARI PERUBAHAN UTAMA ======
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("\n=== PEOPLE COUNTER ENHANCED ===")
        print("Fitur baru:")
        print("• Stabilized counting")
        print("• Real-time analytics") 
        print("• Data logging")
        print("• Capacity alerts")
        print("• Virtual counting zones")
        print("• Web dashboard (tekan W)")
        print("-" * 40)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Gagal membaca frame! Mungkin koneksi ke kamera terputus.")
                break
            
            # Sisa dari kode Anda sama persis seperti sebelumnya...
            frame = cv2.flip(frame, 1)
            height, width, _ = frame.shape
            
            # Calculate FPS
            self.calculate_fps()
            
            # Process detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_results = self.face_detector.process(rgb_frame)
            pose_results = self.pose_detector.process(rgb_frame)
            
            # Count people
            person_count = 0
            detected_faces = []
            
            if face_results.detections:
                person_count = len(face_results.detections)
                
                for idx, detection in enumerate(face_results.detections):
                    bbox = detection.location_data.relative_bounding_box
                    x = int(bbox.xmin * width)
                    y = int(bbox.ymin * height)
                    w = int(bbox.width * width)
                    h = int(bbox.height * height)
                    
                    x = max(0, x)
                    y = max(0, y)
                    w = min(width - x, w)
                    h = min(height - y, h)
                    
                    detected_faces.append((x, y, w, h))
                    
                    # Visualisasi deteksi
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    confidence = detection.score[0] if detection.score else 0.0
                    label = f"#{idx + 1} ({confidence:.2f})"
                    cv2.putText(frame, label, (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                    
                    # Center point
                    center_x = x + w // 2
                    center_y = y + h // 2
                    cv2.circle(frame, (center_x, center_y), 3, (0, 255, 0), -1)
            
            elif pose_results.pose_landmarks:
                person_count = 1
                self.mp_drawing.draw_landmarks(
                    frame, pose_results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2)
                )
            
            # Enhanced UI
            stable_count = self.draw_enhanced_ui(frame, person_count, detected_faces)
            
            # Log data
            self.log_data(stable_count)

            # BLOK KODE BARU UNTUK UPDATE WEB SECARA OTOMATIS
            current_time = time.time()
            if self.web_running and (current_time - self.last_web_update_time > self.web_update_interval):
                self.generate_web_report()
                self.last_web_update_time = current_time
            
            # Display
            cv2.imshow('People Counter - Enhanced Edition', frame)
            
            # Controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("Menyimpan data dan keluar...")
                self.save_session_data()
                break
            elif key == ord('r') or key == ord('R'):
                print("Reset counter...")
                self.stability_buffer.clear()
                self.max_count_today = 0
            elif key == ord('s') or key == ord('S'):
                filename = self.save_session_data()
                if filename:
                    print(f"Data disimpan ke {filename}")
            elif key == ord('c') or key == ord('C'):
                try:
                    new_capacity = int(input("Masukkan kapasitas maksimum baru: "))
                    self.max_capacity = new_capacity
                    print(f"Kapasitas diubah ke: {new_capacity}")
                except:
                    print("Input tidak valid!")
            elif key == ord('w') or key == ord('W'):
                print("Membuka web dashboard...")
                self.open_web_dashboard()
            elif key == 27:  # ESC
                break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        self.face_detector.close()
        self.pose_detector.close()
        self.stop_web_server()
        
        # Final summary
        print("\n=== SESSION SUMMARY ===")
        print(f"Durasi session: {int(time.time() - self.session_start_time)} detik")
        print(f"Max count: {self.max_count_today}")
        print(f"Total frames: {self.frame_count}")
        print(f"Average FPS: {self.fps:.2f}")
        print(f"Data points logged: {len(self.data_log)}")
        
        # Generate final web report
        if self.data_log:
            html_file = self.generate_web_report()
            if html_file:
                print(f"📊 Final dashboard tersimpan: {html_file}")

if __name__ == "__main__":
    try:
        counter = PeopleCounter()
        counter.run()
    except KeyboardInterrupt:
        print("\n⚠️ Program dihentikan oleh user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔚 Program selesai")