#!/usr/bin/env python3
"""
Скрипт для перезапуска Django-сервера
"""
import os
import sys
import subprocess
import signal
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("logs", "restart.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ServerRestart")

def get_server_pid():
    """Получает PID сервера из файла server.pid"""
    try:
        if os.path.exists('server.pid'):
            with open('server.pid', 'r') as f:
                pid = int(f.read().strip())
                return pid
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении PID сервера: {e}")
        return None

def stop_server():
    """Останавливает сервер"""
    pid = get_server_pid()
    if pid:
        try:
            logger.info(f"Остановка сервера с PID {pid}...")
            os.kill(pid, signal.SIGTERM)
            # Ждем завершения процесса
            for _ in range(5):  # Максимум 5 секунд на ожидание
                try:
                    # Проверяем, существует ли процесс
                    os.kill(pid, 0)
                    time.sleep(1)
                except OSError:
                    # Процесс уже не существует
                    break
            logger.info("Сервер успешно остановлен")
            # Удаляем файл PID
            os.remove('server.pid')
            return True
        except Exception as e:
            logger.error(f"Ошибка при остановке сервера: {e}")
            return False
    else:
        logger.warning("Не удалось найти PID сервера")
        return False

def start_server():
    """Запускает сервер"""
    try:
        logger.info("Запуск сервера...")
        # Для Windows
        if sys.platform.startswith('win'):
            process = subprocess.Popen(
                ["python", "manage.py", "runserver", "0.0.0.0:8000"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        # Для Linux/Mac
        else:
            process = subprocess.Popen(
                ["python3", "manage.py", "runserver", "0.0.0.0:8000"],
                start_new_session=True
            )
        
        # Сохраняем PID в файл
        with open('server.pid', 'w') as f:
            f.write(str(process.pid))
        
        logger.info(f"Сервер успешно запущен с PID {process.pid}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при запуске сервера: {e}")
        return False

def migrate_database():
    """Выполняет миграции базы данных"""
    try:
        logger.info("Применение миграций...")
        # Для Windows
        if sys.platform.startswith('win'):
            result = subprocess.run(["python", "manage.py", "migrate"], check=True)
        # Для Linux/Mac
        else:
            result = subprocess.run(["python3", "manage.py", "migrate"], check=True)
        
        if result.returncode == 0:
            logger.info("Миграции успешно применены")
            return True
        else:
            logger.error(f"Ошибка при применении миграций. Код возврата: {result.returncode}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при применении миграций: {e}")
        return False

def collect_static():
    """Собирает статические файлы"""
    try:
        logger.info("Сбор статических файлов...")
        # Для Windows
        if sys.platform.startswith('win'):
            result = subprocess.run(["python", "manage.py", "collectstatic", "--noinput"], check=True)
        # Для Linux/Mac
        else:
            result = subprocess.run(["python3", "manage.py", "collectstatic", "--noinput"], check=True)
        
        if result.returncode == 0:
            logger.info("Статические файлы успешно собраны")
            return True
        else:
            logger.error(f"Ошибка при сборе статических файлов. Код возврата: {result.returncode}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при сборе статических файлов: {e}")
        return False

def restart_server():
    """Перезапускает сервер"""
    logger.info("Начало перезапуска сервера...")
    
    # Останавливаем сервер, если он запущен
    stop_server()
    
    # Применяем миграции и собираем статические файлы
    migrations_success = migrate_database()
    static_success = collect_static()
    
    if not migrations_success:
        logger.warning("Миграции не были применены. Продолжаем перезапуск...")
    
    if not static_success:
        logger.warning("Статические файлы не были собраны. Продолжаем перезапуск...")
    
    # Запускаем сервер
    start_success = start_server()
    
    if start_success:
        logger.info("Сервер успешно перезапущен")
        return True
    else:
        logger.error("Ошибка при перезапуске сервера")
        return False

if __name__ == "__main__":
    # Создаем директорию для логов, если она не существует
    os.makedirs('logs', exist_ok=True)
    
    # Перезапускаем сервер
    success = restart_server()
    
    # Выходим с соответствующим кодом
    sys.exit(0 if success else 1) 