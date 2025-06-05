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
    
    def to_internal_value(self, data):
        """Переопределяем для обработки несуществующих ID приложений"""
        # Сохраняем оригинальный ID приложения для дальнейшей обработки
        original_app_id = data.get('application')
        
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            # Проверяем, является ли ошибка связанной с несуществующим приложением
            if 'application' in e.detail and original_app_id:
                error_msg = str(e.detail['application'][0])
                if 'Недопустимый первичный ключ' in error_msg or 'does not exist' in error_msg:
                    # Убираем application из данных и помечаем для создания
                    data_copy = data.copy()
                    data_copy.pop('application', None)
                    
                    # Сохраняем ID для дальнейшего использования
                    internal_data = super().to_internal_value(data_copy)
                    internal_data['_missing_app_id'] = original_app_id
                    return internal_data
            
            # Если это другая ошибка, пробрасываем дальше
            raise
    
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
    
    def create(self, validated_data):
        """Переопределяем create для обработки _missing_app_id"""
        # Убираем служебные поля
        missing_app_id = validated_data.pop('_missing_app_id', None)
        
        # Если есть missing_app_id, но нет application, создаем приложение
        if missing_app_id and not validated_data.get('application'):
            user = validated_data['user']
            if isinstance(user, int):
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=user)
            
            process_name = f"unknown_app_{missing_app_id}"
            
            # Проверяем существующее приложение
            existing_app = Application.objects.filter(
                user=user,
                process_name=process_name
            ).first()
            
            if existing_app:
                validated_data['application'] = existing_app
            else:
                # Создаем новое приложение
                new_app = Application.objects.create(
                    user=user,
                    name=f"Unknown Application {missing_app_id}",
                    process_name=process_name,
                    is_active=True,
                    is_productive=False
                )
                validated_data['application'] = new_app
        
        return super().create(validated_data)

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