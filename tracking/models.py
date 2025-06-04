from django.db import models
from users.models import CustomUser
from django.utils import timezone
import secrets

class Application(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tracked_apps', null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name='Название приложения')
    process_name = models.CharField(max_length=255, verbose_name='Имя процесса')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    is_productive = models.BooleanField(default=False, verbose_name='Полезное приложение')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Приложение'
        verbose_name_plural = 'Приложения'
        unique_together = ('user', 'process_name')
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'is_productive']),
            models.Index(fields=['process_name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.process_name})"

class UserActivity(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='Приложение')
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    duration = models.DurationField(verbose_name='Длительность', null=True, blank=True)
    keyboard_presses = models.IntegerField(default=0, verbose_name='Количество нажатий клавиш')
    
    def save(self, *args, **kwargs):
        # Автоматически вычисляем duration при сохранении
        if self.start_time and self.end_time and (self.duration is None):
            self.duration = self.end_time - self.start_time
        super().save(*args, **kwargs)
        
        # Полная очистка кэша после сохранения
        from django.core.cache import cache
        
        # Очищаем кэш пользователя
        cache.delete(f'user_activity_{self.user.id}')
        
        # Очищаем кэш за сегодня и вчера (на случай данных, пересекающих полночь)
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)
        
        cache.delete(f'dashboard_{self.user.id}_{today}')
        cache.delete(f'dashboard_{self.user.id}_{yesterday}')
        
        # Очищаем все возможные кэши статистики
        cache.delete(f'statistics_{self.user.id}_None_')
        for days in [7, 14, 30, 90]:
            cache.delete(f'statistics_{self.user.id}_{days}_')
        
        # Очищаем списки приложений
        cache.delete(f'application_list_{self.user.id}')

    class Meta:
        verbose_name = 'Активность пользователя'
        verbose_name_plural = 'Активности пользователей'
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['user', 'end_time']),
            models.Index(fields=['application', 'start_time']),
            models.Index(fields=['application', 'end_time']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.application.name}"

class KeyboardActivity(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    timestamp = models.DateTimeField(verbose_name='Время')
    key_pressed = models.CharField(max_length=50, verbose_name='Нажатая клавиша')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='Приложение')

    class Meta:
        verbose_name = 'Активность клавиатуры'
        verbose_name_plural = 'Активности клавиатуры'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['application', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.key_pressed}"

class TimeLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='timelogs')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['user', 'end_time']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.start_time.date()}"

    @property
    def duration(self):
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            hours = duration.total_seconds() / 3600
            return f"{round(hours, 2)} hours"
        return "N/A"

class QRToken(models.Model):
    """Временные токены для QR-аутентификации"""
    token = models.CharField(max_length=64, unique=True, verbose_name='Токен')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Пользователь')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создан')
    expires_at = models.DateTimeField(verbose_name='Истекает')
    is_used = models.BooleanField(default=False, verbose_name='Использован')
    client_info = models.JSONField(default=dict, blank=True, verbose_name='Информация о клиенте')
    
    class Meta:
        verbose_name = 'QR Токен'
        verbose_name_plural = 'QR Токены'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_used']),
        ]
    
    def __str__(self):
        return f"QR Token {self.token[:8]}... - {self.user.username if self.user else 'Анонимный'}"
    
    @classmethod
    def generate_token(cls, user=None, expires_minutes=10):
        """Генерирует новый QR токен"""
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timezone.timedelta(minutes=expires_minutes)
        
        return cls.objects.create(
            token=token,
            user=user,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """Проверяет действительность токена"""
        return (
            not self.is_used and 
            timezone.now() < self.expires_at
        )
    
    def use_token(self):
        """Отмечает токен как использованный"""
        self.is_used = True
        self.save()
