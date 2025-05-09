import sys
import json
import requests
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QListWidget, QLineEdit, QCheckBox,
                           QMessageBox, QSystemTrayIcon, QMenu, QAction, QDialog,
                           QFormLayout, QDialogButtonBox, QStatusBar, QProgressBar,
                           QTabWidget, QListWidgetItem, QScrollArea, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QComboBox, QFrame)
from PyQt5.QtCore import QTimer, Qt, QUrl, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QDesktopServices
import psutil
from pynput import keyboard, mouse
import pygetwindow as gw
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path
import configparser
import os
import threading
from logging.handlers import RotatingFileHandler
import queue
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
import webbrowser
import re
import warnings
import random
import string
import win32gui
import win32process
import jwt

def get_base_path():
    """Получение базового пути к ресурсам"""
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return Path(base_path)

# Настройка логирования
def setup_logging():
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / 'tracker.log'
    
    # Настройка ротации логов (5 файлов по 1MB каждый)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger('TimeTracker')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# Импортируем APIClient из api_client.py вместо использования встроенного класса
from .api_client import APIClient

# Этот класс больше не используется, но оставлен для совместимости с существующим кодом
# который может ссылаться на него
class _LegacyAPIClient:
    """Класс для взаимодействия с API сервера (устаревший)"""
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        self.app_cache = {}  # Кэш для хранения сопоставления имен приложений и их ID
        # Настройка сессии
        self.session.headers.update({
            'User-Agent': 'TimeTrackerDesktopClient/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
    def login(self, username, password):
        """Авторизация на сервере"""
        try:
            # Выполняем реальный запрос к API для получения токена
            logger.info(f"Попытка авторизации на сервере {self.base_url} с логином {username}")
            
            # Формируем URL для авторизации
            # Убираем возможные двойные слеши в URL
            auth_url = f"{self.base_url.rstrip('/')}/api/token/"
            logger.info(f"Авторизация на URL: {auth_url}")
            
            # Отправляем запрос на получение токена
            response = requests.post(
                auth_url,
                json={
                    'username': username,
                    'password': password
                },
                headers={
                    'Content-Type': 'application/json'
                }
            )
            
            # Проверяем ответ
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                # Устанавливаем токен в заголовки сессии
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                logger.info("Успешная авторизация на сервере")
                
                # После успешной авторизации получаем список приложений
                self.get_applications()
                
                return True, self.token
            else:
                error_msg = f"Ошибка авторизации: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg
        except Exception as e:
            logger.error(f"Ошибка при авторизации: {e}")
            return False, str(e)
            
    def get_applications(self):
        """Получение списка приложений с сервера"""
        try:
            # Убираем возможные двойные слеши в URL
            url = f"{self.base_url.rstrip('/')}/api/applications/"
            logger.info(f"Получение списка приложений с URL: {url}")
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                applications = response.json()
                # Сохраняем сопоставление имен приложений и их ID
                for app in applications:
                    app_id = app.get('id')
                    process_name = app.get('process_name', '').lower()
                    name = app.get('name', '').lower()
                    
                    # Сохраняем в кэше по разным ключам
                    if process_name:
                        # Извлекаем только имя файла без пути
                        base_name = os.path.basename(process_name).lower()
                        self.app_cache[base_name] = app_id
                        
                    if name:
                        self.app_cache[name] = app_id
                        
                logger.info(f"Загружено {len(applications)} приложений с сервера")
                return applications
            else:
                logger.error(f"Ошибка при получении приложений: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении приложений: {e}")
            return []
            
    def get_application_id(self, app_name):
        """Получение ID приложения по его имени"""
        if not app_name:
            return None
            
        # Приводим к нижнему регистру для сравнения
        app_name_lower = app_name.lower()
        
        # Проверяем точное совпадение
        if app_name_lower in self.app_cache:
            return self.app_cache[app_name_lower]
            
        # Проверяем частичное совпадение
        for cached_name, app_id in self.app_cache.items():
            if app_name_lower in cached_name or cached_name in app_name_lower:
                return app_id
                
        # Если не нашли совпадений, пробуем получить свежий список приложений
        if not self.app_cache:
            self.get_applications()
            # Повторяем поиск после обновления кэша
            return self.get_application_id(app_name)
            
        # Если ничего не нашли, возвращаем первый доступный ID или None
        return next(iter(self.app_cache.values()), None)

    def send_activities(self, activities):
        """Отправка данных о активности на сервер"""
        if not self.token:
            return False, "Нет токена авторизации"
            
        try:
            # Убираем возможные двойные слеши в URL
            api_url = f"{self.base_url.rstrip('/')}/api/activities/"
            logger.info(f"Отправка данных активности на URL: {api_url}")
            response = self.session.post(
                api_url,
                json=activities
            )
            
            if response.status_code in [200, 201]:
                return True, response.json()
            else:
                return False, response.text
        except Exception as e:
            logger.error(f"Ошибка при отправке активностей: {e}")
            return False, str(e)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Авторизация")
        self.api_client = None
        
        # Запрещаем закрытие диалога крестиком
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        
        # Флаг, определяющий, могут ли пользователи изменять URL сервера
        self.allow_close_without_auth = False
        
        # Чтение последнего использованного URL из конфигурации
        self.last_server_url = "http://127.0.0.1:8000"
        parent_app = self.parent()
        if parent_app and hasattr(parent_app, 'config'):
            config = parent_app.config
            if config.has_section('Credentials') and config.has_option('Credentials', 'api_base_url'):
                base_url = config.get('Credentials', 'api_base_url')
                self.last_server_url = base_url.rstrip('/api/')
            elif config.has_section('Server') and config.has_option('Server', 'base_url'):
                self.last_server_url = config.get('Server', 'base_url')
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        
        # Добавляем информационный текст
        info_label = QLabel("Перед началом работы необходимо указать адрес сервера и авторизоваться.\nЕсли сервер находится на этом же компьютере, используйте адрес: http://127.0.0.1:8000")
        info_label.setWordWrap(True)
        layout.addRow(info_label)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addRow(line)
        
        self.server_url = QLineEdit()
        self.server_url.setText(self.last_server_url)
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        
        # Checkbox для разрешения работы в оффлайн-режиме (только для отладки)
        self.offline_mode_checkbox = QCheckBox("Разрешить работу в оффлайн-режиме")
        self.offline_mode_checkbox.setChecked(False)
        self.offline_mode_checkbox.stateChanged.connect(self.toggle_offline_mode)
        
        layout.addRow("URL сервера:", self.server_url)
        layout.addRow("Имя пользователя:", self.username)
        layout.addRow("Пароль:", self.password)
        layout.addRow(self.offline_mode_checkbox)
        
        # Кнопка проверки подключения
        self.test_button = QPushButton("Проверить подключение к серверу")
        self.test_button.clicked.connect(self.test_connection)
        layout.addRow(self.test_button)
        
        # Кнопки действий
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.authenticate)
        buttons.rejected.connect(self.reject)
        self.buttons = buttons
        
        layout.addRow(buttons)
        self.setLayout(layout)
    
    def toggle_offline_mode(self, state):
        """Включает/выключает возможность работы в оффлайн-режиме"""
        self.allow_close_without_auth = state == Qt.Checked
        if state == Qt.Checked:
            self.username.setEnabled(False)
            self.password.setEnabled(False)
            self.buttons.button(QDialogButtonBox.Ok).setText("Продолжить без авторизации")
        else:
            self.username.setEnabled(True)
            self.password.setEnabled(True)
            self.buttons.button(QDialogButtonBox.Ok).setText("OK")
    
    def closeEvent(self, event):
        """Переопределяем обработку закрытия окна для предотвращения закрытия без авторизации"""
        if self.allow_close_without_auth:
            event.accept()
        else:
            # Показываем сообщение, что авторизация обязательна
            QMessageBox.critical(self, "Требуется авторизация", 
                                "Для работы приложения требуется авторизация!\n\n"
                                "Если вы не можете подключиться к серверу, включите оффлайн-режим.")
            event.ignore()
    
    def test_connection(self):
        """Проверяет подключение к серверу"""
        server_url = self.server_url.text().strip()
        
        if not server_url:
            QMessageBox.warning(self, "Ошибка", "Введите URL сервера")
            return
        
        # Если URL не содержит протокол, добавляем http://
        if not server_url.startswith('http://') and not server_url.startswith('https://'):
            server_url = 'http://' + server_url
            self.server_url.setText(server_url)
        
        try:
            # Добавляем таймаут для соединения
            response = requests.get(f"{server_url}/api/", timeout=5)
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", f"Подключение к серверу {server_url} успешно установлено!")
            else:
                QMessageBox.warning(self, "Предупреждение", 
                                   f"Сервер доступен, но вернул код {response.status_code}. "
                                   f"API может быть недоступно.")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Ошибка соединения", 
                               f"Не удалось установить соединение с сервером {server_url}. "
                               f"Проверьте, что сервер запущен и URL указан правильно.")
        except requests.exceptions.Timeout:
            QMessageBox.critical(self, "Таймаут соединения", 
                               f"Превышено время ожидания ответа от сервера {server_url}.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при проверке соединения: {str(e)}")
        
    def authenticate(self):
        # Если включен оффлайн-режим, просто продолжаем без авторизации
        if self.offline_mode_checkbox.isChecked():
            parent_app = self.parent()
            if parent_app and hasattr(parent_app, 'config'):
                config = parent_app.config
                if not config.has_section('Settings'):
                    config.add_section('Settings')
                
                # Включаем демо-режим
                config.set('Settings', 'demo_mode', 'True')
                
                # Сохраняем URL сервера для будущего использования
                if not config.has_section('Credentials'):
                    config.add_section('Credentials')
                config.set('Credentials', 'api_base_url', self.server_url.text().strip())
                
                # Сохраняем конфигурацию
                parent_app._save_config(config)
                logger.info("Приложение работает в оффлайн-режиме")
            
            self.accept()
            return
            
        server_url = self.server_url.text().strip()
        username = self.username.text().strip()
        password = self.password.text()
        
        if not all([server_url, username, password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
            
        # Если URL не содержит протокол, добавляем http://
        if not server_url.startswith('http://') and not server_url.startswith('https://'):
            server_url = 'http://' + server_url
            self.server_url.setText(server_url)
        
        # Создаем APIClient с таймаутом
        self.api_client = APIClient(server_url)
        
        try:
            # Отключаем кнопки на время авторизации
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)
            self.buttons.button(QDialogButtonBox.Cancel).setEnabled(False)
            self.test_button.setEnabled(False)
            QApplication.processEvents()  # Обновляем UI
            
            # Пытаемся авторизоваться - вызываем метод login вместо authenticate
            success, token = self.api_client.login(username, password)
            
            if success:
                # Сохраняем токен и данные пользователя в конфигурации
                # Получаем доступ к объекту конфигурации через родительское окно
                parent_app = self.parent()
                if parent_app and hasattr(parent_app, 'config'):
                    config = parent_app.config
                    if not config.has_section('Credentials'):
                        config.add_section('Credentials')
                    
                    # Сохраняем токен и данные пользователя
                    config.set('Credentials', 'api_base_url', server_url.rstrip('/') + '/api/')
                    config.set('Credentials', 'auth_token', self.api_client.token)
                    config.set('Credentials', 'username', username)
                    
                    # Получаем user_id из токена
                    user_id = "1"  # Значение по умолчанию
                    try:
                        # Декодируем токен для получения user_id
                        token_data = jwt.decode(self.api_client.token, options={"verify_signature": False})
                        if "user_id" in token_data:
                            user_id = str(token_data["user_id"])
                    except Exception as e:
                        logger.warning(f"Не удалось извлечь user_id из токена: {e}")
                        
                    config.set('Credentials', 'user_id', user_id)
                    
                    # Отключаем демо-режим после успешной авторизации
                    if not config.has_section('Settings'):
                        config.add_section('Settings')
                    config.set('Settings', 'demo_mode', 'False')
                    
                    # Сохраняем конфигурацию
                    parent_app._save_config(config)
                    logger.info("Токен авторизации успешно сохранен в конфигурации.")
                
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверные учетные данные или проблемы с сервером")
                # Включаем кнопки обратно
                self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
                self.buttons.button(QDialogButtonBox.Cancel).setEnabled(True)
                self.test_button.setEnabled(True)
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Ошибка соединения", 
                               f"Не удалось установить соединение с сервером {server_url}. "
                               f"Проверьте, что сервер запущен и URL указан правильно.")
            # Включаем кнопки обратно
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
            self.buttons.button(QDialogButtonBox.Cancel).setEnabled(True)
            self.test_button.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Проблема при авторизации: {e}")
            # Включаем кнопки обратно
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
            self.buttons.button(QDialogButtonBox.Cancel).setEnabled(True)
            self.test_button.setEnabled(True)

