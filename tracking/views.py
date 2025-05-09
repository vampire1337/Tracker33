from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
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
        today = timezone.now().date()
        
        # Получаем статистику за сегодня
        activities = UserActivity.objects.filter(
            user=user,
            start_time__date=today
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
        
        # Получаем все приложения пользователя за сегодня
        apps = Application.objects.filter(
            useractivity__user=user,
            useractivity__start_time__date=today
        ).annotate(
            total_time=Sum('useractivity__duration'),
            total_seconds=Sum(ExpressionWrapper(
                F('useractivity__duration'), 
                output_field=models.IntegerField()
            ))
        ).order_by('-total_time')
        
        # Форматируем время для каждого приложения
        for app in apps:
            if hasattr(app, 'total_seconds') and app.total_seconds:
                # Преобразуем время в секунды, разделив на 1000000 если значение слишком большое
                seconds_value = app.total_seconds
                if seconds_value > 100000:  # Если значение слишком большое, вероятно это микросекунды
                    seconds_value = seconds_value / 1000000
                
                hours, remainder = divmod(int(seconds_value), 3600)
                minutes, seconds = divmod(remainder, 60)
                app.formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                app.formatted_time = "00:00:00"
        
        # Обновляем названия приложений для отображения
        for app in apps:
            process_name = app.process_name.lower()
            if process_name in self.app_name_mapping:
                app.name = self.app_name_mapping[process_name]
                app.save()
        
        # Добавляем данные в контекст
        context['apps'] = apps
        context['formatted_time'] = formatted_time
        context['keyboard_activity'] = keyboard_activity
        context['today_activity'] = activities.select_related('application').order_by('-start_time')[:10]
        
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
        cache_key = f'user_activity_{self.request.user.id}'
        queryset = cache.get(cache_key)
        if queryset is None:
            queryset = UserActivity.objects.filter(user=self.request.user)
            cache.set(cache_key, queryset, settings.CACHE_TTL)
        return queryset

    def perform_create(self, serializer):
        try:
            # Добавляем отладочную информацию
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Получены данные для создания активности: {serializer.validated_data}")
            
            # Проверяем, есть ли данные о клавиатурной активности
            keyboard_presses = serializer.validated_data.get('keyboard_presses', 0)
            logger.info(f"Количество нажатий клавиш: {keyboard_presses}")
            
            # Проверяем, есть ли данные о приложении
            app_name = serializer.validated_data.get('app_name', '')
            
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
            
            # Проверяем, есть ли процесс в нашем списке известных приложений
            if app_name.lower() in app_name_mapping:
                display_name = app_name_mapping[app_name.lower()]
                # Обновляем название приложения
                application_id = serializer.validated_data.get('application')
                if application_id:
                    try:
                        app = Application.objects.get(id=application_id)
                        app.name = display_name
                        app.save()
                    except Application.DoesNotExist:
                        pass
            
            instance = serializer.save(user=self.request.user)
            cache.delete(f'user_activity_{self.request.user.id}')
            return instance
        except ValidationError as e:
            raise InvalidActivityData(detail=str(e))

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
        return KeyboardActivity.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except ValidationError as e:
            raise InvalidActivityData(detail=str(e))

# Убираем кэширование, чтобы данные обновлялись в реальном времени
# @method_decorator(cache_page(settings.CACHE_TTL), name='dispatch')
class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'statistics.html'

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            
            # Получаем данные за последние 7 дней
            end_date = timezone.now()
            start_date = end_date - timedelta(days=7)
            
            if start_date > end_date:
                raise InvalidTimeRange()
            
            # Получаем фильтры из запроса
            productive_only = self.request.GET.get('productive', None)
            app_ids = self.request.GET.getlist('apps', [])
            
            # Отключаем кэширование, чтобы данные всегда были актуальными
            # Кэш-ключ для статистики
            # cache_key = f'statistics_{self.request.user.id}_{productive_only}_{"-".join(app_ids)}'
            # cached_data = cache.get(cache_key)
            cached_data = None  # Всегда загружаем свежие данные
            
            # Всегда загружаем свежие данные
            if True:
                # Базовый запрос для фильтрации
                activity_query = UserActivity.objects.filter(
                    user=self.request.user,
                    start_time__range=(start_date, end_date)
                )
                
                # Применяем фильтры
                if productive_only == 'true':
                    activity_query = activity_query.filter(
                        application__is_productive=True
                    )
                elif productive_only == 'false':
                    activity_query = activity_query.filter(
                        application__is_productive=False
                    )
                    
                if app_ids:
                    activity_query = activity_query.filter(
                        application__id__in=app_ids
                    )
                
                # Статистика по приложениям
                apps = activity_query.values('application__name').annotate(
                    total_time=Sum('duration')
                ).order_by('-total_time')[:10]
                
                # Клавиатурная активность - используем поле keyboard_presses из модели UserActivity
                keyboard = UserActivity.objects.filter(
                    user=self.request.user,
                    start_time__range=(start_date, end_date)
                ).aggregate(total_keystrokes=Sum('keyboard_presses'))['total_keystrokes'] or 0
                
                # Время работы
                work_time = TimeLog.objects.filter(
                    user=self.request.user,
                    start_time__range=(start_date, end_date)
                ).annotate(
                    duration_seconds=ExpressionWrapper(
                        F('end_time') - F('start_time'),
                        output_field=DurationField()
                    )
                ).aggregate(
                    total_time=Sum('duration_seconds')
                )
                
                # Получаем список всех приложений для фильтрации
                all_apps = Application.objects.filter(user=self.request.user)
                
                cached_data = {
                    'apps': apps,
                    'keyboard_activity': keyboard,
                    'work_time': work_time['total_time'] or timedelta(0),
                    'all_apps': all_apps,
                }
                
                # Не используем кэширование
                # cache.set(cache_key, cached_data, settings.CACHE_TTL)
            
            context.update({
                'apps': cached_data['apps'],
                'keyboard_activity': cached_data['keyboard_activity'],
                'work_time': cached_data['work_time'],
                'start_date': start_date,
                'end_date': end_date,
                'all_apps': cached_data['all_apps'],
                'productive_only': productive_only,
                'selected_apps': app_ids
            })
            
            return context
        except Exception as e:
            messages.error(self.request, str(e))
            return context

# Отключаем кэширование для дашборда
# @method_decorator(cache_page(settings.CACHE_TTL), name='dispatch')
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
            process_name = app.process_name.lower()
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
        
        # Форматируем время для каждого приложения
        for app in apps:
            if hasattr(app, 'total_seconds') and app.total_seconds:
                # Преобразуем время в секунды, разделив на 1000000 если значение слишком большое
                seconds_value = app.total_seconds
                if seconds_value > 100000:  # Если значение слишком большое, вероятно это микросекунды
                    seconds_value = seconds_value / 1000000
                
                hours, remainder = divmod(int(seconds_value), 3600)
                minutes, seconds = divmod(remainder, 60)
                app.formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                app.formatted_time = "00:00:00"
        
        # Отладочная информация
        print(f"\n\nРасчет времени работы: {total_work_time}")
        print(f"Количество активностей: {activities.count()}")
        print(f"Общее время в секундах: {total_seconds}")
        print(f"Форматированное время: {formatted_time}\n\n")
        
        # Обновляем названия приложений для отображения
        for app in apps:
            process_name = app.process_name.lower()
            if process_name in self.app_name_mapping:
                # Обновляем название приложения в базе данных
                app.name = self.app_name_mapping[process_name]
                app.save()
        
        today_stats = {
            'total_work_time': total_work_time,
            'formatted_time': formatted_time,
            'apps': apps,
            
            # Получаем количество нажатий клавиш из модели UserActivity с использованием SQL
            'keystrokes': UserActivity.objects.filter(
                user=user,
                start_time__date=today
            ).aggregate(total_keystrokes=Sum('keyboard_presses'))['total_keystrokes'] or 0,
            
            # Получаем только последние 10 записей о клавиатурной активности
            'debug_keystrokes': list(UserActivity.objects.filter(
                user=user,
                start_time__date=today,
                keyboard_presses__gt=0
            ).order_by('-start_time')[:10].values('id', 'keyboard_presses', 'start_time', 'end_time')),
            
            # Рассчитываем общее время активности
            'keystrokes_time': UserActivity.objects.filter(
                user=user,
                start_time__date=today,
                keyboard_presses__gt=0
            ).aggregate(total_time=Sum('duration'))['total_time'] or timedelta(0)
        }

        # Мы уже получили последние действия в начале метода
        # today_activity = UserActivity.objects.filter(
        #     user=user,
        #     start_time__date=today
        # ).select_related('application').order_by('-start_time')[:10]

        cached_data = {
            'active_apps': active_apps,
            'today_stats': today_stats,
            'today_activity': context['today_activity']
        }

        # Не используем кэширование
        # cache.set(cache_key, cached_data, settings.CACHE_TTL)

        context.update(cached_data)
        return context

class LogsView(LoginRequiredMixin, ListView):
    template_name = 'logs.html'
    model = UserActivity
    context_object_name = 'activities'
    paginate_by = 20

    def get_queryset(self):
        return UserActivity.objects.filter(
            user=self.request.user
        ).order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['keyboard_activities'] = KeyboardActivity.objects.filter(
            user=self.request.user
        ).order_by('-timestamp')[:20]
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
