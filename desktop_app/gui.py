from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QLineEdit, QMessageBox,
    QSystemTrayIcon, QMenu, QAction, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import sys
import os
from pathlib import Path
from .main import TimeTracker, get_base_path
from .styles import setup_dark_theme, STYLES

class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_path = get_base_path()
        self.tracker = TimeTracker()
        self.init_ui()
        self.init_tray()
        self.apply_styles()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_app_list)
        self.update_timer.start(5000)  # Обновляем список каждые 5 секунд

    def apply_styles(self):
        # Применяем стили ко всем элементам
        for widget_type, style in STYLES.items():
            self.setStyleSheet(self.styleSheet() + style)

    def init_ui(self):
        self.setWindowTitle('Time Tracker')
        self.setGeometry(100, 100, 800, 600)

        # Основной виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        header = QLabel('Time Tracker')
        header.setStyleSheet('font-size: 24px; font-weight: bold; margin-bottom: 20px;')
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Статистика
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.StyledPanel)
        stats_layout = QHBoxLayout(stats_frame)
        
        self.total_time_label = QLabel('Общее время: 0:00:00')
        self.active_apps_label = QLabel('Активных приложений: 0')
        
        stats_layout.addWidget(self.total_time_label)
        stats_layout.addWidget(self.active_apps_label)
        
        layout.addWidget(stats_frame)

        # Форма добавления приложения
        add_frame = QFrame()
        add_frame.setFrameShape(QFrame.StyledPanel)
        add_layout = QHBoxLayout(add_frame)
        
        self.app_name_input = QLineEdit()
        self.app_name_input.setPlaceholderText('Название приложения')
        self.process_name_input = QLineEdit()
        self.process_name_input.setPlaceholderText('Имя процесса')
        
        add_button = QPushButton('Добавить')
        add_button.clicked.connect(self.add_app)
        
        add_layout.addWidget(self.app_name_input)
        add_layout.addWidget(self.process_name_input)
        add_layout.addWidget(add_button)
        
        layout.addWidget(add_frame)

        # Список приложений
        apps_frame = QFrame()
        apps_frame.setFrameShape(QFrame.StyledPanel)
        apps_layout = QVBoxLayout(apps_frame)
        
        apps_header = QLabel('Отслеживаемые приложения')
        apps_header.setStyleSheet('font-size: 16px; font-weight: bold; margin-bottom: 10px;')
        apps_layout.addWidget(apps_header)
        
        self.app_list = QListWidget()
        self.update_app_list()
        apps_layout.addWidget(self.app_list)
        
        # Кнопки управления
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        self.toggle_button = QPushButton('Включить/Выключить')
        self.toggle_button.clicked.connect(self.toggle_app)
        
        self.remove_button = QPushButton('Удалить')
        self.remove_button.clicked.connect(self.remove_app)
        
        buttons_layout.addWidget(self.toggle_button)
        buttons_layout.addWidget(self.remove_button)
        
        apps_layout.addWidget(buttons_widget)
        layout.addWidget(apps_frame)

        # Статус отслеживания
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_layout = QVBoxLayout(status_frame)
        
        self.status_label = QLabel("Статус: Не отслеживается")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_frame)

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

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = self.base_path / 'icon.png'
        self.tray_icon.setIcon(QIcon(str(icon_path)))
        
        tray_menu = QMenu()
        show_action = QAction('Показать', self)
        quit_action = QAction('Выход', self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def update_app_list(self):
        self.app_list.clear()
        active_count = 0
        for app in self.tracker.tracked_apps:
            status = '✓' if app['is_active'] else '✗'
            if app['is_active']:
                active_count += 1
            item = f"{status} {app['name']} ({app['process_name']})"
            self.app_list.addItem(item)
        
        self.active_apps_label.setText(f'Активных приложений: {active_count}')

    def add_app(self):
        name = self.app_name_input.text()
        process_name = self.process_name_input.text()
        
        if not name or not process_name:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля')
            return
        
        if self.tracker.add_tracked_app(name, process_name):
            self.app_name_input.clear()
            self.process_name_input.clear()
            self.update_app_list()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось добавить приложение')

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
        self.progress_bar.show()
        self.tracker.start_tracking()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_tracking(self):
        self.status_label.setText("Статус: Отслеживание остановлено")
        self.progress_bar.hide()
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