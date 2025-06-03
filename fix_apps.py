import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracker33.settings')
django.setup()

from tracking.models import Application

print('=== ИСПРАВЛЯЕМ ПРОБЛЕМУ С ЦИФРОВЫМИ PROCESS_NAME ===')

# Находим все приложения с цифровыми process_name
apps_with_numeric_process = Application.objects.filter(process_name__regex=r'^\d+$')
print(f'Найдено приложений с цифровыми process_name: {apps_with_numeric_process.count()}')

for app in apps_with_numeric_process:
    print(f'ПРОБЛЕМА: ID={app.id}, Name="{app.name}", Process="{app.process_name}"')
    
    # Ищем оригинальное приложение с таким же именем но правильным process_name
    original_app = Application.objects.filter(
        name=app.name,
        user=app.user
    ).exclude(process_name__regex=r'^\d+$').first()
    
    if original_app:
        print(f'  Найдено оригинальное приложение: Process="{original_app.process_name}"')
        # Переносим все активности с неправильного приложения на правильное
        app.useractivity_set.update(application=original_app)
        # Удаляем неправильную запись
        app.delete()
        print(f'  Исправлено и удалено!')
    else:
        # Если нет оригинального, пытаемся восстановить название процесса
        # На основе названия приложения
        if app.name.endswith('.exe'):
            app.process_name = app.name
        else:
            app.process_name = app.name.lower().replace(' ', '') + '.exe'
        app.save()
        print(f'  Восстановлен process_name: "{app.process_name}"')

print('\n=== УДАЛЯЕМ ДУБЛИРУЮЩИЕСЯ ПРИЛОЖЕНИЯ ===')

# Находим и удаляем дублирующиеся приложения
seen_apps = {}
for app in Application.objects.all().order_by('id'):
    key = (app.user_id, app.name, app.process_name)
    if key in seen_apps:
        print(f'Дубликат найден: ID={app.id}, Name="{app.name}", Process="{app.process_name}"')
        # Переносим активности на первое приложение
        app.useractivity_set.update(application=seen_apps[key])
        app.delete()
        print(f'  Удален!')
    else:
        seen_apps[key] = app

print('\n=== УДАЛЯЕМ СИСТЕМНЫЕ ПРОЦЕССЫ ===')

# Удаляем явно системные процессы
system_processes = [
    'conhost.exe',
    'SearchHost.exe',
    'Unknown'
]

for process in system_processes:
    apps_to_delete = Application.objects.filter(process_name=process)
    if apps_to_delete.exists():
        print(f'Удаляю системный процесс: {process} ({apps_to_delete.count()} записей)')
        apps_to_delete.delete()

print('\n=== РЕЗУЛЬТАТ ===')
remaining_apps = Application.objects.all()
print(f'Осталось приложений: {remaining_apps.count()}')
for app in remaining_apps.order_by('name'):
    print(f'ID: {app.id}, Name: "{app.name}", Process: "{app.process_name}"')

print('\nИСПРАВЛЕНИЕ ЗАВЕРШЕНО!') 