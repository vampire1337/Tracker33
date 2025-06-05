#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracker33.settings')
django.setup()

from tracking.models import Application
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='admin')
apps = Application.objects.filter(user=user)

print('=== СУЩЕСТВУЮЩИЕ ПРИЛОЖЕНИЯ ===')
for app in apps:
    print(f'ID: {app.id}, Name: {app.name}, Process: {app.process_name}')

print(f'\nВсего приложений: {apps.count()}')

# Проверяем конкретно unknown_app_16
unknown_app = Application.objects.filter(user=user, process_name='unknown_app_16').first()
if unknown_app:
    print(f'\nПриложение unknown_app_16 уже существует: ID {unknown_app.id}')
else:
    print('\nПриложение unknown_app_16 НЕ существует') 