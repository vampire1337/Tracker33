# 📚 TRACKER33: ПОЛНАЯ ТЕХНИЧЕСКАЯ ДОКУМЕНТАЦИЯ

**Система мониторинга и учета рабочего времени**  
*Дипломный проект*

---

## 📋 СОДЕРЖАНИЕ

1. [Введение и архитектура](#введение)
2. [Backend система (Django)](#backend)
3. [Desktop клиент (PyQt6)](#desktop)
4. [REST API интерфейс](#api)
5. [База данных и модели](#database)
6. [Система аутентификации](#auth)
7. [Frontend веб-интерфейс](#frontend)
8. [Безопасность системы](#security)
9. [Производительность и мониторинг](#performance)
10. [Развертывание системы](#deployment)
11. [Планы развития](#future)

---

## 1. ВВЕДЕНИЕ И АРХИТЕКТУРА {#введение}

### 1.1 Описание проекта

Tracker33 представляет собой комплексную систему мониторинга рабочего времени, состоящую из веб-приложения на Django и desktop клиента на PyQt6. Система автоматически отслеживает активность пользователя, анализирует использование приложений и предоставляет детальную статистику продуктивности.

### 1.2 Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Desktop       │    │   Web Server    │    │   Database      │
│   Client        │◄──►│   (Django)      │◄──►│   (SQLite)      │
│   (PyQt6)       │    │   + REST API    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   OS Activity   │    │   Web Interface │
│   Monitoring    │    │   (Bootstrap)   │
└─────────────────┘    └─────────────────┘
```

### 1.3 Ключевые особенности

- **Автоматическое отслеживание**: Мониторинг активных приложений без участия пользователя
- **Система токенов**: Безопасная аутентификация через JWT токены
- **Реальное время**: Синхронизация данных каждые 60 секунд
- **Кроссплатформенность**: Поддержка Windows, Linux, macOS
- **Веб-интерфейс**: Современный dashboard с аналитикой
- **Системный трей**: Незаметная работа в фоне

---

## 2. BACKEND СИСТЕМА (DJANGO) {#backend}

### 2.1 Структура Django проекта

```
Tracker33/
├── tracking/          # Основное приложение
│   ├── models.py     # Модели данных
│   ├── views.py      # REST API endpoints
│   ├── serializers.py # DRF сериализаторы
│   ├── admin.py      # Админ-панель
│   └── middleware.py # Middleware для производительности
├── users/            # Пользователи и аутентификация
├── admin_panel/      # Административная панель
└── Tracker33/        # Настройки проекта
    ├── settings.py   # Конфигурация Django
    └── urls.py       # URL маршрутизация
```

### 2.2 Основные модели данных

#### Application Model
```python
class Application(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    process_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_productive = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
```

#### UserActivity Model
```python
class UserActivity(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.DurationField()
    keyboard_presses = models.IntegerField(default=0)
```

### 2.3 REST API Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/token/` | POST | Получение JWT токена |
| `/api/activities/` | POST | Отправка данных активности |
| `/api/applications/` | GET/POST | Управление приложениями |
| `/api/statistics/` | GET | Получение статистики |
| `/api/user-profile/` | GET | Профиль пользователя |

### 2.4 Система кэширования

Реализован многоуровневый кэш для оптимизации производительности:

```python
# Кэш активности пользователя
cache.set(f'user_activity_{user_id}', data, timeout=300)

# Кэш статистики
cache.set(f'statistics_{user_id}_{days}', stats, timeout=900)

# Автоочистка кэша при изменении данных
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    cache.delete(f'user_activity_{self.user.id}')
```

---

## 3. DESKTOP КЛИЕНТ (PyQt6) {#desktop}

### 3.1 Архитектура клиента

Desktop клиент построен на PyQt6 с многопоточной архитектурой:

```
┌─────────────────┐
│   MainWindow    │ ◄─── GUI Thread
│   (GUI)         │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ TrackerWorker   │ ◄─── Background Thread
│ (Monitoring)    │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ System APIs     │ ◄─── OS Integration
│ (Win32/X11)     │
└─────────────────┘
```

### 3.2 Мониторинг системной активности

#### Отслеживание активных окон
```python
def get_active_window(self) -> Optional[Dict[str, str]]:
    try:
        if platform.system() == "Windows":
            hwnd = win32gui.GetForegroundWindow()
            window_text = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return {
                "title": window_text,
                "process_name": process.name()
            }
    except Exception as e:
        return None
```

#### Подсчет нажатий клавиш
```python
def setup_listeners(self):
    self.keyboard_listener = keyboard.Listener(
        on_press=self._on_keyboard_press
    )
    self.keyboard_listener.start()

def _on_keyboard_press(self, key):
    self.keyboard_count += 1
```

### 3.3 Современный UI/UX

Клиент использует темную тему с современным дизайном:

```python
DARK_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', Calibri, sans-serif;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #667eea, stop:1 #764ba2);
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: bold;
}
"""
```

### 3.4 Системный трей

Клиент работает в системном трее с контекстным меню:

```python
def create_tray_icon(self):
    if QSystemTrayIcon.isSystemTrayAvailable():
        self.tray_icon = QSystemTrayIcon(self.create_icon(), self)
        tray_menu = QMenu()
        
        show_action = QAction("Показать", self)
        quit_action = QAction("Выход", self)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
```

---

## 4. REST API ИНТЕРФЕЙС {#api}

### 4.1 Аутентификация API

Система использует Token Authentication с JWT:

```python
# Получение токена
POST /api/token/
{
    "username": "user",
    "password": "password"
}

# Ответ
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user_id": 1
}

# Использование токена
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 4.2 Отправка данных активности

```python
POST /api/activities/
{
    "application": 15,
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:05:00Z",
    "keyboard_presses": 150
}
```

### 4.3 Получение статистики

```python
GET /api/statistics/?days=7
{
    "total_time": "25:30:00",
    "productive_time": "18:45:00",
    "applications": [
        {
            "name": "Visual Studio Code",
            "time": "08:30:00",
            "percentage": 33.5,
            "is_productive": true
        }
    ]
}
```

---

## 5. БАЗА ДАННЫХ И МОДЕЛИ {#database}

### 5.1 Схема базы данных

```sql
-- Пользователи
CREATE TABLE users_customuser (
    id INTEGER PRIMARY KEY,
    username VARCHAR(150) UNIQUE,
    email VARCHAR(254),
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    date_joined DATETIME
);

-- Приложения
CREATE TABLE tracking_application (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    process_name VARCHAR(255),
    is_active BOOLEAN DEFAULT 1,
    is_productive BOOLEAN DEFAULT 0,
    user_id INTEGER REFERENCES users_customuser(id)
);

-- Активность пользователей
CREATE TABLE tracking_useractivity (
    id INTEGER PRIMARY KEY,
    start_time DATETIME,
    end_time DATETIME,
    duration INTEGER,
    keyboard_presses INTEGER DEFAULT 0,
    user_id INTEGER REFERENCES users_customuser(id),
    application_id INTEGER REFERENCES tracking_application(id)
);
```

### 5.2 Индексы для производительности

```python
class Meta:
    indexes = [
        models.Index(fields=['user', 'start_time']),
        models.Index(fields=['user', 'end_time']),
        models.Index(fields=['application', 'start_time']),
        models.Index(fields=['user', 'is_active']),
        models.Index(fields=['user', 'is_productive']),
    ]
```

### 5.3 Автоматическая очистка кэша

```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    
    # Очищаем все связанные кэши
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    cache.delete(f'dashboard_{self.user.id}_{today}')
    cache.delete(f'dashboard_{self.user.id}_{yesterday}')
    
    for days in [7, 14, 30, 90]:
        cache.delete(f'statistics_{self.user.id}_{days}_')
```

---

## 6. СИСТЕМА АУТЕНТИФИКАЦИИ {#auth}

### 6.1 Текущая система токенов

Используется Django REST Framework Token Authentication:

```python
from rest_framework.authtoken.models import Token

@api_view(['POST'])
def obtain_auth_token(request):
    serializer = AuthTokenSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id})
```

### 6.2 Проверка токенов в клиенте

```python
async def authenticate(self):
    login_data = {
        'username': self.config['username'],
        'password': self.config['password']
    }
    
    async with session.post(auth_url, json=login_data) as response:
        if response.status == 200:
            data = await response.json()
            self.auth_token = data.get('token')
            return True
```

### 6.3 Безопасность токенов

- Токены хранятся в зашифрованном config.json
- Автоматическая проверка валидности каждые 5 минут
- Реаутентификация при истечении токена
- Защита от CSRF атак через Origin headers

---

## 7. FRONTEND ВЕБ-ИНТЕРФЕЙС {#frontend}

### 7.1 Dashboard интерфейс

Современный responsive веб-интерфейс с Bootstrap 5:

```html
<!-- Главная панель -->
<div class="row">
    <div class="col-md-8">
        <canvas id="activityChart" width="400" height="200"></canvas>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5>Сегодня</h5>
                <p class="h3">{{total_time}}</p>
            </div>
        </div>
    </div>
</div>
```

### 7.2 Аналитические графики

Использование Chart.js для визуализации:

```javascript
// График активности по времени
const activityChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: timeLabels,
        datasets: [{
            label: 'Активность',
            data: activityData,
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)'
        }]
    }
});

// Круговая диаграмма приложений
const appsChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: appNames,
        datasets: [{
            data: timeData,
            backgroundColor: colorPalette
        }]
    }
});
```

### 7.3 Фильтрация данных

```html
<!-- Фильтры временного периода -->
<div class="btn-group" role="group">
    <button type="button" class="btn btn-outline-primary" data-period="7">
        7 дней
    </button>
    <button type="button" class="btn btn-outline-primary" data-period="30">
        30 дней
    </button>
    <button type="button" class="btn btn-outline-primary" data-period="90">
        90 дней
    </button>
</div>
```

---

## 8. БЕЗОПАСНОСТЬ СИСТЕМЫ {#security}

### 8.1 Аутентификация и авторизация

- **Django CSRF Protection**: Защита от межсайтовых запросов
- **Token Authentication**: Безопасная аутентификация API
- **Permissions**: Доступ только к собственным данным пользователя
- **Password Hashing**: Использование Django pbkdf2_sha256

### 8.2 CORS настройки

```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
    'x-csrftoken',
]
```

### 8.3 Валидация данных

```python
class ActivitySerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError(
                "Время окончания должно быть больше времени начала"
            )
        return data
```

---

## 9. ПРОИЗВОДИТЕЛЬНОСТЬ И МОНИТОРИНГ {#performance}

### 9.1 Middleware для мониторинга

```python
class PerformanceMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        
        duration = time.time() - start_time
        if duration > settings.SLOW_REQUEST_THRESHOLD:
            logger.warning(f"Медленный запрос: {request.path} - {duration:.2f}s")
        
        return response
```

### 9.2 Логирование системы

```python
LOGGING = {
    'handlers': {
        'file_activity': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/activity.log',
        },
        'file_performance': {
            'level': 'INFO', 
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/performance.log',
        },
    },
    'loggers': {
        'tracking.performance': {
            'handlers': ['file_performance'],
            'level': 'INFO',
        },
    },
}
```

### 9.3 Оптимизация запросов

```python
# Используем select_related для оптимизации
def get_activities(self, user):
    return UserActivity.objects.select_related(
        'application', 'user'
    ).filter(
        user=user
    ).order_by('-start_time')

# Агрегация на уровне БД
stats = UserActivity.objects.filter(
    user=user,
    start_time__date=today
).aggregate(
    total_time=Sum('duration'),
    total_keystrokes=Sum('keyboard_presses')
)
```

---

## 10. РАЗВЕРТЫВАНИЕ СИСТЕМЫ {#deployment}

### 10.1 Системные требования

**Серверная часть:**
- Python 3.9+
- Django 5.0+
- SQLite/PostgreSQL
- 512MB RAM
- 1GB дискового пространства

**Клиентская часть:**
- Windows 10/11, Linux, macOS
- PyQt6
- 100MB дискового пространства
- Права администратора (для мониторинга)

### 10.2 Установка сервера

```bash
# Клонирование репозитория
git clone https://github.com/user/Tracker33.git
cd Tracker33

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка базы данных
python manage.py migrate
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver 0.0.0.0:8000
```

### 10.3 Сборка desktop клиента

```python
# build_exe.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'modern_client.py',
    '--onefile',
    '--windowed',
    '--icon=tracker33_icon.ico',
    '--name=Tracker33',
    '--add-data=config.json;.',
    '--hidden-import=win32gui',
    '--hidden-import=win32process',
])
```

### 10.4 Автоматический запуск

```python
# Добавление в автозагрузку Windows
import winreg

