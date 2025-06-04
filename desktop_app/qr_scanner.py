#!/usr/bin/env python3
"""
🔍 QR-сканер для Tracker33
Модуль для сканирования QR-кодов через камеру
"""

import cv2
import json
import numpy as np
from pyzbar import pyzbar
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QTextEdit, QProgressBar,
                            QGroupBox, QFormLayout)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
import requests
import logging

logger = logging.getLogger(__name__)

class QRScannerThread(QThread):
    """Поток для сканирования QR-кодов"""
    
    frame_ready = pyqtSignal(np.ndarray)
    qr_detected = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.camera = None
        
    def run(self):
        """Основной цикл сканирования"""
        try:
            # Инициализируем камеру
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self.error_occurred.emit("Не удалось открыть камеру")
                return
                
            self.running = True
            logger.info("QR-сканер запущен")
            
            while self.running:
                ret, frame = self.camera.read()
                if not ret:
                    continue
                    
                # Отправляем кадр для отображения
                self.frame_ready.emit(frame)
                
                # Ищем QR-коды
                qr_codes = pyzbar.decode(frame)
                
                for qr_code in qr_codes:
                    # Декодируем данные
                    qr_data = qr_code.data.decode('utf-8')
                    logger.info(f"QR-код обнаружен: {qr_data[:50]}...")
                    
                    # Проверяем, что это наш QR-код
                    try:
                        data = json.loads(qr_data)
                        if 'token' in data and 'api_url' in data:
                            self.qr_detected.emit(qr_data)
                            return
                    except json.JSONDecodeError:
                        # Возможно, это не наш QR-код
                        continue
                        
                # Небольшая задержка
                self.msleep(50)
                
        except Exception as e:
            self.error_occurred.emit(f"Ошибка сканирования: {e}")
        finally:
            if self.camera:
                self.camera.release()
                
    def stop(self):
        """Остановка сканирования"""
        self.running = False
        self.wait()

