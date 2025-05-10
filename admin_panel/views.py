from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Sum
from users.models import CustomUser
from tracking.models import Application, UserActivity, KeyboardActivity, TimeLog
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
import os
import glob
from django.conf import settings
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.db import connection

# Форма для редактирования пользователя суперпользователем
class AdminUserChangeForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False, help_text="Оставьте пустым, если не хотите менять пароль")
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data["password"]:
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

# Миксин для проверки суперпользователя
class SuperUserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

# Главная страница админ-панели
@method_decorator(never_cache, name='dispatch')
class AdminDashboardView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'admin_panel/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Общая статистика
        context['total_users'] = CustomUser.objects.count()
        context['active_users'] = CustomUser.objects.filter(is_active=True).count()
        context['total_applications'] = Application.objects.count()
        context['total_activities'] = UserActivity.objects.count()
        
        # Статистика по пользователям
        context['top_users'] = CustomUser.objects.annotate(
            activity_count=Count('useractivity')
        ).order_by('-activity_count')[:10]
        
        return context

# Список пользователей
class UserListView(LoginRequiredMixin, SuperUserRequiredMixin, ListView):
    model = CustomUser
    template_name = 'admin_panel/user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        return CustomUser.objects.annotate(
            activity_count=Count('useractivity')
        ).order_by('-date_joined')

# Детали пользователя
class UserDetailView(LoginRequiredMixin, SuperUserRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'admin_panel/user_detail.html'
    context_object_name = 'user_obj'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Активность пользователя
        context['activities'] = UserActivity.objects.filter(user=user).order_by('-start_time')[:20]
        
        # Приложения пользователя
        context['applications'] = Application.objects.filter(
            useractivity__user=user
        ).annotate(
            activity_count=Count('useractivity')
        ).order_by('-activity_count').distinct()
        
        return context

# Редактирование пользователя
class UserUpdateView(LoginRequiredMixin, SuperUserRequiredMixin, UpdateView):
    model = CustomUser
    form_class = AdminUserChangeForm
    template_name = 'admin_panel/user_form.html'
    success_url = reverse_lazy('admin_panel:users')
    
    def form_valid(self, form):
        messages.success(self.request, f"Пользователь {form.instance.username} успешно обновлен")
        return super().form_valid(form)

# Список приложений
class ApplicationListView(LoginRequiredMixin, SuperUserRequiredMixin, ListView):
    model = Application
    template_name = 'admin_panel/application_list.html'
    context_object_name = 'applications'
    
    def get_queryset(self):
        return Application.objects.annotate(
            activity_count=Count('useractivity')
        ).order_by('-activity_count')

# Список активности
class ActivityListView(LoginRequiredMixin, SuperUserRequiredMixin, ListView):
    model = UserActivity
    template_name = 'admin_panel/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 50
    
    def get_queryset(self):
        return UserActivity.objects.select_related('user', 'application').order_by('-start_time')

# Просмотр логов
class LogsView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'admin_panel/logs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Путь к директории с логами
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        
        # Получаем список файлов логов
        log_files = glob.glob(os.path.join(log_dir, '*.log'))
        
        # Выбранный файл лога
        selected_log = self.request.GET.get('log')
        
        if selected_log and os.path.exists(os.path.join(log_dir, selected_log)):
            log_path = os.path.join(log_dir, selected_log)
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    # Читаем последние 1000 строк
                    log_content = f.readlines()[-1000:]
                    context['log_content'] = ''.join(log_content)
            except Exception as e:
                context['error'] = f"Ошибка чтения файла лога: {str(e)}"
        
        context['log_files'] = [os.path.basename(f) for f in log_files]
        context['selected_log'] = selected_log
        
        return context

# Просмотр таблиц базы данных
class DatabaseTablesView(LoginRequiredMixin, SuperUserRequiredMixin, TemplateView):
    template_name = 'admin_panel/database_tables.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем список таблиц
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
        
        context['tables'] = [table[0] for table in tables if not table[0].startswith('sqlite_')]
        
        # Выбранная таблица
        selected_table = self.request.GET.get('table')
        
        if selected_table and selected_table in [t[0] for t in tables]:
            # Получаем информацию о столбцах
            with connection.cursor() as cursor:
                cursor.execute(f"PRAGMA table_info({selected_table});")
                columns = cursor.fetchall()
            
            # Получаем данные таблицы (ограничиваем 100 записями)
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {selected_table} LIMIT 100;")
                rows = cursor.fetchall()
            
            context['selected_table'] = selected_table
            context['columns'] = [col[1] for col in columns]
            context['rows'] = rows
            context['total_rows'] = len(rows)
        
        return context 