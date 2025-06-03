import importlib
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
from logging.handlers import RotatingFileHandler, WatchedFileHandler
import queue
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
import webbrowser
import re
import warnings
import random
import string
import platform
import tempfile
try:
    import win32gui
    import win32process
    import win32api
    import win32con
except ImportError:
    # Не загружаем win32 модули на не-Windows системах
    pass
try:
    import jwt
except ImportError:
    # jwt может быть не установлен
    pass

def get_base_path():
    """Получение базового пути к ресурсам"""
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return Path(base_path)

def get_app_data_dir(app_name="TimeTracker"):
    """
    Получение директории для хранения данных приложения, 
    совместимой с разными ОС.
    
    Args:
        app_name: Имя приложения для создания поддиректории
        
    Returns:
        Path: Путь к директории для хранения данных
    """
    system = platform.system()
    
    if system == "Windows":
        # На Windows используем %APPDATA%
        base_dir = os.environ.get("APPDATA")
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    elif system == "Linux":
        # На Linux используем ~/.config
        base_dir = os.path.join(os.path.expanduser("~"), ".config")
    elif system == "Darwin":
        # На macOS используем ~/Library/Application Support
        base_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        # Для других ОС используем временную директорию
        base_dir = tempfile.gettempdir()
    
    # Создаем полный путь к директории приложения
    app_dir = Path(os.path.join(base_dir, app_name))
    
    # Создаем директорию, если она не существует
    app_dir.mkdir(parents=True, exist_ok=True)
    
    return app_dir