class TimeTrackerApp(QMainWindow):
    # Сигналы для взаимодействия с GUI из других потоков
    activity_processed = pyqtSignal(dict)
    update_status_signal = pyqtSignal(str)
    login_required_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Инициализация путей и базовой конфигурации до UI
        self.config_path = Path(get_base_path()) / 'config.ini'
        self.config = self.load_config() 

        # Инициализация session и других атрибутов, зависящих от config
        self.session = requests.Session()
        self.api_base_url = self.config.get('Credentials', 'api_base_url', fallback='http://localhost:8000/api/') 
        self.user_id = self.config.get('Credentials', 'user_id', fallback=None)
        auth_token = self.config.get('Credentials', 'auth_token', fallback=None)
        if auth_token:
            self.session.headers.update({'Authorization': f'Bearer {auth_token}'})
        
        # machine_id теперь должен быть корректно загружен или создан в self.load_config()
        # и сохранен в self.config
        self.machine_id = self.config.get('Settings', 'machine_id') 
        if not self.machine_id:
            # Эта ситуация не должна возникать, если load_config и get_machine_id работают правильно,
            # но на всякий случай добавим лог и попытку пересоздать
            logger.error("КРИТИЧЕСКАЯ ОШИБКА: machine_id отсутствует в конфигурации ПОСЛЕ вызова load_config. Попытка исправить.")
            self.machine_id = self.get_machine_id(self.config) 
            if not self.machine_id: 
                logger.critical("Не удалось установить machine_id! Приложение может работать некорректно.")
                # Можно рассмотреть вариант с генерацией временного ID или прерыванием работы
                self.machine_id = "error_machine_id_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

        # Очередь для активностей
        self.activity_queue = queue.Queue()

        # Атрибуты для отслеживания состояния
        self.current_activity_data = None 
        self.activity_start_time = None 
        self.last_activity_time = time.time() 
        self.idle_threshold_seconds = self.config.getint('Settings', 'idle_threshold_seconds', fallback=300)
        self.is_idle = False 
        self.keyboard_press_count = 0  # Счетчик нажатий клавиш
        # self.active_window_details = {'app_name': '', 'window_title': ''} # Этот атрибут больше не используется
        
        # Кэш для хранения соответствия имен приложений и их ID на сервере
        self.app_cache = {}
        
        # Конфигурация отслеживаемых приложений и игнорируемых процессов
        self.tracked_applications_config = {} 
        # Расширенный список игнорируемых системных процессов
        self.ignored_processes = [
            # Системные процессы Windows
            'explorer.exe', 'dllhost.exe', 'ShellExperienceHost.exe', 'SearchUI.exe', 'LockApp.exe', 'System Idle Process',
            'svchost.exe', 'csrss.exe', 'smss.exe', 'wininit.exe', 'services.exe', 'lsass.exe', 'winlogon.exe',
            'fontdrvhost.exe', 'dwm.exe', 'taskhostw.exe', 'sihost.exe', 'ctfmon.exe', 'conhost.exe', 'rundll32.exe',
            'RuntimeBroker.exe', 'WmiPrvSE.exe', 'spoolsv.exe', 'SearchIndexer.exe', 'audiodg.exe', 'dasHost.exe',
            # Службы и процессы Intel
            'igfxCUIService.exe', 'igfxEM.exe', 'igfxHK.exe', 'igfxTray.exe', 'IntelCpHDCPSvc.exe', 'IntelCpHeciSvc.exe',
            # Службы и процессы NVIDIA
            'nvvsvc.exe', 'nvxdsync.exe', 'NVDisplay.Container.exe', 'nvtray.exe',
            # Другие системные службы
            'AggregatorHost.exe', 'ApplicationFrameHost.exe', 'BTSystemService.exe', 'CrossDeviceService.exe',
            'DDVCollectorSvcApi.exe', 'DDVDataCollector.exe', 'DDVRulesProcessor.exe', 'GameManagerService.exe',
            'HPNetworkCommunicator.exe', 'Integration.Service.exe', 'IntelCpHDCPSvc.exe', 'IntelCpHeciSvc.exe',
            'Licensing.Service.exe', 'LocationNotificationWindows.exe', 'Lsalso.exe', 'Maestro.Service.exe',
            'MemCompression', 'MpDefenderCoreService.exe', 'MsMpEng.exe', 'NVDisplay.Container.exe',
            'Registry', 'SecurityHealthService.exe', 'SgrmBroker.exe', 'System', 'SystemSettings.exe',
            'TextInputHost.exe', 'UserOOBEBroker.exe', 'WUDFHost.exe', 'WerFault.exe', 'WindowsInternal.ComposableShell',
            'YourPhone.exe', 'armsvc.exe', 'esif_assist_64.exe', 'esif_uf.exe', 'jhi_service.exe', 'mDNSResponder.exe',
            'sqlwriter.exe', 'unsecapp.exe', 'wsappx', 'wuauclt.exe'
        ]
        self.load_tracked_applications_config() 
        
        # Состояние паузы отслеживания
        self.tracking_paused = False
        self.pause_action = None # Для QAction в меню трея
        
        # Другие таймеры
        self.update_app_list_timer = QTimer(self)
        self.update_app_list_timer.timeout.connect(self.update_app_list)
        self.update_app_list_timer.start(10000)  # Обновляем список каждые 10 секунд

        self.check_connection_timer = QTimer(self)
        self.check_connection_timer.timeout.connect(self.check_connection)
        self.check_connection_timer.start(30000)

        # Уменьшаем интервал отправки для работы в режиме реального времени
        send_interval_seconds = self.config.getint('Settings', 'send_interval_seconds', fallback=10) # Уменьшаем до 10 секунд по умолчанию
        self.send_data_timer = QTimer(self)
        self.send_data_timer.timeout.connect(self.send_activity_data) 
        self.send_data_timer.start(send_interval_seconds * 1000)
        
        # Сохраняем новый интервал в конфигурацию
        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
        self.config.set('Settings', 'send_interval_seconds', str(send_interval_seconds))
        self._save_config(self.config)

        # UI инициализируется после базовой настройки
        # self.tracker = TimeTracker() 
        self.init_ui() 
        self.init_tray_icon() 
        
        # Настройка слушателей и основного таймера трекинга
        self.setup_activity_listeners_and_tracking_timer() 
        
        # Подключаем сигнал для повторной авторизации
        self.login_required_signal.connect(self.show_login_dialog_if_needed)

        # Таймер для периодического обновления интерфейса
        self.update_ui_timer = QTimer(self)
        self.update_ui_timer.timeout.connect(self.periodic_ui_update)
        self.update_ui_timer.start(1000)  # Обновляем интерфейс каждую секунду

        if not auth_token:
             # Используем QTimer.singleShot для вызова диалога логина после инициализации основного окна
             QTimer.singleShot(0, self.show_login_dialog_if_needed)

    def load_config(self) -> configparser.ConfigParser:
        """Загружает конфигурацию из файла или создает новую, если файл отсутствует/поврежден."""
        config = configparser.ConfigParser()
        if self.config_path.exists() and self.config_path.is_file():
            try:
                config.read(self.config_path, encoding='utf-8')
                logger.info(f"Конфигурация успешно загружена из {self.config_path}")
                # Проверка на наличие machine_id и его генерация при необходимости
                if not config.has_section('Settings') or \
                   not config.has_option('Settings', 'machine_id') or \
                   not config.get('Settings', 'machine_id'):
                    logger.warning("'machine_id' не найден или пуст в конфигурации. Генерирую новый.")
                    _ = self.get_machine_id(config) # Передаем текущий объект config
                    self._save_config(config) # Сохраняем после обновления machine_id
            except configparser.Error as e:
                logger.error(f"Ошибка чтения конфигурационного файла {self.config_path}: {e}. Создается новый файл.", exc_info=True)
                config = self.create_default_config()
                self.get_machine_id(config)
                self._save_config(config)
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при загрузке конфигурации {self.config_path}: {e}. Создается новый файл.", exc_info=True)
                config = self.create_default_config()
                self.get_machine_id(config)
                self._save_config(config)
        else:
            logger.warning(f"Конфигурационный файл {self.config_path} не найден. Создается новый.")
            config = self.create_default_config()
            self.get_machine_id(config)
            self._save_config(config)

        # Гарантируем наличие основных секций
        default_sections = {
            'Credentials': self.create_default_config().items('Credentials'),
            'Settings': self.create_default_config().items('Settings'),
            'Applications': self.create_default_config().items('Applications')
        }
        
        made_changes_to_config = False
        for section_name, default_items in default_sections.items():
            if not config.has_section(section_name):
                logger.warning(f"Секция [{section_name}] отсутствует в конфигурации. Добавляю стандартную.")
                config.add_section(section_name)
                made_changes_to_config = True
            
            for key, value in default_items:
                if not config.has_option(section_name, key):
                    logger.warning(f"Опция {key} отсутствует в секции [{section_name}]. Добавляю значение по умолчанию: {value}")
                    config.set(section_name, key, value)
                    made_changes_to_config = True
        
        if made_changes_to_config:
            self._save_config(config)
            
        return config
        
    def get_machine_id(self, current_config: configparser.ConfigParser) -> str:
        """Получает или генерирует уникальный ID машины."""
        if current_config.has_section('Settings') and current_config.has_option('Settings', 'machine_id'):
            machine_id = current_config.get('Settings', 'machine_id')
            if machine_id:
                return machine_id
                
        # Генерация нового идентификатора
        machine_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        
        logger.info(f"Сгенерирован новый machine_id: {machine_id}")
        
        # Сохранение в конфигурацию
        if not current_config.has_section('Settings'):
            current_config.add_section('Settings')
        current_config.set('Settings', 'machine_id', machine_id)
        
        return machine_id
        
    def create_default_config(self) -> configparser.ConfigParser:
        """Создает конфигурацию по умолчанию."""
        config = configparser.ConfigParser()
        
        # Секция Credentials - для данных авторизации
        config.add_section('Credentials')
        config.set('Credentials', 'api_base_url', 'http://localhost:8000/api/')
        config.set('Credentials', 'username', '')
        config.set('Credentials', 'auth_token', '')
        config.set('Credentials', 'user_id', '')
        
        # Секция Settings - для настроек приложения
        config.add_section('Settings')
        config.set('Settings', 'machine_id', '')  # Будет установлен отдельно
        config.set('Settings', 'idle_threshold_seconds', '300')  # 5 минут по умолчанию
        config.set('Settings', 'send_interval_seconds', '10')   # 10 секунд по умолчанию
        config.set('Settings', 'max_send_batch_size', '20')     # До 20 записей за раз
        config.set('Settings', 'demo_mode', 'False')            # Демо-режим выключен по умолчанию
        
        # Секция Applications - для списка отслеживаемых приложений
        config.add_section('Applications')
        
        return config
        
    def _save_config(self, config_object_to_save: Optional[configparser.ConfigParser] = None):
        """Сохраняет конфигурацию в файл."""
        try:
            # Проверяем, был ли передан отдельный объект конфигурации
            config_to_save = config_object_to_save if config_object_to_save else self.config
            
            with open(self.config_path, 'w', encoding='utf-8') as config_file:
                config_to_save.write(config_file)
            logger.info(f"Конфигурация успешно сохранена в {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении конфигурации: {e}", exc_info=True)
            return False
            
    def load_tracked_applications_config(self):
        """Загружает конфигурацию отслеживаемых приложений."""
        self.tracked_applications_config = {}
        if self.config.has_section('Applications'):
            for key, value in self.config.items('Applications'):
                # Приводим "True"/"False" к булевому типу
                is_useful = value.lower() in ['true', 'yes', '1']
                self.tracked_applications_config[key.lower()] = is_useful
        logger.info(f"Загружено {len(self.tracked_applications_config)} отслеживаемых приложений.")

    def setup_activity_listeners_and_tracking_timer(self):
        # Настройка слушателей и основного таймера трекинга
        self.keyboard_listener = keyboard.Listener(on_press=self.on_keyboard_press)
        self.mouse_listener = mouse.Listener(on_move=self.on_mouse_move, on_click=self.on_mouse_click)
        
        # Запускаем слушатели
        self.keyboard_listener.start()
        self.mouse_listener.start()
        
        # Запускаем поток отслеживания активности
        self.process_activity_thread = threading.Thread(target=self.track_activity, daemon=True)
        self.process_activity_thread.start()
        
        # Таймер для проверки простоя
        self.idle_check_timer = QTimer(self)
        self.idle_check_timer.timeout.connect(self.check_idle_state)
        self.idle_check_timer.start(5000)  # Проверяем каждые 5 секунд
        
    def on_keyboard_press(self, key):
        """Обработчик нажатия клавиш."""
        try:
            # Обновляем время последней активности
            self.last_activity_time = time.time()
            
            # Если состояние было "простой", меняем на "активно"
            if self.is_idle:
                self.is_idle = False
                logger.info("Пользователь снова активен (нажатие клавиши)")
                
            # Увеличиваем счетчик нажатий для текущей активности
            self.keyboard_press_count += 1
            
            # Добавляем отладочную информацию, если нужно
            # logger.debug(f"Нажата клавиша: {key}. Всего нажатий: {self.keyboard_press_count}")
        except Exception as e:
            logger.error(f"Ошибка при обработке нажатия клавиши: {e}", exc_info=True)
    
    def on_mouse_move(self, x, y):
        """Обработчик движения мыши."""
        try:
            # Обновляем время последней активности
            self.last_activity_time = time.time()
            
            # Если состояние было "простой", меняем на "активно"
            if self.is_idle:
                self.is_idle = False
                logger.info("Пользователь снова активен (движение мыши)")
        except Exception as e:
            logger.error(f"Ошибка при обработке движения мыши: {e}", exc_info=True)
    
    def on_mouse_click(self, x, y, button, pressed):
        """Обработчик кликов мыши."""
        try:
            if pressed:  # Обрабатываем только нажатия, не отпускания
                # Обновляем время последней активности
                self.last_activity_time = time.time()
                
                # Если состояние было "простой", меняем на "активно"
                if self.is_idle:
                    self.is_idle = False
                    logger.info("Пользователь снова активен (клик мыши)")
        except Exception as e:
            logger.error(f"Ошибка при обработке клика мыши: {e}", exc_info=True)
    
    def check_idle_state(self):
        """Проверяет, находится ли пользователь в состоянии простоя."""
        try:
            current_time = time.time()
            idle_time = current_time - self.last_activity_time
            
            # Если превышен порог и пользователь еще не считается неактивным
            if idle_time > self.idle_threshold_seconds and not self.is_idle:
                self.is_idle = True
                logger.info(f"Пользователь неактивен (прошло {idle_time:.1f} секунд)")
                
                # Если есть текущая сессия активности, завершаем ее
                if self.current_activity_data:
                    self.end_current_activity_session(event_type="idle")
                    
                # Обновляем UI
                self.status_bar.showMessage("Пользователь неактивен")
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.setToolTip("Пользователь неактивен")
            
            # Если пользователь стал активен, но считается неактивным
            elif idle_time <= self.idle_threshold_seconds and self.is_idle:
                self.is_idle = False
                logger.info("Пользователь снова активен")
                
                # Обновляем UI
                self.status_bar.showMessage("Пользователь активен")
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.setToolTip("Пользователь активен")
        except Exception as e:
            logger.error(f"Ошибка при проверке состояния простоя: {e}", exc_info=True)
    
    def track_activity(self):
        """Основной метод отслеживания активности в отдельном потоке."""
        logger.info("Запущен поток отслеживания активности")
        
        # Задержка перед началом отслеживания, чтобы дать время на инициализацию UI
        time.sleep(1)
        
        # Инициализируем переменные для отслеживания текущего активного окна
        current_app_name = None
        current_window_title = None
        
        while True:
            try:
                # Если отслеживание на паузе, пропускаем итерацию
                if self.tracking_paused:
                    time.sleep(1)
                    continue
                
                # Получаем информацию о текущем активном окне
                active_window_info = self.get_active_window_info()
                
                if not active_window_info:
                    # Если не удалось получить информацию, ждем и пробуем снова
                    time.sleep(1)
                    continue
                
                app_name = active_window_info.get('app_name', '')
                window_title = active_window_info.get('window_title', '')
                
                # Проверяем, является ли приложение игнорируемым системным процессом
                if app_name.lower() in (proc.lower() for proc in self.ignored_processes):
                    # Если это игнорируемый процесс, и у нас есть текущая сессия активности,
                    # завершаем ее только если она не относится к тому же игнорируемому процессу
                    if self.current_activity_data:
                        if self.current_activity_data['app_name'].lower() != app_name.lower():
                            logger.debug(f"Обнаружен игнорируемый процесс: {app_name}. Завершаем текущую сессию.")
                            self.end_current_activity_session(event_type="ignored_process")
                    time.sleep(1)
                    continue
                
                # Если это система или пустое имя, пропускаем итерацию
                if not app_name or app_name.lower() in ['system', 'system idle process']:
                    time.sleep(1)
                    continue
                
                # Если приложение изменилось
                if app_name != current_app_name or window_title != current_window_title:
                    logger.debug(f"Изменилось активное окно: {app_name} ({window_title})")
                    
                    # Проверяем, является ли приложение полезным согласно конфигурации
                    is_useful = self.is_app_useful(app_name)
                    
                    # Если текущая сессия существует, завершаем ее
                    if self.current_activity_data:
                        self.end_current_activity_session(event_type="switch")
                    
                    # Начинаем новую сессию
                    if not self.is_idle:  # Только если пользователь активен
                        self.start_new_activity_session(app_name, window_title, is_useful)
                    
                    # Обновляем текущие значения
                    current_app_name = app_name
                    current_window_title = window_title
                    
                    # Обновляем информацию о текущей активности в UI
                    if hasattr(self, 'current_app_label'):
                        self.update_status_signal.emit(f"Отслеживается: {app_name}")
                
                # Ждем перед следующей проверкой
                time.sleep(1)
            except Exception as e:
                logger.error(f"Ошибка в потоке отслеживания активности: {e}", exc_info=True)
                time.sleep(5)  # В случае ошибки увеличиваем задержку
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle('Time Tracker PRO') 
        self.setGeometry(100, 100, 800, 600)

        # Предотвращаем одновременный запуск нескольких диалогов авторизации
        self._login_dialog = None
        self._login_dialog_active = False

        # Основной виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Статус подключения
        self.connection_status = QLabel("Статус подключения: Проверка...")
        self.connection_status.setStyleSheet("QLabel { color: gray; }")
        layout.addWidget(self.connection_status)

        # Кнопка открытия веб-интерфейса
        web_button = QPushButton("Открыть веб-интерфейс")
        web_button.clicked.connect(self.open_web_interface)
        layout.addWidget(web_button)

        # Текущая активность
        activity_group = QWidget()
        activity_layout = QVBoxLayout(activity_group)
        
        # Заголовок текущей активности
        activity_title = QLabel("Текущая активность:")
        activity_layout.addWidget(activity_title)
        
        # Информация о текущем приложении
        self.current_app_label = QLabel("Нет активности")
        self.current_window_title_label = QLabel("")
        self.current_activity_time_label = QLabel("")
        self.keyboard_activity_label = QLabel("Клавиатурная активность: 0 нажатий")
        
        activity_layout.addWidget(self.current_app_label)
        activity_layout.addWidget(self.current_window_title_label)
        activity_layout.addWidget(self.current_activity_time_label)
        activity_layout.addWidget(self.keyboard_activity_label)
        
        layout.addWidget(activity_group)
        
        # Вкладки для списков приложений
        self.tabs = QTabWidget()
        
        # Вкладка "Все приложения"
        all_apps_tab = QWidget()
        all_apps_layout = QVBoxLayout(all_apps_tab)
        
        # Список всех приложений
        self.app_list = QListWidget()
        self.app_list.setSelectionMode(QListWidget.SingleSelection)
        
        # Кнопки действий для списка всех приложений
        all_apps_buttons = QHBoxLayout()
        
        toggle_app_button = QPushButton("Включить/выключить")
        toggle_app_button.clicked.connect(self.toggle_app)
        
        toggle_productive_button = QPushButton("Отметить как полезное/неполезное")
        toggle_productive_button.clicked.connect(self.toggle_productive)
        
        remove_app_button = QPushButton("Удалить из отслеживаемых")
        remove_app_button.clicked.connect(self.remove_app)
        
        all_apps_buttons.addWidget(toggle_app_button)
        all_apps_buttons.addWidget(toggle_productive_button)
        all_apps_buttons.addWidget(remove_app_button)
        
        all_apps_layout.addWidget(self.app_list)
        all_apps_layout.addLayout(all_apps_buttons)
        
        # Вкладка "Полезные приложения"
        productive_tab = QWidget()
        productive_layout = QVBoxLayout(productive_tab)
        
        # Список полезных приложений
        self.productive_list = QListWidget()
        self.productive_list.setSelectionMode(QListWidget.SingleSelection)
        
        productive_layout.addWidget(self.productive_list)
        
        # Вкладка "Неполезные приложения"
        non_productive_tab = QWidget()
        non_productive_layout = QVBoxLayout(non_productive_tab)
        
        # Список неполезных приложений
        self.non_productive_list = QListWidget()
        self.non_productive_list.setSelectionMode(QListWidget.SingleSelection)
        
        non_productive_layout.addWidget(self.non_productive_list)
        
        # Добавляем вкладки
        self.tabs.addTab(all_apps_tab, "Все приложения")
        self.tabs.addTab(productive_tab, "Полезные приложения")
        self.tabs.addTab(non_productive_tab, "Неполезные приложения")
        
        layout.addWidget(self.tabs)
        
        # Кнопки управления
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Начать отслеживание")
        self.start_button.clicked.connect(self.start_tracking)
        
        self.stop_button = QPushButton("Остановить отслеживание")
        self.stop_button.clicked.connect(self.stop_tracking)
        self.stop_button.setEnabled(False)  # По умолчанию отключена
        
        settings_button = QPushButton("Настройки")
        settings_button.clicked.connect(self.show_settings_dialog)
        
        # Добавляем кнопки в лэйаут
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(settings_button)
        
        layout.addLayout(control_layout)
        
        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово к работе")
        
        # Метка статуса
        self.status_label = QLabel("Статус: Ожидание")
        self.status_bar.addPermanentWidget(self.status_label)
        
        # Подключаем обновление UI по сигналам
        self.update_status_signal.connect(self.update_ui_status)
        
        # Обновляем список приложений в UI
        self.update_app_list()

    def init_tray_icon(self):
        """Инициализация иконки в трее"""
        # Создаем иконку для трея (используем иконку по умолчанию из ресурсов Qt)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(str(get_base_path() / 'icon.png')))
        
        # Если не нашли свою иконку, используем стандартную
        if not self.tray_icon.isSystemTrayAvailable():
            logger.warning("Системный трей недоступен, используем стандартную иконку")
            self.tray_icon.setIcon(QIcon.fromTheme("media-record"))
        
        # Создаем контекстное меню для трея
        tray_menu = QMenu()
        
        # Действие "Показать/скрыть"
        show_action = QAction("Показать/скрыть", self)
        show_action.triggered.connect(self.toggle_window_visibility)
        tray_menu.addAction(show_action)
        
        # Действие "Приостановить/возобновить отслеживание"
        self.pause_action = QAction("Приостановить отслеживание", self)
        self.pause_action.triggered.connect(self.toggle_tracking_pause)
        tray_menu.addAction(self.pause_action)
        
        # Разделитель
        tray_menu.addSeparator()
        
        # Действие "Выйти"
        exit_action = QAction("Выйти", self)
        exit_action.triggered.connect(self.safe_exit)
        tray_menu.addAction(exit_action)
        
        # Устанавливаем меню для трея
        self.tray_icon.setContextMenu(tray_menu)
        
        # Обработка клика по иконке
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Показываем иконку в трее
        self.tray_icon.show()
        
        # Устанавливаем начальный тултип
        self.tray_icon.setToolTip("Time Tracker PRO (ожидание запуска)")
    
    def toggle_window_visibility(self):
        """Переключает видимость главного окна"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()  # Активирует окно и выводит его на передний план
    
    def tray_icon_activated(self, reason):
        """Обработчик активации иконки в трее"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_window_visibility()
    
    def update_ui_status(self, status_text):
        """Обновляет статус в UI"""
        self.current_app_label.setText(status_text)
        
        # Если есть текущая активность, обновляем её детали
        if self.current_activity_data:
            app_name = self.current_activity_data.get('app_name', '')
            window_title = self.current_activity_data.get('window_title', '')
            is_useful = self.current_activity_data.get('is_useful')
            
            self.current_window_title_label.setText(f"Окно: {window_title[:50]}{'...' if len(window_title) > 50 else ''}")
            
            # Обновляем время активности
            if self.activity_start_time:
                elapsed = time.time() - self.activity_start_time
                hours, remainder = divmod(int(elapsed), 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                self.current_activity_time_label.setText(f"Время: {time_str}")
            else:
                self.current_activity_time_label.setText("Время: 00:00:00")
            
            # Обновляем информацию о нажатиях клавиш
            self.keyboard_activity_label.setText(f"Клавиатурная активность: {self.keyboard_press_count} нажатий")
            
            # Устанавливаем разные цвета для полезных и неполезных приложений
            if is_useful is True:
                self.current_app_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            elif is_useful is False:
                self.current_app_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            else:
                self.current_app_label.setStyleSheet("QLabel { color: black; }")
                
            # Обновляем иконку в трее
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.setToolTip(f"Отслеживается: {app_name} - Нажатий: {self.keyboard_press_count}")
        else:
            # Если нет текущей активности, очищаем поля
            self.current_window_title_label.setText("")
            self.current_activity_time_label.setText("Время: 00:00:00")
            self.keyboard_activity_label.setText("Клавиатурная активность: 0 нажатий")
            self.current_app_label.setStyleSheet("QLabel { color: black; }")
            
            # Обновляем иконку в трее
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.setToolTip("Time Tracker PRO - Нет активности")

    def update_app_list(self):
        """Обновляет списки приложений в интерфейсе"""
        try:
            # Сохраняем текущее выделение для восстановления после обновления
            selected_apps = {
                'all': None,
                'productive': None,
                'non_productive': None
            }
            
            # Получаем текущее выделение из каждого списка
            if self.app_list.selectedItems():
                selected_apps['all'] = self.app_list.selectedItems()[0].data(Qt.UserRole)
            if self.productive_list.selectedItems():
                selected_apps['productive'] = self.productive_list.selectedItems()[0].data(Qt.UserRole)
            if self.non_productive_list.selectedItems():
                selected_apps['non_productive'] = self.non_productive_list.selectedItems()[0].data(Qt.UserRole)

            # Очищаем существующие списки
            self.app_list.clear()
            self.productive_list.clear()
            self.non_productive_list.clear()
            
            # Счетчики для статистики
            productive_count = 0
            non_productive_count = 0
            total_tracked = 0
            
            # Получаем список запущенных приложений
            running_apps = self.get_discovered_applications()
            
            # Отсортированный список приложений для отображения
            sorted_apps = []
            
            # Сначала добавляем отслеживаемые приложения из конфигурации
            for app_name, is_useful in self.tracked_applications_config.items():
                # Проверяем, запущено ли сейчас приложение
                is_running = app_name.lower() in (app.lower() for app in running_apps)
                
                item_text = f"{app_name} ({'Полезное' if is_useful else 'Неполезное'}, " \
                         f"{'Запущено' if is_running else 'Не запущено'})"
                
                sorted_apps.append((app_name, item_text, is_useful, is_running))
                
                total_tracked += 1
                if is_useful:
                    productive_count += 1
                else:
                    non_productive_count += 1
            
            # Затем добавляем запущенные приложения, которых нет в конфигурации
            for app_name in running_apps:
                if app_name.lower() not in self.tracked_applications_config:
                    item_text = f"{app_name} (Не отслеживается, Запущено)"
                    sorted_apps.append((app_name, item_text, None, True))
            
            # Сортируем весь список по названию приложения
            sorted_apps.sort(key=lambda x: x[0].lower())
            
            # Заполняем списки
            for app_name, item_text, is_useful, is_running in sorted_apps:
                # Создаем элемент для списка всех приложений
                item_all = QListWidgetItem(item_text)
                item_all.setData(Qt.UserRole, app_name)  # Сохраняем оригинальное имя как данные
                self.app_list.addItem(item_all)
                
                # Если приложение отслеживаемое, добавляем его в соответствующий список
                if is_useful is not None:
                    if is_useful:
                        item_productive = QListWidgetItem(item_text)
                        item_productive.setData(Qt.UserRole, app_name)
                        self.productive_list.addItem(item_productive)
                    else:
                        item_non_productive = QListWidgetItem(item_text)
                        item_non_productive.setData(Qt.UserRole, app_name)
                        self.non_productive_list.addItem(item_non_productive)
            
            # Восстанавливаем выделение
            if selected_apps['all']:
                for i in range(self.app_list.count()):
                    if self.app_list.item(i).data(Qt.UserRole) == selected_apps['all']:
                        self.app_list.setCurrentRow(i)
                        break
                        
            if selected_apps['productive']:
                for i in range(self.productive_list.count()):
                    if self.productive_list.item(i).data(Qt.UserRole) == selected_apps['productive']:
                        self.productive_list.setCurrentRow(i)
                        break
                        
            if selected_apps['non_productive']:
                for i in range(self.non_productive_list.count()):
                    if self.non_productive_list.item(i).data(Qt.UserRole) == selected_apps['non_productive']:
                        self.non_productive_list.setCurrentRow(i)
                        break
            
            # Обновляем заголовки вкладок со статистикой
            self.tabs.setTabText(0, f"Все приложения ({self.app_list.count()})")
            self.tabs.setTabText(1, f"Полезные приложения ({self.productive_list.count()})")
            self.tabs.setTabText(2, f"Неполезные приложения ({self.non_productive_list.count()})")
            
            logger.info(f"Обновлен список приложений: {self.app_list.count()} процессов")
            self.status_bar.showMessage(f"Отслеживается: {total_tracked} приложений " \
                                       f"(полезных: {productive_count}, неполезных: {non_productive_count})")
        except Exception as e:
            logger.error(f"Ошибка при обновлении списка приложений: {e}", exc_info=True)
            self.status_bar.showMessage(f"Ошибка при обновлении списка приложений: {str(e)[:50]}")
            
    def show_login_dialog_if_needed(self):
        """Показывает диалог авторизации, если токен отсутствует или недействителен"""
        # Этот метод будет вызван после того, как главный цикл событий Qt запустится
        
        # Предотвращаем запуск множественных диалогов
        if hasattr(self, '_login_dialog_active') and self._login_dialog_active:
            logger.warning("Диалог авторизации уже активен, пропускаем повторный вызов")
            return
            
        # Устанавливаем флаг, что диалог авторизации активен
        self._login_dialog_active = True
        
        try:
            # Проверяем токен во всех возможных местах
            auth_token = None
            token_is_valid = False
            
            # Проверяем токен в секции Credentials
            if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'auth_token'):
                auth_token = self.config.get('Credentials', 'auth_token')
                
            # Если не нашли, проверяем в секции Server
            if not auth_token and self.config.has_section('Server') and self.config.has_option('Server', 'token'):
                auth_token = self.config.get('Server', 'token')
                
            # Если не нашли, проверяем в секции API
            if not auth_token and self.config.has_section('API') and self.config.has_option('API', 'token'):
                auth_token = self.config.get('API', 'token')
                
            # Если не нашли, проверяем в корне файла
            if not auth_token and self.config.has_option('DEFAULT', 'token'):
                auth_token = self.config.get('DEFAULT', 'token')
                
            # Если токен найден, проверяем его валидность
            if auth_token:
                try:
                    # Декодируем токен и проверяем срок действия
                    token_data = jwt.decode(auth_token, options={"verify_signature": False})
                    exp_timestamp = token_data.get('exp')
                    if exp_timestamp:
                        expiration_time = datetime.fromtimestamp(exp_timestamp)
                        if datetime.now() < expiration_time:
                            token_is_valid = True
                            logger.info("Пользователь уже аутентифицирован (токен действителен).")
                        else:
                            logger.warning(f"Токен истек {expiration_time}. Требуется повторная авторизация.")
                    else:
                        logger.warning("Токен не содержит информации о сроке действия.")
                except Exception as e:
                    logger.error(f"Ошибка при проверке токена: {e}")
                    
            # Если токен не найден или недействителен, показываем диалог авторизации
            if not auth_token or not token_is_valid:
                logger.info("Токен отсутствует или недействителен, вызывается диалог входа.")
                
                # Создаем и запускаем диалог для авторизации
                login_dialog = LoginDialog(parent=self)
                if login_dialog.exec_() == QDialog.Accepted:
                    # После успешного логина LoginDialog должен обновить self.config
                    # и атрибуты self.api_base_url, self.user_id, self.session.headers
                    self.api_base_url = self.config.get('Credentials', 'api_base_url')
                    self.user_id = self.config.get('Credentials', 'user_id')
                    new_auth_token = self.config.get('Credentials', 'auth_token')
                    self.session.headers.update({'Authorization': f'Bearer {new_auth_token}'})
                    logger.info("Вход выполнен успешно через диалог.")
                    # Перезапускаем таймер отправки данных, если интервал мог измениться
                    send_interval_seconds = self.config.getint('Settings', 'send_interval_seconds', fallback=60)
                    self.send_data_timer.setInterval(send_interval_seconds * 1000)
                    
                    # Обновляем состояние подключения в интерфейсе
                    self.connection_status.setText(f"Статус подключения: Подключено ({self.api_base_url})")
                    self.connection_status.setStyleSheet("QLabel { color: green; }")
                else:
                    logger.warning("Диалог входа отменен пользователем или работа в оффлайн-режиме.")
                    # Проверяем, выбран ли оффлайн-режим
                    if self.config.getboolean('Settings', 'demo_mode', fallback=False):
                        self.connection_status.setText("Статус подключения: Оффлайн-режим")
                        self.connection_status.setStyleSheet("QLabel { color: orange; }")
                    else:
                        self.connection_status.setText("Статус подключения: Не авторизовано")
                        self.connection_status.setStyleSheet("QLabel { color: red; }")
                        QMessageBox.warning(self, "Внимание", 
                                        "Авторизация не выполнена. Отслеживание активности будет работать в ограниченном режиме.")
            else:
                # Если токен действителен, обновляем UI
                self.connection_status.setText(f"Статус подключения: Подключено ({self.api_base_url})")
                self.connection_status.setStyleSheet("QLabel { color: green; }")
                logger.info("Пользователь уже аутентифицирован (токен найден и действителен).")
        finally:
            # Снимаем флаг после завершения диалога
            self._login_dialog_active = False

    def toggle_productive(self):
        """Переключает статус полезности приложения"""
        # Получаем текущую вкладку
        current_tab = self.tabs.currentIndex()
        
        # Выбираем соответствующий список приложений
        if current_tab == 0:  # Вкладка "Все приложения"
            app_list_widget = self.app_list
        elif current_tab == 1:  # Вкладка "Полезные приложения"
            app_list_widget = self.productive_list
        elif current_tab == 2:  # Вкладка "Неполезные приложения"
            app_list_widget = self.non_productive_list
        else:
            return
        
        # Получаем выбранный элемент
        selected_items = app_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите приложение из списка")
            return
        
        app_name = selected_items[0].text()
        # Получаем оригинальное имя процесса из данных элемента
        proc_name = selected_items[0].data(Qt.UserRole)
        if not proc_name:
            proc_name = app_name
            
        app_name_lower = app_name.lower()
        proc_name_lower = proc_name.lower()
        
        # Ключ для конфигурации - используем имя процесса для большей точности
        config_key = proc_name_lower
        
        try:
            # Проверяем, отслеживается ли это приложение
            is_tracked = config_key in self.tracked_applications_config
            
            # Если не отслеживается, сначала добавляем его в отслеживаемые приложения
            if not is_tracked:
                is_useful = True  # По умолчанию добавляем как полезное
                self.tracked_applications_config[config_key] = is_useful
                status_text = "добавлено как полезное"
            else:
                # Если уже отслеживается, инвертируем статус полезности
                is_useful = self.tracked_applications_config[config_key]
                new_useful_status = not is_useful
                self.tracked_applications_config[config_key] = new_useful_status
                status_text = "полезное" if new_useful_status else "неполезное"
            
            # Обновляем конфигурацию
            if not self.config.has_section('Applications'):
                self.config.add_section('Applications')
            self.config.set('Applications', config_key, 
                            str(self.tracked_applications_config[config_key]))
            
            # Сохраняем конфигурацию
            self._save_config()
            
            # Обновляем списки приложений
            self.update_app_list()
            
            QMessageBox.information(self, "Успешно", f"Приложение '{app_name}' теперь {status_text}")
            logger.info(f"Изменен статус полезности приложения '{app_name}': {status_text}")
        except Exception as e:
            logger.error(f"Ошибка при изменении статуса полезности приложения '{app_name}': {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось изменить статус приложения: {e}")

    def remove_app(self):
        """Удаляет приложение из списка отслеживаемых"""
        # Получаем текущую вкладку
        current_tab = self.tabs.currentIndex()
        
        # Выбираем соответствующий список приложений
        if current_tab == 0:  # Вкладка "Все приложения"
            app_list_widget = self.app_list
        elif current_tab == 1:  # Вкладка "Полезные приложения"
            app_list_widget = self.productive_list
        elif current_tab == 2:  # Вкладка "Неполезные приложения"
            app_list_widget = self.non_productive_list
        else:
            return
        
        # Получаем выбранный элемент
        selected_items = app_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите приложение из списка")
            return
        
        app_name = selected_items[0].text()
        # Получаем оригинальное имя процесса из данных элемента
        proc_name = selected_items[0].data(Qt.UserRole)
        if not proc_name:
            proc_name = app_name
            
        app_name_lower = app_name.lower()
        proc_name_lower = proc_name.lower()
        
        # Ключ для конфигурации - используем имя процесса для большей точности
        config_key = proc_name_lower
        
        try:
            # Проверяем, отслеживается ли это приложение
            if config_key in self.tracked_applications_config:
                # Удаляем из конфигурации
                del self.tracked_applications_config[config_key]
                if self.config.has_option('Applications', config_key):
                    self.config.remove_option('Applications', config_key)
                QMessageBox.information(self, "Успешно", f"Приложение '{app_name}' удалено из списка отслеживаемых")
                
                # Обновляем список приложений в UI
                self.update_app_list()
            else:
                self.status_bar.showMessage(f"Приложение '{app_name}' не найдено в списке отслеживаемых")
        except Exception as e:
            logger.error(f"Ошибка при удалении приложения '{app_name}': {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось удалить приложение: {e}")

    def safe_exit(self):
        try:
            self.status_bar.showMessage('Завершение работы...')
            
            # Останавливаем отслеживание активности
            self.tracking_paused = True
            
            # Завершаем текущую сессию, если есть
            if self.current_activity_data:
                try:
                    self.end_current_activity_session(event_type="app_close")
                except Exception as e:
                    logger.error(f"Ошибка при завершении текущей сессии: {e}")
            
            # Останавливаем все слушатели и таймеры
            try:
                if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
                    self.keyboard_listener.stop()
                    logger.info("Keyboard listener остановлен")
            except Exception as e:
                logger.error(f"Ошибка остановки keyboard listener: {e}")
                
            try:
                if hasattr(self, 'mouse_listener') and self.mouse_listener:
                    self.mouse_listener.stop()
                    logger.info("Mouse listener остановлен")
            except Exception as e:
                logger.error(f"Ошибка остановки mouse listener: {e}")
            
            # Останавливаем все таймеры, которые могут вызывать задержки
            try:
                if hasattr(self, 'tracking_timer'):
                    self.tracking_timer.stop()
                if hasattr(self, 'ui_update_timer'):
                    self.ui_update_timer.stop()
                if hasattr(self, 'idle_check_timer'):
                    self.idle_check_timer.stop()
            except Exception as e:
                logger.error(f"Ошибка остановки таймеров: {e}")
            
            # Очищаем очередь активностей
            try:
                if hasattr(self, 'activity_queue'):
                    while not self.activity_queue.empty():
                        try:
                            self.activity_queue.get_nowait()
                            self.activity_queue.task_done()
                        except:
                            pass
            except Exception as e:
                logger.error(f"Ошибка очистки очереди: {e}")
            
            logger.info('Приложение завершает работу корректно.')
        except Exception as e:
            logger.error(f'Ошибка завершения: {e}')
        finally:
            # Немедленно выходим из приложения
            QApplication.quit()

    def open_web_interface(self):
        """Открытие веб-интерфейса"""
        if hasattr(self, 'api_base_url'):
            # Убираем возможные двойные слеши в URL
            base_url = self.api_base_url.rstrip('/').replace('/api', '')
            dashboard_url = f"{base_url}/dashboard/"
            logger.info(f"Открываем веб-интерфейс: {dashboard_url}")
            webbrowser.open(dashboard_url)
        else:
            QMessageBox.warning(self, "Ошибка", "Необходима авторизация")
            self.show_login_dialog_if_needed()

    def start_tracking(self):
        self.status_label.setText("Статус: Отслеживание активно")
        # Включаем отслеживание
        self.tracking_paused = False
        if self.pause_action:
            self.pause_action.setText("Приостановить отслеживание")
        # Обновляем интерфейс
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_bar.showMessage("Отслеживание активности запущено")
        logger.info("Отслеживание активности запущено")

    def stop_tracking(self):
        self.status_label.setText("Статус: Отслеживание остановлено")
        # Останавливаем отслеживание
        self.tracking_paused = True
        if self.pause_action:
            self.pause_action.setText("Возобновить отслеживание")
        # Завершаем текущую сессию активности, если она есть
        if self.current_activity_data:
            self.end_current_activity_session(event_type="pause")
        # Обновляем интерфейс
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_bar.showMessage("Отслеживание активности остановлено")
        logger.info("Отслеживание активности остановлено")

    def closeEvent(self, event):
        try:
            reply = QMessageBox.question(
                self,
                'Выход',
                'Вы действительно хотите выйти из приложения?\nВсе сборы активности будут остановлены.',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Принимаем событие закрытия
                event.accept()
                
                # Запускаем безопасное завершение работы через очередь событий Qt
                # Это предотвратит зависание интерфейса
                QTimer.singleShot(0, self.safe_exit)
            else:
                event.ignore()
        except Exception as e:
            logger.error(f"Ошибка в обработчике закрытия: {e}")
            event.accept()
            QTimer.singleShot(0, self.safe_exit)

    def toggle_app(self):
        """Включает/выключает отслеживание приложения"""
        # Получаем текущую вкладку
        current_tab = self.tabs.currentIndex()
        
        # Выбираем соответствующий список приложений
        if current_tab == 0:  # Вкладка "Все приложения"
            app_list_widget = self.app_list
        elif current_tab == 1:  # Вкладка "Полезные приложения"
            app_list_widget = self.productive_list
        elif current_tab == 2:  # Вкладка "Неполезные приложения"
            app_list_widget = self.non_productive_list
        else:
            return
        
        # Получаем выбранный элемент
        selected_items = app_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите приложение из списка")
            return
        
        app_name = selected_items[0].text()
        # Получаем оригинальное имя процесса из данных элемента
        proc_name = selected_items[0].data(Qt.UserRole)
        if not proc_name:
            proc_name = app_name
            
        app_name_lower = app_name.lower()
        proc_name_lower = proc_name.lower()
        
        # Ключ для конфигурации - используем имя процесса для большей точности
        config_key = proc_name_lower
        
        try:
            # Проверяем, есть ли приложение в конфигурации трекера
            is_tracked = config_key in self.tracked_applications_config
            
            # Если приложение уже в списке отслеживаемых - сохраняем его статус полезности
            current_useful_status = False
            if is_tracked:
                current_useful_status = self.tracked_applications_config[config_key]
            
            # Инвертируем состояние "отслеживается / не отслеживается"
            new_tracked_state = not is_tracked
            
            if new_tracked_state:
                # Включаем отслеживание
                self.tracked_applications_config[config_key] = current_useful_status
                if not self.config.has_section('Applications'):
                    self.config.add_section('Applications')
                self.config.set('Applications', config_key, str(current_useful_status))
                status_text = "включено"
            else:
                # Выключаем отслеживание - удаляем из списка отслеживаемых
                if config_key in self.tracked_applications_config:
                    del self.tracked_applications_config[config_key]
                if self.config.has_option('Applications', config_key):
                    self.config.remove_option('Applications', config_key)
                status_text = "выключено"
            
            # Сохраняем конфигурацию
            self._save_config()
            
            # Обновляем списки приложений
            self.update_app_list()
            
            QMessageBox.information(self, "Успешно", f"Отслеживание приложения '{app_name}' {status_text}")
            logger.info(f"Изменен статус отслеживания приложения '{app_name}': {status_text}")
        except Exception as e:
            logger.error(f"Ошибка при изменении статуса отслеживания приложения '{app_name}': {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось изменить статус приложения: {e}")

    def get_active_window_info(self):
        """Получает информацию об активном окне"""
        try:
            active_window_handle = win32gui.GetForegroundWindow()
            if not active_window_handle:
                return None
                
            # Получаем заголовок окна
            window_title = win32gui.GetWindowText(active_window_handle)
            
            # Получаем ID процесса
            _, process_id = win32process.GetWindowThreadProcessId(active_window_handle)
            
            # Получаем имя процесса
            try:
                process = psutil.Process(process_id)
                app_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                app_name = "Unknown"
            
            # Возвращаем словарь с информацией об активном окне
            return {
                'app_name': app_name,
                'window_title': window_title,
                'process_id': process_id
            }
        except Exception as e:
            logger.error(f"Ошибка при получении информации об активном окне: {e}", exc_info=True)
            return None
            
    def is_app_useful(self, app_name):
        """Определяет, является ли приложение полезным согласно конфигурации"""
        if not app_name:
            return False
            
        # Приводим имя к нижнему регистру для сравнения
        app_name_lower = app_name.lower()
        
        # Проверяем, есть ли приложение в конфигурации
        if app_name_lower in self.tracked_applications_config:
            # Возвращаем статус полезности
            return self.tracked_applications_config[app_name_lower]
        
        # Если приложение не найдено в конфигурации, считаем его неполезным
        return False

    def start_new_activity_session(self, app_name, window_title, is_useful=None):
        """Начинает новую сессию активности"""
        try:
            # Проверяем, не находится ли пользователь в состоянии простоя
            if self.is_idle:
                logger.info("Попытка начать сессию активности, но пользователь неактивен.")
                return False
                
            # Проверяем, включено ли отслеживание для этого приложения
            app_name_lower = app_name.lower()
            if app_name_lower in self.tracked_applications_config:
                is_tracked = self.tracked_applications_config[app_name_lower]
                if not is_tracked:
                    logger.info(f"Приложение {app_name} находится в списке неотслеживаемых.")
                    return False
            
            # Если статус полезности не указан, проверяем его в конфигурации
            if is_useful is None:
                if app_name_lower in self.tracked_applications_config:
                    is_useful = self.tracked_applications_config[app_name_lower]
                else:
                    # По умолчанию считаем приложение неполезным
                    is_useful = False
            
            # Создаем запись об активности
            start_time = time.time()
            self.current_activity_data = {
                'app_name': app_name,
                'window_title': window_title,
                'start_time': start_time,
                'start_time_iso_utc': datetime.utcnow().isoformat() + 'Z',
                'is_useful': is_useful,
                'keyboard_presses': 0  # Начальное значение счетчика нажатий
            }
            
            # Запоминаем время начала активности
            self.activity_start_time = start_time
            
            # Сбрасываем счетчик нажатий клавиш
            self.keyboard_press_count = 0
            
            # Обновляем интерфейс
            status_message = f"Начата сессия для '{app_name}'"
            self.update_status_signal.emit(f"Отслеживается: {app_name}")
            self.status_bar.showMessage(status_message)
            
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.setToolTip(f"Отслеживается: {app_name}")
            
            logger.info(f"Начата новая сессия активности: App='{app_name}', Title='{window_title[:30]}{'...' if len(window_title) > 30 else ''}'")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании новой сессии активности: {e}", exc_info=True)
            return False
            
    def end_current_activity_session(self, event_type: str = "switch") -> Optional[Dict[str, Any]]:
        """Завершает текущую сессию активности, подсчитывает длительность и добавляет в очередь."""
        if not self.current_activity_data or self.activity_start_time is None:
            # Используем self.activity_start_time is None для явной проверки инициализации
            logger.debug("Попытка завершить несуществующую сессию активности.")
            return None
        
        # Вычисляем длительность сессии
        end_time = time.time()
        duration_seconds = round(end_time - self.activity_start_time)
        
        if duration_seconds < 1:
            logger.debug(f"Сессия для {self.current_activity_data['app_name']} слишком короткая ({duration_seconds} сек), игнорируется.")
            self.current_activity_data = None
            self.activity_start_time = None
            return None
        
        # Формируем запись для очереди
        activity_entry = self.current_activity_data.copy()
        
        # Добавляем данные о клавиатурной активности
        if 'keyboard_presses' not in activity_entry or activity_entry['keyboard_presses'] == 0:
            activity_entry['keyboard_presses'] = self.keyboard_press_count
            logger.info(f"Добавлено {self.keyboard_press_count} нажатий клавиш в активность")
            # Сбрасываем счетчик после добавления в активность
            self.keyboard_press_count = 0
        
        activity_entry.update({
            'end_time': end_time,
            'end_time_iso_utc': datetime.utcnow().isoformat() + 'Z',
            'duration_seconds': duration_seconds,
            'event_type': event_type
        })
        
        # Добавляем в очередь для отправки
        self.activity_queue.put(activity_entry)
        
        logger.info(
            f"Завершена сессия активности: "
            f"App='{activity_entry['app_name']}', "
            f"Title='{activity_entry['window_title'][:30]}{'...' if len(activity_entry['window_title']) > 30 else ''}, "
            f"Duration={duration_seconds}s. В очереди: {self.activity_queue.qsize()}"
        )
        
        # Обновление статус-бара и тултипа трея
        status_message = f"Сессия для '{activity_entry['app_name']}' завершена. В очереди: {self.activity_queue.qsize()}"
        self.status_bar.showMessage(status_message)
        if hasattr(self, 'tray_icon') and self.tray_icon:
            # Для тултипа можно показать более общее сообщение после завершения сессии
            tooltip_message = f"Готов к отслеживанию. В очереди: {self.activity_queue.qsize()}"
            if self.is_idle: # Если перешли в idle, то сообщение будет другим из handle_idle_state_change
                 tooltip_message = f"Пользователь неактивен. В очереди: {self.activity_queue.qsize()}"
            self.tray_icon.setToolTip(tooltip_message)
            
        # Очистка данных текущей сессии
        self.current_activity_data = None
        self.activity_start_time = None
        return activity_entry
        
    def get_discovered_applications(self) -> List[str]:
        """Возвращает список уникальных имен запущенных приложений."""
        discovered_apps = set()
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    app_name = proc.info['name']
                    if app_name and app_name.strip(): # Проверяем, что имя не пустое
                        # Приводим к нижнему регистру для унификации
                        discovered_apps.add(app_name.lower())
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Эти исключения ожидаемы для некоторых процессов
                    continue 
                except Exception as e:
                    logger.debug(f"Ошибка при получении имени процесса {proc.pid if hasattr(proc, 'pid') else 'N/A'}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при итерации по процессам: {e}", exc_info=True)
        
        # Можно добавить фильтрацию по self.ignored_processes, если это нужно глобально,
        # или оставить это на усмотрение SettingsDialog
        # filtered_apps = {app for app in discovered_apps if app not in self.ignored_processes}
        
        logger.debug(f"Обнаруженные приложения: {sorted(list(discovered_apps))}")
        return sorted(list(discovered_apps))

    def update_tracked_applications_config(self, new_tracked_config: Dict[str, bool]):
        """Обновляет конфигурацию отслеживаемых приложений и сохраняет ее."""
        logger.info("Обновление конфигурации отслеживаемых приложений.")
        self.tracked_applications_config = new_tracked_config
        
        if not self.config.has_section('Applications'):
            self.config.add_section('Applications')
        else:
            # Очищаем старые записи в секции [Applications]
            for key in self.config.options('Applications'):
                self.config.remove_option('Applications', key)
        
        # Добавляем новые записи
        for app_name, is_useful in new_tracked_config.items():
            self.config.set('Applications', app_name.lower(), str(is_useful))
            
        self._save_config() # Сохраняем весь config.ini
        logger.info("Конфигурация отслеживаемых приложений успешно обновлена и сохранена.")
        # После обновления может потребоваться перерисовать UI или перезагрузить какие-то данные
        # Например, если SettingsDialog открыт, его можно уведомить, или он сам закроется.

    def show_settings_dialog(self):
        dialog = SettingsDialog(self) # Передаем ссылку на главное окно
        dialog.exec_()

    def toggle_tracking_pause(self):
        self.tracking_paused = not self.tracking_paused
        if self.tracking_paused:
            logger.info("Отслеживание приостановлено пользователем.")
            if self.current_activity_data:
                # Завершаем текущую сессию, если она была
                self.end_current_activity_session(event_type="tracking_paused")
            
            msg = "Отслеживание приостановлено."
            self.status_bar.showMessage(msg)
            if self.tray_icon:
                self.tray_icon.setToolTip(msg)
            if self.pause_action: 
                self.pause_action.setText("Возобновить отслеживание")
        else:
            logger.info("Отслеживание возобновлено пользователем.")
            # При возобновлении, track_active_window_and_idle_state само определит активность
            # и начнет новую сессию, если это необходимо.
            # Состояние is_idle также будет актуальным благодаря _check_idle_timer.
            msg = "Отслеживание возобновлено. Определение активности..."
            if self.is_idle:
                 msg = "Отслеживание возобновлено (Пользователь неактивен)."

            self.status_bar.showMessage(msg)
            if self.tray_icon:
                self.tray_icon.setToolTip(msg)
            if self.pause_action: 
                self.pause_action.setText("Приостановить отслеживание")

    def send_activity_data(self):
        """Отправляет накопленные данные активности на сервер."""
        if self.activity_queue.empty():
            logger.debug("Очередь активностей пуста, нечего отправлять.")
            return
            
        # Проверяем, включен ли демо-режим
        demo_mode = self.config.getboolean('Settings', 'demo_mode', fallback=False)
        
        if demo_mode:
            # В демо-режиме просто очищаем очередь и логируем данные
            max_batch_size = self.config.getint('Settings', 'max_send_batch_size', fallback=20)
            activities_to_send = []
            
            # Собираем до max_batch_size активностей из очереди
            for _ in range(min(max_batch_size, self.activity_queue.qsize())):
                if not self.activity_queue.empty():
                    activity = self.activity_queue.get()
                    activities_to_send.append(activity)
            
            logger.info(f"Демо-режим: Обработано {len(activities_to_send)} записей активности. Данные не отправляются на сервер.")
            return
        
        # Получаем данные пользователя и токен из конфигурации
        auth_token = None
        user_id = None
        
        # Проверяем токен в секции Credentials
        if self.config.has_section('Credentials'):
            if self.config.has_option('Credentials', 'auth_token'):
                auth_token = self.config.get('Credentials', 'auth_token')
            if self.config.has_option('Credentials', 'user_id'):
                user_id = self.config.get('Credentials', 'user_id')
            
        # Если не нашли в Credentials, проверяем другие секции
        if not auth_token:
            # Проверяем в секции Server
            if self.config.has_section('Server') and self.config.has_option('Server', 'token'):
                auth_token = self.config.get('Server', 'token')
            # Проверяем в секции API
            elif self.config.has_section('API') and self.config.has_option('API', 'token'):
                auth_token = self.config.get('API', 'token')
            # Проверяем в корне файла
            elif self.config.has_option('DEFAULT', 'token'):
                auth_token = self.config.get('DEFAULT', 'token')
        
        # Если не нашли user_id в Credentials, пытаемся получить из токена
        if not user_id and auth_token:
            try:
                token_data = jwt.decode(auth_token, options={"verify_signature": False})
                if "user_id" in token_data:
                    user_id = str(token_data["user_id"])
                    # Сохраняем в конфигурацию для последующего использования
                    if self.config.has_section('Credentials'):
                        self.config.set('Credentials', 'user_id', user_id)
                        self._save_config(self.config)
            except Exception as e:
                logger.error(f"Ошибка при извлечении user_id из токена: {e}")
            
        # Если все еще нет user_id, используем значение по умолчанию
        if not user_id:
            user_id = "1"
            
        # Получаем URL API
        api_url = None
        if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'api_base_url'):
            api_url = self.config.get('Credentials', 'api_base_url')
        elif self.config.has_section('Server') and self.config.has_option('Server', 'base_url'):
            api_url = self.config.get('Server', 'base_url')
        elif self.config.has_section('API') and self.config.has_option('API', 'base_url'):
            api_url = self.config.get('API', 'base_url')
        elif self.config.has_option('DEFAULT', 'base_url'):
            api_url = self.config.get('DEFAULT', 'base_url')
        else:
            api_url = 'http://localhost:8000'
            
        # Добавляем /api/ если необходимо
        if not api_url.endswith('/api/'):
            api_url = api_url.rstrip('/') + '/api/'
            
        api_url += 'activities/'
        
        if not auth_token:
            logger.warning("Отсутствует токен авторизации. Переключение в демо-режим.")
            # Включаем демо-режим
            if not self.config.has_section('Settings'):
                self.config.add_section('Settings')
            self.config.set('Settings', 'demo_mode', 'True')
            self._save_config(self.config)
            return
            
        # Заголовки для запроса
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_token}'
        }
        
        # Обновляем заголовки сессии
        self.session.headers.update({'Authorization': f'Bearer {auth_token}'})
        
        # Собираем пакет данных для отправки
        max_batch_size = self.config.getint('Settings', 'max_send_batch_size', fallback=20)
        activities_to_send = []
        activities_to_send_payload = []
        
        try:
            # Собираем до max_batch_size активностей из очереди
            for _ in range(min(max_batch_size, self.activity_queue.qsize())):
                if self.activity_queue.empty():
                    break
                activity_dict = self.activity_queue.get_nowait()
                activities_to_send.append(activity_dict)
                
                # Формируем данные для API
                # Убедимся, что все обязательные поля заполнены
                start_time = activity_dict.get('start_time_iso_utc', '')
                end_time = activity_dict.get('end_time_iso_utc', '')
                
                # Если поля не заполнены, сгенерируем текущие значения
                if not start_time:
                    start_time = datetime.now(tz=datetime.UTC).isoformat()
                if not end_time:
                    end_time = datetime.now(tz=datetime.UTC).isoformat()
                
                # Сервер ожидает определенный формат данных
                # Добавляем все обязательные поля
                duration_seconds = activity_dict.get('duration_seconds', 0)
                if duration_seconds is None or duration_seconds == 0:
                    duration_seconds = 1  # Минимальная длительность
                
                # Вычисляем длительность на основе start_time и end_time
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    # Вычисляем разницу во времени
                    time_diff = end_dt - start_dt
                    calculated_seconds = time_diff.total_seconds()
                    
                    if calculated_seconds <= 0:
                        calculated_seconds = duration_seconds if duration_seconds > 0 else 1
                        # Создаем объект timedelta для поля duration
                        duration_obj = timedelta(seconds=calculated_seconds)
                    else:
                        # Используем реальную разницу во времени
                        duration_obj = time_diff
                except Exception as e:
                    logger.error(f"Ошибка при вычислении длительности: {e}")
                    calculated_seconds = duration_seconds if duration_seconds > 0 else 1
                    duration_obj = timedelta(seconds=calculated_seconds)
                    
                # Добавляем отладочную информацию
                logger.info(f"Вычисленная длительность: {calculated_seconds} секунд")
                
                # Определяем ID приложения на основе имени процесса
                app_name = activity_dict.get('app_name', '')
                
                # Проверяем, есть ли уже такое приложение в кэше
                app_id = None
                if app_name.lower() in self.app_cache:
                    app_id = self.app_cache[app_name.lower()]
                    logger.debug(f"Найден ID в кэше для {app_name}: {app_id}")
                else:
                    # Если нет в кэше, создаем новое приложение на сервере
                    try:
                        # Создаем новое приложение
                        app_data = {
                            'name': app_name,
                            'process_name': app_name,
                            'is_productive': False  # По умолчанию не продуктивное
                        }
                        
                        # Отправляем запрос на создание приложения
                        app_url = f"{self.api_base_url}applications/"
                        logger.info(f"Отправляем запрос на создание приложения: {app_url}")
                        app_response = self.session.post(app_url, json=app_data)
                        
                        if app_response.status_code == 201:  # Создано успешно
                            app_data = app_response.json()
                            app_id = app_data.get('id')
                            # Сохраняем в кэш
                            self.app_cache[app_name.lower()] = app_id
                            logger.info(f"Создано новое приложение: {app_name} с ID={app_id}")
                        else:
                            # Если не удалось создать, используем ID=1 по умолчанию
                            app_id = 1
                            logger.warning(f"Не удалось создать приложение {app_name}, используем ID по умолчанию")
                    except Exception as e:
                        # В случае ошибки используем ID=1
                        app_id = 1
                        logger.error(f"Ошибка при создании приложения {app_name}: {e}")
                
                # Если все равно не получили ID, используем значение по умолчанию
                if app_id is None:
                    app_id = 1
                    
                # Для отладки выводим информацию о выбранном ID
                logger.info(f"Для приложения {app_name} выбран ID={app_id}")
                
                # Добавляем количество нажатий клавиш в пайлоад
                keyboard_presses = activity_dict.get('keyboard_presses', 0)
                if keyboard_presses == 0 and self.keyboard_press_count > 0:
                    keyboard_presses = self.keyboard_press_count
                    # Сбрасываем счетчик после отправки
                    logger.info(f"Отправляем клавиатурную активность: {self.keyboard_press_count} нажатий")
                    self.keyboard_press_count = 0
                    
                api_payload = {
                    'application': app_id,  # Используем правильный ID приложения
                    'title': activity_dict.get('window_title', ''),
                    'start_time': start_time,
                    'end_time': end_time,
                    # Не отправляем duration, так как сервер вычислит его автоматически
                    'is_productive': activity_dict.get('is_useful', False),
                    'app_name': app_name,
                    'keyboard_presses': keyboard_presses  # Добавляем количество нажатий клавиш
                    # Удаляем поле user, так как пользователь определяется по токену на сервере
                }
                
                # Добавляем отладочную информацию
                logger.info(f"Отправка активности: start_time={start_time}, end_time={end_time}, длительность={calculated_seconds} секунд")
                activities_to_send_payload.append(api_payload)

            if not activities_to_send_payload:
                logger.debug("Нет данных для отправки после фильтрации.")
                return
                
            # Отправляем данные на сервер
            logger.info(f"Отправка {len(activities_to_send_payload)} записей активности на сервер.")
            logger.info(f"API URL: {api_url}, Токен: {auth_token[:10]}...")
            
            # Сервер ожидает отдельные записи, а не массив
            # Отправляем каждую запись по отдельности
            success_count = 0
            for payload in activities_to_send_payload:
                try:
                    # Добавляем отладочную информацию о пайлоаде
                    logger.info(f"Отправляем пайлоад: {payload}")
                    response = self.session.post(api_url, json=payload, headers=headers, timeout=30)
                    if response.status_code in [200, 201]:
                        success_count += 1
                        logger.info(f"Успешно отправлено: {response.status_code} - {response.text}")
                    elif response.status_code == 401:
                        # Ошибка авторизации - токен недействителен
                        logger.error(f"Ошибка авторизации: {response.status_code} - {response.text}")
                        
                        # Удаляем недействительный токен из конфигурации
                        if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'auth_token'):
                            self.config.set('Credentials', 'auth_token', '')
                        if self.config.has_section('Server') and self.config.has_option('Server', 'token'):
                            self.config.set('Server', 'token', '')
                        if self.config.has_section('API') and self.config.has_option('API', 'token'):
                            self.config.set('API', 'token', '')
                        if self.config.has_option('DEFAULT', 'token'):
                            self.config.set('DEFAULT', 'token', '')
                            
                        # Сохраняем обновленную конфигурацию
                        self._save_config(self.config)
                        
                        # Запрашиваем повторную авторизацию
                        logger.info("Требуется повторная авторизация. Запрашиваем новый токен...")
                        
                        # Сигнал для показа диалога авторизации
                        self.login_required_signal.emit()
                        
                        # Возвращаем все активности обратно в очередь для повторной отправки
                        for activity in activities_to_send:
                            self.activity_queue.put(activity)
                        
                        # Прерываем отправку
                        return
                    else:
                        logger.error(f"Ошибка при отправке записи: {response.status_code} - {response.text}")
                        # Возвращаем активность обратно в очередь
                        for i, activity in enumerate(activities_to_send):
                            if activity.get('app_name') == payload.get('app_name') and activity.get('start_time_iso_utc') == payload.get('start_time'):
                                self.activity_queue.put(activity)
                                break
                except Exception as e:
                    logger.error(f"Ошибка при отправке записи: {e}")
            
            # Создаем фиктивный ответ для обработки в основном коде
            class DummyResponse:
                def __init__(self, status_code):
                    self.status_code = status_code
                    self.text = f"Успешно отправлено {success_count} из {len(activities_to_send_payload)} записей"
            
            response = DummyResponse(200 if success_count > 0 else 400)
            
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"Успешно отправлено {len(activities_to_send_payload)} записей активности.")
                self.status_bar.showMessage(f"Отправлено {len(activities_to_send_payload)} записей активности.")
            elif response.status_code == 401:
                logger.warning("Токен недействителен, требуется повторная авторизация.")
                # Удаляем устаревший токен из секций Credentials, Server, API и DEFAULT
                if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'auth_token'):
                    self.config.remove_option('Credentials', 'auth_token')
                if self.config.has_section('Server') and self.config.has_option('Server', 'token'):
                    self.config.remove_option('Server', 'token')
                if self.config.has_section('API') and self.config.has_option('API', 'token'):
                    self.config.remove_option('API', 'token')
                if self.config.has_option(self.config.default_section, 'token'):
                    self.config.remove_option(self.config.default_section, 'token')
                # Включаем демо-режим до повторной авторизации
                if not self.config.has_section('Settings'):
                    self.config.add_section('Settings')
                self.config.set('Settings', 'demo_mode', 'True')
                # Сохраняем конфигурацию и очищаем заголовок авторизации
                self._save_config(self.config)
                self.session.headers.pop('Authorization', None)
                # Запрашиваем повторную авторизацию
                QTimer.singleShot(0, self.show_login_dialog_if_needed)
                # Возвращаем активности обратно в очередь
                for activity in activities_to_send:
                    self.activity_queue.put(activity)
                return
            else:
                logger.error(f"Ошибка при отправке данных: {response.status_code} - {response.text}")
                self.status_bar.showMessage(f"Ошибка отправки данных: {response.status_code}")
                # Возвращаем активности обратно в очередь
                for activity in activities_to_send:
                    self.activity_queue.put(activity)
        except requests.RequestException as e:
            logger.error(f"Ошибка сети при отправке данных: {e}", exc_info=True)
            self.status_bar.showMessage(f"Ошибка сети: {str(e)[:50]}...")
            # Возвращаем активности обратно в очередь
            for activity in activities_to_send:
                self.activity_queue.put(activity)
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при отправке данных: {e}", exc_info=True)
            self.status_bar.showMessage(f"Ошибка: {str(e)[:50]}...")
            # Возвращаем активности обратно в очередь
            for activity in activities_to_send:
                self.activity_queue.put(activity)

    def show_settings_dialog(self):
        dialog = SettingsDialog(self) # Передаем ссылку на главное окно
        dialog.exec_()

    def check_connection(self):
        """Проверяет соединение с сервером"""
        # Если включен демо-режим, пропускаем проверку
        if self.config.getboolean('Settings', 'demo_mode', fallback=False):
            self.connection_status.setText("Статус подключения: Оффлайн-режим")
            self.connection_status.setStyleSheet("QLabel { color: orange; }")
            return
            
        # Если нет токена, вызываем диалог авторизации
        auth_token = None
        if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'auth_token'):
            auth_token = self.config.get('Credentials', 'auth_token')
        
        if not auth_token:
            self.login_required_signal.emit()
            return
            
        # Получаем URL API
        api_url = None
        if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'api_base_url'):
            api_url = self.config.get('Credentials', 'api_base_url').rstrip('/')
        else:
            api_url = 'http://localhost:8000/api'
            
        try:
            # Проверяем соединение напрямую через запрос
            headers = {'Authorization': f'Bearer {auth_token}'} if auth_token else {}
            response = requests.get(f"{api_url}/", headers=headers, timeout=(3, 5))
            
            if response.status_code == 200:
                self.connection_status.setText(f"Статус подключения: Подключено ({api_url})")
                self.connection_status.setStyleSheet("QLabel { color: green; }")
                logger.info(f"Проверка соединения: успешно")
            elif response.status_code == 401:
                self.connection_status.setText("Статус подключения: Ошибка авторизации")
                self.connection_status.setStyleSheet("QLabel { color: red; }")
                logger.warning(f"Ошибка проверки соединения: Недействительный токен (401)")
                
                # Планируем показ диалога авторизации с задержкой
                QTimer.singleShot(1000, self.login_required_signal.emit)
            else:
                self.connection_status.setText("Статус подключения: Ошибка")
                self.connection_status.setStyleSheet("QLabel { color: red; }")
                logger.warning(f"Ошибка проверки соединения: {response.status_code}")
        except Exception as e:
            self.connection_status.setText("Статус подключения: Ошибка")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            logger.error(f"Ошибка при проверке соединения: {e}")
            
            # Отображаем информацию об ошибке
            self.status_bar.showMessage(f"Ошибка соединения: {str(e)[:100]}")
            
            # Планируем показ диалога авторизации с задержкой
            QTimer.singleShot(1000, self.login_required_signal.emit)

    def periodic_ui_update(self):
        """Периодически обновляет интерфейс с текущими данными"""
        try:
            # Обновляем отображение текущей активности
            if self.current_activity_data:
                app_name = self.current_activity_data.get('app_name', '')
                
                # Обновляем отображение времени активности
                if self.activity_start_time:
                    elapsed = time.time() - self.activity_start_time
                    hours, remainder = divmod(int(elapsed), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                    self.current_activity_time_label.setText(f"Время: {time_str}")
                    
                # Обновляем отображение клавиатурной активности
                self.keyboard_activity_label.setText(f"Клавиатурная активность: {self.keyboard_press_count} нажатий")
                
                # Обновляем статус бар
                self.status_bar.showMessage(f"Отслеживается: {app_name} - {time_str} - Клавиатура: {self.keyboard_press_count}")
            else:
                self.status_bar.showMessage("Нет активной сессии отслеживания")
                
        except Exception as e:
            logger.error(f"Ошибка при периодическом обновлении UI: {e}", exc_info=True)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent # Сохраняем ссылку на главное окно для доступа к его данным/методам
        self.setWindowTitle("Настройки отслеживания")
        self.setGeometry(200, 200, 700, 500) # Немного увеличим размер
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.app_list_widget = QTableWidget()
        self.app_list_widget.setColumnCount(3)
        self.app_list_widget.setHorizontalHeaderLabels(["Приложение (имя процесса)", "Отслеживать", "Статус полезности"])
        self.app_list_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.app_list_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.app_list_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.app_list_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.app_list_widget.setEditTriggers(QAbstractItemView.NoEditTriggers) # Запрет редактирования текста ячеек напрямую
        
        layout.addWidget(self.app_list_widget)

        # Кнопки Сохранить и Отмена
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept) # accept - стандартный слот QDialog
        self.button_box.rejected.connect(self.reject) # reject - стандартный слот QDialog
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.load_settings()

    def load_settings(self):
        logger.debug("Загрузка настроек в SettingsDialog...")
        current_tracked_config = self.main_window.tracked_applications_config
        discovered_apps_list = self.main_window.get_discovered_applications()

        # Объединяем известные отслеживаемые приложения и обнаруженные
        all_apps_to_display = set(discovered_apps_list) # Начинаем с обнаруженных
        all_apps_to_display.update(current_tracked_config.keys()) # Добавляем те, что уже в конфиге
        
        sorted_app_list = sorted(list(all_apps_to_display))

        self.app_list_widget.setRowCount(len(sorted_app_list))

        for row, app_name in enumerate(sorted_app_list):
            app_name_item = QTableWidgetItem(app_name)
            # app_name_item.setFlags(app_name_item.flags() & ~Qt.ItemIsEditable) # Делаем имя нередактируемым

            # Чекбокс "Отслеживать"
            checkbox_widget = QCheckBox()
            checkbox_widget.setStyleSheet("margin-left:10px; margin-right:10px;") # Для центрирования
            is_tracked = app_name in current_tracked_config
            checkbox_widget.setChecked(is_tracked)
            
            # Комбо-бокс "Статус"
            status_combo = QComboBox()
            status_combo.addItems(["Полезное", "Неполезное"])
            if is_tracked:
                is_useful = current_tracked_config.get(app_name, True) # По умолчанию True, если вдруг нет ключа
                status_combo.setCurrentIndex(0 if is_useful else 1)
            else:
                status_combo.setCurrentIndex(0) # По умолчанию "Полезное"
            status_combo.setEnabled(is_tracked) # Активен, только если отслеживается

            # Связываем состояние чекбокса с активностью комбо-бокса
            checkbox_widget.toggled.connect(status_combo.setEnabled)

            self.app_list_widget.setItem(row, 0, app_name_item)
            self.app_list_widget.setCellWidget(row, 1, checkbox_widget)
            self.app_list_widget.setCellWidget(row, 2, status_combo)
        
        logger.debug(f"Загружено {len(sorted_app_list)} приложений в таблицу настроек.")

    def accept(self):
        logger.info("Сохранение настроек из SettingsDialog...")
        new_tracked_config = {}
        for row in range(self.app_list_widget.rowCount()):
            app_name_item = self.app_list_widget.item(row, 0)
            checkbox_widget = self.app_list_widget.cellWidget(row, 1)
            status_combo = self.app_list_widget.cellWidget(row, 2)

            if app_name_item and checkbox_widget and status_combo:
                app_name = app_name_item.text()
                if checkbox_widget.isChecked():
                    is_useful = status_combo.currentIndex() == 0 # 0 - Полезное, 1 - Неполезное
                    new_tracked_config[app_name] = is_useful
            else:
                logger.warning(f"Пропуск строки {row} в SettingsDialog: не найдены все виджеты.")

        self.main_window.update_tracked_applications_config(new_tracked_config)
        super().accept() # Закрывает диалог со статусом QDialog.Accepted

    def reject(self):
        logger.info("Изменения в SettingsDialog отменены.")
        super().reject() # Закрывает диалог со статусом QDialog.Rejected


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec_()) 