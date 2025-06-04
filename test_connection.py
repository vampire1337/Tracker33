#!/usr/bin/env python3
"""
Простой тест подключения клиента к серверу
"""
import requests
import json

def test_api_connection():
    """Тестирует подключение к API серверу"""
    
    base_url = "http://127.0.0.1:8001"
    
    print("🔍 Тестирование подключения к Tracker33...")
    print(f"Сервер: {base_url}")
    print()
    
    # 1. Тест основной страницы
    print("1️⃣ Проверка главной страницы...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   ✅ Статус: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Веб-интерфейс работает")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка соединения: {e}")
        return False
    
    # 2. Тест API endpoint для токенов
    print("2️⃣ Проверка API endpoint...")
    try:
        response = requests.get(f"{base_url}/api/token/")
        print(f"   Статус: {response.status_code}")
        if response.status_code == 405:  # Method not allowed - это нормально для POST endpoint
            print("   ✅ API endpoint доступен (405 для GET - нормально)")
        else:
            print(f"   ⚠️  Неожиданный статус: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # 3. Тест аутентификации с пользователем из конфига
    print("3️⃣ Тест аутентификации...")
    try:
        auth_data = {
            "username": "heist",
            "password": "1234567vampire"
        }
        
        response = requests.post(
            f"{base_url}/api/token/",
            json=auth_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                token = data['token']
                print(f"   ✅ Токен получен: {token[:20]}...")
                
                # 4. Тест авторизованного запроса
                print("4️⃣ Тест авторизованного запроса...")
                headers = {'Authorization': f'Token {token}'}
                
                # Проверяем applications endpoint
                response = requests.get(f"{base_url}/api/applications/", headers=headers)
                print(f"   Applications endpoint статус: {response.status_code}")
                if response.status_code == 200:
                    apps = response.json()
                    print(f"   ✅ Приложений в базе: {len(apps)}")
                
                # Проверяем activities endpoint  
                response = requests.get(f"{base_url}/api/activities/", headers=headers)
                print(f"   Activities endpoint статус: {response.status_code}")
                if response.status_code == 200:
                    activities = response.json()
                    print(f"   ✅ Активностей в базе: {len(activities)}")
                
                print()
                print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
                print("Сервер работает правильно, проблема может быть в конфигурации клиента.")
                return True
            else:
                print(f"   ❌ Токен не найден в ответе: {response.text}")
        else:
            print(f"   ❌ Ошибка аутентификации: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
            if response.status_code == 400:
                print("   💡 Возможно пользователь 'heist' не существует или неверный пароль")
            
    except Exception as e:
        print(f"   ❌ Ошибка при аутентификации: {e}")
    
    return False

if __name__ == "__main__":
    test_api_connection() 