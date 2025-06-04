#!/usr/bin/env python3
"""
Скрипт для создания пользователя heist
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracker33.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

def create_heist_user():
    """Создает пользователя heist с токеном"""
    
    username = "heist"
    password = "1234567vampire"
    
    print(f"🔍 Проверяем пользователя {username}...")
    
    # Проверяем существует ли пользователь
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': 'Heist',
            'last_name': 'User',
            'email': 'heist@example.com',
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Пользователь {username} создан")
    else:
        print(f"ℹ️  Пользователь {username} уже существует")
    
    # Устанавливаем пароль
    user.set_password(password)
    user.save()
    print(f"✅ Пароль установлен")
    
    # Создаем или получаем токен
    token, created = Token.objects.get_or_create(user=user)
    
    if created:
        print(f"✅ Токен создан: {token.key}")
    else:
        print(f"ℹ️  Токен уже существует: {token.key}")
    
    print()
    print("📋 Данные для конфигурации клиента:")
    print(f"   username: {username}")
    print(f"   password: {password}")
    print(f"   token: {token.key}")
    print(f"   user_id: {user.id}")
    
    return token.key

if __name__ == "__main__":
    token = create_heist_user()
    print(f"\n🎉 Готово! Токен: {token}") 