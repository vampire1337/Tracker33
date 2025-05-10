"""
Модуль-обертка для запуска TimeTracker с корректной обработкой зависимостей
"""
import os
import sys
import logging
import importlib.util
import requests
import warnings
from pathlib import Path

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

# Подавляем предупреждения
warnings.simplefilter("ignore")

# Подавляем вывод ошибок pynput
logging.getLogger('pynput').setLevel(logging.CRITICAL)

# Проверка наличия и импорт необходимых модулей
required_modules = [
    'PyQt5', 'psutil', 'pynput', 'pygetwindow', 'requests', 
    'win32gui', 'win32process', 'jwt'
]

def check_dependencies():
    """
    Проверяет наличие необходимых зависимостей
    Возвращает True, если все зависимости доступны, и False в противном случае
    """
    missing_modules = []
    
    logger.info("Проверка необходимых зависимостей...")
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            logger.info(f"✓ Модуль {module_name} доступен")
        except ImportError:
            logger.warning(f"✗ Модуль {module_name} не найден")
            missing_modules.append(module_name)
    
    if missing_modules:
        logger.error(f"Отсутствуют необходимые модули: {', '.join(missing_modules)}")
        return False
    
    logger.info("Все необходимые зависимости присутствуют")
    return True

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

def create_qt_app():
    """
    Создает экземпляр QApplication
    Инициализирует PyQt для остальной части приложения
    """
    try:
        from PyQt5.QtWidgets import QApplication
        return QApplication(sys.argv)
    except ImportError:
        logger.critical("Не удалось импортировать PyQt5.QtWidgets.QApplication")
        return None

def show_missing_dependencies_message(missing_modules):
    """
    Отображает диалоговое окно с информацией о недостающих зависимостях
    """
    try:
        from PyQt5.QtWidgets import QMessageBox, QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Отсутствуют зависимости")
        msg.setText("Для работы приложения необходимы дополнительные компоненты")
        msg.setInformativeText(f"Отсутствуют модули: {', '.join(missing_modules)}\n\n"
                              "Приложение будет работать в ограниченном режиме или может быть нестабильным.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    except Exception as e:
        logger.error(f"Не удалось показать диалог о недостающих зависимостях: {e}")

if __name__ == "__main__":
    logger.info("Запуск TimeTracker...")
    
    # Проверяем зависимости
    all_dependencies_available = check_dependencies()
    if not all_dependencies_available:
        logger.warning("Некоторые зависимости отсутствуют, но приложение попытается запуститься")
    
    # Проверяем соединение с сервером
    connection_available = check_server_connection()
    if connection_available:
        logger.info("Соединение с сервером установлено успешно")
    else:
        logger.warning("Не удалось установить соединение с сервером. Приложение будет работать в автономном режиме.")
    
    # Импортируем main.py и запускаем основную функцию
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Добавляем текущую директорию в путь для импорта
        sys.path.append('')
        
        # Импортируем основной модуль приложения
        import main as main_module
        
        # Запускаем основную функцию
        if hasattr(main_module, 'TimeTrackerApp') and hasattr(main_module, 'QApplication'):
            app = main_module.QApplication(sys.argv)
            window = main_module.TimeTrackerApp()
            window.show()
            sys.exit(app.exec_())
        else:
            logger.error("Не удалось найти класс TimeTrackerApp в main.py")
            print("Не удалось найти класс TimeTrackerApp в main.py")
    except ImportError as e:
        logger.error(f"Ошибка импорта при запуске приложения: {e}")
        # Пытаемся показать сообщение пользователю
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            app = QApplication.instance() or QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка запуска")
            msg.setText("Не удалось запустить приложение")
            msg.setInformativeText(f"Ошибка: {str(e)}\n\nВозможно, отсутствуют необходимые компоненты.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        except:
            # Если не удалось показать GUI-сообщение, выводим в консоль
            print(f"Ошибка при запуске приложения: {e}")
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        print(f"Ошибка при запуске приложения: {e}")
        import traceback
        traceback.print_exc() 