from django.contrib import admin
from .models import Application, UserActivity, KeyboardActivity

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'process_name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'process_name')

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'application', 'start_time', 'end_time', 'duration')
    list_filter = ('user', 'application', 'start_time')
    search_fields = ('user__username', 'application__name')
    readonly_fields = ('duration',)

@admin.register(KeyboardActivity)
class KeyboardActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'application', 'timestamp', 'key_pressed')
    list_filter = ('user', 'application', 'timestamp')
    search_fields = ('user__username', 'application__name', 'key_pressed')
