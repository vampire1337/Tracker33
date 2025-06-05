#!/usr/bin/env python3
import requests
import json

def test_missing_application():
    """Тест API с несуществующим ID приложения"""
    url = 'http://localhost:8001/api/activities/'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token 10195f06a8214b020aed20fdfdbf330446ddf317'
    }
    
    # Тестируем с несуществующим ID приложения 16
    data = {
        'application': 16,
        'start_time': '2024-01-01T10:00:00Z',
        'end_time': '2024-01-01T10:05:00Z',
        'keyboard_presses': 50
    }
    
    print("=== ТЕСТ API С НЕСУЩЕСТВУЮЩИМ ПРИЛОЖЕНИЕМ ===")
    print(f"URL: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("❌ ПОЛУЧЕНА ОШИБКА 400 - наши исправления НЕ РАБОТАЮТ!")
            if "Недопустимый первичный ключ" in response.text:
                print("🔥 КРИТИЧНО: Все еще получаем ошибку с несуществующим приложением!")
        elif response.status_code in [200, 201]:
            print("✅ Запрос обработан успешно - наши исправления РАБОТАЮТ!")
            print("🎉 Приложение создано автоматически для несуществующего ID!")
        else:
            print(f"⚠️ Неожиданный статус: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ОШИБКА СОЕДИНЕНИЯ: {e}")
        print("Сервер может быть недоступен!")

def test_another_missing_application():
    """Тест API с другим несуществующим ID приложения"""
    url = 'http://localhost:8001/api/activities/'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token 10195f06a8214b020aed20fdfdbf330446ddf317'
    }
    
    # Тестируем с несуществующим ID приложения 999
    data = {
        'application': 999,
        'start_time': '2024-01-01T11:00:00Z',
        'end_time': '2024-01-01T11:05:00Z',
        'keyboard_presses': 75
    }
    
    print("\n=== ТЕСТ API С ДРУГИМ НЕСУЩЕСТВУЮЩИМ ПРИЛОЖЕНИЕМ ===")
    print(f"URL: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            print("❌ ПОЛУЧЕНА ОШИБКА 400 - наши исправления НЕ РАБОТАЮТ!")
        elif response.status_code == 201:
            print("✅ Запрос обработан успешно - наши исправления РАБОТАЮТ!")
            print("🎉 Новое приложение создано автоматически!")
        else:
            print(f"⚠️ Неожиданный статус код: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении запроса: {e}")

if __name__ == '__main__':
    test_missing_application()
    test_another_missing_application() 