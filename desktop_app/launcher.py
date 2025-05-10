"""
Модуль-обертка для запуска TimeTracker без проверки pip и других зависимостей
"""
import os
import sys
import importlib.util
import types
import builtins
import requests
import logging

# Настройка директории для логов
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "launcher.log")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LauncherTimeTracker")

# Отключаем проверку пользовательских site-packages
os.environ['PYTHONNOUSERSITE'] = '1'

# Переопределяем __import__ для блокировки импорта pip
original_import = builtins.__import__

def patched_import(name, *args, **kwargs):
    """Перехватчик импортов для блокировки pip"""
    # Блокируем попытки импорта pip
    if name == 'pip' or name.startswith('pip.'):
        # Возвращаем фиктивный модуль вместо реального pip
        fake_module = types.ModuleType(name)
        fake_module.__file__ = '<fake-pip>'
        
        # Если это pip._internal, добавляем фиктивные подмодули
        if name == 'pip._internal':
            fake_module.main = lambda *args, **kwargs: 0
        
        return fake_module
    
    # Для всех остальных модулей используем оригинальный импорт
    return original_import(name, *args, **kwargs)

# Устанавливаем перехватчик импорта
builtins.__import__ = patched_import

# Создаем фиктивные модули pip в sys.modules
sys.modules['pip'] = types.ModuleType('pip')
sys.modules['pip._internal'] = types.ModuleType('pip._internal')
sys.modules['pip._internal.main'] = types.ModuleType('pip._internal.main')
sys.modules['pip._internal.main'].main = lambda *args, **kwargs: 0

# Проверяем соединение с сервером
def check_server_connection():
    """Проверка доступности сервера"""
    try:
        logger.info("Проверка соединения с сервером...")
        response = requests.get("http://46.173.26.149:8000/api/", 
                              timeout=10, 
                              verify=False)
        if response.status_code == 200:
            logger.info(f"Сервер доступен. Код ответа: {response.status_code}")
            return True
        else:
            logger.warning(f"Сервер вернул код: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке соединения: {e}")
        return False

# Подавляем предупреждения
import warnings
warnings.simplefilter("ignore")

# Подавляем вывод ошибок pynput
import logging
logging.getLogger('pynput').setLevel(logging.CRITICAL)

# Запускаем основное приложение
print("Запуск TimeTracker...")
logger.info("Инициализация TimeTracker")

if __name__ == "__main__":
    # Проверяем соединение с сервером
    connection_available = check_server_connection()
    if connection_available:
        logger.info("Соединение с сервером установлено успешно")
    else:
        logger.warning("Не удалось установить соединение с сервером. Приложение будет работать в автономном режиме.")
    
    # Импортируем main.py и запускаем основную функцию
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Здесь прямой импорт из main, запускаем приложение
    try:
        # Хак для отключения проверки на относительный импорт
        sys.path.append('')
        
        # Исправляем относительный импорт, который вызывает проблему
        import main_original
        # Используем другое имя, чтобы избежать конфликта имен
        main_module = main_original
        
        # Запускаем основную функцию из main.py
        if hasattr(main_module, 'TimeTrackerApp') and hasattr(main_module, 'QApplication'):
            app = main_module.QApplication(sys.argv)
            window = main_module.TimeTrackerApp()
            window.show()
            sys.exit(app.exec_())
        else:
            logger.error("Не удалось найти класс TimeTrackerApp в main.py")
            print("Не удалось найти класс TimeTrackerApp в main.py")
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        print(f"Ошибка при запуске приложения: {e}")
        import traceback
        traceback.print_exc() 