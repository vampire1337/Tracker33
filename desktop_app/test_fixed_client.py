#!/usr/bin/env python3
"""
🧪 Тест исправленного клиента
Проверяет что клиент использует правильные API endpoints
"""

import requests
import asyncio
import aiohttp
import sys
import os

def test_api_endpoints():
    """Тестирует правильные API endpoints"""
    base_url = "http://127.0.0.1:8001"
    
    print("🧪 Тестирование API endpoints...")
    
    # Тест 1: Проверка доступности сервера
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Сервер доступен: {response.status_code}")
    except:
        print("❌ Сервер недоступен!")
        return False
    
    # Тест 2: Проверка правильного endpoint авторизации
    login_data = {
        'username': 'heist',
        'password': '1234567vampire'
    }
    
    try:
        auth_response = requests.post(
            f"{base_url}/api/token/",
            json=login_data,
            timeout=5
        )
        
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            token = token_data.get('token')
            print(f"✅ Правильный API endpoint работает: получен токен {token[:20]}...")
            
            # Тест 3: Проверка API приложений
            headers = {'Authorization': f'Token {token}'}
            apps_response = requests.get(f"{base_url}/api/applications/", headers=headers)
            print(f"✅ API приложений доступно: {apps_response.status_code}")
            
            return True
        else:
            print(f"❌ Ошибка авторизации: {auth_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

async def test_client_authentication():
    """Тестирует аутентификацию как в клиенте"""
    config = {
        'server_url': 'http://127.0.0.1:8001',
        'username': 'heist',
        'password': '1234567vampire'
    }
    
    print("🔐 Тестирование аутентификации клиента...")
    
    try:
        async with aiohttp.ClientSession() as session:
            login_data = {
                'username': config['username'],
                'password': config['password']
            }
            
            # ИСПРАВЛЕННЫЙ endpoint
            auth_url = f"{config['server_url']}/api/token/"
            
            async with session.post(
                auth_url,
                json=login_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get('token')
                    if token:
                        print(f"✅ Клиентская аутентификация работает: {token[:20]}...")
                        return True
                    else:
                        print("❌ Токен не получен")
                        return False
                else:
                    print(f"❌ Ошибка клиентской аутентификации: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка клиентского теста: {e}")
        return False

def main():
    print("🚀 Запуск тестов исправленного клиента")
    print("=" * 50)
    
    # Тест API endpoints
    if not test_api_endpoints():
        print("❌ Тесты API провалены!")
        return
    
    # Тест клиентской аутентификации
    if not asyncio.run(test_client_authentication()):
        print("❌ Тесты клиента провалены!")
        return
    
    print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    print("✅ Исправленный клиент должен работать корректно")

if __name__ == "__main__":
    main() 