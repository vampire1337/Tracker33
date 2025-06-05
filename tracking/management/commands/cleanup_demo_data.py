from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tracking.models import Application, UserActivity

User = get_user_model()

class Command(BaseCommand):
    help = 'Удаляет демонстрационные данные'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Имя пользователя для очистки данных'
        )

    def handle(self, *args, **options):
        username = options['user']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь "{username}" не найден')
            )
            return

        # Подсчитываем количество записей до удаления
        activities_count = UserActivity.objects.filter(user=user).count()
        apps_count = Application.objects.filter(user=user).count()

        # Удаляем данные
        UserActivity.objects.filter(user=user).delete()
        Application.objects.filter(user=user).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Удалено для пользователя "{username}": '
                f'{activities_count} активностей, {apps_count} приложений'
            )
        ) 