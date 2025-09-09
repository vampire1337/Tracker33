# 📡 API Documentation - Tracker33

## Обзор

Tracker33 предоставляет RESTful API для взаимодействия с десктопным клиентом и внешними системами. API использует JSON для обмена данными и токенную аутентификацию.

## 🔐 Аутентификация

### Получение токена

**Endpoint:** `POST /api-token-auth/`

**Запрос:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Ответ:**
```json
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### Использование токена

Включайте токен в заголовок Authorization для всех запросов:

```http
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## 📊 Эндпоинты активности

### Получение активности пользователя

**Endpoint:** `GET /api/activity/`

**Параметры запроса:**
- `date_from` (optional) - дата начала в формате YYYY-MM-DD
- `date_to` (optional) - дата окончания в формате YYYY-MM-DD
- `application` (optional) - ID приложения для фильтрации

**Пример запроса:**
```http
GET /api/activity/?date_from=2024-01-01&date_to=2024-01-31
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Ответ:**
```json
{
    "count": 150,
    "next": "http://localhost:8001/api/activity/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "application": {
                "id": 1,
                "name": "Google Chrome",
                "process_name": "chrome.exe",
                "is_productive": true
            },
            "start_time": "2024-01-15T09:00:00Z",
            "end_time": "2024-01-15T09:30:00Z",
            "duration": "0:30:00",
            "keyboard_presses": 156
        }
    ]
}
```

### Отправка данных активности

**Endpoint:** `POST /api/activity/`

**Тело запроса:**
```json
{
    "activities": [
        {
            "application_name": "Google Chrome",
            "process_name": "chrome.exe",
            "start_time": "2024-01-15T09:00:00Z",
            "end_time": "2024-01-15T09:30:00Z",
            "keyboard_presses": 156
        },
        {
            "application_name": "Visual Studio Code",
            "process_name": "Code.exe",
            "start_time": "2024-01-15T09:30:00Z",
            "end_time": "2024-01-15T10:00:00Z",
            "keyboard_presses": 342
        }
    ]
}
```

**Ответ:**
```json
{
    "status": "success",
    "created": 2,
    "message": "Activities saved successfully"
}
```

## 📱 Эндпоинты приложений

### Получение списка приложений

**Endpoint:** `GET /api/applications/`

**Ответ:**
```json
{
    "count": 25,
    "results": [
        {
            "id": 1,
            "name": "Google Chrome",
            "process_name": "chrome.exe",
            "is_active": true,
            "is_productive": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-15T12:00:00Z"
        }
    ]
}
```

### Переключение продуктивности приложения

**Endpoint:** `POST /api/toggle-productive/`

**Тело запроса:**
```json
{
    "app_id": 1,
    "is_productive": true
}
```

**Ответ:**
```json
{
    "status": "success",
    "message": "Application productivity status updated",
    "app_id": 1,
    "is_productive": true
}
```

## 📈 Эндпоинты статистики

### Получение общей статистики

**Endpoint:** `GET /api/statistics/`

**Параметры запроса:**
- `days` (optional) - количество дней для анализа (7, 14, 30, 90)

**Пример запроса:**
```http
GET /api/statistics/?days=30
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Ответ:**
```json
{
    "total_time": "120:45:30",
    "total_time_seconds": 434730,
    "productive_time": "85:20:15",
    "productive_time_seconds": 307215,
    "productivity_percentage": 70.5,
    "keyboard_activity": 15420,
    "unique_applications": 12,
    "daily_average": "4:01:30",
    "apps": [
        {
            "id": 1,
            "name": "Visual Studio Code",
            "total_time": "45:30:00",
            "percentage": 37.5,
            "is_productive": true
        },
        {
            "id": 2,
            "name": "Google Chrome",
            "total_time": "30:15:30",
            "percentage": 25.0,
            "is_productive": true
        }
    ],
    "daily_data": [
        {
            "date": "2024-01-15",
            "total_seconds": 28800,
            "productive_seconds": 21600,
            "keyboard_presses": 1250
        }
    ]
}
```

### Получение статистики по часам

**Endpoint:** `GET /api/statistics/hourly/`

**Ответ:**
```json
{
    "hourly_data": [
        {
            "hour": 9,
            "total_seconds": 3600,
            "productive_seconds": 2700,
            "keyboard_presses": 150
        },
        {
            "hour": 10,
            "total_seconds": 3600,
            "productive_seconds": 3200,
            "keyboard_presses": 180
        }
    ]
}
```

## 👤 Эндпоинты пользователей

### Получение профиля пользователя

**Endpoint:** `GET /api/profile/`

