from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Application, UserActivity, KeyboardActivity, TimeLog
from .utils import format_duration, is_system_process

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'process_name', 'user', 'is_productive', 'is_active', 'total_usage_time', 'activities_count', 'created_at']
    list_filter = ['is_productive', 'is_active', 'user', 'created_at']
    search_fields = ['name', 'process_name', 'user__username']
    list_editable = ['is_productive', 'is_active']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'process_name', 'user')
        }),
        ('Настройки', {
            'fields': ('is_productive', 'is_active'),
            'description': 'Отметьте приложение как продуктивное, если оно используется для работы/учебы'
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Исключаем системные процессы из админки
        return queryset.exclude(process_name__in=[
            'python.exe', 'cmd.exe', 'powershell.exe', 'explorer.exe',
            'dwm.exe', 'winlogon.exe', 'csrss.exe', 'system'
        ]).annotate(
            activities_total=Count('useractivity'),
            usage_time=Sum('useractivity__duration')
        )
    
    def total_usage_time(self, obj):
        """Показывает общее время использования приложения"""
        if hasattr(obj, 'usage_time') and obj.usage_time:
            total_seconds = obj.usage_time.total_seconds()
            return format_duration(total_seconds)
        return "00:00:00"
    total_usage_time.short_description = 'Общее время использования'
    total_usage_time.admin_order_field = 'usage_time'
    
    def activities_count(self, obj):
        """Показывает количество активностей"""
        if hasattr(obj, 'activities_total'):
            return obj.activities_total
        return 0
    activities_count.short_description = 'Количество сессий'
    activities_count.admin_order_field = 'activities_total'
    
    actions = ['mark_as_productive', 'mark_as_non_productive', 'activate_apps', 'deactivate_apps']
    
    def mark_as_productive(self, request, queryset):
        """Отметить выбранные приложения как продуктивные"""
        updated = queryset.update(is_productive=True)
        self.message_user(request, f'{updated} приложений отмечено как продуктивные.')
    mark_as_productive.short_description = "Отметить как продуктивные"
    
    def mark_as_non_productive(self, request, queryset):
        """Отметить выбранные приложения как непродуктивные"""
        updated = queryset.update(is_productive=False)
        self.message_user(request, f'{updated} приложений отмечено как непродуктивные.')
    mark_as_non_productive.short_description = "Отметить как непродуктивные"
    
    def activate_apps(self, request, queryset):
        """Активировать отслеживание приложений"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} приложений активировано.')
    activate_apps.short_description = "Активировать отслеживание"
    
    def deactivate_apps(self, request, queryset):
        """Деактивировать отслеживание приложений"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} приложений деактивировано.')
    deactivate_apps.short_description = "Деактивировать отслеживание"

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'application_name', 'formatted_start_time', 'formatted_duration', 'keyboard_presses', 'is_productive_activity']
    list_filter = ['user', 'application__is_productive', 'start_time', 'application']
    search_fields = ['user__username', 'application__name', 'application__process_name']
    date_hierarchy = 'start_time'
    ordering = ['-start_time']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'application', 'start_time', 'end_time', 'duration')
        }),
        ('Активность', {
            'fields': ('keyboard_presses',),
            'description': 'Количество нажатий клавиш во время этой активности'
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'application')
    
    def application_name(self, obj):
        """Показывает название приложения"""
        return obj.application.name if obj.application else '-'
    application_name.short_description = 'Приложение'
    application_name.admin_order_field = 'application__name'
    
    def formatted_start_time(self, obj):
        """Форматированное время начала"""
        if obj.start_time:
            return obj.start_time.strftime('%d.%m.%Y %H:%M:%S')
        return '-'
    formatted_start_time.short_description = 'Время начала'
    formatted_start_time.admin_order_field = 'start_time'
    
    def formatted_duration(self, obj):
        """Форматированная длительность"""
        if obj.duration:
            return format_duration(obj.duration.total_seconds())
        elif obj.start_time and obj.end_time:
            duration = obj.end_time - obj.start_time
            return format_duration(duration.total_seconds())
        return '-'
    formatted_duration.short_description = 'Длительность'
    formatted_duration.admin_order_field = 'duration'
    
    def is_productive_activity(self, obj):
        """Показывает, была ли активность продуктивной"""
        if obj.application:
            if obj.application.is_productive:
                return format_html('<span style="color: green;">✓ Да</span>')
            else:
                return format_html('<span style="color: red;">✗ Нет</span>')
        return '-'
    is_productive_activity.short_description = 'Продуктивная'
    is_productive_activity.admin_order_field = 'application__is_productive'
    
    actions = ['calculate_missing_durations']
    
    def calculate_missing_durations(self, request, queryset):
        """Рассчитать недостающие длительности"""
        updated = 0
        for activity in queryset:
            if not activity.duration and activity.start_time and activity.end_time:
                activity.duration = activity.end_time - activity.start_time
                activity.save()
                updated += 1
        
        self.message_user(request, f'Длительность рассчитана для {updated} активностей.')
    calculate_missing_durations.short_description = "Рассчитать длительности"

@admin.register(KeyboardActivity)
class KeyboardActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'application_name', 'formatted_timestamp', 'key_pressed']
    list_filter = ['user', 'timestamp', 'application']
    search_fields = ['user__username', 'application__name']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'application')
    
    def application_name(self, obj):
        """Показывает название приложения"""
        return obj.application.name if obj.application else '-'
    application_name.short_description = 'Приложение'
    application_name.admin_order_field = 'application__name'
    
    def formatted_timestamp(self, obj):
        """Форматированное время"""
        if obj.timestamp:
            return obj.timestamp.strftime('%d.%m.%Y %H:%M:%S')
        return '-'
    formatted_timestamp.short_description = 'Время'
    formatted_timestamp.admin_order_field = 'timestamp'

@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'formatted_start_time', 'formatted_end_time', 'duration_display', 'description']
    list_filter = ['user', 'start_time']
    search_fields = ['user__username', 'description']
    date_hierarchy = 'start_time'
    ordering = ['-start_time']
    
    fieldsets = (
        ('Информация о времени', {
            'fields': ('user', 'start_time', 'end_time', 'description')
        }),
    )
    
    def formatted_start_time(self, obj):
        """Форматированное время начала"""
        if obj.start_time:
            return obj.start_time.strftime('%d.%m.%Y %H:%M:%S')
        return '-'
    formatted_start_time.short_description = 'Начало'
    formatted_start_time.admin_order_field = 'start_time'
    
    def formatted_end_time(self, obj):
        """Форматированное время окончания"""
        if obj.end_time:
            return obj.end_time.strftime('%d.%m.%Y %H:%M:%S')
        return '-'
    formatted_end_time.short_description = 'Окончание'
    formatted_end_time.admin_order_field = 'end_time'
    
    def duration_display(self, obj):
        """Показывает длительность"""
        if obj.start_time and obj.end_time:
            duration = obj.end_time - obj.start_time
            return format_duration(duration.total_seconds())
        return '-'
    duration_display.short_description = 'Длительность'

# Настройка заголовков админки
admin.site.site_header = "Tracker33 - Админ панель"
admin.site.site_title = "Tracker33"
admin.site.index_title = "Управление системой отслеживания времени"
