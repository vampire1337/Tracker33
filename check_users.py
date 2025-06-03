import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracker33.settings')
django.setup()

from users.models import CustomUser
from django.contrib.auth import authenticate

print('=== ПРОВЕРЯЕМ ПОЛЬЗОВАТЕЛЕЙ ===')

users = CustomUser.objects.all()
for user in users:
    print(f'ID: {user.id}, Username: {user.username}, Email: {user.email}, Active: {user.is_active}')

print('\n=== ПРОВЕРЯЕМ АУТЕНТИФИКАЦИЮ ===')

# Проверяем пароли для пользователя heist
test_passwords = ['Tracker3301', 'tracker3301', 'heist', 'password', 'admin']

for password in test_passwords:
    user = authenticate(username='heist', password=password)
    if user:
        print(f'✅ Пароль "{password}" ПРАВИЛЬНЫЙ для пользователя heist!')
        break
    else:
        print(f'❌ Пароль "{password}" неправильный')

print('\n=== СБРОС ПАРОЛЯ ===')
try:
    user = CustomUser.objects.get(username='heist')
    user.set_password('Tracker3301')
    user.save()
    print('✅ Пароль для пользователя heist установлен как "Tracker3301"')
    
    # Проверяем новый пароль
    user = authenticate(username='heist', password='Tracker3301')
    if user:
        print('✅ Аутентификация с новым паролем работает!')
    else:
        print('❌ Аутентификация с новым паролем НЕ работает!')
        
except Exception as e:
    print(f'❌ Ошибка при сбросе пароля: {e}') 