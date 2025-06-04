#!/usr/bin/env python3
"""
Полный тест клиентского приложения для проверки всех компонентов
"""

import sys
import os
import configparser
from pathlib import Path

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_client import APIClient
import requests

def test_config():
    """Тестирует конфигурацию клиента"""
    print("=== ТЕСТ КОНФИГУРАЦИИ ===")
    
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    # Проверяем основные секции
    sections = ['API', 'Server', 'Credentials', 'Settings']
    for section in sections:
        if config.has_section(section):
            print(f"✅ Секция {section} найдена")
            for key, value in config[section].items():
                print(f"   {key} = {value}")
        else:
            print(f"❌ Секция {section} не найдена")
    
    return config

def test_server_connection():
    """Тестирует подключение к серверу"""
    print("\n=== ТЕСТ ПОДКЛЮЧЕНИЯ К СЕРВЕРУ ===")
    
    base_url = "http://127.0.0.1:8001"
    
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Сервер доступен: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Сервер недоступен на {base_url}")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    
    return True

def test_api_client():
    """Тестирует API клиент"""
    print("\n=== ТЕСТ API КЛИЕНТА ===")
    
    api_client = APIClient("http://127.0.0.1:8001/api")
    
    # Проверяем загрузку токена
    if api_client.token:
        print(f"✅ Токен загружен: {api_client.token[:20]}...")
    else:
        print("❌ Токен не загружен")
    
    # Тестируем подключение
    success, message = api_client.test_connection()
    if success:
        print(f"✅ Подключение к API: {message}")
    else:
        print(f"❌ Подключение к API: {message}")
    
    # Тестируем получение приложений
    try:
        apps = api_client.get_tracked_applications()
        if apps:
            print(f"✅ Получено {len(apps)} приложений")
        else:
            print("❌ Не удалось получить приложения")
    except Exception as e:
        print(f"❌ Ошибка получения приложений: {e}")
    
    return api_client

def test_authentication():
    """Тестирует аутентификацию"""
    print("\n=== ТЕСТ АУТЕНТИФИКАЦИИ ===")
    
    api_client = APIClient("http://127.0.0.1:8001/api")
    
    # Тестируем аутентификацию с правильными данными
    success = api_client.authenticate("heist", "1234567vampire")
    
    if success:
        print("✅ Аутентификация успешна")
        print(f"   Токен: {api_client.token[:20]}...")
    else:
        print("❌ Аутентификация не удалась")
    
    return success

def main():
    """Главная функция тестирования"""
    print("🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ КЛИЕНТА TimeTracker")
    print("=" * 50)
    
    # Тест 1: Конфигурация
    config = test_config()
    
    # Тест 2: Подключение к серверу
    server_ok = test_server_connection()
    
    # Тест 3: API клиент
    if server_ok:
        api_client = test_api_client()
    else:
        print("⚠️ Пропускаем тест API клиента - сервер недоступен")
        return
    
    # Тест 4: Аутентификация
    auth_ok = test_authentication()
    
    # Итоговый результат
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    
    if server_ok and auth_ok:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🎉 Клиент готов к работе!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        if not server_ok:
            print("   - Проблемы с подключением к серверу")
        if not auth_ok:
            print("   - Проблемы с аутентификацией")

if __name__ == "__main__":
    main() 