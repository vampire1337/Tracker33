#!/usr/bin/env python3
"""
🔍 ГЛУБОКАЯ ДИАГНОСТИКА АУТЕНТИФИКАЦИИ
Сравнивает как работает тест VS как работает клиент
"""

import requests
import json
import aiohttp
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

def test_working_auth():
    """Тестирует рабочую аутентификацию (как в check_users.py)"""
    print("🧪 ТЕСТ РАБОЧЕЙ АУТЕНТИФИКАЦИИ")
    print("=" * 50)
    
    url = "http://127.0.0.1:8001/api/token/"
    data = {
        'username': 'heist',
        'password': '1234567vampire'
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print(f"🌐 URL: {url}")
    print(f"📦 Data: {json.dumps(data, indent=2)}")
    print(f"📋 Headers: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ РАБОЧИЙ ТЕСТ ПРОШЕЛ!")
            return True
        else:
            print("❌ РАБОЧИЙ ТЕСТ ПРОВАЛЕН!")
            return False
    except Exception as e:
        print(f"💥 ОШИБКА: {e}")
        return False

async def test_client_auth():
    """Тестирует аутентификацию как в клиенте"""
    print("\n🖥️ ТЕСТ АУТЕНТИФИКАЦИИ КЛИЕНТА")
    print("=" * 50)
    
    url = "http://127.0.0.1:8001/api/token/"
    data = {
        'username': 'heist',
        'password': '1234567vampire'
    }
    
    print(f"🌐 URL: {url}")
    print(f"📦 Data: {json.dumps(data, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"📊 Status: {response.status}")
                response_text = await response.text()
                print(f"📄 Response: {response_text}")
                print(f"📋 Response Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    print("✅ КЛИЕНТСКИЙ ТЕСТ ПРОШЕЛ!")
                    return True
                else:
                    print("❌ КЛИЕНТСКИЙ ТЕСТ ПРОВАЛЕН!")
                    return False
    except Exception as e:
        print(f"💥 ОШИБКА: {e}")
        return False

def test_different_formats():
    """Тестирует различные форматы отправки данных"""
    print("\n🔄 ТЕСТ РАЗЛИЧНЫХ ФОРМАТОВ")
    print("=" * 50)
    
    url = "http://127.0.0.1:8001/api/token/"
    base_data = {
        'username': 'heist',
        'password': '1234567vampire'
    }
    
    test_cases = [
        {
            'name': 'JSON with Content-Type',
            'method': 'json',
            'headers': {'Content-Type': 'application/json'}
        },
        {
            'name': 'Form data',
            'method': 'data',
            'headers': {'Content-Type': 'application/x-www-form-urlencoded'}
        },
        {
            'name': 'Raw JSON string',
            'method': 'raw',
            'headers': {'Content-Type': 'application/json'}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Тестируем: {test_case['name']}")
        
        try:
            if test_case['method'] == 'json':
                response = requests.post(url, json=base_data, headers=test_case['headers'])
            elif test_case['method'] == 'data':
                response = requests.post(url, data=base_data, headers=test_case['headers'])
            elif test_case['method'] == 'raw':
                response = requests.post(url, data=json.dumps(base_data), headers=test_case['headers'])
            
            print(f"   📊 Status: {response.status_code}")
            print(f"   📄 Response: {response.text[:100]}...")
            
            if response.status_code == 200:
                print(f"   ✅ {test_case['name']} РАБОТАЕТ!")
                return test_case
                
        except Exception as e:
            print(f"   💥 Ошибка в {test_case['name']}: {e}")
    
    return None

def test_empty_credentials():
    """Тестирует что происходит с пустыми данными"""
    print("\n🕳️ ТЕСТ ПУСТЫХ ДАННЫХ")
    print("=" * 50)
    
    url = "http://127.0.0.1:8001/api/token/"
    
    test_cases = [
        {'username': '', 'password': ''},
        {'username': 'heist', 'password': ''},
        {'username': '', 'password': '1234567vampire'},
        {'username': None, 'password': None},
    ]
    
    for i, data in enumerate(test_cases):
        print(f"\n🧪 Тест {i+1}: {data}")
        try:
            response = requests.post(url, json=data, timeout=5)
            print(f"   📊 Status: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   💥 Ошибка: {e}")

async def main():
    print("🚀 КОМПЛЕКСНАЯ ДИАГНОСТИКА АУТЕНТИФИКАЦИИ")
    print("=" * 60)
    
    # Тест 1: Рабочая аутентификация
    working = test_working_auth()
    
    # Тест 2: Аутентификация клиента  
    client_working = await test_client_auth()
    
    # Тест 3: Различные форматы
    working_format = test_different_formats()
    
    # Тест 4: Пустые данные
    test_empty_credentials()
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
    print(f"   ✅ Рабочий тест: {'ДА' if working else 'НЕТ'}")
    print(f"   ✅ Клиентский тест: {'ДА' if client_working else 'НЕТ'}")
    print(f"   ✅ Найден рабочий формат: {working_format['name'] if working_format else 'НЕТ'}")
    
    if working and not client_working:
        print("\n⚠️ ПРОБЛЕМА: Тест работает, клиент НЕТ!")
        print("   Скорее всего проблема в формате отправки данных в aiohttp")
    elif not working and not client_working:
        print("\n💥 ПРОБЛЕМА: НИ ОДИН МЕТОД НЕ РАБОТАЕТ!")
        print("   Проверьте сервер и учетные данные")
    else:
        print("\n🎉 ВСЕ РАБОТАЕТ!")

if __name__ == "__main__":
    asyncio.run(main()) 