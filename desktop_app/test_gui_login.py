#!/usr/bin/env python3
"""
Тест GUI логики входа без запуска полного интерфейса
"""

import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import _LegacyAPIClient
import configparser

def test_config_base_url():
    """Тестируем какой URL используется в конфигурации по умолчанию"""
    print("=== ТЕСТ КОНФИГУРАЦИИ ===")
    
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    if config.has_section('Server'):
        base_url = config.get('Server', 'base_url', fallback='НЕ НАЙДЕН')
        print(f"Server base_url: {base_url}")
    
    if config.has_section('API'):
        api_url = config.get('API', 'base_url', fallback='НЕ НАЙДЕН')
        print(f"API base_url: {api_url}")
        
    if config.has_section('Credentials'):
        cred_url = config.get('Credentials', 'api_base_url', fallback='НЕ НАЙДЕН')
        print(f"Credentials api_base_url: {cred_url}")

def test_user_input_simulation():
    """Симулируем ввод пользователя в GUI"""
    print("\n=== СИМУЛЯЦИЯ ВВОДА ПОЛЬЗОВАТЕЛЯ ===")
    
    # Симулируем ввод http://127.0.0.1:8001/api
    user_input_url = "http://127.0.0.1:8001/api"
    username = "heist"
    password = "1234567vampire"
    
    print(f"Пользователь вводит:")
    print(f"  URL: {user_input_url}")
    print(f"  Логин: {username}")
    print(f"  Пароль: {password}")
    
    # Создаем клиент как в реальном GUI
    client = _LegacyAPIClient(user_input_url)
    print(f"Клиент создан с base_url: {client.base_url}")
    
    # Тестируем авторизацию
    try:
        success, result = client.login(username, password)
        print(f"Результат авторизации: success={success}")
        if success:
            print(f"✅ УСПЕХ! Токен: {result}")
        else:
            print(f"❌ ОШИБКА: {result}")
        return success
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

def test_different_url_formats():
    """Тестируем разные форматы URL, которые может ввести пользователь"""
    print("\n=== ТЕСТ РАЗНЫХ ФОРМАТОВ URL ===")
    
    test_cases = [
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8001/",
        "http://127.0.0.1:8001/api",
        "http://127.0.0.1:8001/api/",
        "127.0.0.1:8001",
        "127.0.0.1:8001/api",
    ]
    
    success_count = 0
    
    for url in test_cases:
        print(f"\n--- Тест URL: {url} ---")
        try:
            # Добавляем http:// если его нет
            if not url.startswith('http'):
                url = f"http://{url}"
                
            client = _LegacyAPIClient(url)
            success, result = client.login("heist", "1234567vampire")
            if success:
                print(f"✅ Успех с URL: {url}")
                success_count += 1
            else:
                print(f"❌ Ошибка с URL: {url} - {result}")
        except Exception as e:
            print(f"❌ Исключение с URL: {url} - {e}")
    
    print(f"\nИтого: {success_count}/{len(test_cases)} URL работают правильно")

if __name__ == "__main__":
    test_config_base_url()
    test_user_input_simulation()
    test_different_url_formats() 