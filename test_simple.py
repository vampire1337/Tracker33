import requests

print("Тестирую подключение...")

try:
    # Тест веб интерфейса
    response = requests.get("http://127.0.0.1:8001/")
    print(f"Веб интерфейс: {response.status_code}")
    
    # Тест API endpoint
    response = requests.get("http://127.0.0.1:8001/api/token/")
    print(f"API token endpoint: {response.status_code}")
    
    # Тест аутентификации
    auth_data = {"username": "heist", "password": "1234567vampire"}
    response = requests.post("http://127.0.0.1:8001/api/token/", json=auth_data)
    print(f"Аутентификация: {response.status_code}")
    print(f"Ответ: {response.text}")
    
except Exception as e:
    print(f"Ошибка: {e}") 