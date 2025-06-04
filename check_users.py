#!/usr/bin/env python3
"""
🔍 Проверка пользователей в базе данных
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracker33.settings')
django.setup()

from users.models import CustomUser
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

def check_all_users():
    """Проверяет всех пользователей в системе"""
    print("🔍 ПРОВЕРКА ВСЕХ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 50)
    
    users = CustomUser.objects.all()
    
    if not users:
        print("❌ ПОЛЬЗОВАТЕЛИ НЕ НАЙДЕНЫ!")
        return
    
    for user in users:
        print(f"\n👤 Пользователь: {user.username}")
        print(f"   📧 Email: {user.email}")
        print(f"   ✅ Активен: {user.is_active}")
        print(f"   🏢 Отдел: {user.department}")
        print(f"   💼 Должность: {user.position}")
        
        # Проверяем есть ли токен
        try:
            token = Token.objects.get(user=user)
            print(f"   🔑 Токен: {token.key[:20]}...")
        except Token.DoesNotExist:
            print("   ❌ Токен отсутствует")

def test_auth_with_different_passwords():
    """Тестирует аутентификацию с разными паролями"""
    print("\n🧪 ТЕСТИРОВАНИЕ АУТЕНТИФИКАЦИИ")
    print("=" * 50)
    
    usernames = ['heist', 'admin', 'test']
    passwords = ['1234567vampire', 'admin', 'password', '123456', 'heist']
    
    for username in usernames:
        for password in passwords:
            try:
                user = authenticate(username=username, password=password)
                if user:
                    print(f"✅ РАБОТАЕТ: {username} / {password}")
                    # Создаем токен если нет
                    token, created = Token.objects.get_or_create(user=user)
                    print(f"   🔑 Токен: {token.key}")
                    return username, password
                else:
                    print(f"❌ НЕ РАБОТАЕТ: {username} / {password}")
            except Exception as e:
                print(f"⚠️ ОШИБКА: {username} / {password} -> {e}")
    
    return None, None

def create_simple_user():
    """Создает простого пользователя для тестов"""
    print("\n🔧 СОЗДАНИЕ ПРОСТОГО ПОЛЬЗОВАТЕЛЯ")
    print("=" * 50)
    
    try:
        # Удаляем если существует
        try:
            old_user = CustomUser.objects.get(username='testuser')
            old_user.delete()
            print("🗑️ Удален старый пользователь")
        except CustomUser.DoesNotExist:
            pass
        
        # Создаем нового
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='123456',
            department='IT',
            position='Tester'
        )
        
        # Создаем токен
        token, created = Token.objects.get_or_create(user=user)
        
        print(f"✅ Создан пользователь: testuser")
        print(f"🔑 Пароль: 123456")  
        print(f"🎫 Токен: {token.key}")
        
        return 'testuser', '123456', token.key
        
    except Exception as e:
        print(f"❌ Ошибка создания: {e}")
        return None, None, None

def main():
    print("🚀 ДИАГНОСТИКА ПРОБЛЕМ АУТЕНТИФИКАЦИИ")
    print("=" * 60)
    
    # Проверяем всех пользователей
    check_all_users()
    
    # Тестируем аутентификацию
    working_user, working_pass = test_auth_with_different_passwords()
    
    if not working_user:
        print("\n⚠️ НИ ОДИН ПОЛЬЗОВАТЕЛЬ НЕ РАБОТАЕТ!")
        print("🔧 Создаю тестового пользователя...")
        
        username, password, token = create_simple_user()
        if username:
            print(f"\n🎉 ГОТОВО!")
            print(f"📋 Используйте в клиенте:")
            print(f"   👤 Логин: {username}")
            print(f"   🔑 Пароль: {password}")
    else:
        print(f"\n🎉 НАЙДЕНЫ РАБОЧИЕ ДАННЫЕ:")
        print(f"   👤 Логин: {working_user}")
        print(f"   🔑 Пароль: {working_pass}")

if __name__ == "__main__":
    main() 