from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import time

def health_check(request):
    """
    Health check endpoint для Railway и других платформ
    """
    health_data = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '2.0.0',
        'environment': 'production' if not settings.DEBUG else 'development'
    }
    
    # Проверка базы данных
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_data['database'] = 'connected'
    except Exception as e:
        health_data['database'] = f'error: {str(e)}'
        health_data['status'] = 'unhealthy'
    
    # Проверка кэша (если настроен)
    try:
        cache.set('health_check', 'ok', 30)
        if cache.get('health_check') == 'ok':
            health_data['cache'] = 'connected'
        else:
            health_data['cache'] = 'error'
    except Exception as e:
        health_data['cache'] = f'error: {str(e)}'
    
    status_code = 200 if health_data['status'] == 'healthy' else 503
    return JsonResponse(health_data, status=status_code)