class QRAuthDialog(QDialog):
    """Диалог QR-аутентификации"""
    
    auth_success = pyqtSignal(dict)  # Сигнал успешной аутентификации
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QR-код аутентификация")
        self.setFixedSize(800, 600)
        
        self.scanner_thread = None
        self.config_data = None
        
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("🔗 Сканируйте QR-код для подключения")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #667eea; margin: 10px;")
        layout.addWidget(title)
        
        # Группа камеры
        camera_group = QGroupBox("📷 Камера")
        camera_layout = QVBoxLayout()
        
        # Видео превью
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px solid #667eea;
                border-radius: 10px;
                background-color: #f0f0f0;
            }
        """)
        self.video_label.setText("🎥 Инициализация камеры...")
        camera_layout.addWidget(self.video_label)
        
        # Кнопки управления камерой
        camera_buttons = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Начать сканирование")
        self.start_btn.clicked.connect(self.start_scanning)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        
        self.stop_btn = QPushButton("⏹️ Остановить")
        self.stop_btn.clicked.connect(self.stop_scanning)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c82333; }
        """)
        
        camera_buttons.addWidget(self.start_btn)
        camera_buttons.addWidget(self.stop_btn)
        camera_layout.addLayout(camera_buttons)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # Группа альтернативного ввода
        manual_group = QGroupBox("✏️ Ручной ввод")
        manual_layout = QFormLayout()
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Введите токен из QR-кода...")
        manual_layout.addRow("Токен:", self.token_input)
        
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("http://localhost:8000")
        manual_layout.addRow("Сервер:", self.server_input)
        
        manual_buttons = QHBoxLayout()
        
        connect_btn = QPushButton("🔗 Подключиться")
        connect_btn.clicked.connect(self.manual_connect)
        connect_btn.setStyleSheet("""
            QPushButton {
                background: #007bff;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0056b3; }
        """)
        
        manual_buttons.addWidget(connect_btn)
        manual_layout.addRow("", manual_buttons)
        
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)
        
        # Лог активности
        log_group = QGroupBox("📋 Лог активности")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Прогресс-бар
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
        
    def add_log(self, message):
        """Добавляет сообщение в лог"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def start_scanning(self):
        """Запуск сканирования"""
        if self.scanner_thread and self.scanner_thread.isRunning():
            return
            
        self.add_log("🔄 Запуск QR-сканера...")
        
        self.scanner_thread = QRScannerThread()
        self.scanner_thread.frame_ready.connect(self.update_video)
        self.scanner_thread.qr_detected.connect(self.process_qr_code)
        self.scanner_thread.error_occurred.connect(self.handle_error)
        
        self.scanner_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
    def stop_scanning(self):
        """Остановка сканирования"""
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.add_log("⏹️ Остановка сканера...")
            self.scanner_thread.stop()
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def update_video(self, frame):
        """Обновление видео превью"""
        # Конвертируем в RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Создаем QImage
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Масштабируем и отображаем
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(self.video_label.size(), aspectRatioMode=1)
        self.video_label.setPixmap(scaled_pixmap)
        
    def process_qr_code(self, qr_data):
        """Обработка найденного QR-кода"""
        try:
            self.add_log("✅ QR-код обнаружен! Обработка...")
            
            # Парсим данные
            data = json.loads(qr_data)
            token = data.get('token')
            server_url = data.get('server_url', '').rstrip('/')
            api_url = data.get('api_url', '').rstrip('/')
            
            if not token or not api_url:
                self.add_log("❌ Неверный формат QR-кода")
                return
                
            self.add_log(f"🔗 Подключение к серверу: {server_url}")
            self.add_log(f"🔑 Токен: {token[:12]}...")
            
            # Останавливаем сканирование
            self.stop_scanning()
            
            # Показываем прогресс
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)  # Бесконечный прогресс
            
            # Аутентификация
            self.authenticate_with_token(token, api_url)
            
        except json.JSONDecodeError:
            self.add_log("❌ Ошибка: Неверный формат JSON в QR-коде")
        except Exception as e:
            self.add_log(f"❌ Ошибка обработки QR-кода: {e}")
            
    def authenticate_with_token(self, token, api_url):
        """Аутентификация с QR токеном"""
        try:
            # Отправляем запрос на аутентификацию
            auth_data = {
                'token': token,
                'username': 'QR_User'  # Можно запросить у пользователя
            }
            
            response = requests.post(
                f"{api_url}/qr/authenticate/",
                json=auth_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    self.add_log("✅ Аутентификация успешна!")
                    self.add_log(f"👤 Пользователь: {result.get('username')}")
                    
                    # Подготавливаем конфигурацию
                    config = {
                        'server_url': api_url.replace('/api', ''),
                        'api_url': api_url,
                        'auth_token': result.get('auth_token'),
                        'user_id': result.get('user_id'),
                        'username': result.get('username')
                    }
                    
                    # Сигнализируем об успехе
                    self.auth_success.emit(config)
                    
                    # Закрываем диалог
                    QTimer.singleShot(1000, self.accept)
                    
                else:
                    self.add_log(f"❌ Ошибка аутентификации: {result.get('error')}")
            else:
                self.add_log(f"❌ Ошибка сервера: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.add_log(f"❌ Ошибка сети: {e}")
        except Exception as e:
            self.add_log(f"❌ Неожиданная ошибка: {e}")
        finally:
            self.progress.setVisible(False)
            
    def manual_connect(self):
        """Ручное подключение"""
        token = self.token_input.text().strip()
        server = self.server_input.text().strip() or "http://localhost:8000"
        
        if not token:
            self.add_log("❌ Введите токен")
            return
            
        api_url = f"{server.rstrip('/')}/api"
        self.add_log(f"🔗 Ручное подключение к {api_url}")
        
        self.authenticate_with_token(token, api_url)
        
    def handle_error(self, error_msg):
        """Обработка ошибок"""
        self.add_log(f"❌ {error_msg}")
        self.stop_scanning()
        
    def closeEvent(self, event):
        """Закрытие диалога"""
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.stop()
        event.accept()

# Тестирование
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = QRAuthDialog()
    
    def on_auth_success(config):
        print("Аутентификация успешна!")
        print("Конфигурация:", config)
        
    dialog.auth_success.connect(on_auth_success)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Диалог закрыт с успехом")
    else:
        print("Диалог отменен")
        
    sys.exit(app.exec()) 