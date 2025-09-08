from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta, datetime, time
from .models import Application, UserActivity, KeyboardActivity, TimeLog
from users.models import CustomUser
from .serializers import (
    ApplicationSerializer, 
    UserActivitySerializer, 
    KeyboardActivitySerializer,
    TimeLogSerializer
)
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import action
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count, ExpressionWrapper, F, DurationField
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.db import models
from django.utils.decorators import method_decorator
from django.conf import settings
import logging
from .exceptions import (
    ApplicationAlreadyExists,
    InvalidTimeRange,
    ApplicationNotFound,
    UserActivityNotFound,
    InvalidActivityData
)
from rest_framework.exceptions import ValidationError
from .utils import (
    filter_user_applications,
    group_applications_by_name,
    normalize_app_name,
    format_duration,
    calculate_productivity_stats,
    is_system_process
)
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

# Настройка логирования
logger = logging.getLogger('tracking.error')

# Create your views here.

class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'statistics.html'
    
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
        formatted_time = format_duration(total_seconds)
        
        # Рассчитываем средние показатели на день
        avg_seconds_per_day = total_seconds / days if days > 0 else 0
        average_daily_time = format_duration(avg_seconds_per_day)
        average_daily_keystrokes = int(keyboard_activity / days) if days > 0 else 0
        
        # Получаем все приложения пользователя за период - без кэширования
        apps_queryset = Application.objects.filter(
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
        
        # Применяем фильтрацию системных процессов и группировку
        apps_data = []
        grouped_apps = {}
        
        for app in apps_queryset:
            # Проверяем, не системный ли это процесс
            if is_system_process(app.process_name):
                continue
                
            # Нормализуем название приложения
            normalized_result = normalize_app_name(app.process_name)
            if normalized_result[0] is None:
                continue
                
            normalized_name, default_productive = normalized_result
            
            # Преобразуем время в секунды правильно
            seconds_value = getattr(app, 'total_seconds', 0) or 0
            if seconds_value > 100000:  # Если значение слишком большое, вероятно это микросекунды
                seconds_value = seconds_value / 1000000
            
            if normalized_name in grouped_apps:
                # Суммируем время для одинаковых приложений
                grouped_apps[normalized_name]['total_seconds'] += seconds_value
                grouped_apps[normalized_name]['activities_count'] += 1
            else:
                # Создаем новую запись с правильным названием
                grouped_apps[normalized_name] = {
                    'id': app.id,
                    'name': normalized_name,
                    'process_name': app.process_name,
                    'total_seconds': seconds_value,
                    'activities_count': 1,
                    'is_productive': getattr(app, 'is_productive', default_productive)
                }
        
        # Преобразуем в список и сортируем по времени
        apps_data = sorted(grouped_apps.values(), key=lambda x: x['total_seconds'], reverse=True)
        
        # Общее количество секунд для всех приложений
        all_apps_seconds = sum(app['total_seconds'] for app in apps_data)
        
        # Форматируем время для каждого приложения и рассчитываем проценты
        for app in apps_data:
            app['formatted_time'] = format_duration(app['total_seconds'])
            app['percentage'] = round((app['total_seconds'] / all_apps_seconds) * 100, 1) if all_apps_seconds > 0 else 0
            
            # Для совместимости с шаблоном добавляем тренд (пока что нейтральный)
            app['trend'] = 0
            app['trend_class'] = 'bg-secondary'
            app['is_new'] = False
        
        # Создаем объекты для совместимости с шаблоном
        apps = []
        for app_data in apps_data:
            class AppMock:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
                        
                def __str__(self):
                    return self.name
                    
                def get_display_name(self):
                    """Метод для совместимости с шаблонами"""
                    return self.name
            apps.append(AppMock(app_data))
        
        # ОТЛАДКА: Проверяем что передаем в контекст
        import logging
        logger = logging.getLogger('tracking.performance')
        logger.debug(f"Statistics - Created {len(apps)} applications")
        for i, app in enumerate(apps[:5]):  # Показываем первые 5
            logger.debug(f"  App {i}: name='{app.name}', process_name='{getattr(app, 'process_name', 'None')}', percentage={getattr(app, 'percentage', 0)}")
        
        # Получаем данные по дням для графика
        daily_data = []
        for i in range(days):
            date = today - timedelta(days=days-1-i)
            day_activities = activities.filter(start_time__date=date)
            
            day_seconds = 0
            day_productive_seconds = 0
            
            for activity in day_activities:
                # Проверяем, не системное ли это приложение
                if is_system_process(activity.application.process_name):
                    continue
                    
                if activity.duration:
                    activity_seconds = activity.duration.total_seconds()
                elif activity.start_time and activity.end_time:
                    duration = activity.end_time - activity.start_time
                    activity_seconds = duration.total_seconds()
                else:
                    continue
                
                day_seconds += activity_seconds
                
                # Проверяем продуктивность
                if activity.application.is_productive:
                    day_productive_seconds += activity_seconds
            
            daily_data.append({
                'date': date,
                'hours': round(day_seconds / 3600, 1),
                'productive_hours': round(day_productive_seconds / 3600, 1),
                'minutes': round(day_seconds / 60, 0)
            })
        
        # Убедимся, что у нас есть данные для графиков
        if not daily_data:
            for i in range(days):
                date = today - timedelta(days=days-1-i)
                daily_data.append({
                    'date': date,
                    'hours': 0,
                    'productive_hours': 0,
                    'minutes': 0
                })
        
        logger.debug(f"[DEBUG] StatisticsView - daily_data: {daily_data}")
        
        # Рассчитываем продуктивность
        productive_seconds = sum(app['total_seconds'] for app in apps_data if app.get('is_productive', False))
        productivity_percent = round((productive_seconds / all_apps_seconds) * 100, 1) if all_apps_seconds > 0 else 0
        
        # Добавляем данные в контекст
        context.update({
            'apps': apps,
            'formatted_time': formatted_time,
            'keyboard_activity': keyboard_activity,
            'today_activity': activities.select_related('application').order_by('-start_time')[:10],
            'daily_data': daily_data,
            'average_daily_time': average_daily_time,
            'average_daily_keystrokes': average_daily_keystrokes,
            'productivity_percent': productivity_percent
        })
        
        logger.debug(f"[DEBUG] Statistics - Apps found: {len(apps)}, Daily data: {len(daily_data)}, Total time: {formatted_time}, Productivity: {productivity_percent}%")
        
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
            process_name = request_data.get('process_name', request_data.get('application', ''))
            keyboard_presses = request_data.get('keyboard_presses', 0)
            
            # Проверяем валидность данных
            try:
                keyboard_presses = int(keyboard_presses)
            except (ValueError, TypeError):
                keyboard_presses = 0
            
            # Логируем полученные данные для отладки
            logger.debug(f"Получены данные: app_name={app_name}, process_name={process_name}, keyboard_presses={keyboard_presses}")
            
            # Получаем приложение из сериализатора (может быть None)
            application = serializer.validated_data.get('application')
            
            # Если приложение не передано или не найдено, пытаемся найти/создать его
            if not application:
                # ИСПРАВЛЕНИЕ: Проверяем, передан ли ID приложения как строка/число
                application_id = None
                try:
                    # Проверяем разные способы передачи ID приложения
                    if isinstance(process_name, (int, str)) and str(process_name).isdigit():
                        application_id = int(process_name)
                    elif 'application' in request_data:
                        app_field = request_data['application']
                        if isinstance(app_field, (int, str)) and str(app_field).isdigit():
                            application_id = int(app_field)
                    
                    # Если ID передан, пытаемся найти приложение
                    if application_id:
                        try:
                            application = Application.objects.get(id=application_id, user=self.request.user)
                            logger.debug(f"Найдено приложение по ID={application_id}: {application}")
                        except Application.DoesNotExist:
                            logger.debug(f"Приложение с ID={application_id} не найдено, создаем новое")
                            # Создаем новое приложение с правильными данными
                            application_name = app_name or f"Восстановленное приложение {application_id}"
                            process_name_for_db = app_name or f"app_{application_id}.exe"
                            
                            # Проверяем, не существует ли уже приложение с таким process_name
                            existing_app = Application.objects.filter(
                                user=self.request.user,
                                process_name=process_name_for_db
                            ).first()
                            
                            if existing_app:
                                # Используем существующее приложение
                                application = existing_app
                                logger.debug(f"Найдено существующее приложение с process_name {process_name_for_db}: {application}")
                            else:
                                # Создаем новое приложение
                                application = Application.objects.create(
                                    user=self.request.user,
                                    name=application_name,
                                    process_name=process_name_for_db,
                                    is_productive=False  # По умолчанию не продуктивное
                                )
                                logger.debug(f"Создано новое приложение: {application}")
                except (TypeError, ValueError, AttributeError) as e:
                    logger.debug(f"Ошибка при обработке ID приложения: {e}")
                
                # Если до сих пор не нашли приложение, создаем по имени процесса
                if not application:
                    process_name_str = str(process_name) if process_name else ""
                    app_name_str = str(app_name) if app_name else ""
                    
                    if process_name_str:
                        # Пытаемся найти существующее приложение по имени процесса
                        application = Application.objects.filter(
                            user=self.request.user,
                            process_name__icontains=process_name_str
                        ).first()
                        
                        if not application:
                            # Создаем новое приложение
                            application_name = app_name_str or process_name_str
                            application = Application.objects.create(
                                user=self.request.user,
                                name=application_name,
                                process_name=process_name_str,
                                is_productive=False
                            )
                            logger.debug(f"Создано новое приложение по имени: {application}")
                    else:
                        # Создаем приложение с базовым именем
                        timestamp = timezone.now().timestamp()
                        application = Application.objects.create(
                            user=self.request.user,
                            name=f"Неизвестное приложение {timestamp}",
                            process_name="unknown.exe",
                            is_productive=False
                        )
                        logger.debug(f"Создано fallback приложение: {application}")
            
            # Проверяем и устанавливаем даты для активности
            start_time = request_data.get('start_time')
            end_time = request_data.get('end_time')
            
            # Убедимся, что у нас есть валидные даты
            if not start_time:
                start_time = timezone.now()
            
            # Если есть и start_time и end_time, вычисляем duration
            duration = None
            if end_time and start_time:
                try:
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    duration = end_time - start_time
                except (ValueError, TypeError) as e:
                    logger.debug(f"Ошибка при вычислении duration: {e}")
            
            # Сохраняем активность с правильным объектом приложения и всеми данными
            activity = serializer.save(
                user=self.request.user,
                application=application,
                keyboard_presses=keyboard_presses,
                start_time=start_time,
                end_time=end_time,
                duration=duration
            )
            
            logger.debug(f"Активность успешно сохранена: {activity.id}, приложение: {application.name}")
            return activity
            
        except Exception as e:
            logger.debug(f"Ошибка при создании активности: {e}")
            # Логируем детальную ошибку, но возвращаем успешный ответ для клиента
            import traceback
            traceback.print_exc()
            raise ValidationError(detail=f"Ошибка сохранения активности: {str(e)}")

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        # ВРЕМЕННО: показываем данные за последние 30 дней вместо только сегодня
        start_date = today - timedelta(days=30)
        
        # Добавляем timestamp для предотвращения кэширования
        context['timestamp'] = timezone.now().timestamp()

        # Загружаем последние активности за 30 дней
        recent_activities = UserActivity.objects.filter(
            user=user,
            start_time__date__gte=start_date
        ).select_related('application').order_by('-start_time')[:10]
        
        # Фильтруем системные процессы из активностей
        filtered_activities = []
        for activity in recent_activities:
            if not is_system_process(activity.application.process_name):
                filtered_activities.append(activity)
        
        # Убедимся, что у каждой активности есть правильная длительность
        for activity in filtered_activities:
            if not activity.duration and activity.start_time and activity.end_time:
                activity.duration = activity.end_time - activity.start_time
                activity.save()
            
            # Форматируем duration в строку для отображения
            if activity.duration:
                seconds = int(activity.duration.total_seconds())
                hours, remainder = divmod(seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                activity.formatted_duration = f"{hours}:{minutes:02d}:{seconds:02d}"
                
            # Если активность не завершена, рассчитываем текущую длительность
            elif activity.start_time and not activity.end_time:
                current_time = timezone.now()
                activity.current_duration = current_time - activity.start_time
                seconds = int(activity.current_duration.total_seconds())
                hours, remainder = divmod(seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                activity.formatted_duration = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        context['today_activity'] = filtered_activities[:10]  # Ограничиваем до 10
        
        # Получаем активные приложения за последние 30 дней
        active_apps_queryset = Application.objects.filter(
            useractivity__user=user,
            useractivity__start_time__date__gte=start_date
        ).distinct()
        
        # Фильтруем системные процессы
        active_apps = filter_user_applications(active_apps_queryset)

        # Получаем статистику за последние 30 дней
        activities = UserActivity.objects.filter(
            user=user,
            start_time__date__gte=start_date
        )
        
        # Рассчитываем общее время работы на основе пользовательских приложений
        total_seconds = 0
        keyboard_total = 0
        
        for activity in activities:
            # Пропускаем системные процессы
            if is_system_process(activity.application.process_name):
                continue
                
            if activity.duration:
                total_seconds += activity.duration.total_seconds()
            elif activity.start_time and activity.end_time:
                duration = activity.end_time - activity.start_time
                total_seconds += duration.total_seconds()
            
            keyboard_total += activity.keyboard_presses or 0
        
        # Форматируем время в строку для отображения
        formatted_time = format_duration(total_seconds)
        
        # Получаем все приложения пользователя за последние 30 дней с группировкой
        apps_queryset = Application.objects.filter(
            useractivity__user=user,
            useractivity__start_time__date__gte=start_date
        ).annotate(
            total_time=Sum('useractivity__duration'),
            total_seconds=Sum(ExpressionWrapper(
                F('useractivity__duration'), 
                output_field=models.IntegerField()
            ))
        ).order_by('-total_time').distinct()
        
        # Применяем фильтрацию и группировку
        apps_data = []
        grouped_apps = {}
        
        for app in apps_queryset:
            # Проверяем, не системный ли это процесс
            if is_system_process(app.process_name):
                continue
                
            # Нормализуем название приложения
            normalized_result = normalize_app_name(app.process_name)
            if normalized_result[0] is None:
                continue
                
            normalized_name, default_productive = normalized_result
            
            # Преобразуем время правильно
            seconds_value = getattr(app, 'total_seconds', 0) or 0
            if seconds_value > 100000:
                seconds_value = seconds_value / 1000000
            
            if normalized_name in grouped_apps:
                grouped_apps[normalized_name]['total_seconds'] += seconds_value
            else:
                grouped_apps[normalized_name] = {
                    'id': app.id,
                    'name': normalized_name,
                    'process_name': app.process_name,
                    'total_seconds': seconds_value,
                    'is_productive': getattr(app, 'is_productive', default_productive)
                }
        
        # Преобразуем в список и рассчитываем проценты
        apps_data = sorted(grouped_apps.values(), key=lambda x: x['total_seconds'], reverse=True)
        all_apps_seconds = sum(app['total_seconds'] for app in apps_data)
        
        for app in apps_data:
            app['formatted_time'] = format_duration(app['total_seconds'])
            app['percentage'] = round((app['total_seconds'] / all_apps_seconds) * 100, 1) if all_apps_seconds > 0 else 0
        
        # Создаем объекты для совместимости с шаблоном
        apps = []
        for app_data in apps_data:
            class AppMock:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
                        
                def __str__(self):
                    return self.name
                    
                def get_display_name(self):
                    """Метод для совместимости с шаблонами"""
                    return self.name
            apps.append(AppMock(app_data))
        
        # ОТЛАДКА: Проверяем что передаем в контекст
        logger.debug(f"[DEBUG] Dashboard - Создано {len(apps)} приложений:")
        for i, app in enumerate(apps[:5]):  # Показываем первые 5
            logger.debug(f"  App {i}: name='{app.name}', process_name='{getattr(app, 'process_name', 'None')}', percentage={getattr(app, 'percentage', 0)}")
        
        # Создаем активность по часам - ОПТИМИЗИРОВАНО: один запрос вместо 24
        hourly_activity = []
        
        # Получаем все активности за сегодня одним запросом
        today_start = timezone.make_aware(datetime.combine(today, time.min))
        today_end = timezone.make_aware(datetime.combine(today, time.max))
        
        activities_today = activities.filter(
            start_time__gte=today_start,
            start_time__lte=today_end
        ).values('start_time', 'duration', 'application__process_name')
        
        # Создаем массив для 24 часов
        hours_data = {hour: 0 for hour in range(24)}
        
        # Обрабатываем все активности за один проход
        for activity in activities_today:
            # Пропускаем системные процессы
            if is_system_process(activity['application__process_name']):
                continue
                
            hour = activity['start_time'].hour
            if activity['duration']:
                hours_data[hour] += activity['duration'].total_seconds()
        
        # Формируем результат для графика
        for hour in range(24):
            hour_minutes = round(hours_data[hour] / 60, 0)
            hourly_activity.append({
                'hour': hour,
                'minutes': hour_minutes,
                'seconds': hours_data[hour]
            })
        
        # Рассчитываем продуктивность
        productive_seconds = sum(app['total_seconds'] for app in apps_data if app.get('is_productive', False))
        productivity_percent = round((productive_seconds / all_apps_seconds) * 100, 1) if all_apps_seconds > 0 else 0
        
        today_stats = {
            'total_work_time': timedelta(seconds=int(total_seconds)),
            'formatted_time': formatted_time,
            'total_hours': total_seconds / 3600,
            'apps': apps,
            'keystrokes': keyboard_total,
            'productivity_percent': productivity_percent
        }

        context.update({
            'active_apps': active_apps,
            'today_stats': today_stats,
            'hourly_activity': hourly_activity
        })
        
        logger.debug(f"[DEBUG] Dashboard - Apps: {len(apps)}, Time: {formatted_time}, Productivity: {productivity_percent}%")
        
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
        
        # Форматируем длительность для каждой активности
        activities = context['activities']
        for activity in activities:
            if activity.duration:
                total_seconds = int(activity.duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                activity.formatted_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            elif activity.start_time and activity.end_time:
                duration = activity.end_time - activity.start_time
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                activity.formatted_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                activity.formatted_duration = "00:00:00"
        
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
        
        # Добавляем список приложений для выпадающего списка (только пользовательские)
        all_apps = Application.objects.filter(
            useractivity__user=self.request.user
        ).distinct()
        
        # Фильтруем системные процессы
        context['applications'] = filter_user_applications(all_apps)
        
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
        """
        Переключает статус продуктивности для приложения.
        """
        try:
            app = self.get_object()
            # Удаляем проверку на суперпользователя с именем 'dfyz'
            # Теперь любой авторизованный пользователь может изменять свои приложения
            
            # Логируем для отладки
            logger.info(f"Попытка изменения статуса продуктивности приложения {app.id} '{app.name}' пользователем {request.user.username}")
            
            # Проверка специального случая для user01
            if request.user.username == 'user01':
                logger.info(f"Обработка особого случая для пользователя user01")
                # Дополнительная обработка для user01
                # Устанавливаем принудительно нужный флаг и сохраняем
                app.is_productive = not app.is_productive
                app.save(update_fields=['is_productive'])
            else:
                # Стандартная обработка
                app.is_productive = not app.is_productive
                app.save()
                
            # Очищаем кэш для всех пользователей
            cache.clear()
            logger.info(f"Успешно изменен статус продуктивности приложения {app.id} '{app.name}' на {app.is_productive}")
            return Response({'status': 'success', 'is_productive': app.is_productive})
        except Exception as e:
            logger.error(f"Ошибка при изменении статуса продуктивности: {str(e)}", exc_info=True)
            return Response(
                {'status': 'error', 'message': f'Произошла ошибка при изменении статуса приложения: {str(e)}'},
                status=500
            )

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

# NEW API VIEWS

class StatisticsAPIView(APIView):
    """
    API для получения статистики использования приложений.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        days = int(request.query_params.get('days', 7))
        
        today = timezone.now().date()
        start_date = today - timedelta(days=days-1)
        
        # Получаем активности пользователя за указанный период
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
        
        # Рассчитываем средние показатели
        avg_seconds_per_day = total_seconds / days if days > 0 else 0
        
        # Получаем статистику по приложениям
        app_statistics = []
        all_apps_seconds = 0
        
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
        
        # Считаем общее время для всех приложений
        for app in apps:
            if hasattr(app, 'total_seconds') and app.total_seconds:
                all_apps_seconds += app.total_seconds
        
        # Формируем статистику по приложениям
        for app in apps:
            if hasattr(app, 'total_seconds') and app.total_seconds:
                seconds_value = app.total_seconds
                if seconds_value > 100000:  # Если значение слишком большое, вероятно это микросекунды
                    seconds_value = seconds_value / 1000000
                
                hours, remainder = divmod(int(seconds_value), 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
                
                percentage = round((app.total_seconds / all_apps_seconds) * 100, 1) if all_apps_seconds > 0 else 0
                
                app_statistics.append({
                    'id': app.id,
                    'name': app.name,
                    'process_name': app.process_name,
                    'total_seconds': app.total_seconds,
                    'formatted_time': formatted_time,
                    'percentage': percentage,
                    'is_productive': app.is_productive
                })
        
        # Форматируем общее время
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        total_formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Форматируем среднее время в день
        avg_hours, avg_remainder = divmod(int(avg_seconds_per_day), 3600)
        avg_minutes, avg_seconds = divmod(avg_remainder, 60)
        avg_formatted_time = f"{avg_hours}:{avg_minutes:02d}:{avg_seconds:02d}"
        
        # Собираем данные по дням
        daily_data = {}
        for day_offset in range(days):
            date = today - timedelta(days=days-1-day_offset)
            date_str = date.strftime('%Y-%m-%d')
            
            day_activities = activities.filter(
                start_time__date=date
            )
            
            day_seconds = 0
            for activity in day_activities:
                if activity.duration:
                    day_seconds += activity.duration.total_seconds()
                elif activity.start_time and activity.end_time:
                    duration = activity.end_time - activity.start_time
                    day_seconds += duration.total_seconds()
            
            day_hours = day_seconds / 3600
            
            daily_data[date_str] = {
                'date': date_str,
                'day_name': date.strftime('%A'),
                'total_seconds': day_seconds,
                'hours': round(day_hours, 2)
            }
        
        # Формируем итоговый ответ
        response_data = {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': today.strftime('%Y-%m-%d'),
                'days': days
            },
            'summary': {
                'total_seconds': total_seconds,
                'total_time': total_formatted_time,
                'average_time_per_day': avg_formatted_time,
                'keyboard_activity': keyboard_activity,
                'average_keyboard_per_day': int(keyboard_activity / days) if days > 0 else 0
            },
            'applications': app_statistics,
            'daily_data': list(daily_data.values())
        }
        
        return Response(response_data)

class ExportStatisticsAPIView(APIView):
    """
    API для экспорта статистики использования приложений в CSV формате.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        days = int(request.query_params.get('days', 7))
        
        today = timezone.now().date()
        start_date = today - timedelta(days=days-1)
        
        # Получаем активности пользователя за указанный период
        activities = UserActivity.objects.filter(
            user=user,
            start_time__date__gte=start_date,
            start_time__date__lte=today
        ).select_related('application').order_by('start_time')
        
        import csv
        from django.http import HttpResponse
        
        # Создаем HTTP ответ с CSV файлом с явным указанием кодировки utf-8 и BOM для Excel
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response.write('\ufeff')  # Добавляем BOM для лучшей совместимости с Excel
        response['Content-Disposition'] = f'attachment; filename="activity_report_{start_date.strftime("%Y-%m-%d")}_{today.strftime("%Y-%m-%d")}.csv"'
        
        writer = csv.writer(response, delimiter=';')  # Используем точку с запятой в качестве разделителя для лучшей совместимости с Excel
        writer.writerow(['Дата', 'Время начала', 'Время окончания', 'Длительность', 'Приложение', 'Процесс', 'Нажатия клавиш', 'Продуктивное'])
        
        for activity in activities:
            if activity.duration:
                duration_str = str(activity.duration)
            elif activity.start_time and activity.end_time:
                duration = activity.end_time - activity.start_time
                duration_str = str(duration)
            else:
                duration_str = '00:00:00'
            
            writer.writerow([
                activity.start_time.strftime('%Y-%m-%d'),
                activity.start_time.strftime('%H:%M:%S'),
                activity.end_time.strftime('%H:%M:%S') if activity.end_time else '',
                duration_str,
                activity.application.name,
                activity.application.process_name,
                activity.keyboard_presses,
                'Да' if activity.application.is_productive else 'Нет'
            ])
        
        return response

class DailyActivityAPIView(APIView):
    """
    API для получения активности по дням.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        date_str = request.query_params.get('date')
        
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            date = timezone.now().date()
        
        # Получаем активности пользователя за указанный день
        day_activities = UserActivity.objects.filter(
            user=user,
            start_time__date=date
        ).order_by('start_time')
        
        activity_data = []
        
        for activity in day_activities:
            if activity.duration:
                duration_seconds = activity.duration.total_seconds()
            elif activity.start_time and activity.end_time:
                duration = activity.end_time - activity.start_time
                duration_seconds = duration.total_seconds()
            else:
                duration_seconds = 0
            
            hours, remainder = divmod(int(duration_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_duration = f"{hours}:{minutes:02d}:{seconds:02d}"
            
            activity_data.append({
                'id': activity.id,
                'application_name': activity.application.name,
                'process_name': activity.application.process_name,
                'start_time': activity.start_time.strftime('%H:%M:%S'),
                'end_time': activity.end_time.strftime('%H:%M:%S') if activity.end_time else None,
                'duration_seconds': duration_seconds,
                'formatted_duration': formatted_duration,
                'is_productive': activity.application.is_productive,
                'keyboard_presses': activity.keyboard_presses
            })
        
        # Рассчитываем общую продолжительность за день
        total_seconds = sum(item['duration_seconds'] for item in activity_data)
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        total_formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Расчет продуктивного времени
        productive_seconds = sum(
            item['duration_seconds'] for item in activity_data 
            if item['is_productive']
        )
        
        hours, remainder = divmod(int(productive_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        productive_formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        productivity_percentage = round((productive_seconds / total_seconds) * 100, 1) if total_seconds > 0 else 0
        
        # Группировка по часам
        hourly_data = {}
        for hour in range(24):
            hourly_data[hour] = {
                'hour': hour,
                'total_seconds': 0,
                'activities': []
            }
        
        for activity in activity_data:
            if activity['start_time']:
                hour = int(activity['start_time'].split(':')[0])
                hourly_data[hour]['total_seconds'] += activity['duration_seconds']
                hourly_data[hour]['activities'].append(activity)
        
        # Формируем итоговый ответ
        response_data = {
            'date': date.strftime('%Y-%m-%d'),
            'day_name': date.strftime('%A'),
            'summary': {
                'total_seconds': total_seconds,
                'total_time': total_formatted_time,
                'productive_seconds': productive_seconds,
                'productive_time': productive_formatted_time,
                'productivity_percentage': productivity_percentage,
                'activity_count': len(activity_data)
            },
            'activities': activity_data,
            'hourly_data': list(hourly_data.values())
        }
        
        return Response(response_data)

class TimeDistributionAPIView(APIView):
    """
    API для получения распределения времени по приложениям.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        days = int(request.query_params.get('days', 7))
        
        today = timezone.now().date()
        start_date = today - timedelta(days=days-1)
        
        # Получаем активности пользователя за указанный период
        activities = UserActivity.objects.filter(
            user=user,
            start_time__date__gte=start_date,
            start_time__date__lte=today
        )
        
        # Группируем по приложениям
        app_data = {}
        
        for activity in activities:
            app_id = activity.application.id
            app_name = activity.application.name
            process_name = activity.application.process_name
            is_productive = activity.application.is_productive
            
            if activity.duration:
                duration_seconds = activity.duration.total_seconds()
            elif activity.start_time and activity.end_time:
                duration = activity.end_time - activity.start_time
                duration_seconds = duration.total_seconds()
            else:
                continue
            
            if app_id not in app_data:
                app_data[app_id] = {
                    'id': app_id,
                    'name': app_name,
                    'process_name': process_name,
                    'is_productive': is_productive,
                    'total_seconds': 0,
                    'activities_count': 0
                }
            
            app_data[app_id]['total_seconds'] += duration_seconds
            app_data[app_id]['activities_count'] += 1
        
        # Сортируем по времени использования
        sorted_apps = sorted(
            app_data.values(), 
            key=lambda x: x['total_seconds'], 
            reverse=True
        )
        
        # Рассчитываем общее время
        total_seconds = sum(app['total_seconds'] for app in sorted_apps)
        
        # Добавляем процентное соотношение и форматированное время
        for app in sorted_apps:
            app['percentage'] = round((app['total_seconds'] / total_seconds) * 100, 1) if total_seconds > 0 else 0
            
            hours, remainder = divmod(int(app['total_seconds']), 3600)
            minutes, seconds = divmod(remainder, 60)
            app['formatted_time'] = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Рассчитываем продуктивность
        productive_seconds = sum(
            app['total_seconds'] for app in sorted_apps 
            if app['is_productive']
        )
        
        productivity_percentage = round((productive_seconds / total_seconds) * 100, 1) if total_seconds > 0 else 0
        
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        total_formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        hours, remainder = divmod(int(productive_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        productive_formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        # Формируем итоговый ответ
        response_data = {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': today.strftime('%Y-%m-%d'),
                'days': days
            },
            'summary': {
                'total_seconds': total_seconds,
                'total_time': total_formatted_time,
                'productive_seconds': productive_seconds,
                'productive_time': productive_formatted_time,
                'productivity_percentage': productivity_percentage,
                'applications_count': len(sorted_apps)
            },
            'applications': sorted_apps
        }
        
        return Response(response_data)

class DashboardAPIView(APIView):
    """
    API для получения данных дашборда.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user
        today = timezone.now().date()
        
        # Получаем активности пользователя за сегодня
        today_activities = UserActivity.objects.filter(
            user=user,
            start_time__date=today
        )
        
        # Рассчитываем общее время работы за сегодня
        total_seconds = 0
        keyboard_activity = 0
        
        for activity in today_activities:
            if activity.duration:
                total_seconds += activity.duration.total_seconds()
            elif activity.start_time and activity.end_time:
                duration = activity.end_time - activity.start_time
                total_seconds += duration.total_seconds()
            
            # Суммируем нажатия клавиш
            keyboard_activity += activity.keyboard_presses or 0
        
        # Получаем статистику по приложениям за сегодня
        app_statistics = []
        all_apps_seconds = 0
        
        apps = Application.objects.filter(
            useractivity__user=user,
            useractivity__start_time__date=today
        ).annotate(
            total_time=Sum('useractivity__duration'),
            total_seconds=Sum(ExpressionWrapper(
                F('useractivity__duration'), 
                output_field=models.IntegerField()
            ))
        ).order_by('-total_time').distinct()
        
        # Считаем общее время для всех приложений
        for app in apps:
            if hasattr(app, 'total_seconds') and app.total_seconds:
                all_apps_seconds += app.total_seconds
        
        # Формируем статистику по приложениям
        for app in apps:
            if hasattr(app, 'total_seconds') and app.total_seconds:
                seconds_value = app.total_seconds
                if seconds_value > 100000:  # Если значение слишком большое, вероятно это микросекунды
                    seconds_value = seconds_value / 1000000
                
                hours, remainder = divmod(int(seconds_value), 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
                
                percentage = round((app.total_seconds / all_apps_seconds) * 100, 1) if all_apps_seconds > 0 else 0
                
                app_statistics.append({
                    'id': app.id,
                    'name': app.name,
                    'process_name': app.process_name,
                    'total_seconds': app.total_seconds,
                    'formatted_time': formatted_time,
                    'percentage': percentage,
                    'is_productive': app.is_productive
                })
        
        # Рассчитываем продуктивность
        productive_seconds = sum(app['total_seconds'] for app in app_statistics if app['is_productive'])
        productivity_percent = round((productive_seconds / all_apps_seconds) * 100, 1) if all_apps_seconds > 0 else 0
        
        # Рассчитываем активность по часам
        hourly_activity = []
        
        # Получаем все активности за сегодня одним запросом
        today_start = timezone.make_aware(datetime.combine(today, time.min))
        today_end = timezone.make_aware(datetime.combine(today, time.max))
        
        activities_today = today_activities.filter(
            start_time__gte=today_start,
            start_time__lte=today_end
        ).values('start_time', 'duration', 'application__process_name')
        
        # Создаем массив для 24 часов
        hours_data = {hour: 0 for hour in range(24)}
        
        # Обрабатываем все активности за один проход
        for activity in activities_today:
            # Пропускаем системные процессы
            if is_system_process(activity['application__process_name']):
                continue
                
            hour = activity['start_time'].hour
            if activity['duration']:
                hours_data[hour] += activity['duration'].total_seconds()
        
        # Формируем результат для графика
        for hour in range(24):
            hour_minutes = round(hours_data[hour] / 60, 0)
            hourly_activity.append({
                'hour': hour,
                'minutes': hour_minutes,
                'seconds': hours_data[hour]
            })
        
        # Форматируем общее время
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{hours}:{minutes:02d}:{seconds:02d}"
        
        return Response({
            'total_time_seconds': total_seconds,
            'formatted_time': formatted_time,
            'keyboard_activity': keyboard_activity,
            'productivity_percent': productivity_percent,
            'hourly_activity': hourly_activity,
            'app_statistics': app_statistics,
            'unique_apps': len(app_statistics)
        })

@csrf_exempt
@require_POST
@login_required
def toggle_productive(request):
    """API для переключения статуса продуктивности приложения"""
    try:
        data = json.loads(request.body)
        app_id = data.get('app_id')
        is_productive = data.get('is_productive', False)
        
        if not app_id:
            return JsonResponse({'success': False, 'error': 'app_id is required'})
        
        # Находим приложение пользователя
        try:
            app = Application.objects.get(id=app_id, user=request.user)
            app.is_productive = is_productive
            app.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Приложение {app.name} {"отмечено как продуктивное" if is_productive else "больше не продуктивное"}'
            })
            
        except Application.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Application not found'})
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f"Error in toggle_productive: {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

# Конец новых API_views

@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_auth_token(request):
    """Получение токена аутентификации"""
    from rest_framework.authtoken.models import Token
    from django.contrib.auth import authenticate
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'success': False,
            'error': 'Имя пользователя и пароль обязательны'
        }, status=400)
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'success': True,
            'token': token.key,
            'user_id': user.id,
            'username': user.username
        })
    else:
        return Response({
            'success': False,
            'error': 'Неверные учетные данные'
        }, status=400)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_activity(request):
    """Создание записи активности"""
    try:
        data = request.data.copy()
        data['user'] = request.user.id
        
        logger.info(f"create_activity called with data: {data}")
        
        serializer = UserActivitySerializer(data=data, context={'request': request})
        logger.info(f"Serializer created, checking validity...")
        
        if serializer.is_valid():
            logger.info(f"Serializer is valid")
            # Проверяем, есть ли несуществующий ID приложения
            validated_data = serializer.validated_data.copy()
            missing_app_id = validated_data.pop('_missing_app_id', None)
            
            logger.info(f"Missing app ID: {missing_app_id}")
            logger.info(f"Validated data: {validated_data}")
            
            if missing_app_id:
                # Создаем новое приложение для несуществующего ID
                logger.warning(f"Application with ID {missing_app_id} not found for user {request.user.id}. Creating new application.")
                
                process_name = f"unknown_app_{missing_app_id}"
                logger.info(f"Looking for existing app with process_name: {process_name}")
                
                # Проверяем, не существует ли уже приложение с таким process_name
                existing_app = Application.objects.filter(
                    user=request.user,
                    process_name=process_name
                ).first()
                
                if existing_app:
                    # Используем существующее приложение
                    validated_data['application'] = existing_app
                    logger.info(f"Using existing application {existing_app.id} for missing ID {missing_app_id}")
                else:
                    # Создаем новое приложение
                    logger.info(f"Creating new application with process_name: {process_name}")
                    try:
                        new_app = Application.objects.create(
                            user=request.user,
                            name=f"Unknown Application {missing_app_id}",
                            process_name=process_name,
                            is_active=True,
                            is_productive=False
                        )
                        
                        # Устанавливаем новое приложение
                        validated_data['application'] = new_app
                        logger.info(f"Created new application {new_app.id} for missing ID {missing_app_id}")
                    except Exception as create_error:
                        logger.error(f"Error creating application: {create_error}")
                        raise
            
            # Убираем все служебные поля перед созданием
            clean_data = {k: v for k, v in validated_data.items() if not k.startswith('_')}
            logger.info(f"Clean data for UserActivity.create: {clean_data}")
            
            # Сохраняем активность
            activity = UserActivity.objects.create(user=request.user, **clean_data)
            logger.info(f"Activity created successfully: {activity.id}")
            
            return Response({
                'success': True,
                'data': UserActivitySerializer(activity).data
            })
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=400)
            
    except Exception as e:
        logger.error(f"Ошибка создания активности: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_applications(request):
    """Получение списка приложений пользователя"""
    try:
        applications = Application.objects.filter(user=request.user)
        serializer = ApplicationSerializer(applications, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения приложений: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_statistics(request):
    """Получение статистики пользователя"""
    try:
        days = int(request.GET.get('days', 7))
        today = timezone.now().date()
        start_date = today - timedelta(days=days-1)
        
        activities = UserActivity.objects.filter(
            user=request.user,
            start_time__date__gte=start_date,
            start_time__date__lte=today
        )
        
        total_seconds = 0
        for activity in activities:
            if activity.duration:
                total_seconds += activity.duration.total_seconds()
        
        return Response({
            'success': True,
            'data': {
                'total_time': format_duration(total_seconds),
                'total_seconds': total_seconds,
                'activities_count': activities.count(),
                'period_days': days
            }
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_profile(request):
    """Получение профиля пользователя"""
    try:
        user = request.user
        
        return Response({
            'success': True,
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined
            }
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