def add_to_startup():
    key = winreg.HKEY_CURRENT_USER
    key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    with winreg.OpenKey(key, key_value, 0, winreg.KEY_ALL_ACCESS) as reg_key:
        winreg.SetValueEx(
            reg_key, "Tracker33", 0, 
            winreg.REG_SZ, sys.executable
        )
```

---

## 11. ПЛАНЫ РАЗВИТИЯ {#future}

### 11.1 QR-код аутентификация

Планируется внедрение современной системы аутентификации через QR-коды:

**Преимущества:**
- Безопасность (одноразовые токены)
- Простота использования
- Не требует регистрации
- Современный UX

**Архитектура:**
```python
# Backend: генерация QR-кодов
def generate_qr_token():
    token = secrets.token_urlsafe(32)
    QRToken.objects.create(
        token=token,
        expires_at=timezone.now() + timedelta(minutes=10)
    )
    return token

# Client: сканирование QR
def scan_qr_code():
    qr_data = camera.scan()
    token = extract_token(qr_data)
    response = requests.post('/api/qr-auth/', {'token': token})
    return response.json()['access_token']
```

### 11.2 Улучшения безопасности

- **PASETO токены**: Замена JWT на более безопасные PASETO
- **WebAuthn**: Биометрическая аутентификация
- **Zero-trust**: Архитектура с проверкой каждого запроса

### 11.3 Расширенная аналитика

- **AI-анализ**: Машинное обучение для определения продуктивности
- **Предиктивная аналитика**: Прогнозирование производительности
- **Командная работа**: Анализ работы команд

### 11.4 Мобильное приложение

Планируется разработка мобильного приложения на Flutter:

```dart
// Flutter клиент
class TrackerApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Tracker33',
      theme: ThemeData.dark(),
      home: DashboardScreen(),
    );
  }
}
```

---

## ЗАКЛЮЧЕНИЕ

Tracker33 представляет собой современную, масштабируемую систему мониторинга рабочего времени с прочной архитектурной основой для дальнейшего развития. Система демонстрирует применение современных технологий веб-разработки, desktop приложений и принципов безопасности.

**Ключевые достижения:**
- Полнофункциональная система мониторинга
- Современная архитектура с REST API
- Безопасная аутентификация
- Высокая производительность
- Готовность к масштабированию

**Техническая экспертиза:**
- Django + DRF для backend
- PyQt6 для desktop клиента
- JWT токены для API
- Многопоточность и асинхронность
- Современные практики разработки

Система готова к промышленному использованию и дальнейшему развитию в направлении современных методов аутентификации и расширенной аналитики.

---

*Документация создана в рамках дипломного проекта  
Версия: 1.0  
Дата: Январь 2024* 