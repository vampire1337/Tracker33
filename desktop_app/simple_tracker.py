#!/usr/bin/env python3
"""
🚀 Tracker33 - Современный легкий клиент
Простой, надежный и быстрый трекер активности

Возможности:
- Интерактивная настройка при первом запуске
- Автоматическое отслеживание активности
- Надежная работа с API
- Простая настройка через config.json
- Системные уведомления
"""

import json
import time
import logging
import asyncio
import aiohttp
import psutil
import getpass
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import platform
import sys
import signal

# Кроссплатформенные зависимости
try:
    import pygetwindow as gw
    from pynput import keyboard, mouse
except ImportError as e:
    print(f"❌ Не удалось импортировать зависимости: {e}")
    print("Установите зависимости: pip install pygetwindow pynput")
    sys.exit(1)

# Системные уведомления
try:
    if platform.system() == "Windows":
        import win10toast
        HAS_NOTIFICATIONS = True
    else:
        # Для Linux/macOS можно использовать plyer или другие библиотеки
        HAS_NOTIFICATIONS = False
except ImportError:
    HAS_NOTIFICATIONS = False

@dataclass
class Config:
    """Конфигурация трекера"""
    server_url: str = "http://127.0.0.1:8001"
    username: str = ""
    password: str = ""
    check_interval: int = 5  # секунды
    idle_threshold: int = 300  # 5 минут
    log_level: str = "INFO"

