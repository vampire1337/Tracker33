from rest_framework.exceptions import APIException
from rest_framework import status

class ApplicationAlreadyExists(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Приложение с таким именем процесса уже существует.'
    default_code = 'application_exists'

class InvalidTimeRange(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Неверный временной диапазон.'
    default_code = 'invalid_time_range'

class ApplicationNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Приложение не найдено.'
    default_code = 'application_not_found'

class UserActivityNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Активность пользователя не найдена.'
    default_code = 'user_activity_not_found'

class InvalidActivityData(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Неверные данные активности.'
    default_code = 'invalid_activity_data' 