# Настройка логирования
def setup_logging():
    """
    Настраивает логирование с учетом особенностей ОС.
    
    Returns:
        logger: Настроенный объект логгера
    """
    # Получаем директорию для хранения логов
    app_data_dir = get_app_data_dir()
    log_dir = app_data_dir / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / 'tracker.log'
    
    logger = logging.getLogger('TimeTracker')
    logger.setLevel(logging.INFO)
    
    # Очищаем существующие обработчики логов, если они есть
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Выбираем обработчик файлов в зависимости от ОС
    system = platform.system()
    try:
        if system == "Windows":
            # На Windows используем обработчик с блокировкой файлов
            # для предотвращения конфликтов доступа
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=1024*1024,  # 1 МБ
                backupCount=5,
                encoding='utf-8',
                delay=True  # Открываем файл только при необходимости записи
            )
            
            # Добавляем обработчик с более безопасной ротацией для Windows
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        else:
            # На Unix-системах используем WatchedFileHandler,
            # который автоматически переоткрывает файл при ротации
            file_handler = WatchedFileHandler(
                log_file,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Дополнительно настраиваем ротацию через системный logrotate
            # для Unix-систем (логика ротации в системе)
    except Exception as e:
        # Если не удалось настроить обработчик файлов, логируем ошибку
        # и продолжаем работу только с консольным выводом
        console_handler.setLevel(logging.WARNING)
        logger.warning(f"Не удалось настроить логирование в файл: {e}")
        
        # Создаем резервный обработчик в безопасной директории
        try:
            backup_log_file = Path(tempfile.gettempdir()) / f'tracker_{random.randint(1000, 9999)}.log'
            backup_handler = logging.FileHandler(backup_log_file, encoding='utf-8')
            backup_handler.setFormatter(formatter)
            logger.addHandler(backup_handler)
            logger.info(f"Логирование перенаправлено в резервный файл: {backup_log_file}")
        except Exception:
            logger.warning("Не удалось создать резервный файл логов. Логирование только в консоль.")
    
    # Добавляем обработку ошибок логирования
    logger.info(f"Логирование настроено. Файл логов: {log_file}")
    return logger

logger = setup_logging()

# Импортируем APIClient из api_client.py вместо использования встроенного класса
try:
    from api_client import APIClient
except ImportError:
    logger.error("Не удалось импортировать APIClient. Проверьте наличие файла api_client.py")
    class APIClient:
        """Заглушка для APIClient в случае ошибки импорта"""
        def __init__(self, *args, **kwargs):
            pass

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
            
            # Формируем URL для авторизации правильно
            # Если base_url уже содержит /api, то добавляем только /token/
            if self.base_url.endswith('/api') or self.base_url.endswith('/api/'):
                auth_url = f"{self.base_url.rstrip('/')}/token/"
            else:
                # Если base_url не содержит /api, добавляем /api/token/
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
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Получаем токен для Django REST Framework
                token = data.get('token')
                if token:
                    self.token = token
                    logger.info("Успешная авторизация на сервере")
                    
                    # Проверяем доступность приложений после авторизации
                    if self.get_applications():
                        return True, token
                    else:
                        logger.warning("Авторизация прошла, но не удалось загрузить приложения")
                        return True, token  # Всё равно считаем успешным
                else:
                    logger.error("Токен не найден в ответе сервера")
                    return False, "Сервер не вернул токен"
            else:
                logger.error(f"Ошибка авторизации: {response.status_code} - {response.text}")
                return False, f"Ошибка сервера: {response.status_code}"
        except requests.exceptions.Timeout:
            logger.error("Таймаут при авторизации")
            return False, "Превышено время ожидания ответа сервера"
        except requests.exceptions.ConnectionError:
            logger.error("Ошибка соединения при авторизации")
            return False, "Не удалось подключиться к серверу"
        except Exception as e:
            logger.error(f"Неожиданная ошибка при авторизации: {e}")
            return False, f"Ошибка: {str(e)}"
            
    def get_applications(self):
        """Получение списка приложений с сервера"""
        try:
            if not self.token:
                logger.warning("Токен отсутствует для получения приложений")
                return []
            
            # Формируем URL для получения приложений правильно
            if self.base_url.endswith('/api') or self.base_url.endswith('/api/'):
                apps_url = f"{self.base_url.rstrip('/')}/applications/"
            else:
                apps_url = f"{self.base_url.rstrip('/')}/api/applications/"
            
            logger.info(f"Получение списка приложений с URL: {apps_url}")
            
            headers = {
                'Authorization': f'Token {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                apps_url,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                apps = response.json()
                logger.info(f"Загружено {len(apps)} приложений с сервера")
                return apps
            else:
                logger.error(f"Ошибка получения приложений: {response.status_code} - {response.text}")
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
        """Отправка данных активности на сервер"""
        try:
            if not self.token:
                logger.warning("Токен отсутствует для отправки активности")
                return False
                
            # Формируем URL для отправки активности правильно
            if self.base_url.endswith('/api') or self.base_url.endswith('/api/'):
                activities_url = f"{self.base_url.rstrip('/')}/activities/"
            else:
                activities_url = f"{self.base_url.rstrip('/')}/api/activities/"
            
            headers = {
                'Authorization': f'Token {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                activities_url,
                json=activities,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Успешно отправлено {len(activities)} активностей")
                return True
            else:
                logger.error(f"Ошибка отправки активности: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при отправке активности: {e}")
            return False


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Авторизация")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setMinimumWidth(400)
        self.api_client = None
        self.allow_close_without_auth = False
        self.setup_ui()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        layout = QVBoxLayout()
        
        # Основные элементы формы
        form_layout = QFormLayout()
        
        # URL сервера
        self.server_url = QLineEdit()
        # Загружаем URL из настроек
        if self.parent() and hasattr(self.parent(), 'api_base_url'):
            self.server_url.setText(self.parent().api_base_url)
        else:
            self.server_url.setText("http://localhost:8000")
            
        form_layout.addRow("URL сервера:", self.server_url)
        
        # Тестовая кнопка для проверки соединения
        self.test_button = QPushButton("Проверить соединение")
        self.test_button.clicked.connect(self.test_connection)
        form_layout.addRow("", self.test_button)
        
        # Имя пользователя
        self.username = QLineEdit()
        form_layout.addRow("Имя пользователя:", self.username)
        
        # Пароль
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Пароль:", self.password)
        
        # Добавляем форму на основной layout
        layout.addLayout(form_layout)
        
        # Кнопки диалога
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.authenticate)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        self.setLayout(layout)
    
    def closeEvent(self, event):
        """Переопределяем обработку закрытия окна для предотвращения закрытия без авторизации"""
        # Больше не поддерживаем автономную работу
        # Показываем сообщение, что авторизация обязательна
        QMessageBox.critical(self, "Требуется авторизация", 
                            "Для работы приложения требуется авторизация!\n\n"
                            "Пожалуйста, подключитесь к серверу и введите данные учетной записи.")
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
                    
                    # Предотвращаем дублирование '/api/' в URL
                    base_api_url = server_url.rstrip('/')
                    if not base_api_url.endswith('/api'):
                        base_api_url += '/api'
                        
                    # Сохраняем токен и данные пользователя
                    config.set('Credentials', 'api_base_url', base_api_url + '/')
                    config.set('Credentials', 'auth_token', self.api_client.token)
                    config.set('Credentials', 'username', username)
                    
                    # Для простых токенов Django используем фиксированный user_id или получаем из конфигурации
                    user_id = "3"  # ID пользователя heist
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
        """Инициализация приложения"""
        super().__init__(parent)
        
        # Инициализация переменных класса
        self.tracking_active = False
        self.tracking_paused = False  # Добавляем переменную для паузы отслеживания
        self.api_client = None
        self.keyboard_listener = None
        self.mouse_listener = None
        self.activity_queue = queue.Queue()
        self.current_activity = None
        self.current_activity_data = {}  # Инициализируем пустым словарем
        self.db_connection = None
        self.config = None
        self.keyboard_press_count = 0
        self.mouse_move_count = 0
        self.mouse_click_count = 0
        self.last_window_title = ""
        self.last_app_name = ""
        self.app_list = None
        self.config_loaded = False
        self.is_idle = False
        self.last_activity_time = time.time()
        self.activities_to_send = []
        self.activity_start_time = None  # Время начала текущей активности
        self.idle_threshold_seconds = 300  # По умолчанию 5 минут
        self.session = requests.Session()  # Инициализируем сессию для HTTP запросов
        
        # Список игнорируемых системных процессов
        self.ignored_processes = [
            "explorer.exe", 
            "system", 
            "system idle process", 
            "dwm.exe", 
            "taskhost.exe", 
            "taskhostw.exe", 
            "svchost.exe",
            "runtimebroker.exe",
            "searchui.exe",
            "shellexperiencehost.exe",
            "winlogon.exe",
            "wininit.exe",
            "csrss.exe",
            "services.exe",
            "lsass.exe",
            "fontdrvhost.exe",
            "smss.exe"
        ]
        
        # Получаем пути к данным и конфигурации в зависимости от ОС
        self.app_data_dir = get_app_data_dir()
        self.setup_app_directories()
        
        # Загружаем конфигурацию
        self.config = self.load_config() 
        self.config_loaded = True
        
        # Проверяем и исправляем конфигурацию
        self.validate_and_fix_config()
        
        # Загружаем значение порога бездействия из конфигурации, если есть
        if self.config.has_section('Settings') and self.config.has_option('Settings', 'idle_threshold_seconds'):
            self.idle_threshold_seconds = self.config.getint('Settings', 'idle_threshold_seconds')
        
        # Инициализируем API клиент
        self.init_api_client()
        
        # Загружаем конфигурацию отслеживания
        self.load_tracked_applications_config()
        
        # Инициализируем пользовательский интерфейс
        self.init_ui()
        
        # Настраиваем иконку в системном трее
        self.init_tray_icon()
        
        # Устанавливаем слушатели активности и таймеры
        self.setup_activity_listeners_and_tracking_timer()
        
        # Запускаем обновление списка приложений
        self.update_app_list()
        
        # Проверяем соединение с сервером
        QTimer.singleShot(1000, self.check_connection)
        
        # Запускаем обновление UI и проверку соединения
        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.timeout.connect(self.periodic_ui_update)
        self.ui_update_timer.start(5000)  # Обновляем каждые 5 секунд
        
        # Отображаем окно входа, если необходимо
        QTimer.singleShot(1500, self.show_login_dialog_if_needed)
        
        logger.info("Приложение TimeTracker успешно инициализировано")
        
    def setup_app_directories(self):
        """Создает необходимые директории для работы приложения"""
        # Создаем основные директории
        # data_dir - для хранения локальных данных (БД SQLite, кэш и т.д.)
        # logs_dir - для хранения логов
        # config_dir - для хранения конфигурационных файлов
        
        self.data_dir = self.app_data_dir / 'data'
        self.logs_dir = self.app_data_dir / 'logs'
        self.config_dir = self.app_data_dir
        
        # Создаем директории, если они не существуют
        for directory in [self.data_dir, self.logs_dir, self.config_dir]:
            directory.mkdir(exist_ok=True, parents=True)
            
        # Устанавливаем путь к базе данных SQLite
        self.db_path = self.data_dir / 'activity.db'
        
        logger.info(f"Директории приложения настроены: {self.app_data_dir}")
        
    def init_api_client(self):
        """Инициализирует API клиент для связи с сервером"""
        try:
            # Получаем базовый URL API из конфигурации
            base_url = self.config.get('API', 'base_url', fallback='http://localhost:8000')
            
            # Проверяем формат URL и корректируем его при необходимости
            if base_url.endswith('/api/api'):
                # Исправляем ошибку дублирования /api
                base_url = base_url.replace('/api/api', '/api')
            elif not '/api' in base_url:
                # Добавляем /api, если его нет
                base_url = base_url.rstrip('/') + '/api'
                
            # Записываем обратно в конфигурацию, если URL был исправлен
            if base_url != self.config.get('API', 'base_url', fallback=''):
                self.config.set('API', 'base_url', base_url)
                self._save_config()
                
            # Создаем экземпляр APIClient
            self.api_client = APIClient(base_url)
            
            # Сохраняем базовый URL для использования в других методах
            self.api_base_url = base_url
            
            # Пробуем восстановить токен из конфигурации
            token = self.config.get('API', 'token', fallback=None)
            if token:
                self.api_client.token = token
                logger.info("Токен API восстановлен из конфигурации")
                
            logger.info(f"API клиент инициализирован с базовым URL: {base_url}")
        except Exception as e:
            logger.error(f"Ошибка при инициализации API клиента: {e}")
            # Создаем заглушку для API клиента в случае ошибки
            self.api_client = type('DummyAPIClient', (), {
                'login': lambda *args, **kwargs: (False, "Ошибка подключения к API"),
                'get_applications': lambda *args, **kwargs: [],
                'get_application_id': lambda *args, **kwargs: None,
                'token': None
            })

    def load_config(self) -> configparser.ConfigParser:
        """Загрузка конфигурации из файла config.ini"""
        config = configparser.ConfigParser()
        
        # Используем кросс-платформенный путь к файлу конфигурации
        app_data_dir = get_app_data_dir()
        config_file = app_data_dir / 'config.ini'
        
        # Переменная для хранения местоположения конфигурационного файла
        self.config_file_path = config_file
        
        # Список возможных расположений конфигурационного файла
        config_locations = [
            config_file,                     # Основной путь в директории данных приложения
            Path('config.ini'),              # В текущей директории
            Path('desktop_app/config.ini'),  # В поддиректории проекта
            Path(get_base_path()) / 'config.ini',  # В базовой директории приложения
        ]
        
        loaded = False
        
        # Пробуем загрузить из всех возможных мест
        for loc in config_locations:
            try:
                if loc.exists():
                    config.read(loc, encoding='utf-8')
                    logger.info(f"Конфигурация загружена из {loc}")
                    self.config_file_path = loc  # Запоминаем путь к загруженному файлу
                    loaded = True
                    break
            except Exception as e:
                logger.warning(f"Ошибка при загрузке конфигурации из {loc}: {e}")
        
        # Если не нашли конфигурацию, создаем новую
        if not loaded:
            logger.info("Конфигурационный файл не найден. Создание новой конфигурации.")
            config = self.create_default_config()
            
            # Сохраняем новую конфигурацию в предпочтительном месте
            try:
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    config.write(f)
                logger.info(f"Создан новый конфигурационный файл: {self.config_file_path}")
            except Exception as e:
                logger.error(f"Не удалось сохранить новую конфигурацию: {e}")
                
                # Пробуем сохранить в текущей директории как запасной вариант
                try:
                    local_config_path = Path('config.ini')
                    with open(local_config_path, 'w', encoding='utf-8') as f:
                        config.write(f)
                    self.config_file_path = local_config_path
                    logger.info(f"Создан новый конфигурационный файл в текущей директории: {local_config_path}")
                except Exception as backup_error:
                    logger.error(f"Не удалось сохранить резервную конфигурацию: {backup_error}")
                    # Продолжаем с конфигурацией в памяти, без сохранения
        
        # Проверяем, содержит ли конфигурация все необходимые разделы и поля
        self._ensure_config_complete(config)
        
        return config
        
    def _ensure_config_complete(self, config: configparser.ConfigParser) -> None:
        """
        Проверяет и дополняет конфигурацию необходимыми полями
        
        Args:
            config: Объект конфигурации для проверки и дополнения
        """
        default_config = self.create_default_config()
        
        # Проверяем и добавляем недостающие разделы и параметры
        for section in default_config.sections():
            if not config.has_section(section):
                config.add_section(section)
                
            for key, value in default_config[section].items():
                if not config.has_option(section, key):
                    config.set(section, key, value)
        
        # Добавляем или обновляем machine_id, если его нет
        if not config.has_option('Settings', 'machine_id') or not config['Settings']['machine_id']:
            config.set('Settings', 'machine_id', self.get_machine_id(config))
            
        # Сохраняем обновленную конфигурацию, если были изменения
        self._save_config(config)
        
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
        """Создает объект конфигурации со значениями по умолчанию"""
        config = configparser.ConfigParser()
        
        # API и серверные настройки
        config.add_section('API')
        config.set('API', 'base_url', 'http://127.0.0.1:8001/api')
        config.set('API', 'token', '')
        
        config.add_section('Server')
        config.set('Server', 'base_url', 'http://127.0.0.1:8001')
        config.set('Server', 'username', '')
        config.set('Server', 'password', '')
        config.set('Server', 'token', '')
        
        # Основные настройки
        config.add_section('Settings')
        config.set('Settings', 'update_interval', '5')
        config.set('Settings', 'log_level', 'INFO')
        config.set('Settings', 'auto_start', 'false')
        config.set('Settings', 'minimize_to_tray', 'true')
        config.set('Settings', 'machine_id', '')  # Будет заполнено позже
        config.set('Settings', 'idle_threshold_seconds', '300')
        config.set('Settings', 'send_interval_seconds', '10')
        config.set('Settings', 'max_send_batch_size', '20')
        config.set('Settings', 'demo_mode', 'false')
        
        # Отслеживаемые приложения
        config.add_section('Applications')
        
        # Настройки логирования
        config.add_section('Logging')
        config.set('Logging', 'level', 'INFO')
        config.set('Logging', 'file', 'activity.log')
        
        # Метаданные
        config.add_section('Meta')
        config.set('Meta', 'locked', 'false')
        
        # Учетные данные
        config.add_section('Credentials')
        # Правильный формат URL без дублирования /api
        config.set('Credentials', 'api_base_url', 'http://127.0.0.1:8001/api/')
        config.set('Credentials', 'username', '')
        config.set('Credentials', 'auth_token', '')
        config.set('Credentials', 'user_id', '')
        
        # Платформенно-зависимые настройки
        config.add_section('Platform')
        config.set('Platform', 'system', platform.system())
        config.set('Platform', 'version', platform.version())
        config.set('Platform', 'machine', platform.machine())
        
        return config
        
    def _save_config(self, config_object_to_save: Optional[configparser.ConfigParser] = None):
        """Сохраняет конфигурацию в файл"""
        config_to_save = config_object_to_save or self.config
        try:
            if not hasattr(self, 'config_file_path'):
                # Если путь к файлу конфигурации не установлен, используем кросс-платформенный путь
                self.config_file_path = get_app_data_dir() / 'config.ini'
                
            # Создаем директорию для конфигурации, если она не существует
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
                
            with open(self.config_file_path, 'w', encoding='utf-8') as config_file:
                config_to_save.write(config_file)
                
            logger.info(f"Конфигурация успешно сохранена в {self.config_file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении конфигурации: {e}")
            
            # Пробуем сохранить в текущей директории как запасной вариант
            try:
                local_config_path = Path('config.ini')
                with open(local_config_path, 'w', encoding='utf-8') as f:
                    config_to_save.write(f)
                self.config_file_path = local_config_path
                logger.info(f"Конфигурация сохранена в резервное место: {local_config_path}")
                return True
            except Exception as backup_error:
                logger.error(f"Не удалось сохранить резервную конфигурацию: {backup_error}")
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
        """Настройка слушателей и основного таймера трекинга"""
        try:
            # Принудительно импортируем библиотеки pynput
            try:
                from pynput import keyboard, mouse
                logger.info("Библиотеки pynput успешно импортированы")
            except ImportError as e:
                logger.error(f"Библиотеки pynput не установлены: {e}")
                return
                
            # Инициализируем счетчики активности, если их нет
            if not hasattr(self, 'keyboard_press_count'):
                self.keyboard_press_count = 0
            if not hasattr(self, 'mouse_click_count'):
                self.mouse_click_count = 0
            if not hasattr(self, 'mouse_move_count'):
                self.mouse_move_count = 0
                
            # Безопасное создание слушателей без методов подавления
            try:
                # Используем безопасные обработчики событий
                self.keyboard_listener = keyboard.Listener(
                    on_press=lambda key: self.on_keyboard_press(key),
                    on_release=None
                )
                logger.info("Слушатель клавиатуры создан успешно")
            except Exception as e:
                logger.error(f"Ошибка при создании слушателя клавиатуры: {e}")
                self.keyboard_listener = None
                
            try:
                # Обходим проблему с NotImplementedError при подавлении событий мыши
                self.mouse_listener = mouse.Listener(
                    on_move=lambda x, y: self.on_mouse_move(x, y),
                    on_click=lambda x, y, button, pressed: self.on_mouse_click(x, y, button, pressed),
                    on_scroll=None
                )
                logger.info("Слушатель мыши создан успешно")
            except Exception as e:
                logger.error(f"Ошибка при создании слушателя мыши: {e}")
                self.mouse_listener = None
                
            # Запускаем слушатели, если они были успешно созданы
            if self.keyboard_listener:
                try:
                    if not self.keyboard_listener.is_alive():
                        self.keyboard_listener.start()
                        logger.info("Слушатель клавиатуры запущен успешно")
                except Exception as e:
                    logger.error(f"Ошибка при запуске слушателя клавиатуры: {e}")
                    self.keyboard_listener = None
                    
            if self.mouse_listener:
                try:
                    if not self.mouse_listener.is_alive():
                        self.mouse_listener.start()
                        logger.info("Слушатель мыши запущен успешно")
                except Exception as e:
                    logger.error(f"Ошибка при запуске слушателя мыши: {e}")
                    self.mouse_listener = None
                    
            # Настраиваем таймер обновления интерфейса
            update_interval_seconds = self.config.getint('Settings', 'update_interval', fallback=5)
            self.tracking_timer = QTimer(self)
            self.tracking_timer.timeout.connect(self.update_tracking)
            self.tracking_timer.start(update_interval_seconds * 1000)  # Преобразуем секунды в миллисекунды
            
            # Запускаем таймер отправки данных каждые 10 секунд для быстрой синхронизации
            send_interval_seconds = self.config.getint('Settings', 'send_interval_seconds', fallback=10)
            self.sending_timer = QTimer(self)
            self.sending_timer.timeout.connect(self.send_activity_data)
            self.sending_timer.start(send_interval_seconds * 1000)  # Используем настройку из конфигурации
            
            logger.info(f"Настройка слушателей и таймеров завершена успешно. Интервал обновления: {update_interval_seconds} сек, отправка данных: {send_interval_seconds} сек.")
        except Exception as e:
            logger.error(f"Ошибка при настройке слушателей активности: {e}", exc_info=True)
            
    def update_tracking(self):
        """Обновляет отслеживание активности по таймеру."""
        try:
            # Проверяем состояние простоя
            self.check_idle_state()
            
            # Логируем текущее состояние для отладки
            logger.debug(f"update_tracking: is_idle={self.is_idle}, tracking_paused={getattr(self, 'tracking_paused', 'не установлено')}")
            
            # Если мы не в режиме простоя и не на паузе, проверяем активное окно
            if not self.is_idle and not getattr(self, 'tracking_paused', False):
                active_window_info = self.get_active_window_info()
                
                if active_window_info:
                    app_name = active_window_info.get('app_name', '')
                    window_title = active_window_info.get('window_title', '')
                    
                    logger.debug(f"Активное окно: {app_name} - {window_title[:50]}{'...' if len(window_title) > 50 else ''}")
                    
                    # Пропускаем пустые имена и системные процессы
                    if not app_name or app_name.lower() in ['system', 'system idle process'] or app_name.isdigit():
                        logger.debug(f"Пропускаем системное приложение: {app_name}")
                        return
                    
                    # Проверяем, входит ли процесс в список игнорируемых
                    if app_name and hasattr(self, 'ignored_processes') and self.ignored_processes:
                        app_name_lower = app_name.lower()
                        for ignored_proc in self.ignored_processes:
                            if ignored_proc.lower() == app_name_lower:
                                logger.debug(f"Пропускаем игнорируемое приложение: {app_name}")
                                return
                    
                    # Если у нас уже есть активная сессия
                    if self.current_activity_data:
                        # Если приложение или заголовок изменились, завершаем текущую сессию
                        if (self.current_activity_data['app_name'] != app_name or 
                            self.current_activity_data['window_title'] != window_title):
                            logger.info(f"Изменилось активное окно: {self.current_activity_data['app_name']} -> {app_name}")
                            self.end_current_activity_session(event_type="switch")
                            # Начинаем новую сессию
                            is_useful = self.is_app_useful(app_name)
                            self.start_new_activity_session(app_name, window_title, is_useful)
                        else:
                            logger.debug(f"Продолжается сессия для {app_name}, клавиатурных нажатий: {self.keyboard_press_count}")
                    else:
                        # Если нет активной сессии, начинаем новую
                        logger.info(f"Начинаем новую сессию для {app_name}")
                        is_useful = self.is_app_useful(app_name)
                        self.start_new_activity_session(app_name, window_title, is_useful)
                else:
                    logger.debug("Не удалось получить информацию об активном окне")
            else:
                logger.debug(f"Отслеживание приостановлено: is_idle={self.is_idle}, tracking_paused={getattr(self, 'tracking_paused', False)}")
        except Exception as e:
            logger.error(f"Ошибка в функции update_tracking: {e}", exc_info=True)
            
    def on_keyboard_press(self, key):
        """Обработчик нажатия клавиши"""
        try:
            # Инкрементируем счетчик нажатий клавиш
            self.keyboard_press_count += 1
            
            # Обновляем время последней активности для обнаружения простоя
            self.last_activity_time = time.time()
            
            # Каждые 10 нажатий логируем информацию для отладки
            if self.keyboard_press_count % 10 == 0:
                logger.debug(f"Зарегистрировано {self.keyboard_press_count} нажатий клавиш")
                
            # Если находились в режиме простоя, выходим из него
            if self.is_idle:
                self.handle_idle_state_change(False)
        except Exception as e:
            logger.error(f"Ошибка при обработке нажатия клавиши: {e}")
        
        # Функция должна возвращать значение для продолжения слушателя
        return True
        
    def on_mouse_move(self, x, y):
        """Обработчик движения мыши"""
        try:
            # Инкрементируем счетчик движений мыши
            self.mouse_move_count += 1
            
            # Обновляем время последней активности для обнаружения простоя
            self.last_activity_time = time.time()
            
            # Логируем каждое 100-е движение для экономии места в логах
            if self.mouse_move_count % 100 == 0:
                logger.debug(f"Зарегистрировано {self.mouse_move_count} движений мыши")
                
            # Если находились в режиме простоя, выходим из него
            if self.is_idle:
                self.handle_idle_state_change(False)
        except Exception as e:
            logger.error(f"Ошибка при обработке движения мыши: {e}")
            
        # Функция должна возвращать значение для продолжения слушателя
        return True
        
    def on_mouse_click(self, x, y, button, pressed):
        """Обработчик клика мыши"""
        try:
            # Считаем только нажатия кнопок мыши, не отпускания
            if pressed:
                # Инкрементируем счетчик кликов мыши
                self.mouse_click_count += 1
                
                # Обновляем время последней активности для обнаружения простоя
                self.last_activity_time = time.time()
                
                # Логируем каждый 5-й клик для экономии места в логах
                if self.mouse_click_count % 5 == 0:
                    logger.debug(f"Зарегистрировано {self.mouse_click_count} кликов мыши")
                    
                # Если находились в режиме простоя, выходим из него
                if self.is_idle:
                    self.handle_idle_state_change(False)
        except Exception as e:
            logger.error(f"Ошибка при обработке клика мыши: {e}")
            
        # Функция должна возвращать значение для продолжения слушателя
        return True
    
    def check_idle_state(self):
        """Проверяет, находится ли пользователь в состоянии простоя."""
        try:
            # Получаем время с последней активности пользователя
            current_time = time.time()
            idle_time = current_time - self.last_activity_time
            
            # Получаем порог простоя из конфигурации, если он не был установлен ранее
            if not hasattr(self, 'idle_threshold_seconds') or self.idle_threshold_seconds is None:
                self.idle_threshold_seconds = self.config.getint('Settings', 'idle_threshold_seconds', fallback=300)
                logger.debug(f"Установлен порог простоя: {self.idle_threshold_seconds} секунд")
            
            # Проверяем, превышено ли время простоя
            if idle_time > self.idle_threshold_seconds and not self.is_idle:
                # Пользователь перешел в состояние простоя
                self.handle_idle_state_change(False)
            
            # Проверяем, вернулся ли пользователь из состояния простоя
            elif idle_time <= self.idle_threshold_seconds and self.is_idle:
                # Пользователь вернулся из состояния простоя
                self.handle_idle_state_change(True)
        
        except Exception as e:
            logger.error(f"Ошибка при проверке состояния простоя: {e}", exc_info=True)
    
    def handle_idle_state_change(self, is_active):
        """Обрабатывает изменение состояния активности пользователя."""
        try:
            if is_active and self.is_idle:
                # Пользователь вернулся из состояния простоя
                self.is_idle = False
                logger.info("Пользователь вернулся из состояния простоя")
                # Обновляем UI, если он доступен
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage("Активен")
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.setToolTip("Активен")
            elif not is_active and not self.is_idle:
                # Пользователь перешел в состояние простоя
                self.is_idle = True
                logger.info(f"Пользователь перешел в состояние простоя (неактивен {int(time.time() - self.last_activity_time)} секунд)")
                # Приостанавливаем текущую сессию активности, если она есть
                if self.current_activity_data:
                    self.end_current_activity_session(event_type="idle")
                # Обновляем UI, если он доступен
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage(f"Простой (неактивен {int(time.time() - self.last_activity_time)} секунд)")
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.setToolTip(f"Пользователь неактивен. В очереди: {self.activity_queue.qsize()}")
        except Exception as e:
            logger.error(f"Ошибка при обработке изменения состояния простоя: {e}", exc_info=True)

    def track_activity(self):
        """Основной метод отслеживания активности в отдельном потоке."""
        logger.info("Запущен поток отслеживания активности")
        
        # Задержка перед началом отслеживания, чтобы дать время на инициализацию UI
        time.sleep(1)
        
        # Инициализируем переменные для отслеживания текущего активного окна
        current_app_name = None
        current_window_title = None
        
        # Инициализируем атрибут для отслеживания паузы, если он отсутствует
        if not hasattr(self, 'tracking_paused'):
            self.tracking_paused = False
            
        # Убедимся, что список игнорируемых процессов существует
        if not hasattr(self, 'ignored_processes') or self.ignored_processes is None:
            # Создаем список игнорируемых системных процессов, если он не был инициализирован
            self.ignored_processes = [
                "explorer.exe", "system", "system idle process", 
                "dwm.exe", "taskhost.exe", "taskhostw.exe", "svchost.exe",
                "runtimebroker.exe", "searchui.exe", "shellexperiencehost.exe",
                "winlogon.exe", "wininit.exe", "csrss.exe", "services.exe",
                "lsass.exe", "fontdrvhost.exe", "smss.exe"
            ]
            logger.info("Инициализирован список игнорируемых процессов")
        
        while True:
            try:
                # Если отслеживание на паузе, пропускаем итерацию
                if hasattr(self, 'tracking_paused') and self.tracking_paused:
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
                
                # Проверяем, что имя процесса не пустое и не содержит только цифры
                if not app_name or app_name.isdigit():
                    time.sleep(1)
                    continue
                
                # Безопасная проверка на игнорируемые процессы
                should_ignore = False
                if app_name and hasattr(self, 'ignored_processes') and self.ignored_processes:
                    app_name_lower = app_name.lower()
                    # Проверяем, входит ли процесс в список игнорируемых
                    for ignored_proc in self.ignored_processes:
                        if ignored_proc.lower() == app_name_lower:
                            should_ignore = True
                            break
                
                # Если это игнорируемый процесс
                if should_ignore:
                    # Если у нас есть текущая сессия активности,
                    # завершаем ее только если она не относится к тому же игнорируемому процессу
                    if self.current_activity_data and app_name:
                        if self.current_activity_data.get('app_name', '').lower() != app_name.lower():
                            logger.debug(f"Обнаружен игнорируемый процесс: {app_name}. Завершаем текущую сессию.")
                            self.end_current_activity_session(event_type="ignored_process")
                    time.sleep(1)
                    continue
                
                # Если это система или пустое имя, пропускаем итерацию
                if not app_name or app_name.lower() in ['system', 'system idle process'] or app_name.isdigit():
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
        
        # Список приложений (без вкладок)
        apps_group = QWidget()
        apps_layout = QVBoxLayout(apps_group)
        
        apps_title = QLabel("Отслеживаемые приложения:")
        apps_layout.addWidget(apps_title)
        
        # Список всех приложений
        self.app_list = QListWidget()
        self.app_list.setSelectionMode(QListWidget.SingleSelection)
        apps_layout.addWidget(self.app_list)
        
        layout.addWidget(apps_group)
        
        # Кнопки управления
        control_layout = QHBoxLayout()
        
        settings_button = QPushButton("Настройки")
        settings_button.clicked.connect(self.show_settings_dialog)
        
        # Добавляем кнопку в лэйаут
        control_layout.addWidget(settings_button)
        
        layout.addLayout(control_layout)
        
        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово к работе")
        
        # Метка статуса
        self.status_label = QLabel("Статус: Отслеживание активно")
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
        
        # Действие "Открыть веб-интерфейс"
        web_action = QAction("Открыть веб-интерфейс", self)
        web_action.triggered.connect(self.open_web_interface)
        tray_menu.addAction(web_action)
        
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
        self.tray_icon.setToolTip("Time Tracker PRO (отслеживание активно)")
    
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
        """Обновляет список приложений в интерфейсе"""
        try:
            # Периодически синхронизируем список приложений с сервера
            if not hasattr(self, '_last_server_sync_time') or time.time() - self._last_server_sync_time > 30:
                self._last_server_sync_time = time.time()
                sync_result = self.sync_productive_apps_from_server()
                if sync_result:
                    logger.info("Список приложений обновлен с сервера")
            
            # Сохраняем текущее выделение для восстановления после обновления
            selected_app = None
            
            # Получаем текущее выделение
            if self.app_list.selectedItems():
                selected_app = self.app_list.selectedItems()[0].data(Qt.UserRole)

            # Очищаем существующий список
            self.app_list.clear()
            
            # Получаем список запущенных приложений
            running_apps = self.get_discovered_applications()
            logger.info(f"Обнаружено запущенных приложений: {len(running_apps)}")
            logger.debug(f"Запущенные приложения: {running_apps}")
            
            # Создаем словарь для определения, запущено ли приложение
            running_apps_dict = {app.lower(): app for app in running_apps}
            
            # Отсортированный список приложений для отображения
            sorted_apps = []
            
            # Добавляем только запущенные приложения - меняем логику отображения
            for app_name in running_apps:
                app_name_lower = app_name.lower()
                is_tracked = app_name_lower in self.tracked_applications_config
                is_useful = self.tracked_applications_config.get(app_name_lower, False)
                
                item_text = f"{app_name} ({'Полезное' if is_useful else 'Не полезное'})"
                sorted_apps.append((app_name, item_text, True, is_useful))
                
            # Сортируем весь список по названию приложения
            sorted_apps.sort(key=lambda x: x[0].lower())
            
            # Заполняем список
            for app_name, item_text, is_running, is_useful in sorted_apps:
                # Создаем элемент для списка всех приложений
                item_all = QListWidgetItem(item_text)
                item_all.setData(Qt.UserRole, app_name)  # Сохраняем оригинальное имя как данные
                
                # Устанавливаем цвет в зависимости от полезности
                if is_useful:
                    item_all.setForeground(Qt.green)
                else:
                    item_all.setForeground(Qt.red)
                    
                self.app_list.addItem(item_all)
            
            # Восстанавливаем выделение
            if selected_app:
                for i in range(self.app_list.count()):
                    if self.app_list.item(i).data(Qt.UserRole) == selected_app:
                        self.app_list.setCurrentRow(i)
                        break
            
            logger.info(f"Обновлен список приложений: {self.app_list.count()} запущенных процессов")
            self.status_bar.showMessage(f"Отслеживается: {self.app_list.count()} запущенных приложений")
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
            # Инициализируем сессию, если она отсутствует
            if not hasattr(self, 'session') or self.session is None:
                self.session = requests.Session()
                logger.info("Сессия HTTP запросов инициализирована")
                
            # Проверяем наличие и действительность токена
            auth_token = None
            token_is_valid = False
            
            # Пытаемся загрузить токен из конфигурации
            if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'auth_token'):
                auth_token = self.config.get('Credentials', 'auth_token')
                
            # Проверяем действительность токена
            if auth_token:
                try:
                    # Если в конфигурации есть api_base_url, используем его
                    if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'api_base_url'):
                        self.api_base_url = self.config.get('Credentials', 'api_base_url')
                        
                        # Исправляем URL, если в нем дублируется /api
                        if self.api_base_url.endswith('/api/api/'):
                            self.api_base_url = self.api_base_url.replace('/api/api/', '/api/')
                            self.config.set('Credentials', 'api_base_url', self.api_base_url)
                            self._save_config()
                            logger.info(f"Исправлен URL с дублированием /api: {self.api_base_url}")
                            
                    # Проверяем токен, делая запрос к серверу
                    verify_url = f"{self.api_base_url}verify-token/"
                    # Убедимся, что URL не содержит дублирования /api
                    if '/api/api/' in verify_url:
                        verify_url = verify_url.replace('/api/api/', '/api/')
                        
                    headers = {'Authorization': f'Bearer {auth_token}'}
                    response = requests.get(verify_url, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        token_is_valid = True
                        # Проверяем, получен ли user_id и сохраняем его
                        if 'user_id' in response.json():
                            self.user_id = response.json()['user_id']
                            if not self.config.has_section('Credentials'):
                                self.config.add_section('Credentials')
                            self.config.set('Credentials', 'user_id', str(self.user_id))
                            self._save_config(self.config)
                    else:
                        logger.warning(f"Токен недействителен, код ответа: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Загруженный токен истек, требуется повторная авторизация")
                    token_is_valid = False
                    
            # Если токен не найден или недействителен, показываем диалог авторизации
            if not auth_token or not token_is_valid:
                logger.info("Токен отсутствует или недействителен, вызывается диалог входа.")
                
                # Создаем и запускаем диалог для авторизации
                login_dialog = LoginDialog(parent=self)
                if login_dialog.exec_() == QDialog.Accepted:
                    # После успешного логина LoginDialog должен обновить self.config
                    # и атрибуты self.api_base_url, self.user_id, self.session.headers
                    if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'api_base_url'):
                        self.api_base_url = self.config.get('Credentials', 'api_base_url')
                    if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'user_id'):
                        self.user_id = self.config.get('Credentials', 'user_id')
                    if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'auth_token'):
                        new_auth_token = self.config.get('Credentials', 'auth_token')
                        if not hasattr(self, 'session') or self.session is None:
                            self.session = requests.Session()
                        self.session.headers.update({'Authorization': f'Bearer {new_auth_token}'})
                        logger.info("Вход выполнен успешно через диалог.")
                    
                    # Перезапускаем таймер отправки данных, если интервал мог измениться
                    send_interval_seconds = self.config.getint('Settings', 'send_interval_seconds', fallback=60)
                    if hasattr(self, 'send_data_timer'):
                        self.send_data_timer.setInterval(send_interval_seconds * 1000)
                    
                    # Обновляем состояние подключения в интерфейсе
                    if hasattr(self, 'connection_status'):
                        self.connection_status.setText(f"Статус подключения: Подключено ({self.api_base_url})")
                        self.connection_status.setStyleSheet("QLabel { color: green; }")
                else:
                    logger.warning("Диалог входа отменен пользователем или работа в оффлайн-режиме.")
                    # Проверяем, выбран ли оффлайн-режим
                    if self.config.getboolean('Settings', 'demo_mode', fallback=False):
                        if hasattr(self, 'connection_status'):
                            self.connection_status.setText("Статус подключения: Оффлайн-режим")
                            self.connection_status.setStyleSheet("QLabel { color: orange; }")
                    else:
                        if hasattr(self, 'connection_status'):
                            self.connection_status.setText("Статус подключения: Не авторизовано")
                            self.connection_status.setStyleSheet("QLabel { color: red; }")
                        QMessageBox.warning(self, "Внимание", 
                                        "Авторизация не выполнена. Отслеживание активности будет работать в ограниченном режиме.")
            else:
                # Если токен действителен, обновляем UI
                if hasattr(self, 'connection_status'):
                    self.connection_status.setText(f"Статус подключения: Подключено ({self.api_base_url})")
                    self.connection_status.setStyleSheet("QLabel { color: green; }")
                logger.info("Пользователь уже аутентифицирован (токен найден и действителен).")
        except Exception as e:
            logger.error(f"Ошибка при проверке авторизации: {e}", exc_info=True)
            if hasattr(self, 'connection_status'):
                self.connection_status.setText("Статус подключения: Ошибка")
                self.connection_status.setStyleSheet("QLabel { color: red; }")
        finally:
            # Снимаем флаг после завершения диалога
            self._login_dialog_active = False

    def toggle_productive(self):
        """Переключает статус продуктивности приложения"""
        # Получаем текущую вкладку
        current_tab = self.tabs.currentIndex()
        
        # Выбираем соответствующий список приложений
        if current_tab == 0:  # Вкладка "Все приложения"
            app_list_widget = self.app_list
        elif current_tab == 1:  # Вкладка "Продуктивные приложения"
            app_list_widget = self.productive_list
        elif current_tab == 2:  # Вкладка "Непродуктивные приложения"
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
                is_useful = True  # По умолчанию добавляем как продуктивное
                self.tracked_applications_config[config_key] = is_useful
                status_text = "добавлено как продуктивное"
            else:
                # Если уже отслеживается, инвертируем статус продуктивности
                is_useful = self.tracked_applications_config[config_key]
                new_useful_status = not is_useful
                self.tracked_applications_config[config_key] = new_useful_status
                status_text = "продуктивное" if new_useful_status else "непродуктивное"
            
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
            logger.info(f"Изменен статус продуктивности приложения '{app_name}': {status_text}")
        except Exception as e:
            logger.error(f"Ошибка при изменении статуса продуктивности приложения '{app_name}': {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось изменить статус приложения: {e}")

    def remove_app(self):
        """Удаляет приложение из списка отслеживаемых"""
        # Получаем текущую вкладку
        current_tab = self.tabs.currentIndex()
        
        # Выбираем соответствующий список приложений
        if current_tab == 0:  # Вкладка "Все приложения"
            app_list_widget = self.app_list
        elif current_tab == 1:  # Вкладка "Продуктивные приложения"
            app_list_widget = self.productive_list
        elif current_tab == 2:  # Вкладка "Непродуктивные приложения"
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
        # Обновляем статус
        self.status_bar.showMessage("Отслеживание активности запущено")
        logger.info("Отслеживание активности запущено")

    def stop_tracking(self):
        self.status_label.setText("Статус: Отслеживание остановлено")
        # Останавливаем отслеживание
        self.tracking_paused = True
        # Завершаем текущую сессию активности, если она есть
        if self.current_activity_data:
            self.end_current_activity_session(event_type="pause")
        # Обновляем статус
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
        # Получаем выбранный элемент
        selected_items = self.app_list.selectedItems()
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
            
            # Если приложение уже в списке отслеживаемых - сохраняем его статус продуктивности
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
            
            # Обновляем список приложений
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
                
                # Стандартизируем имена приложений для решения проблемы с несколькими экземплярами
                # Словарь стандартизации имен приложений (нижний регистр)
                standardize_apps = {
                    'chrome.exe': 'chrome.exe',  # Стандартизируем Chrome, включая разные версии
                    'msedge.exe': 'msedge.exe',  # Microsoft Edge
                    'firefox.exe': 'firefox.exe',  # Firefox
                    'browser.exe': 'browser.exe',  # Generic browser
                    'iexplore.exe': 'iexplore.exe',  # Internet Explorer
                    'opera.exe': 'opera.exe',  # Opera
                    'brave.exe': 'brave.exe',  # Brave
                    'cursor.exe': 'cursor.exe',  # Cursor
                    'code.exe': 'code.exe',     # VS Code
                    'explorer.exe': 'explorer.exe',  # Windows Explorer
                    'telegram.exe': 'telegram.exe', # Telegram
                    'winword.exe': 'winword.exe',  # Word
                    'excel.exe': 'excel.exe',   # Excel
                    'powerpnt.exe': 'powerpnt.exe',  # PowerPoint
                    'outlook.exe': 'outlook.exe',  # Outlook
                    'notepad.exe': 'notepad.exe',  # Notepad
                    'notepad++.exe': 'notepad++.exe',  # Notepad++
                }
                
                # Нормализуем app_name - приводим к нижнему регистру
                app_name_lower = app_name.lower()
                
                # Если приложение есть в словаре стандартизации, используем стандартное имя
                # иначе оставляем оригинальное имя
                app_name = standardize_apps.get(app_name_lower, app_name)
                
                # Также игнорируем номера экземпляров в имени процесса 
                # (например, chrome.exe (1), chrome.exe (2))
                if '(' in app_name and ')' in app_name:
                    app_name = app_name.split('(')[0].strip()
                
                # Для Chrome, Firefox и других браузеров, всегда приводим к стандартному имени
                # независимо от версии или дополнительных суффиксов
                for browser_base in ['chrome', 'firefox', 'msedge', 'opera', 'brave']:
                    if browser_base in app_name_lower:
                        app_name = f"{browser_base}.exe"
                        break
                
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
        """Определяет, является ли приложение продуктивным согласно конфигурации"""
        if not app_name:
            return False
            
        # Приводим имя к нижнему регистру для сравнения
        app_name_lower = app_name.lower()
        
        # Проверяем, есть ли приложение в конфигурации
        if app_name_lower in self.tracked_applications_config:
            # Возвращаем статус продуктивности
            return self.tracked_applications_config[app_name_lower]
        
        # Если приложение не найдено в конфигурации, считаем его непродуктивным
        return False

    def start_new_activity_session(self, app_name, window_title, is_useful=None):
        """Начинает новую сессию активности"""
        try:
            # Проверяем, не находится ли пользователь в состоянии простоя
            if self.is_idle:
                logger.debug("Попытка начать сессию активности, но пользователь неактивен.")
                return False
                
            # Нормализуем имя приложения для поиска в конфигурации
            app_name_lower = app_name.lower()
            
            # Автоматически добавляем новые приложения в конфигурацию как отслеживаемые
            if app_name_lower not in self.tracked_applications_config:
                # По умолчанию новые приложения отслеживаются и считаются полезными
                self.tracked_applications_config[app_name_lower] = True
                
                # Добавляем в секцию конфигурации
                if not self.config.has_section('Applications'):
                    self.config.add_section('Applications')
                self.config.set('Applications', app_name_lower, 'True')
                
                # Сохраняем конфигурацию
                self._save_config()
                logger.info(f"Новое приложение {app_name} автоматически добавлено в отслеживаемые как полезное")
            
            # Получаем статус полезности из конфигурации
            if is_useful is None:
                is_useful = self.tracked_applications_config.get(app_name_lower, True)  # По умолчанию полезное
            
            # Создаем запись об активности
            start_time = time.time()
            
            # Используем новый метод для получения UTC времени в формате ISO
            start_time_iso_utc = self.get_utc_now_iso()
            
            self.current_activity_data = {
                'app_name': app_name,
                'window_title': window_title,
                'start_time': start_time,
                'start_time_iso_utc': start_time_iso_utc,
                'is_useful': is_useful,
                'keyboard_presses': 0  # Начальное значение счетчика нажатий
            }
            
            # Запоминаем время начала активности
            self.activity_start_time = start_time
            
            # НЕ сбрасываем счетчик нажатий клавиш здесь, чтобы накопить активность
            
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
        
        # Добавляем текущее количество нажатий клавиш к сессии
        current_keyboard_presses = self.keyboard_press_count
        
        # Добавляем клавиатурную активность к записи активности
        activity_entry['keyboard_presses'] = current_keyboard_presses
        
        # Используем новый метод для получения UTC времени в формате ISO
        current_time_utc = self.get_utc_now_iso()
        
        activity_entry.update({
            'end_time': end_time,
            'end_time_iso_utc': current_time_utc,
            'duration_seconds': duration_seconds,
            'event_type': event_type
        })
        
        # Добавляем в очередь для отправки
        self.activity_queue.put(activity_entry)
        
        logger.info(
            f"Завершена сессия активности: "
            f"App='{activity_entry['app_name']}', "
            f"Title='{activity_entry['window_title'][:30]}{'...' if len(activity_entry['window_title']) > 30 else ''}, "
            f"Duration={duration_seconds}s, Keyboard={current_keyboard_presses} нажатий. В очереди: {self.activity_queue.qsize()}"
        )
        
        # Сбрасываем счетчик нажатий ТОЛЬКО после добавления в очередь
        self.keyboard_press_count = 0
        
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
        
        # Принудительно запускаем отправку данных, если размер очереди достиг определенного предела
        if self.activity_queue.qsize() >= 1:
            logger.info("В очереди есть активности, запускаем немедленную отправку данных")
            # Запускаем отправку данных в следующем цикле событий для избежания блокировки
            QTimer.singleShot(100, self.send_activity_data)
            
        return activity_entry
        
    def get_discovered_applications(self) -> List[str]:
        """Возвращает список уникальных имен запущенных приложений."""
        discovered_apps = set()
        try:
            # Создаем безопасную копию списка игнорируемых процессов
            ignored_processes = []
            if hasattr(self, 'ignored_processes') and self.ignored_processes:
                ignored_processes = [p.lower() for p in self.ignored_processes]
            else:
                # Используем стандартный список игнорируемых системных процессов
                ignored_processes = [
                    "explorer.exe", "system", "system idle process", 
                    "dwm.exe", "taskhost.exe", "taskhostw.exe", "svchost.exe",
                    "runtimebroker.exe", "searchui.exe", "shellexperiencehost.exe",
                    "winlogon.exe", "wininit.exe", "csrss.exe", "services.exe",
                    "lsass.exe", "fontdrvhost.exe", "smss.exe"
                ]
            
            logger.info("Поиск запущенных приложений...")
            
            # Счетчики для диагностики
            total_processes = 0
            filtered_processes = 0
            
            # Получаем список процессов
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    total_processes += 1
                    proc_info = proc.info
                    proc_name = proc_info['name']
                    
                    # Если имя процесса пустое или None, пропускаем
                    if not proc_name:
                        continue
                        
                    # Нормализуем имя процесса - убираем расширение .exe
                    if proc_name.lower().endswith('.exe'):
                        proc_name = proc_name[:-4]
                    
                    # Пропускаем игнорируемые процессы (более точная проверка)
                    proc_name_lower = proc_name.lower()
                    skip_process = False
                    
                    # Проверяем точное соответствие в списке игнорируемых процессов
                    for ignored in ignored_processes:
                        ignored_base = ignored
                        if ignored.lower().endswith('.exe'):
                            ignored_base = ignored[:-4].lower()
                        
                        if proc_name_lower == ignored_base:
                            skip_process = True
                            filtered_processes += 1
                            break
                    
                    if skip_process:
                        continue
                    
                    # Пропускаем процессы без имени или только с цифрами
                    if not proc_name or proc_name.isdigit() or not any(c.isalpha() for c in proc_name):
                        continue
                        
                    # Проверка на пропуск процессов с именами, состоящими только из цифр и специальных символов
                    if all(not c.isalpha() for c in proc_name):
                        continue
                    
                    # Пытаемся получить путь к исполняемому файлу для дополнительной информации
                    try:
                        exe_path = proc_info.get('exe')
                        if exe_path:
                            logger.debug(f"Процесс {proc_name}, путь: {exe_path}")
                    except Exception:
                        pass
                    
                    # Добавляем имя процесса в список обнаруженных приложений
                    discovered_apps.add(proc_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Пропускаем процессы, к которым нет доступа или которые уже завершились
                    pass
                except Exception as e:
                    # Логируем ошибку и продолжаем
                    logger.error(f"Ошибка при обработке процесса: {e}")
            
            # Сортируем список для более стабильного вывода
            discovered_apps_list = sorted(list(discovered_apps))
            
            # Добавляем отладочную информацию
            logger.info(f"Обнаружено {len(discovered_apps_list)} приложений из {total_processes} процессов (отфильтровано {filtered_processes})")
            logger.debug(f"Список обнаруженных приложений: {discovered_apps_list}")
            
            return discovered_apps_list
        except Exception as e:
            logger.error(f"Ошибка при получении списка приложений: {e}", exc_info=True)
            return []

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

    def send_activity_data(self):
        """Отправляет накопленные данные активности на сервер."""
        try:
            if self.activity_queue.empty():
                logger.debug("Очередь активностей пуста, нечего отправлять.")
                return
            
            # Добавляем подробное логирование размера очереди
            queue_size = self.activity_queue.qsize()
            logger.info(f"Начинаем отправку данных. В очереди {queue_size} записей активности.")
            
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

            # Переменная для хранения всех активностей, которые не удалось отправить
            failed_activities = []
            
            # Получаем данные пользователя и токен из конфигурации
            auth_token = None
            user_id = None
            
            # Проверяем токен в секции Credentials - приоритетный источник
            if self.config.has_section('Credentials'):
                if self.config.has_option('Credentials', 'auth_token'):
                    auth_token = self.config.get('Credentials', 'auth_token')
                    # Добавляем диагностику токена
                    if auth_token:
                        logger.info(f"Найден токен авторизации длиной {len(auth_token)} символов.")
                    else:
                        logger.warning("Токен авторизации пустой в секции Credentials.")
                if self.config.has_option('Credentials', 'user_id'):
                    user_id = self.config.get('Credentials', 'user_id')
                    logger.info(f"Используется user_id: {user_id}")
            
            # Если не нашли в Credentials, проверяем другие секции
            if not auth_token:
                logger.warning("Токен не найден в секции Credentials, проверяем другие секции...")
                # Проверяем в секции Server
                if self.config.has_section('Server') and self.config.has_option('Server', 'token'):
                    auth_token = self.config.get('Server', 'token')
                    logger.info("Токен найден в секции Server")
                # Проверяем в секции API
                elif self.config.has_section('API') and self.config.has_option('API', 'token'):
                    auth_token = self.config.get('API', 'token')
                    logger.info("Токен найден в секции API")
                # Проверяем в корне файла
                elif self.config.has_option('DEFAULT', 'token'):
                    auth_token = self.config.get('DEFAULT', 'token')
                    logger.info("Токен найден в секции DEFAULT")

            # Если не нашли user_id в Credentials, пытаемся получить из токена
            if not user_id and auth_token:
                try:
                    token_data = jwt.decode(auth_token, options={"verify_signature": False})
                    if "user_id" in token_data:
                        user_id = str(token_data["user_id"])
                        logger.info(f"Извлечен user_id из токена: {user_id}")
                        # Сохраняем в конфигурацию для последующего использования
                        if self.config.has_section('Credentials'):
                            self.config.set('Credentials', 'user_id', user_id)
                            self._save_config(self.config)
                    else:
                        logger.warning("В токене отсутствует поле user_id")
                except Exception as e:
                    logger.error(f"Ошибка при извлечении user_id из токена: {e}")
            
            # Если все еще нет user_id, используем значение по умолчанию
            if not user_id:
                user_id = "1"
                logger.warning(f"Не удалось получить user_id, используется значение по умолчанию: {user_id}")
            
            # Получаем URL API
            api_url = None
            if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'api_base_url'):
                api_url = self.config.get('Credentials', 'api_base_url')
                logger.info(f"URL API из секции Credentials: {api_url}")
            elif self.config.has_section('Server') and self.config.has_option('Server', 'base_url'):
                api_url = self.config.get('Server', 'base_url')
                logger.info(f"URL API из секции Server: {api_url}")
            elif self.config.has_section('API') and self.config.has_option('API', 'base_url'):
                api_url = self.config.get('API', 'base_url')
                logger.info(f"URL API из секции API: {api_url}")
            elif self.config.has_option('DEFAULT', 'base_url'):
                api_url = self.config.get('DEFAULT', 'base_url')
                logger.info(f"URL API из секции DEFAULT: {api_url}")
            else:
                api_url = 'http://localhost:8000'
                logger.warning(f"URL API не найден в конфигурации, используется значение по умолчанию: {api_url}")
            
            # Исправляем потенциально некорректный URL API
            if '/api/api' in api_url:
                old_url = api_url
                api_url = api_url.replace('/api/api', '/api')
                logger.info(f"Исправлен дублированный путь API в URL: {old_url} -> {api_url}")
                
                # Сохраняем исправленный URL в конфигурацию
                if self.config.has_section('Credentials'):
                    self.config.set('Credentials', 'api_base_url', api_url)
                    self._save_config()
                    logger.info("Исправленный URL сохранен в конфигурации")
            
            # Убедимся, что URL заканчивается на /api/
            if not api_url.endswith('/api/'):
                old_url = api_url
                if api_url.endswith('/api'):
                    api_url += '/'
                elif not '/api' in api_url:
                    api_url = api_url.rstrip('/') + '/api/'
                logger.info(f"Нормализован URL API: {old_url} -> {api_url}")
                
                # Сохраняем нормализованный URL в конфигурацию
                if self.config.has_section('Credentials'):
                    self.config.set('Credentials', 'api_base_url', api_url)
                    self._save_config()
                    logger.info("Нормализованный URL сохранен в конфигурации")
            
            activities_url = f"{api_url}activities/"
            
            # Логируем URL для отладки
            logger.info(f"URL для отправки активностей: {activities_url}")
            
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
            logger.debug(f"Заголовки запроса: {headers}")
            
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
                    
                    # Детальное логирование активности
                    logger.debug(f"Готовится к отправке активность: {activity_dict}")
                    
                    # Формируем данные для API
                    # Убедимся, что все обязательные поля заполнены
                    start_time = activity_dict.get('start_time_iso_utc', '')
                    end_time = activity_dict.get('end_time_iso_utc', '')
                    
                    # Если поля не заполнены, сгенерируем текущие значения
                    if not start_time:
                        start_time = self.get_utc_now_iso()
                        logger.warning(f"Отсутствует start_time_iso_utc, сгенерировано: {start_time}")
                    if not end_time:
                        end_time = self.get_utc_now_iso()
                        logger.warning(f"Отсутствует end_time_iso_utc, сгенерировано: {end_time}")
                    
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
                    
                    # Для предотвращения возможных ошибок с неинициализированным кэшем
                    if not hasattr(self, 'app_cache'):
                        self.app_cache = {}
                    
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
                            app_url = f"{api_url}applications/"
                            
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
                                logger.warning(f"Не удалось создать приложение {app_name}, используем ID по умолчанию. Код ответа: {app_response.status_code}")
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
                
                # Сервер ожидает отдельные записи, а не массив
                # Отправляем каждую запись по отдельности
                success_count = 0
                for payload in activities_to_send_payload:
                    try:
                        # Добавляем отладочную информацию о пайлоаде
                        logger.info(f"Отправляем пайлоад: {payload}")
                        response = self.session.post(activities_url, json=payload, headers=headers, timeout=30)
                        
                        # Добавляем полное логирование ответа
                        logger.info(f"Ответ сервера: код={response.status_code}, тело={response.text}")
                        
                        if response.status_code in [200, 201]:
                            success_count += 1
                            logger.info(f"Успешно отправлено: {response.status_code} - {response.text}")
                            
                            # Проверяем формат ответа и логируем для отладки
                            try:
                                response_data = response.json()
                                logger.info(f"Ответ сервера в JSON: {response_data}")
                            except Exception as json_e:
                                logger.warning(f"Ответ сервера не является JSON: {json_e}")
                            
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
                                    logger.info(f"Активность возвращена в очередь для повторной отправки")
                                    break
                    except Exception as e:
                        logger.error(f"Ошибка при отправке записи: {e}", exc_info=True)
                        # Возвращаем активность в очередь
                        # (добавим конкретную активность, которая вызвала ошибку)
                        logger.info(f"Активность возвращена в очередь из-за ошибки: {e}")
                        self.activity_queue.put(activities_to_send[activities_to_send_payload.index(payload)])
                
                # Создаем фиктивный ответ для обработки в основном коде
                class DummyResponse:
                    def __init__(self, status_code):
                        self.status_code = status_code
                        self.text = f"Успешно отправлено {success_count} из {len(activities_to_send_payload)} записей"
                
                response = DummyResponse(200 if success_count > 0 else 400)
                
                if response.status_code == 200 or response.status_code == 201:
                    logger.info(f"Успешно отправлено {success_count} из {len(activities_to_send_payload)} записей активности.")
                    self.status_bar.showMessage(f"Отправлено {success_count} из {len(activities_to_send_payload)} записей активности.")
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
            logger.info("Проверка соединения пропущена - приложение в демо-режиме")
            return
            
        # Если нет токена, вызываем диалог авторизации
        auth_token = None
        if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'auth_token'):
            auth_token = self.config.get('Credentials', 'auth_token')
        
        if not auth_token:
            logger.warning("Проверка соединения: отсутствует токен авторизации")
            self.connection_status.setText("Статус подключения: Требуется авторизация")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            self.login_required_signal.emit()
            return
            
        # Получаем URL API
        api_url = None
        if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'api_base_url'):
            api_url = self.config.get('Credentials', 'api_base_url').rstrip('/')
        else:
            api_url = 'http://localhost:8000/api'
            
        # Проверяем на дублирование /api в URL
        if api_url.endswith('/api/api'):
            api_url = api_url.replace('/api/api', '/api')
            # Сохраняем исправленный URL в конфигурацию
            if self.config.has_section('Credentials'):
                self.config.set('Credentials', 'api_base_url', api_url + '/')
                self._save_config()
        
        logger.info(f"Проверка соединения с сервером: {api_url}")
                
        try:
            # Проверяем соединение напрямую через запрос
            headers = {'Authorization': f'Bearer {auth_token}'} if auth_token else {}
            logger.debug(f"Заголовки запроса проверки соединения: {headers}")
            
            # Пробуем сначала обратиться к корневому URL API для проверки базового соединения
            response = requests.get(f"{api_url}/", headers=headers, timeout=(3, 5))
            
            if response.status_code == 200:
                self.connection_status.setText(f"Статус подключения: Подключено ({api_url})")
                self.connection_status.setStyleSheet("QLabel { color: green; }")
                logger.info(f"Проверка соединения: успешно, сервер доступен и отвечает")
                
                # Дополнительно проверяем активности для текущего пользователя
                try:
                    # Получаем user_id
                    user_id = None
                    if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'user_id'):
                        user_id = self.config.get('Credentials', 'user_id')
                    
                    if user_id:
                        # Проверяем активности пользователя
                        activities_url = f"{api_url}/activities/?user={user_id}&limit=1"
                        logger.info(f"Запрос активностей пользователя: {activities_url}")
                        activities_response = requests.get(activities_url, headers=headers, timeout=(3, 5))
                        
                        if activities_response.status_code == 200:
                            try:
                                activities_data = activities_response.json()
                                logger.info(f"Ответ API активностей: {activities_data}")
                                
                                if activities_data and isinstance(activities_data, list) and len(activities_data) > 0:
                                    # Получаем последнюю активность
                                    last_activity = activities_data[0]
                                    last_time = last_activity.get('end_time', '')
                                    logger.info(f"Последняя активность пользователя на сервере: {last_time}")
                                    self.status_bar.showMessage(f"Последняя синхронизированная активность: {last_time}")
                                else:
                                    logger.warning("Нет активностей для пользователя на сервере")
                                    self.status_bar.showMessage("Нет записанных активностей на сервере")
                            except Exception as e:
                                logger.error(f"Ошибка при обработке ответа активностей: {e}")
                        else:
                            logger.warning(f"Не удалось получить активности: {activities_response.status_code} - {activities_response.text}")
                except Exception as e:
                    logger.error(f"Ошибка при проверке активностей: {e}")
            elif response.status_code == 401:
                self.connection_status.setText("Статус подключения: Ошибка авторизации")
                self.connection_status.setStyleSheet("QLabel { color: red; }")
                logger.warning(f"Ошибка проверки соединения: Недействительный токен (401)")
                
                # Показываем детали ответа для отладки
                logger.debug(f"Детали ответа 401: {response.text}")
                
                # Планируем показ диалога авторизации с задержкой
                QTimer.singleShot(1000, self.login_required_signal.emit)
            else:
                self.connection_status.setText(f"Статус подключения: Ошибка {response.status_code}")
                self.connection_status.setStyleSheet("QLabel { color: red; }")
                logger.warning(f"Ошибка проверки соединения: {response.status_code} - {response.text}")
                
                # Дополнительная отладочная информация
                self.status_bar.showMessage(f"Ошибка сервера: {response.status_code} - {response.text[:50]}")
        except requests.exceptions.ConnectionError as e:
            self.connection_status.setText("Статус подключения: Сервер недоступен")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            logger.error(f"Ошибка соединения с сервером: {e}")
            self.status_bar.showMessage(f"Сервер недоступен: проверьте подключение к сети")
        except requests.exceptions.Timeout as e:
            self.connection_status.setText("Статус подключения: Таймаут")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            logger.error(f"Таймаут при подключении к серверу: {e}")
            self.status_bar.showMessage(f"Сервер не отвечает: превышено время ожидания")
        except Exception as e:
            self.connection_status.setText("Статус подключения: Ошибка")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            logger.error(f"Ошибка при проверке соединения: {e}", exc_info=True)
            
            # Отображаем информацию об ошибке
            self.status_bar.showMessage(f"Ошибка соединения: {str(e)[:100]}")
            
            # Планируем показ диалога авторизации с задержкой
            QTimer.singleShot(1000, self.login_required_signal.emit)

    def periodic_ui_update(self):
        """Периодически обновляет интерфейс с текущими данными"""
        try:
            # Обновляем отображение текущей активности
            if hasattr(self, 'current_activity_data') and self.current_activity_data:
                app_name = self.current_activity_data.get('app_name', '')
                
                # Обновляем отображение времени активности
                if hasattr(self, 'activity_start_time') and self.activity_start_time:
                    elapsed = time.time() - self.activity_start_time
                    hours, remainder = divmod(int(elapsed), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                    
                    if hasattr(self, 'current_activity_time_label'):
                        self.current_activity_time_label.setText(f"Время: {time_str}")
                    
                # Обновляем отображение клавиатурной активности
                if hasattr(self, 'keyboard_activity_label'):
                    self.keyboard_activity_label.setText(f"Клавиатурная активность: {self.keyboard_press_count} нажатий")
                
                # Обновляем статус бар
                if hasattr(self, 'status_bar') and hasattr(self, 'activity_start_time') and self.activity_start_time:
                    elapsed = time.time() - self.activity_start_time
                    hours, remainder = divmod(int(elapsed), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                    self.status_bar.showMessage(f"Отслеживается: {app_name} - {time_str} - Клавиатура: {self.keyboard_press_count}")
            else:
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage("Нет активной сессии отслеживания")
                
        except Exception as e:
            logger.error(f"Ошибка при периодическом обновлении UI: {e}", exc_info=True)

    def sync_productive_apps_from_server(self):
        """Синхронизирует список продуктивных приложений с сервера"""
        try:
            if not hasattr(self, 'api_client') or not self.api_client:
                logger.warning("API клиент не инициализирован, синхронизация не выполнена")
                return False

            # Получаем список приложений с сервера
            tracked_apps = self.api_client.get_tracked_applications()
            if not tracked_apps:
                logger.warning("Не удалось получить список приложений с сервера")
                return False

            # Создаем словарь для новой конфигурации
            new_config = {}
            
            # Копируем текущую конфигурацию
            for app_name, is_useful in self.tracked_applications_config.items():
                new_config[app_name] = is_useful
            
            # Применяем данные с сервера
            changes_made = False
            
            for app in tracked_apps:
                app_process_name = app.get('process_name', '').lower()
                app_is_productive = app.get('is_productive', False)
                
                # Если это новое приложение или информация о его полезности изменилась
                if app_process_name and (
                    app_process_name not in new_config or 
                    new_config[app_process_name] != app_is_productive
                ):
                    new_config[app_process_name] = app_is_productive
                    changes_made = True
                    logger.info(f"Обновлена информация о приложении из сервера: {app_process_name} (Полезное: {app_is_productive})")
            
            # Если были изменения, обновляем конфигурацию и сохраняем её
            if changes_made:
                self.update_tracked_applications_config(new_config)
                self._save_config()
                return True
            else:
                logger.info("Обновлений с сервера для приложений не обнаружено")
                return False
        except Exception as e:
            logger.error(f"Ошибка при синхронизации продуктивных приложений с сервера: {e}", exc_info=True)
            return False

    def validate_and_fix_config(self):
        """Проверяет конфигурацию на наличие ошибок и исправляет их"""
        logger.info("Проверка и исправление конфигурации")
        
        try:
            # Проверяем и исправляем URL API
            if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'api_base_url'):
                api_url = self.config.get('Credentials', 'api_base_url')
                
                # Исправляем дублирование /api
                if '/api/api' in api_url:
                    fixed_url = api_url.replace('/api/api', '/api')
                    self.config.set('Credentials', 'api_base_url', fixed_url)
                    logger.info(f"Исправлен URL API с дублированием: {api_url} -> {fixed_url}")
                    
            # Проверяем наличие атрибута ignored_processes и устанавливаем его, если он отсутствует
            if not hasattr(self, 'ignored_processes') or self.ignored_processes is None:
                self.ignored_processes = [
                    "explorer.exe", "system", "system idle process", 
                    "dwm.exe", "taskhost.exe", "taskhostw.exe", "svchost.exe",
                    "runtimebroker.exe", "searchui.exe", "shellexperiencehost.exe",
                    "winlogon.exe", "wininit.exe", "csrss.exe", "services.exe",
                    "lsass.exe", "fontdrvhost.exe", "smss.exe"
                ]
                logger.info("Установлен атрибут ignored_processes")
                
            # Сохраняем изменения в конфигурацию
            self._save_config()
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке и исправлении конфигурации: {e}")
            return False
            
    def __init__(self, parent=None):
        """Инициализация приложения"""
        super().__init__(parent)

        # Инициализация переменных класса
        self.tracking_active = False
        self.tracking_paused = False  # Добавляем переменную для паузы отслеживания
        self.api_client = None
        self.keyboard_listener = None
        self.mouse_listener = None
        self.activity_queue = queue.Queue()
        self.current_activity = None
        self.current_activity_data = {}  # Инициализируем пустым словарем
        self.db_connection = None
        self.config = None
        self.keyboard_press_count = 0
        self.mouse_move_count = 0
        self.mouse_click_count = 0
        self.last_window_title = ""
        self.last_app_name = ""
        self.app_list = None
        self.config_loaded = False
        self.is_idle = False
        self.last_activity_time = time.time()
        self.activities_to_send = []
        self.activity_start_time = None  # Время начала текущей активности
        self.idle_threshold_seconds = 300  # По умолчанию 5 минут
        self.session = requests.Session()  # Инициализируем сессию для HTTP запросов
        
        # Список игнорируемых системных процессов
        self.ignored_processes = [
            "explorer.exe", 
            "system", 
            "system idle process", 
            "dwm.exe", 
            "taskhost.exe", 
            "taskhostw.exe", 
            "svchost.exe",
            "runtimebroker.exe",
            "searchui.exe",
            "shellexperiencehost.exe",
            "winlogon.exe",
            "wininit.exe",
            "csrss.exe",
            "services.exe",
            "lsass.exe",
            "fontdrvhost.exe",
            "smss.exe"
        ]
        
        # Получаем пути к данным и конфигурации в зависимости от ОС
        self.app_data_dir = get_app_data_dir()
        self.setup_app_directories()
        
        # Загружаем конфигурацию
        self.config = self.load_config() 
        self.config_loaded = True
        
        # Проверяем и исправляем конфигурацию
        self.validate_and_fix_config()
        
        # Загружаем значение порога бездействия из конфигурации, если есть
        if self.config.has_section('Settings') and self.config.has_option('Settings', 'idle_threshold_seconds'):
            self.idle_threshold_seconds = self.config.getint('Settings', 'idle_threshold_seconds')
        
        # Инициализируем API клиент
        self.init_api_client()
        
        # Загружаем конфигурацию отслеживания
        self.load_tracked_applications_config()
        
        # Инициализируем пользовательский интерфейс
        self.init_ui()
        
        # Настраиваем иконку в системном трее
        self.init_tray_icon()
        
        # Устанавливаем слушатели активности и таймеры
        self.setup_activity_listeners_and_tracking_timer()
        
        # Запускаем обновление списка приложений
        self.update_app_list()
        
        # Проверяем соединение с сервером
        QTimer.singleShot(1000, self.check_connection)
        
        # Запускаем обновление UI и проверку соединения
        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.timeout.connect(self.periodic_ui_update)
        self.ui_update_timer.start(5000)  # Обновляем каждые 5 секунд
        
        # Отображаем окно входа, если необходимо
        QTimer.singleShot(1500, self.show_login_dialog_if_needed)
        
        logger.info("Приложение TimeTracker успешно инициализировано")

    def get_process_name(self, window_handle) -> Tuple[str, str]:
        """
        Получает имя запущенного процесса и заголовок окна.
        Возвращает кортеж (app_name, window_title)
        """
        try:
            if window_handle is None:
                return "Unknown", "Unknown Window"
                
            # Получаем PID активного окна
            pid = win32process.GetWindowThreadProcessId(window_handle)[1]
            
            # Попытка получить имя процесса через win32process
            try:
                # Получаем дескриптор процесса
                process_handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
                
                # Получаем путь к исполняемому файлу
                exe_path = win32process.GetModuleFileNameEx(process_handle, 0)
                
                # Закрываем дескриптор процесса
                win32api.CloseHandle(process_handle)
                
                # Извлекаем имя файла из полного пути
                app_name = os.path.basename(exe_path)
                
                # Логирование для отладки
                logger.debug(f"Получено имя процесса через win32process: {app_name} (PID: {pid})")
            except Exception as e:
                # Если не удалось получить через win32process, пробуем через psutil
                logger.debug(f"Не удалось получить имя через win32process: {e}")
                
                try:
                    process = psutil.Process(pid)
                    app_name = process.name()
                    logger.debug(f"Получено имя процесса через psutil: {app_name} (PID: {pid})")
                except Exception as e2:
                    # Если не удалось и через psutil, возвращаем значение по умолчанию
                    logger.error(f"Не удалось получить имя процесса через psutil: {e2}")
                    app_name = f"pid_{pid}"
            
            # Получаем заголовок окна
            window_title = win32gui.GetWindowText(window_handle)
            
            # Если заголовок пустой, используем имя процесса как заголовок
            if not window_title:
                window_title = app_name
            
            # Нормализуем имя процесса - убираем расширение файла, если оно есть
            if app_name.lower().endswith('.exe'):
                app_name = app_name[:-4]  # Убираем расширение .exe
                
            # Логируем полученные данные для отладки
            logger.debug(f"Определено имя процесса и заголовок: {app_name}, {window_title}")
            
            return app_name, window_title
            
        except Exception as e:
            # В случае любой ошибки возвращаем безопасные значения по умолчанию
            logger.error(f"Ошибка при получении имени процесса: {e}", exc_info=True)
            return "Unknown", "Unknown Window"

    def validate_compatibility(self):
        """Проверяет совместимость с версией Python и зависимостями."""
        try:
            # Проверяем версию Python
            python_version = sys.version_info
            logger.info(f"Версия Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
            
            # Проверяем наличие datetime.UTC (добавлено в Python 3.11)
            has_datetime_utc = hasattr(datetime, 'UTC')
            logger.info(f"Поддержка datetime.UTC: {has_datetime_utc}")
            
            # Если datetime.UTC не доступен, создаем альтернативу
            if not has_datetime_utc:
                # Создаем timezone для UTC если его нет
                if not hasattr(datetime, 'UTC'):
                    try:
                        # Пытаемся использовать timezone
                        datetime.UTC = datetime.timezone.utc
                        logger.info("Создан альтернативный datetime.UTC используя datetime.timezone.utc")
                    except Exception:
                        # Если timezone тоже недоступен, создаем функцию-заглушку
                        def utcnow_with_z():
                            """Создает строку ISO формата с UTC и 'Z' на конце."""
                            return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                        self.utcnow_with_z = utcnow_with_z
                        logger.info("Создана функция-заглушка utcnow_with_z")
            
            # Проверяем доступность необходимых модулей
            required_modules = ['PyQt5', 'requests', 'psutil', 'win32gui', 'win32process', 'pynput']
            missing_modules = []
            
            for module in required_modules:
                try:
                    importlib.import_module(module)
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                logger.warning(f"Отсутствуют следующие модули: {', '.join(missing_modules)}")
            else:
                logger.info("Все необходимые модули доступны")
                
            # Возвращаем True, если все проверки прошли успешно
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке совместимости: {e}", exc_info=True)
            return False
            
    def get_utc_now_iso(self):
        """Возвращает текущее время в формате ISO с UTC и 'Z' на конце."""
        try:
            if hasattr(datetime, 'UTC'):
                # Используем datetime.UTC если доступен (Python 3.11+)
                return datetime.now(datetime.UTC).isoformat() + 'Z'
            elif hasattr(datetime, 'timezone') and hasattr(datetime.timezone, 'utc'):
                # Используем datetime.timezone.utc для более старых версий
                return datetime.now(datetime.timezone.utc).isoformat() + 'Z'
            else:
                # Для очень старых версий используем utcnow
                return datetime.utcnow().isoformat() + 'Z'
        except Exception as e:
            logger.error(f"Ошибка при получении UTC времени: {e}")
            # В случае ошибки возвращаем текущее время без UTC
            return datetime.now().isoformat() + 'Z'

    def _send_with_retry(self, url, data, headers, max_retries=3, base_delay=2):
        """
        Отправляет данные на сервер с механизмом повторных попыток.
        
        Args:
            url: URL для отправки данных
            data: Данные для отправки (будут сериализованы в JSON)
            headers: Заголовки запроса
            max_retries: Максимальное количество попыток
            base_delay: Базовая задержка между попытками (в секундах)
            
        Returns:
            tuple: (success, response, error_message)
                success - булево значение успешности операции
                response - объект ответа requests.Response или None
                error_message - строка с сообщением об ошибке или None
        """
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    logger.info(f"Повторная попытка {attempt}/{max_retries} отправки данных")
                
                # Отправляем запрос
                response = self.session.post(url, json=data, headers=headers, timeout=(5, 30))
                
                # Проверяем код ответа
                if response.status_code in [200, 201]:
                    # Успешный ответ
                    return True, response, None
                elif response.status_code == 401:
                    # Ошибка авторизации, требуется новый токен
                    return False, response, "Требуется авторизация"
                elif response.status_code in [429, 500, 502, 503, 504]:
                    # Временные ошибки сервера, можно повторить
                    logger.warning(f"Временная ошибка сервера: {response.status_code}. Попытка {attempt}/{max_retries}")
                    
                    if attempt < max_retries:
                        # Увеличиваем задержку с каждой попыткой (экспоненциальная задержка)
                        current_delay = base_delay * (2 ** (attempt - 1))
                        logger.info(f"Ожидание {current_delay} секунд перед следующей попыткой...")
                        time.sleep(current_delay)
                    else:
                        # Достигнуто максимальное количество попыток
                        return False, response, f"Ошибка сервера после {max_retries} попыток: {response.status_code}"
                else:
                    # Другие ошибки
                    return False, response, f"Ошибка сервера: {response.status_code} - {response.text[:100]}"
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Ошибка соединения при попытке {attempt}/{max_retries}: {e}")
                if attempt < max_retries:
                    current_delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Ожидание {current_delay} секунд перед следующей попыткой...")
                    time.sleep(current_delay)
                else:
                    return False, None, f"Ошибка соединения после {max_retries} попыток: {str(e)}"
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"Таймаут при попытке {attempt}/{max_retries}: {e}")
                if attempt < max_retries:
                    current_delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"Ожидание {current_delay} секунд перед следующей попыткой...")
                    time.sleep(current_delay)
                else:
                    return False, None, f"Таймаут после {max_retries} попыток: {str(e)}"
                    
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при отправке данных: {e}", exc_info=True)
                return False, None, f"Непредвиденная ошибка: {str(e)}"
        
        # Если мы дошли до этой точки, значит все попытки исчерпаны
        return False, None, f"Все {max_retries} попытки отправки исчерпаны"
        
    def check_connection(self):
        """Проверяет соединение с сервером"""
        # Если включен демо-режим, пропускаем проверку
        if self.config.getboolean('Settings', 'demo_mode', fallback=False):
            self.connection_status.setText("Статус подключения: Оффлайн-режим")
            self.connection_status.setStyleSheet("QLabel { color: orange; }")
            logger.info("Проверка соединения пропущена - приложение в демо-режиме")
            return
            
        # Если нет токена, вызываем диалог авторизации
        auth_token = None
        if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'auth_token'):
            auth_token = self.config.get('Credentials', 'auth_token')
        
        if not auth_token:
            logger.warning("Проверка соединения: отсутствует токен авторизации")
            self.connection_status.setText("Статус подключения: Требуется авторизация")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            self.login_required_signal.emit()
            return
            
        # Получаем URL API
        api_url = None
        if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'api_base_url'):
            api_url = self.config.get('Credentials', 'api_base_url').rstrip('/')
        else:
            api_url = 'http://localhost:8000/api'
            
        # Проверяем на дублирование /api в URL
        if api_url.endswith('/api/api'):
            api_url = api_url.replace('/api/api', '/api')
            # Сохраняем исправленный URL в конфигурацию
            if self.config.has_section('Credentials'):
                self.config.set('Credentials', 'api_base_url', api_url + '/')
                self._save_config()
        
        logger.info(f"Проверка соединения с сервером: {api_url}")
                
        try:
            # Проверяем соединение напрямую через запрос
            headers = {'Authorization': f'Bearer {auth_token}'} if auth_token else {}
            logger.debug(f"Заголовки запроса проверки соединения: {headers}")
            
            # Пробуем сначала обратиться к корневому URL API для проверки базового соединения
            response = requests.get(f"{api_url}/", headers=headers, timeout=(3, 5))
            
            if response.status_code == 200:
                self.connection_status.setText(f"Статус подключения: Подключено ({api_url})")
                self.connection_status.setStyleSheet("QLabel { color: green; }")
                logger.info(f"Проверка соединения: успешно, сервер доступен и отвечает")
                
                # Дополнительно проверяем активности для текущего пользователя
                try:
                    # Получаем user_id
                    user_id = None
                    if self.config.has_section('Credentials') and self.config.has_option('Credentials', 'user_id'):
                        user_id = self.config.get('Credentials', 'user_id')
                    
                    if user_id:
                        # Проверяем активности пользователя
                        activities_url = f"{api_url}/activities/?user={user_id}&limit=1"
                        logger.info(f"Запрос активностей пользователя: {activities_url}")
                        activities_response = requests.get(activities_url, headers=headers, timeout=(3, 5))
                        
                        if activities_response.status_code == 200:
                            try:
                                activities_data = activities_response.json()
                                logger.info(f"Ответ API активностей: {activities_data}")
                                
                                if activities_data and isinstance(activities_data, list) and len(activities_data) > 0:
                                    # Получаем последнюю активность
                                    last_activity = activities_data[0]
                                    last_time = last_activity.get('end_time', '')
                                    logger.info(f"Последняя активность пользователя на сервере: {last_time}")
                                    self.status_bar.showMessage(f"Последняя синхронизированная активность: {last_time}")
                                else:
                                    logger.warning("Нет активностей для пользователя на сервере")
                                    self.status_bar.showMessage("Нет записанных активностей на сервере")
                            except Exception as e:
                                logger.error(f"Ошибка при обработке ответа активностей: {e}")
                        else:
                            logger.warning(f"Не удалось получить активности: {activities_response.status_code} - {activities_response.text}")
                except Exception as e:
                    logger.error(f"Ошибка при проверке активностей: {e}")
            elif response.status_code == 401:
                self.connection_status.setText("Статус подключения: Ошибка авторизации")
                self.connection_status.setStyleSheet("QLabel { color: red; }")
                logger.warning(f"Ошибка проверки соединения: Недействительный токен (401)")
                
                # Показываем детали ответа для отладки
                logger.debug(f"Детали ответа 401: {response.text}")
                
                # Планируем показ диалога авторизации с задержкой
                QTimer.singleShot(1000, self.login_required_signal.emit)
            else:
                self.connection_status.setText(f"Статус подключения: Ошибка {response.status_code}")
                self.connection_status.setStyleSheet("QLabel { color: red; }")
                logger.warning(f"Ошибка проверки соединения: {response.status_code} - {response.text}")
                
                # Дополнительная отладочная информация
                self.status_bar.showMessage(f"Ошибка сервера: {response.status_code} - {response.text[:50]}")
        except requests.exceptions.ConnectionError as e:
            self.connection_status.setText("Статус подключения: Сервер недоступен")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            logger.error(f"Ошибка соединения с сервером: {e}")
            self.status_bar.showMessage(f"Сервер недоступен: проверьте подключение к сети")
        except requests.exceptions.Timeout as e:
            self.connection_status.setText("Статус подключения: Таймаут")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            logger.error(f"Таймаут при подключении к серверу: {e}")
            self.status_bar.showMessage(f"Сервер не отвечает: превышено время ожидания")
        except Exception as e:
            self.connection_status.setText("Статус подключения: Ошибка")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            logger.error(f"Ошибка при проверке соединения: {e}", exc_info=True)
            
            # Отображаем информацию об ошибке
            self.status_bar.showMessage(f"Ошибка соединения: {str(e)[:100]}")
            
            # Планируем показ диалога авторизации с задержкой
            QTimer.singleShot(1000, self.login_required_signal.emit)


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
        self.app_list_widget.setColumnCount(2)
        self.app_list_widget.setHorizontalHeaderLabels(["Приложение (имя процесса)", "Отслеживать"])
        self.app_list_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.app_list_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
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

            self.app_list_widget.setItem(row, 0, app_name_item)
            self.app_list_widget.setCellWidget(row, 1, checkbox_widget)
        
        logger.debug(f"Загружено {len(sorted_app_list)} приложений в таблицу настроек.")

    def accept(self):
        logger.info("Сохранение настроек из SettingsDialog...")
        new_tracked_config = {}
        for row in range(self.app_list_widget.rowCount()):
            app_name_item = self.app_list_widget.item(row, 0)
            checkbox_widget = self.app_list_widget.cellWidget(row, 1)

            if app_name_item and checkbox_widget:
                app_name = app_name_item.text()
                if checkbox_widget.isChecked():
                    # Все приложения имеют одинаковый статус, так как у нас нет разделения на продуктивные/непродуктивные
                    new_tracked_config[app_name] = True
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