import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracker33.settings')
django.setup()

from tracking.models import Application

# Проверяем все приложения в базе
apps = Application.objects.all()
print('=== ВСЕ ПРИЛОЖЕНИЯ В БАЗЕ ===')
for app in apps:
    print(f'ID: {app.id}, Name: "{app.name}", Process: "{app.process_name}"')

print(f'\nВсего приложений: {apps.count()}')

# Проверяем приложения с цифровыми именами
numeric_apps = apps.filter(name__regex=r'^\d+$')
print(f'\nПриложения с цифровыми именами: {numeric_apps.count()}')
for app in numeric_apps:
    print(f'ПРОБЛЕМА - ID: {app.id}, Name: "{app.name}", Process: "{app.process_name}"')

# Удаляем приложения с цифровыми именами
if numeric_apps.count() > 0:
    print(f'\nУдаляю {numeric_apps.count()} проблемных приложений...')
    numeric_apps.delete()
    print('Удаление завершено!')
else:
    print('\nПроблемных приложений не найдено.') 