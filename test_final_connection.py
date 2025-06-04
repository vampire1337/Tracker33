#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ тест подключения TimeTracker клиента к серверу
"""

import configparser
import requests
import json

def test_connection():
    print("🔍 ФИНАЛЬНАЯ ПРОВЕРКА ПОДКЛЮЧЕНИЯ")
    print("=" * 50)
    
    # Читаем конфигурацию
    config = configparser.ConfigParser()
    config.read('desktop_app/config.ini', encoding='utf-8')
    
    # Получаем данные
    api_url = config.get('Credentials', 'api_base_url')
    username = config.get('Credentials', 'username')
    auth_token = config.get('Credentials', 'auth_token')
    user_id = config.get('Credentials', 'user_id')
    demo_mode = config.get('Settings', 'demo_mode')
    
    print(f"📋 Конфигурация:")
    print(f"   API URL: {api_url}")
    print(f"   Username: {username}")
    print(f"   Token: {auth_token[:20]}...")
    print(f"   User ID: {user_id}")
    print(f"   Demo Mode: {demo_mode}")
    print()
    
    # Проверяем demo_mode
    if demo_mode.lower() == 'true':
        print("❌ ОШИБКА: demo_mode = True! Данные не будут отправляться!")
        return False
    else:
        print("✅ demo_mode = false - данные будут отправляться")
    
    # Тест подключения к серверу
    try:
        print("🔌 Тестируем подключение к серверу...")
        response = requests.get('http://127.0.0.1:8001/api/', timeout=5)
        print(f"✅ Сервер доступен! Статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        return False
    
    # Тест авторизации
    try:
        print("🔐 Тестируем авторизацию...")
        headers = {'Authorization': f'Token {auth_token}'}
        response = requests.get(f'{api_url}applications/', headers=headers, timeout=5)
        
        if response.status_code == 200:
            print("✅ Авторизация успешна!")
            print(f"   Получены приложения: {len(response.json())} шт.")
        else:
            print(f"❌ Ошибка авторизации: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании авторизации: {e}")
        return False
    
    print()
    print("🎯 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Клиент готов к работе!")
    return True

if __name__ == "__main__":
    test_connection() 