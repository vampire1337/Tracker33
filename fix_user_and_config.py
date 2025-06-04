#!/usr/bin/env python3
"""
Скрипт для исправления всех проблем с пользователем и конфигурацией
"""
import os
import sys
import django
import configparser
from pathlib import Path

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracker33.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

def fix_everything():
    """Исправляет все проблемы разом"""
    
    print("🔧 ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ TRACKER33")
    print("=" * 50)
    
    # 1. Создаем/проверяем пользователя heist
    username = "heist"
    password = "1234567vampire"
    
    print(f"1️⃣ Работаем с пользователем {username}...")
    
    try:
        user = User.objects.get(username=username)
        print(f"   ✅ Пользователь {username} найден (ID: {user.id})")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name='Heist',
            last_name='User',
            email='heist@example.com'
        )
        print(f"   ✅ Пользователь {username} создан (ID: {user.id})")
    
    # Обновляем пароль на всякий случай
    user.set_password(password)
    user.save()
    print(f"   ✅ Пароль обновлен")
    
    # 2. Создаем/получаем токен
    print("2️⃣ Работаем с токеном...")
    token, created = Token.objects.get_or_create(user=user)
    
    if created:
        print(f"   ✅ Новый токен создан: {token.key}")
    else:
        print(f"   ✅ Токен найден: {token.key}")
    
    # 3. Исправляем конфигурацию клиента
    print("3️⃣ Исправляем конфигурацию клиента...")
    
    config_path = Path("desktop_app/config.ini")
    if config_path.exists():
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        # Приводим все URL к единому виду
        base_url = "http://127.0.0.1:8001"
        api_url = f"{base_url}/api"
        
        # Обновляем все секции
        sections_to_update = {
            'API': {
                'base_url': api_url,
                'token': token.key
            },
            'Server': {
                'base_url': base_url,
                'username': username,
                'password': password,
                'token': token.key
            },
            'Credentials': {
                'api_base_url': f"{api_url}/",
                'username': username,
                'auth_token': token.key,
                'user_id': str(user.id)
            }
        }
        
        for section_name, settings in sections_to_update.items():
            if not config.has_section(section_name):
                config.add_section(section_name)
            
            for key, value in settings.items():
                config.set(section_name, key, value)
        
        # Сохраняем конфигурацию
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        print(f"   ✅ Конфигурация обновлена: {config_path}")
        print(f"   ✅ Все URL приведены к единому виду: {base_url}")
        print(f"   ✅ Токен добавлен во все секции: {token.key[:10]}...")
    else:
        print(f"   ❌ Файл конфигурации не найден: {config_path}")
    
    # 4. Исправляем requirements.txt (PyQt6 -> PyQt5)
    print("4️⃣ Проверяем requirements.txt...")
    
    req_path = Path("requirements.txt")
    if req_path.exists():
        content = req_path.read_text(encoding='utf-8')
        if 'PyQt6' in content:
            content = content.replace('PyQt6==6.6.1', 'PyQt5==5.15.9')
            req_path.write_text(content, encoding='utf-8')
            print("   ✅ PyQt6 исправлен на PyQt5 в requirements.txt")
        else:
            print("   ✅ requirements.txt уже корректен")
    
    print()
    print("🎉 ВСЕ ИСПРАВЛЕНО!")
    print("=" * 50)
    print("📋 ИТОГОВАЯ КОНФИГУРАЦИЯ:")
    print(f"   Сервер: {base_url}")
    print(f"   API: {api_url}")
    print(f"   Пользователь: {username}")
    print(f"   Пароль: {password}")
    print(f"   Токен: {token.key}")
    print(f"   User ID: {user.id}")
    print()
    print("📝 ИНСТРУКЦИИ:")
    print("1. Запустите сервер: python manage.py runserver 127.0.0.1:8001")
    print("2. Запустите клиент: cd desktop_app && python main.py")
    print("3. В окне входа используйте: heist / 1234567vampire")
    
    return token.key

if __name__ == "__main__":
    try:
        fix_everything()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1) 