class SimpleTracker:
    """Простой и надежный трекер активности"""
    
    def __init__(self):
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.session = None
        self.auth_token = None
        self.current_app = None
        self.start_time = None
        self.keyboard_presses = 0
        self.last_activity = time.time()
        self.running = True
        
        # Регистрируем обработчики сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Config:
        """Загружает конфигурацию из файла"""
        config_file = Path("config.json")
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Config(**data)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки конфигурации: {e}")
        
        # Создаем конфигурацию по умолчанию
        config = Config()
        self._save_config(config)
        print("📄 Создан файл конфигурации config.json")
        return config
    
    def _save_config(self, config: Config):
        """Сохраняет конфигурацию в файл"""
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(config.__dict__, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Настройка логирования"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        return logging.getLogger('Tracker33')
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        self.logger.info("🛑 Получен сигнал завершения")
        self.running = False
    
    async def _notify(self, title: str, message: str):
        """Показывает системное уведомление"""
        if HAS_NOTIFICATIONS and platform.system() == "Windows":
            try:
                toaster = win10toast.ToastNotifier()
                toaster.show_toast(title, message, duration=3)
            except:
                pass
        
        # Для других систем просто логируем
        self.logger.info(f"📢 {title}: {message}")
    
    def _interactive_setup(self) -> bool:
        """Интерактивная настройка при первом запуске"""
        print("\n" + "="*50)
        print("🚀 ПЕРВОНАЧАЛЬНАЯ НАСТРОЙКА TRACKER33")
        print("="*50)
        
        # Проверяем, нужна ли настройка
        if self.config.username and self.config.password:
            print(f"✅ Найдены сохраненные настройки для пользователя: {self.config.username}")
            
            # Спрашиваем, хочет ли пользователь изменить настройки
            while True:
                choice = input("\n🔄 Хотите изменить настройки? (y/n): ").lower().strip()
                if choice in ['n', 'no', 'н', 'нет', '']:
                    return True
                elif choice in ['y', 'yes', 'д', 'да']:
                    break
                else:
                    print("❌ Пожалуйста, введите 'y' для да или 'n' для нет")
        
        print("\n📝 НАСТРОЙКА ПОДКЛЮЧЕНИЯ К СЕРВЕРУ")
        print("-" * 40)
        
        # Адрес сервера
        current_url = self.config.server_url
        print(f"Текущий адрес сервера: {current_url}")
        new_url = input("🌐 Введите адрес сервера (или нажмите Enter для использования текущего): ").strip()
        if new_url:
            self.config.server_url = new_url
        
        # Учетные данные
        print("\n🔐 УЧЕТНЫЕ ДАННЫЕ")
        print("-" * 20)
        
        while True:
            username = input("👤 Введите имя пользователя: ").strip()
            if username:
                break
            print("❌ Имя пользователя не может быть пустым!")
        
        while True:
            password = getpass.getpass("🔒 Введите пароль: ").strip()
            if password:
                break
            print("❌ Пароль не может быть пустым!")
        
        # Сохраняем временно для проверки
        old_username = self.config.username
        old_password = self.config.password
        
        self.config.username = username
        self.config.password = password
        
        print("\n🔄 Проверка подключения...")
        
        # Проверяем подключение
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            auth_result = loop.run_until_complete(self._test_authentication())
            if auth_result:
                print("✅ Подключение успешно! Сохраняю настройки...")
                self._save_config(self.config)
                print("💾 Настройки сохранены в config.json")
                return True
            else:
                print("❌ Ошибка подключения!")
                # Восстанавливаем старые настройки
                self.config.username = old_username
                self.config.password = old_password
                
                print("\n🔄 Хотите попробовать ещё раз? (y/n): ", end="")
                retry = input().lower().strip()
                if retry in ['y', 'yes', 'д', 'да']:
                    return self._interactive_setup()
                else:
                    return False
        finally:
            loop.close()
    
    async def _test_authentication(self) -> bool:
        """Тестирует аутентификацию с текущими настройками"""
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    'username': self.config.username,
                    'password': self.config.password
                }
                
                async with session.post(
                    f"{self.config.server_url}/api/auth/login/",
                    json=login_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return 'token' in data
                    else:
                        error_text = await response.text()
                        print(f"Ошибка сервера ({response.status}): {error_text}")
                        return False
        
        except asyncio.TimeoutError:
            print("❌ Превышено время ожидания. Проверьте адрес сервера.")
            return False
        except aiohttp.ClientConnectorError:
            print("❌ Не удалось подключиться к серверу. Проверьте адрес и доступность.")
            return False
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def authenticate(self) -> bool:
        """Аутентификация на сервере"""
        if not self.config.username or not self.config.password:
            self.logger.error("❌ Не заданы логин и пароль")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    'username': self.config.username,
                    'password': self.config.password
                }
                
                async with session.post(
                    f"{self.config.server_url}/api/auth/login/",
                    json=login_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.auth_token = data.get('token')
                        self.logger.info("✅ Успешная аутентификация")
                        await self._notify("Tracker33", "Подключение установлено")
                        return True
                    else:
                        self.logger.error(f"❌ Ошибка аутентификации: {response.status}")
                        return False
        
        except Exception as e:
            self.logger.error(f"❌ Ошибка подключения: {e}")
            return False
    
    def _get_active_window(self) -> Optional[Dict[str, str]]:
        """Получает информацию об активном окне"""
        try:
            if platform.system() == "Windows":
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                window_title = win32gui.GetWindowText(hwnd)
                
                # Получаем имя процесса
                import win32process
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                app_name = process.name()
                
                return {
                    'app_name': app_name,
                    'window_title': window_title
                }
            else:
                # Для Linux/macOS используем pygetwindow
                active_window = gw.getActiveWindow()
                if active_window:
                    return {
                        'app_name': active_window._hWnd.split('/')[-1] if hasattr(active_window, '_hWnd') else 'Unknown',
                        'window_title': active_window.title
                    }
        except Exception as e:
            self.logger.debug(f"Ошибка получения окна: {e}")
        
        return None
    
    def _on_keyboard_press(self, key):
        """Обработчик нажатий клавиш"""
        self.keyboard_presses += 1
        self.last_activity = time.time()
    
    def _setup_listeners(self):
        """Настройка слушателей активности"""
        try:
            self.keyboard_listener = keyboard.Listener(on_press=self._on_keyboard_press)
            self.keyboard_listener.start()
            self.logger.info("🎧 Слушатели активности запущены")
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска слушателей: {e}")
    
    async def _send_activity(self, activity: Dict[str, Any]) -> bool:
        """Отправляет данные активности на сервер"""
        if not self.auth_token:
            return False
        
        try:
            headers = {
                'Authorization': f'Token {self.auth_token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.server_url}/api/activities/",
                    json=activity,
                    headers=headers
                ) as response:
                    if response.status in [200, 201]:
                        self.logger.debug(f"✅ Активность отправлена: {activity['app_name']}")
                        return True
                    else:
                        self.logger.error(f"❌ Ошибка отправки: {response.status}")
                        return False
        
        except Exception as e:
            self.logger.error(f"❌ Ошибка отправки активности: {e}")
            return False
    
    async def _track_current_activity(self):
        """Отслеживает текущую активность"""
        window_info = self._get_active_window()
        
        if not window_info:
            return
        
        current_app = window_info['app_name']
        current_time = time.time()
        
        # Если приложение изменилось, отправляем предыдущую активность
        if self.current_app and self.current_app != current_app and self.start_time:
            duration = current_time - self.start_time
            
            if duration > 1:  # Игнорируем активности менее 1 секунды
                activity = {
                    'app_name': self.current_app,
                    'title': '',  # Упрощаем, не отправляем заголовок
                    'start_time': datetime.fromtimestamp(self.start_time, timezone.utc).isoformat(),
                    'end_time': datetime.fromtimestamp(current_time, timezone.utc).isoformat(),
                    'keyboard_presses': self.keyboard_presses,
                    'is_productive': True  # По умолчанию считаем продуктивным
                }
                
                await self._send_activity(activity)
                
                self.logger.info(
                    f"📊 {self.current_app}: {int(duration)}s, "
                    f"нажатий: {self.keyboard_presses}"
                )
        
        # Обновляем текущую активность
        if self.current_app != current_app:
            self.current_app = current_app
            self.start_time = current_time
            self.keyboard_presses = 0
    
    async def _check_idle(self):
        """Проверяет состояние простоя"""
        idle_time = time.time() - self.last_activity
        
        if idle_time > self.config.idle_threshold:
            if self.current_app:
                self.logger.info("😴 Пользователь неактивен")
                self.current_app = None
                self.start_time = None
    
    async def run(self):
        """Главный цикл трекера"""
        self.logger.info("🚀 Запуск Tracker33 Simple Client")
        
        # Интерактивная настройка при необходимости
        if not self.config.username or not self.config.password:
            print("⚙️ Требуется первоначальная настройка...")
            if not self._interactive_setup():
                print("❌ Настройка отменена")
                return
        
        # Аутентификация
        if not await self.authenticate():
            self.logger.error("❌ Не удалось подключиться к серверу")
            print("\n🔧 Для изменения настроек удалите файл config.json и перезапустите программу")
            return
        
        # Настройка слушателей
        self._setup_listeners()
        
        print("\n✅ Трекер запущен и работает!")
        print("📊 Отслеживание активности начато...")
        print("⏹️ Для остановки нажмите Ctrl+C")
        print("-" * 50)
        
        # Главный цикл
        try:
            while self.running:
                await self._track_current_activity()
                await self._check_idle()
                await asyncio.sleep(self.config.check_interval)
        
        except KeyboardInterrupt:
            self.logger.info("⏹️ Остановка трекера (Ctrl+C)")
        
        finally:
            await self._cleanup()
    
    async def _cleanup(self):
        """Очистка ресурсов"""
        self.logger.info("🧹 Очистка ресурсов...")
        
        # Останавливаем слушателей
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
        
        # Отправляем последнюю активность
        if self.current_app and self.start_time:
            current_time = time.time()
            duration = current_time - self.start_time
            
            if duration > 1:
                activity = {
                    'app_name': self.current_app,
                    'title': '',
                    'start_time': datetime.fromtimestamp(self.start_time, timezone.utc).isoformat(),
                    'end_time': datetime.fromtimestamp(current_time, timezone.utc).isoformat(),
                    'keyboard_presses': self.keyboard_presses,
                    'is_productive': True
                }
                
                await self._send_activity(activity)
        
        self.logger.info("✅ Трекер остановлен")

def main():
    """Точка входа"""
    print("🚀 Tracker33 Simple Client v2.1")
    print("Простой и надежный трекер активности")
    print("-" * 40)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == '--reset':
            config_file = Path("config.json")
            if config_file.exists():
                config_file.unlink()
                print("🔄 Настройки сброшены. Запустите программу заново для настройки.")
            else:
                print("ℹ️ Файл настроек не найден.")
            return
        elif sys.argv[1] == '--help':
            print("\nДоступные команды:")
            print("  --reset    Сбросить все настройки")
            print("  --help     Показать эту справку")
            return
    
    tracker = SimpleTracker()
    
    try:
        asyncio.run(tracker.run())
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 