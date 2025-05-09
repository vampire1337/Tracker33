from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta, datetime, time
from .models import Application, UserActivity, KeyboardActivity, TimeLog
from .serializers import (
    ApplicationSerializer, 
    UserActivitySerializer, 
    KeyboardActivitySerializer,
    TimeLogSerializer
)
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.decorators import action
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count, ExpressionWrapper, F, DurationField
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.db import models
from django.utils.decorators import method_decorator
from django.conf import settings
from .exceptions import (
    ApplicationAlreadyExists,
    InvalidTimeRange,
    ApplicationNotFound,
    UserActivityNotFound,
    InvalidActivityData
)
from rest_framework.exceptions import ValidationError

# Create your views here.

class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'statistics.html'
    
    # Словарь для отображения понятных названий приложений
    app_name_mapping = {
        'browser.exe': 'Yandex Браузер',
        'chrome.exe': 'Google Chrome',
        'firefox.exe': 'Mozilla Firefox',
        'msedge.exe': 'Microsoft Edge',
        'opera.exe': 'Opera',
        'safari.exe': 'Safari',
        'brave.exe': 'Brave Browser',
        'vivaldi.exe': 'Vivaldi',
        'iexplore.exe': 'Internet Explorer',
        'word.exe': 'Microsoft Word',
        'excel.exe': 'Microsoft Excel',
        'powerpnt.exe': 'Microsoft PowerPoint',
        'outlook.exe': 'Microsoft Outlook',
        'winword.exe': 'Microsoft Word',
        'notepad.exe': 'Notepad',
        'notepad++.exe': 'Notepad++',
        'code.exe': 'Visual Studio Code',
        'devenv.exe': 'Visual Studio',
        'pycharm64.exe': 'PyCharm',
        'idea64.exe': 'IntelliJ IDEA',
        'photoshop.exe': 'Adobe Photoshop',
        'illustrator.exe': 'Adobe Illustrator',
        'acrobat.exe': 'Adobe Acrobat',
        'acrord32.exe': 'Adobe Reader',
        'slack.exe': 'Slack',
        'teams.exe': 'Microsoft Teams',
        'discord.exe': 'Discord',
        'telegram.exe': 'Telegram',
        'whatsapp.exe': 'WhatsApp',
        'skype.exe': 'Skype',
        'zoom.exe': 'Zoom',
        'steam.exe': 'Steam',
        'spotify.exe': 'Spotify',
        'vlc.exe': 'VLC Media Player',
        'wmplayer.exe': 'Windows Media Player',
        'explorer.exe': 'Windows Explorer',
        'cmd.exe': 'Командная строка',
        'powershell.exe': 'PowerShell',
        'python.exe': 'Python',
        'javaw.exe': 'Java',
        'node.exe': 'Node.js'
    }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Добавляем timestamp для предотвращения кэширования
        context['timestamp'] = timezone.now().timestamp()
        
        # Получаем количество дней для статистики из параметров запроса
        days = int(self.request.GET.get('days', 7))
        today = timezone.now().date()
        start_date = today - timedelta(days=days-1)  # -1 потому что сегодня тоже входит
        
        # Получаем статистику за выбранный период - принудительно обновляем
        activities = UserActivity.objects.filter(
            user=user,
            start_time__date__gte=start_date,
            start_time__date__lte=today
        )
        
        # Рассчитываем общее время работы
        total_seconds = 0
        keyboard_activity = 0
        
        for activity in activities:
            if activity.duration:
                total_seconds += activity.duration.total_seconds()
            elif activity.start_time and activity.end_time:
                duration = activity.end_time - activity.start_time
                total_seconds += duration.total_seconds()
            
            # Суммируем нажатия клавиш
            keyboard_activity += activity.keyboard_presses or 0
        
        # Форматируем время в строку для отображения
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Рассчитываем средние показатели на день
        avg_seconds_per_day = total_seconds / days if days > 0 else 0
        avg_hours, avg_remainder = divmod(int(avg_seconds_per_day), 3600)
        avg_minutes, avg_seconds = divmod(avg_remainder, 60)
        average_daily_time = f"{avg_hours}:{avg_minutes:02d}:{avg_seconds:02d}"
        
        average_daily_keystrokes = int(keyboard_activity / days) if days > 0 else 0
        
        # Получаем все приложения пользователя за период - без кэширования
        apps = Application.objects.filter(
            useractivity__user=user,
            useractivity__start_time__date__gte=start_date,
            useractivity__start_time__date__lte=today
        ).annotate(
            total_time=Sum('useractivity__duration'),
            total_seconds=Sum(ExpressionWrapper(
                F('useractivity__duration'), 
                output_field=models.IntegerField()
            ))
        ).order_by('-total_time').distinct()
        
        # Форматируем время для каждого приложения и рассчитываем проценты
        # Общее количество секунд для всех приложений
        all_apps_seconds = sum(app.total_seconds for app in apps if getattr(app, 'total_seconds', None))
        
        # Получаем предыдущие данные для сравнения и расчета тренда
        prev_start_date = start_date - timedelta(days=days)
        prev_end_date = start_date - timedelta(days=1)
        
        previous_apps = Application.objects.filter(
            useractivity__user=user,
            useractivity__start_time__date__gte=prev_start_date,
            useractivity__start_time__date__lte=prev_end_date
        ).annotate(
            total_time=Sum('useractivity__duration'),
            total_seconds=Sum(ExpressionWrapper(
                F('useractivity__duration'), 
                output_field=models.IntegerField()
            ))
        )
        
        # Создаем словарь предыдущих данных для быстрого поиска
        prev_app_data = {}
        for app in previous_apps:
            if getattr(app, 'total_seconds', None):
                prev_app_data[app.id] = app.total_seconds
        
        for app in apps:
            if hasattr(app, 'total_seconds') and app.total_seconds:
                # Преобразуем время в секунды, разделив на 1000000 если значение слишком большое
                seconds_value = app.total_seconds
                if seconds_value > 100000:  # Если значение слишком большое, вероятно это микросекунды
                    seconds_value = seconds_value / 1000000
                
                hours, remainder = divmod(int(seconds_value), 3600)
                minutes, seconds = divmod(remainder, 60)
                app.formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
                
                # Рассчитываем процент от общего времени
                app.percentage = round((app.total_seconds / all_apps_seconds) * 100, 1) if all_apps_seconds > 0 else 0
                
                # Рассчитываем тренд по сравнению с предыдущим периодом
                prev_seconds = prev_app_data.get(app.id, 0)
                if prev_seconds > 0:
                    app.trend = round(((app.total_seconds - prev_seconds) / prev_seconds) * 100, 1)
                    # Определяем класс стиля для тренда
                    if app.trend > 0:
                        app.trend_class = 'bg-success'
                    elif app.trend < 0:
                        app.trend_class = 'bg-danger'
                    else:
                        app.trend_class = 'bg-secondary'
                else:
                    app.trend = 100  # Если раньше не было активности, то тренд 100%
                    app.trend_class = 'bg-success'
            else:
                app.formatted_time = "00:00:00"
                app.percentage = 0
                app.trend = 0
                app.trend_class = 'bg-secondary'
        
        # Обновляем названия приложений для отображения
        for app in apps:
            process_name = app.process_name.lower() if app.process_name else ""
            if process_name in self.app_name_mapping:
                app.name = self.app_name_mapping[process_name]
                app.save()
        
        # Получаем данные по дням для графика - принудительно обновляем
        daily_data = []
        for i in range(days):
            date = today - timedelta(days=days-1-i)
            day_activities = activities.filter(start_time__date=date)
            
            day_seconds = 0
            for activity in day_activities:
                if activity.duration:
                    day_seconds += activity.duration.total_seconds()
                elif activity.start_time and activity.end_time:
                    duration = activity.end_time - activity.start_time
                    day_seconds += duration.total_seconds()
            
            daily_data.append({
                'date': date,
                'hours': round(day_seconds / 3600, 1),
                'minutes': round(day_seconds / 60, 0)
            })
        
        # Проверка и создание демо-данных, если нет реальных
        if not daily_data:
            for i in range(days):
                date = today - timedelta(days=days-1-i)
                daily_data.append({
                    'date': date,
                    'hours': 0,
                    'minutes': 0
                })
        
        # Убедимся, что у нас есть хотя бы одно приложение для пирожка
        if not apps.exists():
            # Создаем фиктивное приложение
            dummy_app = Application()
            dummy_app.name = "Нет данных"
            dummy_app.percentage = 100
            dummy_app.formatted_time = "00:00:00"
            dummy_app.trend = 0
            dummy_app.trend_class = 'bg-secondary'
            apps = [dummy_app]
        
        # Рассчитываем продуктивность
        productive_apps = [app for app in apps if getattr(app, 'is_productive', False)]
        productive_seconds = sum(app.total_seconds for app in productive_apps if getattr(app, 'total_seconds', None))
        productivity_percent = round((productive_seconds / all_apps_seconds) * 100) if all_apps_seconds > 0 else 0
        
        # Добавляем данные в контекст
        context['apps'] = apps
        context['formatted_time'] = formatted_time
        context['keyboard_activity'] = keyboard_activity
        context['today_activity'] = activities.select_related('application').order_by('-start_time')[:10]
        context['daily_data'] = daily_data
        context['average_daily_time'] = average_daily_time
        context['average_daily_keystrokes'] = average_daily_keystrokes
        context['productivity_percent'] = productivity_percent
        
        print(f"[DEBUG] Statistics Timestamp: {context['timestamp']}, Time: {formatted_time}, Keystrokes: {keyboard_activity}")
        
        return context

