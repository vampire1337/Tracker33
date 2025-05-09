from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.generic import FormView
from django.urls import reverse_lazy
from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.exceptions import ValidationError

User = get_user_model()

class SimplePasswordResetForm(forms.Form):
    username = forms.CharField(label="Имя пользователя")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким именем не найден")
        return username


class SimplePasswordResetView(FormView):
    template_name = 'account/simple_password_reset.html'
    form_class = SimplePasswordResetForm
    success_url = reverse_lazy('simple_password_reset_confirm')
    
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        user = User.objects.get(username=username)
        
        # Генерируем токен и сохраняем его в сессии
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        self.request.session['reset_user_uid'] = uid
        self.request.session['reset_user_token'] = token
        
        return super().form_valid(form)


class SimplePasswordResetConfirmView(FormView):
    template_name = 'account/simple_password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('login')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        
        # Проверяем, есть ли информация о пользователе в сессии
        uid = self.request.session.get('reset_user_uid')
        token = self.request.session.get('reset_user_token')
        
        if not (uid and token):
            return kwargs
        
        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)
            
            # Проверяем валидность токена
            if default_token_generator.check_token(user, token):
                kwargs['user'] = user
                return kwargs
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            pass
        
        # Если не удалось получить пользователя или токен неверный, очищаем сессию
        if 'reset_user_uid' in self.request.session:
            del self.request.session['reset_user_uid']
        if 'reset_user_token' in self.request.session:
            del self.request.session['reset_user_token']
        
        return kwargs
    
    def get(self, request, *args, **kwargs):
        form_kwargs = self.get_form_kwargs()
        if 'user' not in form_kwargs:
            messages.error(request, "Неверная ссылка для сброса пароля или срок её действия истёк.")
            return redirect('simple_password_reset')
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Пароль успешно изменен. Теперь вы можете войти в систему.")
        
        # Очищаем сессию после успешной смены пароля
        if 'reset_user_uid' in self.request.session:
            del self.request.session['reset_user_uid']
        if 'reset_user_token' in self.request.session:
            del self.request.session['reset_user_token']
        
        return super().form_valid(form) 