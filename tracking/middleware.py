from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from .exceptions import (
    ApplicationAlreadyExists,
    InvalidTimeRange,
    ApplicationNotFound,
    UserActivityNotFound,
    InvalidActivityData
)
from .logging import PerformanceLogger, ErrorLogger
from .alerts import AlertManager
import time
from django.db import connection
from django.conf import settings

class PerformanceMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Время начала обработки запроса
        start_time = time.time()

        # Количество запросов к БД до обработки запроса
        n_queries_before = len(connection.queries)

        response = self.get_response(request)

        # Время окончания обработки запроса
        end_time = time.time()

        # Количество запросов к БД после обработки запроса
        n_queries_after = len(connection.queries)

        # Вычисляем время выполнения и количество запросов
        execution_time = end_time - start_time
        n_queries = n_queries_after - n_queries_before

        # Логируем информацию о производительности
        if hasattr(request, 'resolver_match') and request.resolver_match:
            view_name = request.resolver_match.view_name
        else:
            view_name = 'unknown'

        PerformanceLogger.log_view_performance(
            view_name=view_name,
            response_time=execution_time,
            status_code=response.status_code
        )

        # Если время выполнения превышает порог, логируем предупреждение и отправляем алерт
        if execution_time > getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1.0):
            details = {
                'view_name': view_name,
                'method': request.method,
                'path': request.path,
                'n_queries': n_queries
            }
            
            ErrorLogger.log_error(
                error_type='SlowRequest',
                error_message=f'Slow request detected: {execution_time:.2f}s',
                details=details
            )

            AlertManager.performance_alert(
                view_name=view_name,
                response_time=execution_time,
                threshold=settings.SLOW_REQUEST_THRESHOLD
            )

        # Проверяем медленные запросы к БД
        slow_queries = []
        for query in connection.queries[n_queries_before:]:
            query_time = float(query.get('time', 0))
            if query_time > getattr(settings, 'SLOW_QUERY_THRESHOLD', 0.1):
                slow_queries.append({
                    'sql': query.get('sql'),
                    'time': query_time
                })

        if slow_queries:
            ErrorLogger.log_error(
                error_type='SlowQueries',
                error_message=f'Detected {len(slow_queries)} slow queries',
                details={'queries': slow_queries}
            )

            AlertManager.performance_alert(
                view_name=view_name,
                response_time=max(q['time'] for q in slow_queries),
                threshold=settings.SLOW_QUERY_THRESHOLD
            )

        return response

def custom_exception_handler(exc, context):
    # Сначала вызываем стандартный обработчик исключений DRF
    response = exception_handler(exc, context)

    # Если это ValidationError из Django, преобразуем его в DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(detail=exc.message)

    # Логируем ошибку
    error_details = {'context': str(context)}
    if hasattr(exc, 'get_full_details'):
        error_details.update(exc.get_full_details())

    ErrorLogger.log_error(
        error_type=exc.__class__.__name__,
        error_message=str(exc),
        details=error_details
    )

    # Отправляем алерт для серьезных ошибок
    if isinstance(exc, (ApplicationNotFound, UserActivityNotFound)):
        AlertManager.error_alert(
            error_type=exc.__class__.__name__,
            error_message=str(exc),
            details=error_details
        )

    # Если это одно из наших пользовательских исключений
    if isinstance(exc, (ApplicationAlreadyExists, InvalidTimeRange, 
                       ApplicationNotFound, UserActivityNotFound, InvalidActivityData)):
        data = {
            'status': 'error',
            'code': exc.default_code,
            'detail': exc.detail
        }
        return Response(data, status=exc.status_code)

    # Если это стандартное исключение DRF
    if response is not None:
        data = {
            'status': 'error',
            'code': response.status_code,
            'detail': response.data
        }
        response.data = data
        return response

    # Для всех остальных исключений
    AlertManager.error_alert(
        error_type='UnhandledException',
        error_message='Произошла внутренняя ошибка сервера.',
        details={'exception': str(exc)}
    )

    return Response(
        {
            'status': 'error',
            'code': 'internal_error',
            'detail': 'Произошла внутренняя ошибка сервера.'
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    ) 