class LandingView(TemplateView):
    template_name = 'landing.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Полностью отключаем кэширование для получения актуальных данных
        # cache_key = f'application_list_{self.request.user.id}'
        # queryset = cache.get(cache_key)
        # if queryset is None:
        queryset = Application.objects.filter(useractivity__user=self.request.user).distinct()
        # cache.set(cache_key, queryset, settings.CACHE_TTL)
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            raise ApplicationAlreadyExists(detail=str(e))

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Application.DoesNotExist:
            raise ApplicationNotFound()

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Application.DoesNotExist:
            raise ApplicationNotFound()

class UserActivityViewSet(viewsets.ModelViewSet):
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user).order_by('-start_time')

    def perform_create(self, serializer):
        try:
            # Получаем данные запроса
            request_data = self.request.data
            app_name = request_data.get('app_name', '')
            process_name = request_data.get('application', '')  # Могло быть передано как ID или как имя процесса
            keyboard_presses = request_data.get('keyboard_presses', 0)
            
            # Логируем полученные данные для отладки
            print(f"Получены данные: app_name={app_name}, process_name={process_name}, keyboard_presses={keyboard_presses}")
            
            # Пытаемся получить существующее приложение
            application = None
            
            # Проверяем, является ли process_name числом или строкой с числом
            is_numeric = False
            try:
                # Если process_name уже число или строка с числом
                if isinstance(process_name, int) or (isinstance(process_name, str) and process_name.isdigit()):
                    is_numeric = True
                    process_id = int(process_name)
                    try:
                        application = Application.objects.get(id=process_id, user=self.request.user)
                    except Application.DoesNotExist:
                        pass
            except (TypeError, ValueError, AttributeError):
                pass
            
            # Если приложение не найдено по ID, ищем по имени процесса
            if not application:
                try:
                    # Если process_name не число, используем его как есть
                    process_name_str = str(process_name) if process_name is not None else ""
                    application = Application.objects.get(process_name=process_name_str, user=self.request.user)
                except Application.DoesNotExist:
                    # Создаем новое приложение
                    application = Application.objects.create(
                        name=app_name or str(process_name),
                        process_name=str(process_name) if process_name is not None else "",
                        user=self.request.user
                    )
            
            # Сохраняем активность с правильным объектом приложения и всеми данными
            serializer.save(
                user=self.request.user,
                application=application,
                keyboard_presses=keyboard_presses
            )
        except Exception as e:
            print(f"Ошибка при создании активности: {e}")
            raise ValidationError(detail=str(e))

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except UserActivity.DoesNotExist:
            raise UserActivityNotFound()

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except UserActivity.DoesNotExist:
            raise UserActivityNotFound()

