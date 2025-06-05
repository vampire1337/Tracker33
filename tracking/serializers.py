from rest_framework import serializers
from .models import Application, UserActivity, KeyboardActivity, TimeLog

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('id', 'name', 'process_name', 'is_active', 'is_productive', 'user')
        read_only_fields = ('id', 'user')

    def validate(self, data):
        user = self.context['request'].user
        process_name = data.get('process_name')
        
        # Проверяем, не существует ли уже приложение с таким process_name для пользователя
        if Application.objects.filter(user=user, process_name=process_name).exists():
            raise serializers.ValidationError(
                {'process_name': 'Приложение с таким именем процесса уже отслеживается.'}
            )
        
        return data

class UserActivitySerializer(serializers.ModelSerializer):
    # Делаем поле application необязательным для безопасной обработки несуществующих ID
    application = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.none(),  # Пустой queryset по умолчанию
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = UserActivity
        fields = ('id', 'user', 'application', 'start_time', 'end_time', 'duration', 'keyboard_presses')
        read_only_fields = ('id', 'user', 'duration')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем queryset для пользователя из контекста, если доступен
        if 'context' in kwargs and 'request' in kwargs['context']:
            user = kwargs['context']['request'].user
            if user and user.is_authenticated:
                self.fields['application'].queryset = Application.objects.filter(user=user)
    
    def validate_application(self, value):
        """Кастомная валидация для поля application"""
        if value is None:
            # Если application не передан, это нормально - будет создан в perform_create
            return value
            
        # Проверяем, что приложение принадлежит текущему пользователю
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            if value.user != user:
                raise serializers.ValidationError("Приложение не принадлежит текущему пользователю")
        
        return value

class KeyboardActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyboardActivity
        fields = ('id', 'user', 'timestamp', 'key_pressed', 'application')
        read_only_fields = ('id', 'user')

class TimeLogSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()

    class Meta:
        model = TimeLog
        fields = ['id', 'user', 'start_time', 'end_time', 'description', 'duration']
        read_only_fields = ['user', 'duration']

    def get_duration(self, obj):
        if obj.end_time and obj.start_time:
            duration = obj.end_time - obj.start_time
            hours = duration.total_seconds() / 3600
            return round(hours, 2)
        return None

    def validate(self, data):
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("End time must be after start time")
        return data 