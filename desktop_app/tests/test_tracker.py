#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки работы трекера активности
"""

import sys
import os
import time
import logging
from pathlib import Path

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_connection():
    """Тестирует соединение с API"""
    try:
        from api_client import APIClient
        import configparser
        
        # Загружаем конфигурацию
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent / 'config.ini'
        config.read(config_path, encoding='utf-8')
        
        # Получаем URL API
        api_url = config.get('Credentials', 'api_base_url', fallback='http://147.45.153.16:8000/api/')
        logger.info(f"Тестируем соединение с API: {api_url}")
        
        # Создаем клиент
        client = APIClient(api_url)
        
        # Получаем токен из конфигурации
        token = config.get('Credentials', 'auth_token', fallback=None)
        if token:
            client.token = token
            logger.info("Токен найден в конфигурации")
        else:
            logger.error("Токен не найден в конфигурации")
            return False
        
        # Тестируем запрос к API
        try:
            response = client.session.get(f"{client.base_url}/applications/", 
                                        headers={'Authorization': f'Bearer {token}'}, 
                                        timeout=10)
            logger.info(f"Ответ API: {response.status_code}")
            if response.status_code == 200:
                logger.info("✅ Соединение с API работает")
                return True
            else:
                logger.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка соединения с API: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании API: {e}")
        return False

def test_window_detection():
    """Тестирует обнаружение активного окна"""
    try:
        # Импортируем функции для работы с окнами
        if sys.platform == "win32":
            import win32gui
            import win32process
            import psutil
            
            def get_window_info():
                """Получает информацию об активном окне"""
                try:
                    # Получаем дескриптор активного окна
                    hwnd = win32gui.GetForegroundWindow()
                    if not hwnd:
                        return None
                    
                    # Получаем заголовок окна
                    window_title = win32gui.GetWindowText(hwnd)
                    
                    # Получаем ID процесса
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    # Получаем информацию о процессе
                    try:
                        process = psutil.Process(pid)
                        app_name = process.name()
                        return {
                            'app_name': app_name,
                            'window_title': window_title,
                            'pid': pid
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return None
                        
                except Exception as e:
                    logger.error(f"Ошибка при получении информации об окне: {e}")
                    return None
            
            # Тестируем обнаружение окна
            logger.info("Тестируем обнаружение активного окна...")
            for i in range(5):
                window_info = get_window_info()
                if window_info:
                    logger.info(f"Обнаружено окно: {window_info['app_name']} - {window_info['window_title'][:50]}")
                else:
                    logger.warning("Не удалось обнаружить активное окно")
                time.sleep(1)
            
            return True
        else:
            logger.warning("Тест обнаружения окон доступен только на Windows")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании обнаружения окон: {e}")
        return False

def test_keyboard_tracking():
    """Тестирует отслеживание клавиатуры"""
    try:
        from pynput import keyboard
        
        logger.info("Тестируем отслеживание клавиатуры (нажмите несколько клавиш в течение 5 секунд)...")
        
        key_count = 0
        
        def on_press(key):
            nonlocal key_count
            key_count += 1
            logger.info(f"Нажата клавиша (всего: {key_count})")
        
        def on_release(key):
            # Останавливаем тест при нажатии Escape
            if key == keyboard.Key.esc:
                return False
        
        # Запускаем слушатель
        try:
            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
            logger.info("Слушатель клавиатуры запущен")
            
            # Ждем 5 секунд
            time.sleep(5)
            
            # Останавливаем слушатель
            listener.stop()
            listener.join()
            
            if key_count > 0:
                logger.info(f"✅ Отслеживание клавиатуры работает. Зафиксировано {key_count} нажатий")
                return True
            else:
                logger.warning("❌ Нажатия клавиш не зафиксированы. Возможно нужны права администратора.")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при создании/запуске слушателя клавиатуры: {e}")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта pynput: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании клавиатуры: {e}")
        return False

def main():
    """Главная функция тестирования"""
    logger.info("🔍 Запуск тестов трекера активности...")
    
    results = {
        'api_connection': test_api_connection(),
        'window_detection': test_window_detection(),
        'keyboard_tracking': test_keyboard_tracking()
    }
    
    logger.info("\n📊 Результаты тестирования:")
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
        logger.info(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        logger.info("\n🎉 Все тесты пройдены успешно!")
    else:
        logger.error("\n⚠️ Некоторые тесты не пройдены. Проверьте конфигурацию и зависимости.")
    
    return all_passed

if __name__ == "__main__":
    main() 