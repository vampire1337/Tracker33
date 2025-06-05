from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta, time
import random
from tracking.models import Application, UserActivity

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает демонстрационные данные для тестирования интерфейса'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Имя пользователя для создания данных'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Количество дней для генерации данных'
        )

    def handle(self, *args, **options):
        username = options['user']
        days_count = options['days']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь "{username}" не найден')
            )
            return

        # Удаляем старые демо-данные
        UserActivity.objects.filter(user=user).delete()
        Application.objects.filter(user=user).delete()

        # Создаем приложения
        apps_data = [
            {'name': 'Visual Studio Code', 'process_name': 'Code.exe', 'is_productive': True},
            {'name': 'Google Chrome', 'process_name': 'chrome.exe', 'is_productive': False},
            {'name': 'PyCharm', 'process_name': 'pycharm64.exe', 'is_productive': True},
            {'name': 'Telegram', 'process_name': 'Telegram.exe', 'is_productive': False},
            {'name': 'Word', 'process_name': 'WINWORD.EXE', 'is_productive': True},
            {'name': 'Firefox', 'process_name': 'firefox.exe', 'is_productive': False},
            {'name': 'Notepad++', 'process_name': 'notepad++.exe', 'is_productive': True},
            {'name': 'Steam', 'process_name': 'steam.exe', 'is_productive': False},
            {'name': 'Terminal', 'process_name': 'WindowsTerminal.exe', 'is_productive': True},
            {'name': 'Discord', 'process_name': 'Discord.exe', 'is_productive': False},
        ]

        apps = []
        for app_data in apps_data:
            app = Application.objects.create(
                user=user,
                name=app_data['name'],
                process_name=app_data['process_name'],
                is_productive=app_data['is_productive'],
                is_active=True
            )
            apps.append(app)

        self.stdout.write(f'Создано {len(apps)} приложений')

        # Генерируем активности за последние дни
        total_activities = 0
        today = timezone.now().date()
        
        for day_offset in range(days_count):
            current_date = today - timedelta(days=day_offset)
            
            # Генерируем активности для рабочего дня (9:00 - 18:00)
            work_hours = list(range(9, 18))
            # Добавляем немного активности в вечернее время
            evening_hours = list(range(19, 22))
            all_hours = work_hours + evening_hours
            
            day_activities = 0
            for hour in all_hours:
                # Вероятность активности в этот час
                if hour in work_hours:
                    activity_probability = 0.8  # 80% шанс активности в рабочие часы
                    session_count = random.randint(2, 5)  # 2-5 сессий в час
                else:
                    activity_probability = 0.4  # 40% шанс активности вечером
                    session_count = random.randint(1, 3)  # 1-3 сессии в час
                
                if random.random() < activity_probability:
                    for _ in range(session_count):
                        # Выбираем случайное приложение
                        if hour in work_hours:
                            # В рабочие часы больше продуктивных приложений
                            productive_apps = [app for app in apps if app.is_productive]
                            non_productive_apps = [app for app in apps if not app.is_productive]
                            if random.random() < 0.7:  # 70% продуктивных приложений
                                app = random.choice(productive_apps)
                            else:
                                app = random.choice(non_productive_apps)
                        else:
                            # Вечером больше развлечений
                            app = random.choice(apps)
                        
                        # Генерируем время начала сессии
                        start_minute = random.randint(0, 50)
                        start_time = timezone.make_aware(
                            datetime.combine(current_date, time(hour, start_minute))
                        )
                        
                        # Генерируем длительность (5-45 минут)
                        duration_minutes = random.randint(5, 45)
                        end_time = start_time + timedelta(minutes=duration_minutes)
                        
                        # Генерируем активность клавиатуры
                        keyboard_presses = random.randint(
                            50 if app.is_productive else 10,
                            500 if app.is_productive else 100
                        )
                        
                        # Создаем активность
                        UserActivity.objects.create(
                            user=user,
                            application=app,
                            start_time=start_time,
                            end_time=end_time,
                            duration=end_time - start_time,
                            keyboard_presses=keyboard_presses
                        )
                        
                        day_activities += 1
                        total_activities += 1
            
            self.stdout.write(f'День {current_date}: {day_activities} активностей')

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно создано {total_activities} активностей за {days_count} дней для пользователя "{username}"'
            )
        )
        
        # Выводим статистику
        productive_time = UserActivity.objects.filter(
            user=user,
            application__is_productive=True
        ).aggregate(
            total=timezone.now().replace(hour=0, minute=0, second=0) - timezone.now().replace(hour=0, minute=0, second=0)
        )
        
        self.stdout.write('Демонстрационные данные готовы для тестирования интерфейса!')
        self.stdout.write('Запустите сервер и проверьте дашборд и статистику.') 