**Ответ:**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "department": "IT",
    "position": "Developer",
    "is_active_tracking": true,
    "date_joined": "2024-01-01T00:00:00Z"
}
```

### Обновление настроек отслеживания

**Endpoint:** `PATCH /api/profile/`

**Тело запроса:**
```json
{
    "is_active_tracking": false
}
```

## 📝 Эндпоинты логов

### Получение логов активности

**Endpoint:** `GET /api/logs/`

**Параметры запроса:**
- `date_from` (optional) - дата начала
- `date_to` (optional) - дата окончания
- `application` (optional) - ID приложения
- `page` (optional) - номер страницы
- `page_size` (optional) - размер страницы (по умолчанию 50)

**Ответ:**
```json
{
    "count": 500,
    "next": "http://localhost:8001/api/logs/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "start_time": "2024-01-15T09:00:00Z",
            "end_time": "2024-01-15T09:30:00Z",
            "duration": "0:30:00",
            "application": {
                "name": "Visual Studio Code",
                "is_productive": true
            },
            "keyboard_presses": 156
        }
    ]
}
```

## 🔍 Эндпоинт здоровья системы

### Проверка состояния API

**Endpoint:** `GET /api/health/`

**Ответ:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T12:00:00Z",
    "version": "2.0.0",
    "database": "connected",
    "cache": "connected"
}
```

## 📊 Экспорт данных

### Экспорт статистики

**Endpoint:** `GET /api/export/statistics/`

**Параметры запроса:**
- `format` - формат экспорта (json, csv, xlsx)
- `days` (optional) - количество дней

**Пример запроса:**
```http
GET /api/export/statistics/?format=csv&days=30
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

**Ответ:** Файл в указанном формате

### Экспорт активности

**Endpoint:** `GET /api/export/activity/`

**Параметры запроса:**
- `format` - формат экспорта (json, csv, xlsx)
- `date_from` (optional) - дата начала
- `date_to` (optional) - дата окончания

## 🚨 Коды ошибок

### HTTP статус коды

- `200` - Успешный запрос
- `201` - Ресурс создан
- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Ресурс не найден
- `429` - Слишком много запросов
- `500` - Внутренняя ошибка сервера

### Примеры ошибок

**401 Unauthorized:**
```json
{
    "detail": "Invalid token."
}
```

**400 Bad Request:**
```json
{
    "error": "Invalid date format",
    "details": {
        "date_from": ["Enter a valid date."]
    }
}
```

**429 Too Many Requests:**
```json
{
    "detail": "Request was throttled. Expected available in 60 seconds."
}
```

## 🔒 Ограничения скорости

API имеет следующие ограничения:

- **Анонимные пользователи**: 100 запросов/час
- **Авторизованные пользователи**: 1000 запросов/час
- **Отправка данных активности**: 60 запросов/минуту

## 📱 Примеры использования

### Python (requests)

```python
import requests
import json

# Получение токена
auth_response = requests.post('http://localhost:8001/api-token-auth/', {
    'username': 'your_username',
    'password': 'your_password'
})
token = auth_response.json()['token']

# Настройка заголовков
headers = {
    'Authorization': f'Token {token}',
    'Content-Type': 'application/json'
}

# Получение статистики
stats_response = requests.get(
    'http://localhost:8001/api/statistics/?days=7',
    headers=headers
)
statistics = stats_response.json()
print(f"Продуктивность: {statistics['productivity_percentage']}%")

# Отправка данных активности
activity_data = {
    'activities': [
        {
            'application_name': 'PyCharm',
            'process_name': 'pycharm64.exe',
            'start_time': '2024-01-15T10:00:00Z',
            'end_time': '2024-01-15T11:00:00Z',
            'keyboard_presses': 500
        }
    ]
}

activity_response = requests.post(
    'http://localhost:8001/api/activity/',
    headers=headers,
    data=json.dumps(activity_data)
)
print(activity_response.json())
```

### JavaScript (fetch)

```javascript
// Получение токена
async function getToken(username, password) {
    const response = await fetch('http://localhost:8001/api-token-auth/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    });
    const data = await response.json();
    return data.token;
}

// Получение статистики
async function getStatistics(token, days = 7) {
    const response = await fetch(`http://localhost:8001/api/statistics/?days=${days}`, {
        headers: {
            'Authorization': `Token ${token}`
        }
    });
    return await response.json();
}

// Использование
const token = await getToken('your_username', 'your_password');
const stats = await getStatistics(token, 30);
console.log(`Продуктивность: ${stats.productivity_percentage}%`);
```

### cURL

```bash
# Получение токена
curl -X POST http://localhost:8001/api-token-auth/ \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'

# Получение статистики
curl -X GET "http://localhost:8001/api/statistics/?days=7" \
     -H "Authorization: Token your_token_here"

# Отправка данных активности
curl -X POST http://localhost:8001/api/activity/ \
     -H "Authorization: Token your_token_here" \
     -H "Content-Type: application/json" \
     -d '{
       "activities": [
         {
           "application_name": "Terminal",
           "process_name": "bash",
           "start_time": "2024-01-15T10:00:00Z",
           "end_time": "2024-01-15T11:00:00Z",
           "keyboard_presses": 200
         }
       ]
     }'
```

## 📞 Поддержка

Если у вас есть вопросы по API:

1. Проверьте эту документацию
2. Изучите примеры кода
3. Проверьте коды ошибок
4. Создайте issue в репозитории проекта
