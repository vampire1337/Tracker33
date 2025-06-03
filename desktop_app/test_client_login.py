#!/usr/bin/env python3
"""
Тест для отладки проблемы с входом в клиент
"""

import sys
import os
import configparser
from pathlib import Path

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import _LegacyAPIClient
import requests

def test_login_url_formation():
    """Тестируем формирование URL для входа"""
    print("=== ТЕСТ ФОРМИРОВАНИЯ URL ===")
    
    # Тестируем разные варианты базового URL
    test_urls = [
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8001/",
        "http://127.0.0.1:8001/api",
        "http://127.0.0.1:8001/api/",
    ]
    
    for base_url in test_urls:
        print(f"\n--- Тестирую базовый URL: {base_url} ---")
        
        client = _LegacyAPIClient(base_url)
        print(f"Базовый URL клиента: {client.base_url}")
        
        # Симулируем формирование URL для аутентификации
        auth_url = f"{client.base_url.rstrip('/')}/api/token/"
        print(f"URL для аутентификации: {auth_url}")
        
        # Тестируем запрос
        try:
            response = requests.post(
                auth_url,
                json={
                    'username': 'heist',
                    'password': '1234567vampire'
                },
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            print(f"Ответ сервера: {response.status_code}")
            if response.status_code == 200:
                print("✅ Успешно!")
                token_data = response.json()
                print(f"Токен: {token_data.get('token', 'НЕ НАЙДЕН')}")
            else:
                print(f"❌ Ошибка: {response.text}")
        except Exception as e:
            print(f"❌ Исключение: {e}")

def test_legacy_client_login():
    """Тестируем метод login в _LegacyAPIClient"""
    print("\n=== ТЕСТ МЕТОДА LOGIN ===")
    
    base_url = "http://127.0.0.1:8001/api"
    print(f"Создаем клиент с URL: {base_url}")
    
    client = _LegacyAPIClient(base_url)
    print(f"Базовый URL клиента: {client.base_url}")
    
    # Тестируем login метод
    try:
        success, result = client.login("heist", "1234567vampire")
        print(f"Результат login: success={success}")
        if success:
            print(f"✅ Токен получен: {result}")
        else:
            print(f"❌ Ошибка: {result}")
    except Exception as e:
        print(f"❌ Исключение в login: {e}")

if __name__ == "__main__":
    test_login_url_formation()
    test_legacy_client_login() 