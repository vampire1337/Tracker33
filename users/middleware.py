from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
import logging

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            return JsonResponse({
                'error': 'У вас нет прав для выполнения этого действия',
                'status': 'error'
            }, status=403)
        
        if isinstance(exception, APIException):
            return JsonResponse({
                'error': str(exception),
                'status': 'error'
            }, status=exception.status_code)
        
        logger.error(f"Unhandled exception: {str(exception)}", exc_info=True)
        return JsonResponse({
            'error': 'Произошла внутренняя ошибка сервера',
            'status': 'error'
        }, status=500)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        response.data = {
            'error': str(exc),
            'status': 'error',
            'data': response.data
        }
    
    return response 