class KeyboardActivityViewSet(viewsets.ModelViewSet):
    queryset = KeyboardActivity.objects.all()
    serializer_class = KeyboardActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return KeyboardActivity.objects.filter(user=self.request.user).order_by('-timestamp')
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    
    # Сопоставление известных процессов с их реальными названиями
    app_name_mapping = {
        'browser.exe': 'Yandex Браузер',
        'chrome.exe': 'Google Chrome',
        'firefox.exe': 'Mozilla Firefox',
        'msedge.exe': 'Microsoft Edge',
        'opera.exe': 'Opera',
        'safari.exe': 'Safari',
        'brave.exe': 'Brave Browser',
        'vivaldi.exe': 'Vivaldi',
        'iexplore.exe': 'Internet Explorer',
        'word.exe': 'Microsoft Word',
        'excel.exe': 'Microsoft Excel',
        'powerpnt.exe': 'Microsoft PowerPoint',
        'outlook.exe': 'Microsoft Outlook',
        'winword.exe': 'Microsoft Word',
        'notepad.exe': 'Notepad',
        'notepad++.exe': 'Notepad++',
        'code.exe': 'Visual Studio Code',
        'devenv.exe': 'Visual Studio',
        'pycharm64.exe': 'PyCharm',
        'idea64.exe': 'IntelliJ IDEA',
        'photoshop.exe': 'Adobe Photoshop',
        'illustrator.exe': 'Adobe Illustrator',
        'acrobat.exe': 'Adobe Acrobat',
        'acrord32.exe': 'Adobe Reader',
        'slack.exe': 'Slack',
        'teams.exe': 'Microsoft Teams',
        'discord.exe': 'Discord',
        'telegram.exe': 'Telegram',
        'whatsapp.exe': 'WhatsApp',
        'skype.exe': 'Skype',
        'zoom.exe': 'Zoom',
        'steam.exe': 'Steam',
        'spotify.exe': 'Spotify',
        'vlc.exe': 'VLC Media Player',
        'wmplayer.exe': 'Windows Media Player',
        'explorer.exe': 'Windows Explorer',
        'cmd.exe': 'Командная строка',
        'powershell.exe': 'PowerShell',
        'python.exe': 'Python',
        'javaw.exe': 'Java',
        'node.exe': 'Node.js'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        # Добавляем timestamp для предотвращения кэширования
        context['timestamp'] = timezone.now().timestamp()

        # Всегда загружаем свежие данные
        # Добавляем также последние активности для отображения в таблице "Последние действия"
        context['today_activity'] = UserActivity.objects.filter(
            user=user,
            start_time__date=today
        ).select_related('application').order_by('-start_time')[:10]  # Ограничиваем до 10 последних записей
        
        # Получаем активные приложения
        active_apps = Application.objects.filter(
            useractivity__user=user,
            useractivity__start_time__date=today
        ).distinct()
        
        # Обновляем названия активных приложений
        for app in active_apps:
            process_name = app.process_name.lower() if app.process_name else ""
            if process_name in self.app_name_mapping:
                app.name = self.app_name_mapping[process_name]
                app.save()

        # Получаем статистику за сегодня
        # Добавляем общее время работы за сегодня
        # Используем прямой SQL-запрос для более точного расчета
        from django.db import connection
        from django.db.models import Sum
        
        # Используем объекты Django вместо прямого SQL для совместимости с SQLite
        # Исправляем расчет времени работы, чтобы оно корректно отображалось
        activities = UserActivity.objects.filter(
            user=user,
            start_time__date=today
        )
        
        # Рассчитываем общее время работы на основе всех активностей
        total_seconds = 0
        for activity in activities:
            if activity.duration:
                total_seconds += activity.duration.total_seconds()
            elif activity.start_time and activity.end_time:
                duration = activity.end_time - activity.start_time
                total_seconds += duration.total_seconds()
        
        # Создаем объект timedelta для отображения
        total_work_time = timedelta(seconds=int(total_seconds))
        
        # Форматируем время в строку для отображения
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Получаем все приложения пользователя за сегодня
        apps = Application.objects.filter(
            useractivity__user=user,
            useractivity__start_time__date=today
        ).annotate(
            total_time=Sum('useractivity__duration'),
            # Добавляем поле для отформатированного времени
            total_seconds=Sum(ExpressionWrapper(
                F('useractivity__duration'), 
                output_field=models.IntegerField()
            ))
        ).order_by('-total_time')
        
        # Рассчитываем проценты для приложений
        all_apps_seconds = sum(app.total_seconds for app in apps if getattr(app, 'total_seconds', None))
        
        # Форматируем время для каждого приложения и добавляем проценты
        for app in apps:
            if hasattr(app, 'total_seconds') and app.total_seconds:
                # Преобразуем время в секунды, разделив на 1000000 если значение слишком большое
                seconds_value = app.total_seconds
                if seconds_value > 100000:  # Если значение слишком большое, вероятно это микросекунды
                    seconds_value = seconds_value / 1000000
                
                hours, remainder = divmod(int(seconds_value), 3600)
                minutes, seconds = divmod(remainder, 60)
                app.formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
                
                # Добавляем процент от общего времени
                app.percentage = round((app.total_seconds / all_apps_seconds) * 100, 1) if all_apps_seconds > 0 else 0
            else:
                app.formatted_time = "00:00:00"
                app.percentage = 0
        
        # Обновляем названия приложений для отображения
        for app in apps:
            process_name = app.process_name.lower() if app.process_name else ""
            if process_name in self.app_name_mapping:
                # Обновляем название приложения в базе данных
                app.name = self.app_name_mapping[process_name]
                app.save()
        
        # Создаем почасовую статистику для графика
        hourly_activity = []
        for hour in range(24):
            start_hour = timezone.make_aware(datetime.combine(today, time(hour=hour, minute=0)))
            end_hour = timezone.make_aware(datetime.combine(today, time(hour=hour + 1 if hour < 23 else 23, minute=59, second=59)))
            
            # Получаем активности только за этот час
            hour_activities = activities.filter(
                start_time__gte=start_hour,
                start_time__lt=end_hour
            )
            
            # Рассчитываем общее время активности за час
            hour_seconds = 0
            for activity in hour_activities:
                if activity.duration:
                    hour_seconds += activity.duration.total_seconds()
                elif activity.start_time and activity.end_time:
                    duration = activity.end_time - activity.start_time
                    hour_seconds += duration.total_seconds()
            
            # Переводим секунды в минуты
            hour_minutes = round(hour_seconds / 60, 0)
            
            hourly_activity.append({
                'hour': hour,
                'minutes': hour_minutes,
                'seconds': hour_seconds
            })
        
        today_stats = {
            'total_work_time': total_work_time,
            'formatted_time': formatted_time,
            'apps': apps,
            
            # Получаем количество нажатий клавиш из модели UserActivity с использованием SQL
            'keystrokes': UserActivity.objects.filter(
                user=user,
                start_time__date=today
            ).aggregate(total_keystrokes=Sum('keyboard_presses'))['total_keystrokes'] or 0,
        }

        # Готовим данные напрямую без кэширования
        context.update({
            'active_apps': active_apps,
            'today_stats': today_stats,
            'today_activity': context['today_activity'],
            'hourly_activity': hourly_activity
        })
        
        print(f"[DEBUG] Timestamp: {context['timestamp']}, Time: {formatted_time}, Keystrokes: {today_stats['keystrokes']}")
        
        return context

class LogsView(LoginRequiredMixin, ListView):
    template_name = 'logs.html'
    model = UserActivity
    context_object_name = 'activities'
    paginate_by = 20

    def get_queryset(self):
        queryset = UserActivity.objects.filter(user=self.request.user)
        
        # Фильтрация по дате от
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(start_time__date__gte=date_from)
        
        # Фильтрация по дате до
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(start_time__date__lte=date_to)
        
        # Фильтрация по приложению
        application_id = self.request.GET.get('application')
        if application_id:
            queryset = queryset.filter(application_id=application_id)
        
        return queryset.select_related('application').order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем клавиатурную активность
        keyboard_queryset = KeyboardActivity.objects.filter(user=self.request.user)
        
        # Применяем те же фильтры, что и для активности
        date_from = self.request.GET.get('date_from')
        if date_from:
            keyboard_queryset = keyboard_queryset.filter(timestamp__date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            keyboard_queryset = keyboard_queryset.filter(timestamp__date__lte=date_to)
        
        application_id = self.request.GET.get('application')
        if application_id:
            keyboard_queryset = keyboard_queryset.filter(application_id=application_id)
        
        context['keyboard_activities'] = keyboard_queryset.select_related('application').order_by('-timestamp')[:20]
        
        # Добавляем список приложений для выпадающего списка
        context['applications'] = Application.objects.filter(
            useractivity__user=self.request.user
        ).distinct()
        
        return context

class TrackedApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        app = self.get_object()
        app.is_active = not app.is_active
        app.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def toggle_productive(self, request, pk=None):
        app = self.get_object()
        app.is_productive = not app.is_productive
        app.save()
        return Response({'status': 'success'})

    @action(detail=False)
    def active_apps(self, request):
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def productive_apps(self, request):
        queryset = self.get_queryset().filter(is_productive=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def non_productive_apps(self, request):
        queryset = self.get_queryset().filter(is_productive=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class TimeLogListCreateView(generics.ListCreateAPIView):
    queryset = TimeLog.objects.all()
    serializer_class = TimeLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TimeLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TimeLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TimeLog.objects.all()
    serializer_class = TimeLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TimeLog.objects.filter(user=self.request.user)

class TimeLogListView(LoginRequiredMixin, ListView):
    model = TimeLog
    template_name = 'tracking/timelog_list.html'
    context_object_name = 'timelogs'

    def get_queryset(self):
        return TimeLog.objects.filter(user=self.request.user)

class TimeLogCreateView(LoginRequiredMixin, CreateView):
    model = TimeLog
    template_name = 'tracking/timelog_form.html'
    fields = ['start_time', 'end_time', 'description']
    success_url = reverse_lazy('timelog-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Time log was created successfully.')
        return super().form_valid(form)

class TimeLogUpdateView(LoginRequiredMixin, UpdateView):
    model = TimeLog
    template_name = 'tracking/timelog_form.html'
    fields = ['start_time', 'end_time', 'description']
    success_url = reverse_lazy('timelog-list')

    def get_queryset(self):
        return TimeLog.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Time log was updated successfully.')
        return super().form_valid(form)

class TimeLogDeleteView(LoginRequiredMixin, DeleteView):
    model = TimeLog
    template_name = 'tracking/timelog_confirm_delete.html'
    success_url = reverse_lazy('timelog-list')

    def get_queryset(self):
        return TimeLog.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Time log was deleted successfully.')
        return super().delete(request, *args, **kwargs)
