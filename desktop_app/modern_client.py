#!/usr/bin/env python3
"""
🚀 Tracker33 Modern GUI Client
Современный, незаметный и надежный клиент с системным треем

Особенности:
- Современный темный интерфейс
- Работа в системном трее
- Автоматическое переподключение
- Интуитивная настройка
- Автозапуск с системой
"""

import sys
import json
import time
import logging
import asyncio
import aiohttp
import psutil
import platform
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Any
import threading
import queue
import requests
from qr_scanner import QRAuthDialog

# GUI зависимости
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                                QTextEdit, QCheckBox, QSystemTrayIcon, QMenu,
                                QDialog, QFormLayout, QSpinBox, QComboBox,
                                QGroupBox, QProgressBar, QFrame, QGridLayout,
                                QTabWidget, QMessageBox, QScrollArea)
    from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QSettings
    from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QAction
except ImportError:
    print("❌ PyQt6 не установлен! Установите: pip install PyQt6")
    sys.exit(1)

# Системные зависимости
try:
    import pygetwindow as gw
    from pynput import keyboard, mouse
    if platform.system() == "Windows":
        import win32gui, win32process
except ImportError as e:
    print(f"❌ Отсутствуют зависимости: {e}")
    print("Установите: pip install pygetwindow pynput pywin32")
    sys.exit(1)

class ModernStyle:
    """Современные стили для GUI"""
    
    DARK_THEME = """
    QMainWindow, QDialog, QWidget {
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: 'Segoe UI', Calibri, sans-serif;
        font-size: 11pt;
    }
    
    QGroupBox {
        background-color: #2d2d2d;
        border: 2px solid #404040;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: bold;
        color: #ffffff;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px 0 8px;
        color: #00d4ff;
        font-size: 12pt;
        font-weight: bold;
    }
    
    QLineEdit, QSpinBox, QComboBox {
        background-color: #404040;
        border: 2px solid #666666;
        border-radius: 6px;
        padding: 10px;
        color: #ffffff;
        font-size: 11pt;
        font-weight: normal;
        selection-background-color: #00d4ff;
        selection-color: #000000;
    }
    
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
        border-color: #00d4ff;
        background-color: #4a4a4a;
        color: #ffffff;
    }
    
    QLineEdit:hover, QSpinBox:hover, QComboBox:hover {
        background-color: #4a4a4a;
        border-color: #888888;
    }
    
    QLineEdit::placeholder {
        color: #999999;
        font-style: italic;
    }
    
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #667eea, stop:1 #764ba2);
        border: none;
        border-radius: 8px;
        color: white;
        padding: 12px 24px;
        font-weight: bold;
        font-size: 11pt;
        min-height: 20px;
    }
    
    QPushButton:hover {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #778bef, stop:1 #8759af);
    }
    
    QPushButton:pressed {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #556de6, stop:1 #6b4c9a);
    }
    
    QPushButton:disabled {
        background-color: #555555;
        color: #888888;
    }
    
    QTextEdit {
        background-color: #2d2d2d;
        border: 2px solid #555555;
        border-radius: 6px;
        padding: 8px;
        color: #ffffff;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 10pt;
        selection-background-color: #00d4ff;
        selection-color: #000000;
    }
    
    QProgressBar {
        border: 2px solid #555555;
        border-radius: 6px;
        text-align: center;
        background-color: #2d2d2d;
        color: #ffffff;
        font-weight: bold;
    }
    
    QProgressBar::chunk {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #00d4ff, stop:1 #0099cc);
        border-radius: 4px;
    }
    
    QCheckBox {
        color: #ffffff;
        spacing: 8px;
        font-size: 11pt;
    }
    
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border: 2px solid #666666;
        border-radius: 4px;
        background-color: #404040;
    }
    
    QCheckBox::indicator:hover {
        border-color: #00d4ff;
        background-color: #4a4a4a;
    }
    
    QCheckBox::indicator:checked {
        background-color: #00d4ff;
        border-color: #00d4ff;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
    }
    
    QLabel {
        color: #ffffff;
        font-size: 11pt;
    }
    
    QFrame[frameShape="4"] {
        background-color: #555555;
        max-height: 1px;
    }
    
    QFormLayout QLabel {
        color: #cccccc;
        font-weight: bold;
        min-width: 120px;
    }
    """

