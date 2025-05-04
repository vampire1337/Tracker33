import logging
import json
from django.conf import settings
from datetime import datetime

# Создаем логгеры для разных типов событий
activity_logger = logging.getLogger('tracking.activity')
performance_logger = logging.getLogger('tracking.performance')
error_logger = logging.getLogger('tracking.error')

class ActivityLogger:
    @staticmethod
    def log_user_activity(user, activity_type, details):
        """
        Логирует активность пользователя
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user.id,
            'username': user.username,
            'activity_type': activity_type,
            'details': details
        }
        activity_logger.info(json.dumps(log_data))

    @staticmethod
    def log_application_activity(user, application, action):
        """
        Логирует действия с приложениями
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user.id,
            'username': user.username,
            'application_id': application.id,
            'application_name': application.name,
            'action': action
        }
        activity_logger.info(json.dumps(log_data))

class PerformanceLogger:
    @staticmethod
    def log_query_performance(view_name, query_time, query_type, details=None):
        """
        Логирует производительность запросов
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'view_name': view_name,
            'query_time': query_time,
            'query_type': query_type,
            'details': details
        }
        performance_logger.info(json.dumps(log_data))

    @staticmethod
    def log_view_performance(view_name, response_time, status_code):
        """
        Логирует производительность представлений
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'view_name': view_name,
            'response_time': response_time,
            'status_code': status_code
        }
        performance_logger.info(json.dumps(log_data))

class ErrorLogger:
    @staticmethod
    def log_error(error_type, error_message, details=None):
        """
        Логирует ошибки
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error_message),
            'details': details
        }
        error_logger.error(json.dumps(log_data))

    @staticmethod
    def log_validation_error(model_name, field_name, error_message):
        """
        Логирует ошибки валидации
        """
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': 'ValidationError',
            'model': model_name,
            'field': field_name,
            'message': str(error_message)
        }
        error_logger.error(json.dumps(log_data)) 