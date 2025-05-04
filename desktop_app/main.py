import sys
import json
import requests
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QListWidget, QLineEdit, QCheckBox,
                           QMessageBox, QSystemTrayIcon, QMenu, QAction, QDialog,
                           QFormLayout, QDialogButtonBox, QStatusBar, QProgressBar,
                           QTabWidget, QListWidgetItem)
from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
import psutil
from pynput import keyboard, mouse
import pygetwindow as gw
import time
from datetime import datetime
import logging
from pathlib import Path
import configparser
import os
import threading
from logging.handlers import RotatingFileHandler
import queue
import sqlite3
from typing import Dict, List, Optional
import webbrowser
from api_client import APIClient

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

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Авторизация")
        self.api_client = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        
        self.server_url = QLineEdit()
        self.server_url.setText("http://127.0.0.1:8000")  # Значение по умолчанию
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        
        layout.addRow("URL сервера:", self.server_url)
        layout.addRow("Имя пользователя:", self.username)
        layout.addRow("Пароль:", self.password)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.authenticate)
        buttons.rejected.connect(self.reject)
        
        layout.addRow(buttons)
        self.setLayout(layout)
        
    def authenticate(self):
        server_url = self.server_url.text()
        username = self.username.text()
        password = self.password.text()
        
        if not all([server_url, username, password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
            
        self.api_client = APIClient(server_url)
        if self.api_client.authenticate(username, password):
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверные учетные данные или проблемы с сервером")

class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tracker = TimeTracker()
        self.init_ui()
        self.init_tray()
        self.check_dependencies()
        self.check_auth()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_app_list)
        self.update_timer.start(5000)  # Обновляем список каждые 5 секунд
        
        # Таймер для проверки соединения
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(30000)  # Проверяем каждые 30 секунд

    def init_ui(self):
        self.setWindowTitle('Time Tracker')
        self.setGeometry(100, 100, 800, 600)

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

        # Создаем вкладки
        self.tabs = QTabWidget()
        
        # Вкладка "Все приложения"
        all_apps_tab = QWidget()
        all_apps_layout = QVBoxLayout(all_apps_tab)
        self.app_list = QListWidget()
        all_apps_layout.addWidget(self.app_list)
        self.tabs.addTab(all_apps_tab, "Все приложения")
        
        # Вкладка "Полезные приложения"
        productive_tab = QWidget()
        productive_layout = QVBoxLayout(productive_tab)
        self.productive_list = QListWidget()
        productive_layout.addWidget(self.productive_list)
        self.tabs.addTab(productive_tab, "Полезные приложения")
        
        # Вкладка "Неполезные приложения"
        non_productive_tab = QWidget()
        non_productive_layout = QVBoxLayout(non_productive_tab)
        self.non_productive_list = QListWidget()
        non_productive_layout.addWidget(self.non_productive_list)
        self.tabs.addTab(non_productive_tab, "Неполезные приложения")
        
        layout.addWidget(self.tabs)

        # Кнопки управления
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        self.toggle_button = QPushButton('Включить/Выключить')
        self.toggle_button.clicked.connect(self.toggle_app)
        
        self.toggle_productive_button = QPushButton('Отметить как полезное/неполезное')
        self.toggle_productive_button.clicked.connect(self.toggle_productive)
        
        self.remove_button = QPushButton('Удалить')
        self.remove_button.clicked.connect(self.remove_app)
        
        buttons_layout.addWidget(self.toggle_button)
        buttons_layout.addWidget(self.toggle_productive_button)
        buttons_layout.addWidget(self.remove_button)
        
        layout.addWidget(buttons_widget)

        # Статус отслеживания
        self.status_label = QLabel("Статус: Не отслеживается")
        layout.addWidget(self.status_label)

        # Кнопки управления отслеживанием
        tracking_buttons = QWidget()
        tracking_layout = QHBoxLayout(tracking_buttons)
        
        self.start_button = QPushButton('Начать отслеживание')
        self.stop_button = QPushButton('Остановить отслеживание')
        
        self.start_button.clicked.connect(self.start_tracking)
        self.stop_button.clicked.connect(self.stop_tracking)
        
        tracking_layout.addWidget(self.start_button)
        tracking_layout.addWidget(self.stop_button)
        
        layout.addWidget(tracking_buttons)

        # Добавляем статус бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готов к работе")

    def check_dependencies(self):
        """Проверка необходимых зависимостей"""
        missing_deps = []
        
        # Проверяем Python
        if sys.version_info < (3, 8):
            missing_deps.append("Python 3.8 или выше")
            
        # Проверяем pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            missing_deps.append("pip")
            
        # Проверяем PyQt5
        try:
            import PyQt5
        except ImportError:
            missing_deps.append("PyQt5")
            
        # Проверяем psutil
        try:
            import psutil
        except ImportError:
            missing_deps.append("psutil")
            
        # Проверяем pynput
        try:
            import pynput
        except ImportError:
            missing_deps.append("pynput")
            
        # Проверяем pygetwindow
        try:
            import pygetwindow
        except ImportError:
            missing_deps.append("pygetwindow")
            
        if missing_deps:
            msg = "Отсутствуют необходимые компоненты:\n\n"
            msg += "\n".join(missing_deps)
            msg += "\n\nУстановить автоматически?"
            
            reply = QMessageBox.question(
                self, 'Необходимые компоненты',
                msg,
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.install_dependencies(missing_deps)
            else:
                QMessageBox.warning(
                    self, 'Ошибка',
                    'Приложение не может работать без необходимых компонентов'
                )
                sys.exit(1)

    def install_dependencies(self, deps):
        """Установка отсутствующих зависимостей"""
        progress = QProgressBar()
        progress.setMaximum(len(deps))
        self.statusBar.addWidget(progress)
        
        for i, dep in enumerate(deps):
            self.statusBar.showMessage(f"Установка {dep}...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep],
                             check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                QMessageBox.critical(
                    self, 'Ошибка',
                    f'Не удалось установить {dep}:\n{e.stderr.decode()}'
                )
                sys.exit(1)
            progress.setValue(i + 1)
            
        self.statusBar.removeWidget(progress)
        self.statusBar.showMessage("Все компоненты установлены")

    def check_connection(self):
        """Проверка соединения с сервером"""
        if not self.tracker.api_client:
            self.connection_status.setText("Статус подключения: Не авторизован")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            return
            
        if self.tracker.api_client.is_token_valid():
            self.connection_status.setText("Статус подключения: Подключен")
            self.connection_status.setStyleSheet("QLabel { color: green; }")
        else:
            self.connection_status.setText("Статус подключения: Ошибка подключения")
            self.connection_status.setStyleSheet("QLabel { color: red; }")
            self.check_auth()

    def open_web_interface(self):
        """Открытие веб-интерфейса"""
        if self.tracker.api_client:
            webbrowser.open(f"{self.tracker.api_client.base_url}/dashboard/")
        else:
            QMessageBox.warning(self, "Ошибка", "Необходима авторизация")
            self.check_auth()

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.png'))
        
        tray_menu = QMenu()
        show_action = QAction('Показать', self)
        web_action = QAction('Открыть веб-интерфейс', self)
        quit_action = QAction('Выход', self)
        
        show_action.triggered.connect(self.show)
        web_action.triggered.connect(self.open_web_interface)
        quit_action.triggered.connect(QApplication.quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(web_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def check_auth(self):
        """Проверка аутентификации"""
        if not self.tracker.api_client or not self.tracker.api_client.is_token_valid():
            self.show_login_dialog()

    def show_login_dialog(self):
        """Показ диалога входа"""
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.api_client:
            self.tracker.set_api_client(dialog.api_client)
            self.update_app_list()
        else:
            QMessageBox.critical(self, "Ошибка", "Необходима авторизация")
            self.show_login_dialog()

    def scan_applications(self):
        """Сканирование всех запущенных приложений"""
        processes = []
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                processes.append({
                    'name': proc.info['name'],
                    'pid': proc.info['pid']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        # Создаем диалог выбора приложений
        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор приложений для отслеживания")
        layout = QVBoxLayout()
        
        scroll = QWidget()
        scroll_layout = QVBoxLayout()
        
        for proc in processes:
            checkbox = QCheckBox(f"{proc['name']} (PID: {proc['pid']})")
            checkbox.setChecked(False)
            scroll_layout.addWidget(checkbox)
            
        scroll.setLayout(scroll_layout)
        layout.addWidget(scroll)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # Сохраняем выбранные приложения
            config = self.tracker.load_config()
            for i in range(scroll_layout.count()):
                checkbox = scroll_layout.itemAt(i).widget()
                if checkbox.isChecked():
                    app_name = checkbox.text().split(' (')[0]
                    config['Applications'][app_name] = app_name
            self.tracker.save_config(config)
            self.update_app_list()

    def update_app_list(self):
        """Обновление списков приложений"""
        # Очищаем все списки
        self.app_list.clear()
        self.productive_list.clear()
        self.non_productive_list.clear()
        
        # Получаем данные с сервера
        try:
            config = self.tracker.load_config()
            headers = {'Authorization': f'Token {config.get("Server", "token")}'}
            
            # Получаем все приложения
            response = requests.get(
                f"{config.get('Server', 'base_url')}/tracked-apps/",
                headers=headers
            )
            if response.status_code == 200:
                apps = response.json()
                
                # Распределяем приложения по спискам
                for app in apps:
                    item = QListWidgetItem(f"{app['name']} ({app['process_name']})")
                    item.setData(Qt.UserRole, app['id'])
                    
                    # Добавляем в общий список
                    self.app_list.addItem(item)
                    
                    # Добавляем в соответствующий список по продуктивности
                    if app['is_productive']:
                        self.productive_list.addItem(item.clone())
                    else:
                        self.non_productive_list.addItem(item.clone())
                        
                    # Добавляем иконку статуса
                    if app['is_active']:
                        item.setIcon(QIcon('icon.png'))
        except Exception as e:
            self.statusBar.showMessage(f"Ошибка при обновлении списка: {str(e)}")

    def toggle_app(self):
        current_item = self.app_list.currentItem()
        if not current_item:
            return
        
        index = self.app_list.row(current_item)
        app = self.tracker.tracked_apps[index]
        
        if self.tracker.toggle_app_tracking(app['id']):
            self.update_app_list()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось изменить статус приложения')

    def remove_app(self):
        current_item = self.app_list.currentItem()
        if not current_item:
            return
        
        index = self.app_list.row(current_item)
        app = self.tracker.tracked_apps[index]
        
        reply = QMessageBox.question(
            self, 'Подтверждение',
            f'Удалить приложение {app["name"]}?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.tracker.remove_app(app['id']):
                self.update_app_list()
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось удалить приложение')

    def start_tracking(self):
        self.status_label.setText("Статус: Отслеживание активно")
        self.tracker.start_tracking()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_tracking(self):
        self.status_label.setText("Статус: Отслеживание остановлено")
        self.tracker.stop_tracking()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            'Time Tracker',
            'Приложение продолжает работать в фоновом режиме',
            QSystemTrayIcon.Information,
            2000
        )

    def toggle_productive(self):
        """Переключение статуса полезности приложения"""
        current_item = self.app_list.currentItem()
        if not current_item:
            return
            
        app_id = current_item.data(Qt.UserRole)
        try:
            config = self.tracker.load_config()
            headers = {'Authorization': f'Token {config.get("Server", "token")}'}
            
            response = requests.post(
                f"{config.get('Server', 'base_url')}/tracked-apps/{app_id}/toggle_productive/",
                headers=headers
            )
            
            if response.status_code == 200:
                self.update_app_list()
                self.statusBar.showMessage("Статус полезности обновлен")
            else:
                self.statusBar.showMessage("Ошибка при обновлении статуса")
        except Exception as e:
            self.statusBar.showMessage(f"Ошибка: {str(e)}")

class TimeTracker:
    def __init__(self, config_path='config.ini'):
        self.config_path = config_path
        self.config = self.load_config()
        self.api_client = None
        self.tracked_apps = []
        self.is_tracking = False
        self.keyboard_listener = None
        self.mouse_listener = None
        self.activity_queue = queue.Queue()
        self.db_path = Path.home() / '.timetracker' / 'tracker.db'
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
        self.process_activity_thread = threading.Thread(target=self.process_activity_queue, daemon=True)
        self.process_activity_thread.start()

    def set_api_client(self, api_client):
        """Установка API-клиента"""
        self.api_client = api_client
        if self.api_client:
            self.sync_applications()

    def sync_applications(self):
        """Синхронизация списка приложений с сервером"""
        if not self.api_client:
            return
            
        try:
            user_info = self.api_client.get_user_info()
            if user_info:
                # TODO: Синхронизировать список приложений с сервером
                pass
        except Exception as e:
            logger.error(f"Ошибка синхронизации приложений: {e}")

    def save_activity(self, app: Dict, duration: float):
        """Сохранение данных об активности"""
        if not self.api_client:
            return
            
        activity_data = {
            'application': app['name'],
            'process_name': app['process_name'],
            'duration': duration,
            'is_productive': app.get('is_productive', False),
            'timestamp': datetime.now().isoformat()
        }
        
        self.activity_queue.put(activity_data)

    def process_activity_queue(self):
        """Обработка очереди активности"""
        while True:
            try:
                activity_data = self.activity_queue.get()
                if self.api_client:
                    if not self.api_client.send_activity(activity_data):
                        # Если не удалось отправить, сохраняем в локальную БД
                        self.save_to_local_db(activity_data)
                else:
                    self.save_to_local_db(activity_data)
                self.activity_queue.task_done()
            except Exception as e:
                logger.error(f"Ошибка обработки активности: {e}")
                time.sleep(1)  # Пауза перед следующей попыткой

    def save_to_local_db(self, activity_data: Dict):
        """Сохранение активности в локальную БД"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activities 
                (application, process_name, duration, is_productive, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                activity_data['application'],
                activity_data['process_name'],
                activity_data['duration'],
                activity_data['is_productive'],
                activity_data['timestamp']
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка сохранения в локальную БД: {e}")
        finally:
            if conn:
                conn.close()

    def init_database(self):
        """Инициализация базы данных"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Создаем таблицу для хранения активности
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT,
                process_name TEXT,
                start_time TEXT,
                end_time TEXT,
                duration INTEGER,
                is_synced INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()

    def load_config(self) -> configparser.ConfigParser:
        """Загрузка конфигурации из файла"""
        config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            config['API'] = {
                'base_url': 'http://localhost:8000/api',
                'token': ''
            }
            config['Settings'] = {
                'update_interval': '5',
                'log_level': 'INFO',
                'auto_start': 'false',
                'minimize_to_tray': 'true'
            }
            with open(self.config_path, 'w') as f:
                config.write(f)
        config.read(self.config_path)
        return config

    def save_config(self):
        """Сохранение конфигурации в файл"""
        with open(self.config_path, 'w') as f:
            self.config.write(f)

    def get_db_connection(self):
        """Получение нового соединения с базой данных"""
        return sqlite3.connect(str(self.db_path))

    def start_tracking(self):
        """Запуск отслеживания активности"""
        if self.is_tracking:
            return
        
        self.is_tracking = True
        self.start_time = time.time()
        
        # Запускаем слушатели клавиатуры и мыши
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press
        )
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move
        )
        
        self.keyboard_listener.start()
        self.mouse_listener.start()
        
        # Запускаем поток отслеживания
        self.tracking_thread = threading.Thread(
            target=self.track_activity,
            daemon=True
        )
        self.tracking_thread.start()
        
        logger.info("Отслеживание активности запущено")

    def stop_tracking(self):
        """Остановка отслеживания активности"""
        if not self.is_tracking:
            return
        
        self.is_tracking = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        if self.current_app:
            duration = time.time() - self.start_time
            self.save_activity(self.current_app, duration)
            self.current_app = None
        
        logger.info("Отслеживание активности остановлено")

    def track_activity(self):
        """Основной цикл отслеживания активности"""
        while self.is_tracking:
            active_window = self.get_active_window()
            if not active_window:
                time.sleep(1)
                continue
            
            # Проверяем, является ли приложение отслеживаемым
            tracked_app = next(
                (app for app in self.tracked_apps 
                 if app['process_name'].lower() == active_window['process_name'].lower() 
                 and app['is_active']),
                None
            )
            
            if tracked_app:
                if self.current_app != tracked_app:
                    if self.current_app:
                        duration = time.time() - self.start_time
                        self.save_activity(self.current_app, duration)
                    
                    self.current_app = tracked_app
                    self.start_time = time.time()
                    logger.info(f"Начато отслеживание: {tracked_app['name']}")
            
            time.sleep(1)

    def on_key_press(self, key):
        """Обработчик нажатия клавиш"""
        if self.current_app:
            self.start_time = time.time()  # Обновляем время последней активности

    def on_mouse_move(self, x, y):
        """Обработчик движения мыши"""
        if self.current_app:
            self.start_time = time.time()  # Обновляем время последней активности

    def add_tracked_app(self, name: str, process_name: str) -> bool:
        """Добавление нового приложения для отслеживания"""
        try:
            response = requests.post(
                f"{self.base_url}/tracked-apps/",
                headers=self.headers,
                json={
                    'name': name,
                    'process_name': process_name,
                    'is_active': True
                },
                timeout=5
            )
            response.raise_for_status()
            
            self.tracked_apps = self.get_tracked_apps()
            logger.info(f"Добавлено приложение для отслеживания: {name}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при добавлении приложения: {e}")
            return False

    def remove_app(self, app_id: int) -> bool:
        """Удаление приложения из списка отслеживаемых"""
        try:
            response = requests.delete(
                f"{self.base_url}/tracked-apps/{app_id}/",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            
            self.tracked_apps = self.get_tracked_apps()
            logger.info(f"Удалено приложение: {app_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при удалении приложения: {e}")
            return False

    def toggle_app_tracking(self, app_id: int) -> bool:
        """Включение/выключение отслеживания приложения"""
        try:
            app = next((a for a in self.tracked_apps if a['id'] == app_id), None)
            if not app:
                return False
            
            response = requests.patch(
                f"{self.base_url}/tracked-apps/{app_id}/",
                headers=self.headers,
                json={'is_active': not app['is_active']},
                timeout=5
            )
            response.raise_for_status()
            
            self.tracked_apps = self.get_tracked_apps()
            logger.info(f"Изменен статус отслеживания приложения: {app_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при изменении статуса приложения: {e}")
            return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec_()) 