class TrackerWorker(QThread):
    """Рабочий поток для отслеживания активности"""
    
    status_update = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    activity_update = pyqtSignal(dict)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True
        self.session = None
        self.auth_token = None
        self.current_app = None
        self.start_time = None
        self.keyboard_presses = 0
        self.last_activity = time.time()
        self.setup_listeners()
    
    def setup_listeners(self):
        """Настройка слушателей активности"""
        try:
            self.keyboard_listener = keyboard.Listener(on_press=self._on_keyboard_press)
            self.keyboard_listener.start()
        except Exception as e:
            self.status_update.emit(f"❌ Ошибка запуска слушателей: {e}")
    
    def _on_keyboard_press(self, key):
        """Обработчик нажатий клавиш"""
        self.keyboard_presses += 1
        self.last_activity = time.time()
    
    async def authenticate(self):
        """Аутентификация на сервере"""
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    'username': self.config['username'],
                    'password': self.config['password']
                }
                
                auth_url = f"{self.config['server_url']}/api/token/"
                
                async with session.post(
                    auth_url,
                    json=login_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.auth_token = data.get('token')
                        if self.auth_token:
                            self.connection_status.emit(True)
                            self.status_update.emit("✅ Подключение установлено")
                            return True
                        else:
                            self.connection_status.emit(False)
                            self.status_update.emit("❌ Токен не получен от сервера")
                            return False
                    else:
                        self.connection_status.emit(False)
                        self.status_update.emit(f"❌ Ошибка авторизации: {response.status}")
                        return False
        except Exception as e:
            self.connection_status.emit(False)
            self.status_update.emit(f"❌ Ошибка подключения: {e}")
            return False
    
    def get_active_window(self) -> Optional[Dict[str, str]]:
        """Получает информацию об активном окне"""
        try:
            if platform.system() == "Windows":
                hwnd = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                app_name = process.name()
                
                return {
                    'app_name': app_name,
                    'window_title': window_title,
                    'process_name': app_name  # Добавляю process_name для создания Application
                }
        except Exception:
            pass
        return None
    
    async def get_or_create_application(self, app_name: str) -> Optional[int]:
        """Получает или создает приложение и возвращает его ID"""
        if not self.auth_token:
            return None
            
        try:
            headers = {
                'Authorization': f'Token {self.auth_token}',
                'Content-Type': 'application/json'
            }
            
            # Сначала пытаемся найти существующее приложение
            apps_url = f"{self.config['server_url']}/api/applications/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(apps_url, headers=headers) as response:
                    if response.status == 200:
                        apps = await response.json()
                        for app in apps:
                            if app.get('process_name') == app_name:
                                return app.get('id')
                
                # Если приложение не найдено, создаем новое
                new_app_data = {
                    'name': app_name,
                    'process_name': app_name,
                    'is_productive': True  # По умолчанию считаем продуктивным
                }
                
                async with session.post(apps_url, json=new_app_data, headers=headers) as response:
                    if response.status in [200, 201]:
                        app_data = await response.json()
                        return app_data.get('id')
                    else:
                        error_text = await response.text()
                        self.status_update.emit(f"⚠️ Ошибка создания приложения: {error_text[:50]}...")
                        return None
                        
        except Exception as e:
            self.status_update.emit(f"⚠️ Ошибка получения приложения: {str(e)[:50]}...")
            return None
    
    async def send_activity(self, activity: Dict[str, Any]) -> bool:
        """Отправляет данные активности на сервер"""
        if not self.auth_token:
            return False
        
        try:
            headers = {
                'Authorization': f'Token {self.auth_token}',
                'Content-Type': 'application/json'
            }
            
            activity_url = f"{self.config['server_url']}/api/activities/"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    activity_url,
                    json=activity,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    success = response.status in [200, 201]
                    if not success:
                        error_text = await response.text()
                        self.status_update.emit(f"⚠️ Ошибка отправки активности: {response.status} - {error_text[:50]}...")
                    return success
        except Exception as e:
            self.status_update.emit(f"⚠️ Ошибка отправки активности: {str(e)[:50]}...")
            return False
    
    async def track_activity(self):
        """Отслеживает текущую активность"""
        window_info = self.get_active_window()
        
        if not window_info:
            return
        
        current_app = window_info['app_name']
        current_time = time.time()
        
        # Если приложение изменилось, отправляем предыдущую активность
        if self.current_app and self.current_app != current_app and self.start_time:
            duration = current_time - self.start_time
            
            if duration > 1:  # Минимум 1 секунда активности
                # Получаем ID приложения
                app_id = await self.get_or_create_application(self.current_app)
                
                if app_id:
                    activity = {
                        'application': app_id,  # ИСПРАВЛЯЮ: Использую ID приложения
                        'start_time': datetime.fromtimestamp(self.start_time, timezone.utc).isoformat(),
                        'end_time': datetime.fromtimestamp(current_time, timezone.utc).isoformat(),
                        'keyboard_presses': self.keyboard_presses
                    }
                    
                    success = await self.send_activity(activity)
                    if success:
                        self.activity_update.emit({
                            'app': self.current_app,
                            'duration': int(duration),
                            'keys': self.keyboard_presses
                        })
                        self.status_update.emit(f"📊 Отправлена активность: {self.current_app} ({int(duration)}с, {self.keyboard_presses} кл.)")
                    else:
                        self.status_update.emit(f"⚠️ Не удалось отправить активность для {self.current_app}")
        
        # Обновляем текущую активность
        if self.current_app != current_app:
            self.current_app = current_app
            self.start_time = current_time
            self.keyboard_presses = 0
            self.status_update.emit(f"🎯 Переключение на: {current_app}")
    
    async def main_loop(self):
        """Главный цикл отслеживания"""
        # Аутентификация с повторными попытками
        max_retries = 3
        for attempt in range(max_retries):
            if await self.authenticate():
                break
            if attempt < max_retries - 1:
                self.status_update.emit(f"🔄 Повторная попытка подключения ({attempt + 2}/{max_retries})")
                await asyncio.sleep(5)
        else:
            self.status_update.emit("❌ Не удалось подключиться к серверу")
            return
        
        # Основной цикл
        while self.running:
            try:
                await self.track_activity()
                await asyncio.sleep(self.config.get('check_interval', 5))
            except Exception as e:
                self.status_update.emit(f"⚠️ Ошибка отслеживания: {e}")
                await asyncio.sleep(10)
    
    def run(self):
        """Запуск рабочего потока"""
        self.status_update.emit("🚀 Запуск отслеживания...")
        
        # Создаем новый event loop для потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.main_loop())
        except Exception as e:
            self.status_update.emit(f"❌ Критическая ошибка: {e}")
        finally:
            loop.close()
    
    def stop(self):
        """Остановка отслеживания"""
        self.running = False
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
        self.status_update.emit("⏹️ Отслеживание остановлено")

class SettingsDialog(QDialog):
    """Диалог настроек"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("⚙️ Настройки Tracker33")
        self.setFixedSize(550, 500)  # Увеличил ширину окна
        self.setStyleSheet(ModernStyle.DARK_THEME)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)  # Больше отступов между группами
        
        # Группа подключения
        connection_group = QGroupBox("🌐 Подключение к серверу")
        connection_layout = QFormLayout()
        connection_layout.setSpacing(12)  # Отступы между полями
        connection_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText("Например: http://192.168.1.100:8001 или http://localhost:8001")
        self.server_edit.setMinimumWidth(350)  # Минимальная ширина
        
        # Добавляю кнопку автопоиска
        server_layout = QHBoxLayout()
        server_layout.addWidget(self.server_edit)
        
        auto_detect_btn = QPushButton("🔍 Найти")
        auto_detect_btn.setMaximumWidth(80)
        auto_detect_btn.clicked.connect(self.auto_detect_server)
        server_layout.addWidget(auto_detect_btn)
        
        connection_layout.addRow("Адрес сервера:", server_layout)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Ваш логин от веб-интерфейса")
        self.username_edit.setMinimumWidth(350)
        connection_layout.addRow("Пользователь:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Ваш пароль от веб-интерфейса")
        self.password_edit.setMinimumWidth(350)
        connection_layout.addRow("Пароль:", self.password_edit)
        
        # Статус подключения
        self.connection_status = QLabel("❓ Статус не проверен")
        self.connection_status.setStyleSheet("color: #cccccc; font-style: italic;")
        connection_layout.addRow("Статус:", self.connection_status)
        
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Группа отслеживания
        tracking_group = QGroupBox("📊 Параметры отслеживания")
        tracking_layout = QFormLayout()
        tracking_layout.setSpacing(10)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setSuffix(" сек")
        self.interval_spin.setMinimumWidth(120)
        tracking_layout.addRow("Интервал проверки:", self.interval_spin)
        
        self.idle_spin = QSpinBox()
        self.idle_spin.setRange(60, 3600)
        self.idle_spin.setSuffix(" сек")
        self.idle_spin.setMinimumWidth(120)
        tracking_layout.addRow("Порог простоя:", self.idle_spin)
        
        tracking_group.setLayout(tracking_layout)
        layout.addWidget(tracking_group)
        
        # Группа автозапуска
        startup_group = QGroupBox("🚀 Автозапуск")
        startup_layout = QVBoxLayout()
        startup_layout.setSpacing(8)
        
        self.autostart_check = QCheckBox("Запускать с системой")
        startup_layout.addWidget(self.autostart_check)
        
        self.minimize_check = QCheckBox("Запускать свернутым в трей")
        startup_layout.addWidget(self.minimize_check)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # Справочная информация
        help_group = QGroupBox("💡 Подсказки")
        help_layout = QVBoxLayout()
        
        help_text = QLabel(
            "• Сервер обычно работает на порту 8001\n"
            "• Используйте те же логин/пароль что и для веб-интерфейса\n"
            "• Для локального сервера: http://127.0.0.1:8001\n"
            "• Для сервера в сети: http://IP_АДРЕС:8001"
        )
        help_text.setStyleSheet("color: #999999; font-size: 10pt;")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        test_btn = QPushButton("🔍 Тест подключения")
        test_btn.clicked.connect(self.test_connection)
        buttons_layout.addWidget(test_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def load_settings(self):
        """Загрузка настроек"""
        self.server_edit.setText(self.config.get('server_url', 'http://127.0.0.1:8001'))
        self.username_edit.setText(self.config.get('username', ''))
        self.password_edit.setText(self.config.get('password', ''))
        self.interval_spin.setValue(self.config.get('check_interval', 5))
        self.idle_spin.setValue(self.config.get('idle_threshold', 300))
        self.autostart_check.setChecked(self.config.get('autostart', False))
        self.minimize_check.setChecked(self.config.get('minimize_to_tray', True))
    
    def auto_detect_server(self):
        """Автоматический поиск сервера в сети"""
        self.connection_status.setText("🔍 Поиск сервера...")
        self.connection_status.setStyleSheet("color: #00d4ff;")
        
        # Список возможных адресов для проверки
        candidates = [
            "http://127.0.0.1:8001",
            "http://localhost:8001",
        ]
        
        # Добавляем адреса локальной сети
        import socket
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            ip_base = '.'.join(local_ip.split('.')[:-1])
            
            # Проверяем несколько IP в локальной сети
            for i in [1, 100, 101, 102, 110, 200]:
                candidates.append(f"http://{ip_base}.{i}:8001")
        except:
            pass
        
        found_servers = []
        
        for url in candidates:
            try:
                import requests
                response = requests.get(f"{url}/", timeout=2)
                if response.status_code == 200 and "tracker" in response.text.lower():
                    found_servers.append(url)
            except:
                continue
        
        if found_servers:
            self.server_edit.setText(found_servers[0])
            self.connection_status.setText(f"✅ Найден: {found_servers[0]}")
            self.connection_status.setStyleSheet("color: #00ff88;")
            
            if len(found_servers) > 1:
                self.connection_status.setText(f"✅ Найдено {len(found_servers)} серверов, выбран первый")
        else:
            self.connection_status.setText("❌ Сервер не найден")
            self.connection_status.setStyleSheet("color: #ff4444;")
    
    def test_connection(self):
        """Тестирование подключения с детальной диагностикой"""
        server_url = self.server_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not server_url:
            self.connection_status.setText("❌ Укажите адрес сервера")
            self.connection_status.setStyleSheet("color: #ff4444;")
            return
        
        self.connection_status.setText("🔄 Проверка подключения...")
        self.connection_status.setStyleSheet("color: #00d4ff;")
        
        try:
            import requests
            
            # Шаг 1: Проверка доступности сервера
            try:
                response = requests.get(server_url, timeout=5)
                if response.status_code != 200:
                    self.connection_status.setText(f"❌ Сервер недоступен (код: {response.status_code})")
                    self.connection_status.setStyleSheet("color: #ff4444;")
                    return
            except requests.exceptions.ConnectionError:
                self.connection_status.setText("❌ Сервер недоступен (нет соединения)")
                self.connection_status.setStyleSheet("color: #ff4444;")
                return
            except requests.exceptions.Timeout:
                self.connection_status.setText("❌ Тайм-аут подключения")
                self.connection_status.setStyleSheet("color: #ff4444;")
                return
            
            # Шаг 2: Проверка API
            api_url = f"{server_url}/api/"
            try:
                api_response = requests.get(api_url, timeout=5)
                if api_response.status_code not in [200, 401, 403]:
                    self.connection_status.setText("❌ API недоступно")
                    self.connection_status.setStyleSheet("color: #ff4444;")
                    return
            except:
                self.connection_status.setText("❌ API не найдено")
                self.connection_status.setStyleSheet("color: #ff4444;")
                return
            
            # Шаг 3: Проверка авторизации (если указаны логин/пароль)
            if username and password:
                login_data = {
                    'username': username,
                    'password': password
                }
                
                try:
                    auth_response = requests.post(
                        f"{server_url}/api/token/",
                        json=login_data,
                        timeout=5
                    )
                    
                    if auth_response.status_code == 200:
                        response_data = auth_response.json()
                        if response_data.get('token'):
                            self.connection_status.setText("✅ Подключение успешно!")
                            self.connection_status.setStyleSheet("color: #00ff88;")
                        else:
                            self.connection_status.setText("❌ Токен не получен")
                            self.connection_status.setStyleSheet("color: #ff4444;")
                    elif auth_response.status_code == 400:
                        self.connection_status.setText("❌ Неверный логин или пароль")
                        self.connection_status.setStyleSheet("color: #ff4444;")
                    else:
                        self.connection_status.setText(f"❌ Ошибка авторизации (код: {auth_response.status_code})")
                        self.connection_status.setStyleSheet("color: #ff4444;")
                except Exception as e:
                    self.connection_status.setText(f"❌ Ошибка авторизации: {str(e)[:30]}...")
                    self.connection_status.setStyleSheet("color: #ff4444;")
            else:
                self.connection_status.setText("✅ Сервер доступен (укажите логин/пароль)")
                self.connection_status.setStyleSheet("color: #ffc107;")
                
        except ImportError:
            self.connection_status.setText("❌ Требуется модуль requests")
            self.connection_status.setStyleSheet("color: #ff4444;")
        except Exception as e:
            self.connection_status.setText(f"❌ Ошибка: {str(e)[:50]}...")
            self.connection_status.setStyleSheet("color: #ff4444;")
    
    def save_settings(self):
        """Сохранение настроек"""
        self.config['server_url'] = self.server_edit.text().strip()
        self.config['username'] = self.username_edit.text().strip()
        self.config['password'] = self.password_edit.text()
        self.config['check_interval'] = self.interval_spin.value()
        self.config['idle_threshold'] = self.idle_spin.value()
        self.config['autostart'] = self.autostart_check.isChecked()
        self.config['minimize_to_tray'] = self.minimize_check.isChecked()
        
        self.accept()

class LoginDialog(QDialog):
    """Диалог входа в систему"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход в Tracker33")
        self.setFixedSize(450, 350)
        self.setModal(True)
        
        # Результат аутентификации
        self.auth_result = None
        
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("🔐 Вход в систему")
        title.setStyleSheet("font-size: 20pt; font-weight: bold; color: #667eea; margin: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Табы для разных способов входа
        tabs = QTabWidget()
        
        # Вкладка обычного входа
        login_tab = QWidget()
        login_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя пользователя")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 14pt;
                background-color: #ffffff;
                color: #333333;
                min-width: 300px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background-color: #f8f9ff;
            }
        """)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setStyleSheet(self.username_input.styleSheet())
        
        login_layout.addRow("👤 Пользователь:", self.username_input)
        login_layout.addRow("🔒 Пароль:", self.password_input)
        
        # Кнопки для обычного входа
        login_buttons = QHBoxLayout()
        
        login_btn = QPushButton("🔑 Войти")
        login_btn.clicked.connect(self.login_with_password)
        login_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14pt;
                border: none;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
            }
        """)
        
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14pt;
                border: none;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        
        login_buttons.addWidget(login_btn)
        login_buttons.addWidget(cancel_btn)
        login_layout.addRow("", login_buttons)
        
        login_tab.setLayout(login_layout)
        tabs.addTab(login_tab, "🔑 Логин/Пароль")
        
        # Вкладка QR-кода
        qr_tab = QWidget()
        qr_layout = QVBoxLayout()
        
        qr_info = QLabel("📱 Сканируйте QR-код на веб-сайте для быстрого входа")
        qr_info.setStyleSheet("font-size: 12pt; color: #666; margin: 10px;")
        qr_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(qr_info)
        
        qr_btn = QPushButton("📷 Открыть QR-сканер")
        qr_btn.clicked.connect(self.open_qr_scanner)
        qr_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(45deg, #ff6b6b, #feca57);
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16pt;
                border: none;
                margin: 20px;
            }
            QPushButton:hover {
                background: linear-gradient(45deg, #ff5252, #ffb300);
            }
        """)
        qr_layout.addWidget(qr_btn)
        
        # Альтернативный ввод токена
        token_group = QGroupBox("✏️ Ручной ввод токена")
        token_layout = QFormLayout()
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Вставьте токен из QR-кода")
        self.token_input.setStyleSheet(self.username_input.styleSheet())
        
        token_btn = QPushButton("🔗 Подключиться")
        token_btn.clicked.connect(self.login_with_token)
        token_btn.setStyleSheet(login_btn.styleSheet())
        
        token_layout.addRow("Токен:", self.token_input)
        token_layout.addRow("", token_btn)
        
        token_group.setLayout(token_layout)
        qr_layout.addWidget(token_group)
        
        qr_tab.setLayout(qr_layout)
        tabs.addTab(qr_tab, "📱 QR-код")
        
        layout.addWidget(tabs)
        
        # Статус
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold; margin: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Enter для входа
        self.password_input.returnPressed.connect(self.login_with_password)
        self.token_input.returnPressed.connect(self.login_with_token)
        
    def login_with_password(self):
        """Вход с логином и паролем"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            self.status_label.setText("❌ Введите логин и пароль")
            return
            
        self.status_label.setText("🔄 Проверка учетных данных...")
        
        try:
            # Отправляем запрос на аутентификацию
            response = requests.post(
                "http://localhost:8000/api/token/",
                json={'username': username, 'password': password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.auth_result = {
                        'auth_token': data.get('token'),
                        'user_id': data.get('user_id'),
                        'username': data.get('username'),
                        'server_url': 'http://localhost:8000',
                        'api_url': 'http://localhost:8000/api'
                    }
                    self.accept()
                else:
                    self.status_label.setText(f"❌ {data.get('error', 'Ошибка входа')}")
            else:
                self.status_label.setText("❌ Ошибка сервера")
                
        except requests.exceptions.RequestException:
            self.status_label.setText("❌ Не удалось подключиться к серверу")
        except Exception as e:
            self.status_label.setText(f"❌ Ошибка: {e}")
            
    def open_qr_scanner(self):
        """Открытие QR-сканера"""
        try:
            qr_dialog = QRAuthDialog(self)
            qr_dialog.auth_success.connect(self.on_qr_auth_success)
            qr_dialog.exec()
        except Exception as e:
            self.status_label.setText(f"❌ Ошибка QR-сканера: {e}")
            
    def on_qr_auth_success(self, config):
        """Обработка успешной QR-аутентификации"""
        self.auth_result = config
        self.accept()
        
    def login_with_token(self):
        """Вход с токеном"""
        token = self.token_input.text().strip()
        
        if not token:
            self.status_label.setText("❌ Введите токен")
            return
            
        self.status_label.setText("🔄 Проверка токена...")
        
        try:
            # Отправляем запрос на аутентификацию с токеном
            response = requests.post(
                "http://localhost:8000/api/qr/authenticate/",
                json={'token': token, 'username': 'QR_User'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.auth_result = {
                        'auth_token': data.get('auth_token'),
                        'user_id': data.get('user_id'),
                        'username': data.get('username'),
                        'server_url': 'http://localhost:8000',
                        'api_url': 'http://localhost:8000/api'
                    }
                    self.accept()
                else:
                    self.status_label.setText(f"❌ {data.get('error', 'Неверный токен')}")
            else:
                self.status_label.setText("❌ Ошибка сервера")
                
        except requests.exceptions.RequestException:
            self.status_label.setText("❌ Не удалось подключиться к серверу")
        except Exception as e:
            self.status_label.setText(f"❌ Ошибка: {e}")

class TrackerMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Инициализация переменных
        self.config = self.load_config()
        self.auth_token = None
        self.user_id = None
        self.username = None
        
        # Проверяем аутентификацию
        if not self.check_authentication():
            # Показываем диалог входа
            login_dialog = LoginDialog(self)
            if login_dialog.exec() == QDialog.DialogCode.Accepted:
                auth_result = login_dialog.auth_result
                if auth_result:
                    # Сохраняем данные аутентификации
                    self.auth_token = auth_result['auth_token']
                    self.user_id = auth_result['user_id']
                    self.username = auth_result['username']
                    
                    # Обновляем конфигурацию
                    self.config.update({
                        'server_url': auth_result.get('server_url', 'http://localhost:8000'),
                        'api_url': auth_result.get('api_url', 'http://localhost:8000/api'),
                        'auth_token': self.auth_token,
                        'user_id': self.user_id,
                        'username': self.username
                    })
                    
                    # Сохраняем конфигурацию
                    self.save_config()
                else:
                    sys.exit(1)
            else:
                sys.exit(1)
        
        # Инициализация интерфейса
        self.init_ui()
        self.init_tray()
        
        # Запуск мониторинга
        self.start_monitoring()

    def check_authentication(self):
        """Проверка действительности аутентификации"""
        if not self.config.get('auth_token'):
            return False
            
        try:
            # Проверяем токен на сервере
            response = requests.get(
                f"{self.config.get('api_url', 'http://localhost:8000/api')}/user-profile/",
                headers={'Authorization': f"Token {self.config['auth_token']}"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.auth_token = self.config['auth_token']
                    self.user_id = data['data']['id']
                    self.username = data['data']['username']
                    return True
                    
        except Exception as e:
            print(f"Ошибка проверки аутентификации: {e}")
            
        return False

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("🚀 Tracker33 Modern Client")
        self.setFixedSize(600, 500)
        self.setStyleSheet(ModernStyle.DARK_THEME)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        title_label = QLabel("🚀 Tracker33")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        settings_btn = QPushButton("⚙️ Настройки")
        settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(settings_btn)
        
        layout.addLayout(header_layout)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)
        
        # Статус подключения
        status_group = QGroupBox("🔗 Статус подключения")
        status_layout = QVBoxLayout()
        
        self.connection_label = QLabel("❌ Не подключен")
        self.connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.connection_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Активность
        activity_group = QGroupBox("📊 Текущая активность")
        activity_layout = QGridLayout()
        
        activity_layout.addWidget(QLabel("Приложение:"), 0, 0)
        self.app_label = QLabel("Нет данных")
        activity_layout.addWidget(self.app_label, 0, 1)
        
        activity_layout.addWidget(QLabel("Время:"), 1, 0)
        self.time_label = QLabel("00:00:00")
        activity_layout.addWidget(self.time_label, 1, 1)
        
        activity_layout.addWidget(QLabel("Нажатий клавиш:"), 2, 0)
        self.keys_label = QLabel("0")
        activity_layout.addWidget(self.keys_label, 2, 1)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        # Лог активности
        log_group = QGroupBox("📝 Журнал событий")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Кнопки управления
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Запустить")
        self.start_btn.clicked.connect(self.start_tracking)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Остановить")
        self.stop_btn.clicked.connect(self.stop_tracking)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()
        
        minimize_btn = QPushButton("📦 В трей")
        minimize_btn.clicked.connect(self.hide)
        controls_layout.addWidget(minimize_btn)
        
        layout.addLayout(controls_layout)
        
        central_widget.setLayout(layout)
        
        # Добавляем текст в лог
        self.add_log("🚀 Tracker33 Modern Client запущен")
        
        if not self.config.get('username'):
            self.add_log("⚙️ Требуется настройка. Откройте настройки для конфигурации.")
    
    def create_tray_icon(self):
        """Создание иконки в системном трее"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.add_log("❌ Системный трей недоступен")
            return
        
        # Создаем простую иконку
        self.tray_icon = QSystemTrayIcon(self)
        
        # Создаем контекстное меню
        tray_menu = QMenu()
        
        show_action = QAction("📊 Показать", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        settings_action = QAction("⚙️ Настройки", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("❌ Выход", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Создаем простую иконку программно
        icon = self.create_icon()
        self.tray_icon.setIcon(icon)
        
        self.tray_icon.show()
        self.add_log("📦 Иконка в системном трее создана")
    
    def create_icon(self):
        """Создание простой иконки"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setBrush(Qt.GlobalColor.blue)
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        
        return QIcon(pixmap)
    
    def tray_icon_activated(self, reason):
        """Обработка клика по иконке в трее"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
                self.raise_()
    
    def load_config(self) -> dict:
        """Загрузка конфигурации"""
        config_file = Path("config.json")
        default_config = {
            'server_url': 'http://127.0.0.1:8001',
            'username': '',
            'password': '',
            'check_interval': 5,
            'idle_threshold': 300,
            'autostart': False,
            'minimize_to_tray': True
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Объединяем с настройками по умолчанию
                    default_config.update(config)
                    return default_config
            except Exception as e:
                print(f"⚠️ Ошибка загрузки конфигурации: {e}")
        else:
            # При первом запуске пытаемся найти сервер автоматически
            self.auto_detect_initial_server(default_config)
        
        return default_config
    
    def auto_detect_initial_server(self, config):
        """Автопоиск сервера при первом запуске"""
        try:
            import requests
            
            # Проверяем локальные адреса
            candidates = [
                "http://127.0.0.1:8001",
                "http://localhost:8001",
            ]
            
            for url in candidates:
                try:
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200 and "tracker" in response.text.lower():
                        config['server_url'] = url
                        print(f"✅ Автоматически найден сервер: {url}")
                        break
                except:
                    continue
        except:
            pass
    
    def save_config(self):
        """Сохранение конфигурации"""
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.add_log(f"❌ Ошибка сохранения: {e}")
    
    def add_log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Автопрокрутка
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def open_settings(self):
        """Открытие диалога настроек"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.config = dialog.config
            self.save_config()
            self.add_log("💾 Настройки сохранены")
            
            # Перезапуск отслеживания если оно было активно
            if self.worker and self.worker.isRunning():
                self.stop_tracking()
                self.start_tracking()
    
    def start_tracking(self):
        """Запуск отслеживания"""
        if not self.config.get('username') or not self.config.get('password'):
            self.add_log("⚠️ Не заданы учетные данные. Откройте настройки.")
            self.open_settings()
            return
        
        if self.worker and self.worker.isRunning():
            self.add_log("⚠️ Отслеживание уже запущено")
            return
        
        self.worker = TrackerWorker(self.config)
        self.worker.status_update.connect(self.add_log)
        self.worker.connection_status.connect(self.update_connection_status)
        self.worker.activity_update.connect(self.update_activity)
        
        self.worker.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.add_log("🚀 Запуск отслеживания...")
    
    def stop_tracking(self):
        """Остановка отслеживания"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(5000)  # Ждем 5 секунд
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.update_connection_status(False)
        self.add_log("⏹️ Отслеживание остановлено")
    
    def update_connection_status(self, connected: bool):
        """Обновление статуса подключения"""
        if connected:
            self.connection_label.setText("✅ Подключен")
            self.connection_label.setStyleSheet("color: #00ff88;")
        else:
            self.connection_label.setText("❌ Не подключен")
            self.connection_label.setStyleSheet("color: #ff4444;")
    
    def update_activity(self, activity: dict):
        """Обновление информации об активности"""
        self.app_label.setText(activity.get('app', 'Неизвестно'))
        self.keys_label.setText(str(activity.get('keys', 0)))
        
        # Обновляем время (здесь можно добавить счетчик времени)
        duration = activity.get('duration', 0)
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.config.get('minimize_to_tray', True) and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "Tracker33",
                    "Приложение свернуто в трей",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        else:
            self.quit_application()
    
    def quit_application(self):
        """Полное завершение приложения"""
        self.add_log("🛑 Завершение работы...")
        self.stop_tracking()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        QApplication.quit()

class TrackerApp(QApplication):
    """Главный класс приложения"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        
        # Проверяем единственность экземпляра
        self.setApplicationName("Tracker33")
        self.setApplicationVersion("2.1")
        
        # Применяем темную тему
        self.setStyleSheet(ModernStyle.DARK_THEME)
    
    def create_main_window(self):
        """Создание главного окна"""
        self.main_window = TrackerMainWindow()
        
        # Показываем окно (убрал автоскрытие!)
        self.main_window.show()
        
        return self.main_window

def main():
    """Точка входа"""
    app = TrackerApp(sys.argv)
    
    # Создаем главное окно
    main_window = app.create_main_window()
    
    # Запускаем приложение
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 