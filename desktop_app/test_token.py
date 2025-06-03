import requests
import configparser
import os

# Загрузка токена из конфигурации
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

token = None
if config.has_section('Credentials') and config.has_option('Credentials', 'auth_token'):
    token = config.get('Credentials', 'auth_token').strip()

print(f"Токен из конфигурации: {token}")

# Тест запроса к API
if token:
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"Заголовки: {headers}")
    
    try:
        response = requests.get('http://127.0.0.1:8001/api/applications/', headers=headers)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}")
    except Exception as e:
        print(f"Ошибка: {e}")
else:
    print("Токен не найден в конфигурации") 