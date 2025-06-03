import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracker33.settings')
django.setup()

from tracking.models import UserActivity, Application
from users.models import CustomUser

print('=== ПРОВЕРЯЕМ АКТИВНОСТИ ПОЛЬЗОВАТЕЛЕЙ ===')

# Проверяем пользователей
users = CustomUser.objects.all()
print(f'Всего пользователей: {users.count()}')
for user in users:
    print(f'User ID: {user.id}, Username: {user.username}, Email: {user.email}')

print('\n=== ПРОВЕРЯЕМ АКТИВНОСТИ ===')

# Проверяем активности
activities = UserActivity.objects.all()
print(f'Всего активностей: {activities.count()}')

# Группируем по пользователям
for user in users:
    user_activities = UserActivity.objects.filter(user=user)
    print(f'\nПользователь {user.username} (ID: {user.id}):')
    print(f'  Всего активностей: {user_activities.count()}')
    
    if user_activities.exists():
        # Показываем последние 5 активностей
        recent_activities = user_activities.order_by('-start_time')[:5]
        for activity in recent_activities:
            print(f'  - {activity.application.name}: {activity.duration} ({activity.start_time})')
    
    # Проверяем сегодняшние активности
    from django.utils import timezone
    from datetime import datetime, time
    
    today = timezone.now().date()
    today_activities = user_activities.filter(start_time__date=today)
    print(f'  Сегодняшних активностей: {today_activities.count()}')

print('\n=== ПРОВЕРЯЕМ API ENDPOINTS ===')

# Проверяем настройки URL
try:
    from Tracker33.urls import urlpatterns
    print('URL patterns найдены')
    for pattern in urlpatterns:
        print(f'  - {pattern.pattern}')
except Exception as e:
    print(f'Ошибка с URL: {e}')

print('\nПРОВЕРКА ЗАВЕРШЕНА!') 