# Tracker33 - Система отслеживания времени и анализа продуктивности

![Python](https://img.shields.io/badge/python-v3.10+-blue.svg)
![Django](https://img.shields.io/badge/django-v5.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 📋 Описание

Tracker33 - это комплексное решение для отслеживания рабочего времени и анализа продуктивности. Система состоит из веб-интерфейса для анализа данных и десктопного клиента для сбора информации о активности пользователя.

### ✨ Основные возможности

- 🕐 **Автоматическое отслеживание времени** - отслеживание времени, проведенного в различных приложениях
- ⌨️ **Мониторинг активности клавиатуры** - анализ клавиатурной активности для оценки продуктивности
- 📊 **Детальная статистика** - графики и отчеты по использованию времени
- 🎯 **Управление продуктивностью** - классификация приложений на продуктивные и непродуктивные
- 👥 **Многопользовательская система** - поддержка нескольких пользователей
- 📱 **Адаптивный интерфейс** - работает на всех устройствах
- 🔒 **Безопасность** - защита данных пользователей

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Node.js (для фронтенда, опционально)
- Git

### Установка

1. **Клонирование репозитория**
```bash
git clone https://github.com/your-username/tracker33.git
cd tracker33
```

2. **Создание виртуального окружения**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

4. **Настройка переменных окружения**
```bash
# Скопируйте файл примера
cp env.example .env
# Отредактируйте .env файл под ваши нужды
```

5. **Применение миграций**
```bash
python manage.py migrate
```

6. **Создание суперпользователя**
```bash
python manage.py createsuperuser
```

7. **Сбор статических файлов**
```bash
python manage.py collectstatic
```

8. **Запуск сервера**
```bash
python manage.py runserver 8001
```

Сервер будет доступен по адресу: http://localhost:8001

## 📁 Структура проекта

```
tracker33/
├── 📁 config/              # Конфигурационные файлы
│   └── Tracker33.service   # Systemd service файл
├── 📁 docs/                # Документация
│   ├── BUILD_INSTRUCTIONS.md
│   ├── api_schema.mmd
│   ├── architecture_diagram.mmd
│   ├── er_diagram.mmd
│   └── monitoring_algorithm.mmd
├── 📁 scripts/             # Скрипты для развертывания
│   ├── start_server.sh
│   ├── stop_background.sh
│   └── setup_service.sh
├── 📁 desktop_app/         # Десктопный клиент
├── 📁 Tracker33/           # Основные настройки Django
├── 📁 tracking/            # Приложение для отслеживания
├── 📁 users/               # Пользовательское приложение
├── 📁 admin_panel/         # Административная панель
├── 📁 templates/           # HTML шаблоны
├── 📁 static/              # Статические файлы
├── manage.py               # Django management
├── requirements.txt        # Python зависимости
└── env.example            # Пример переменных окружения
```

## 🖥️ Десктопный клиент

### Установка клиента

1. Скачайте клиент через веб-интерфейс или соберите самостоятельно
2. Запустите `TimeTracker.exe`
3. Введите данные для входа
4. Клиент автоматически начнет отслеживание

### Настройка клиента

Отредактируйте `config.ini` в папке клиента:

```ini
[API]
base_url = http://your-server:8001

[Settings]
update_interval = 5
auto_start = true
minimize_to_tray = true
idle_threshold_seconds = 300
```

## 📊 API

### Основные эндпоинты

- `GET /api/activity/` - получение данных активности
- `POST /api/activity/` - отправка данных активности
- `GET /api/statistics/` - получение статистики
- `POST /api/toggle-productive/` - переключение продуктивности приложения

### Аутентификация

API использует токенную аутентификацию. Получите токен через:
```bash
curl -X POST http://localhost:8001/api-token-auth/ \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
```

## 🚀 Развертывание

### Разработка

```bash
# Запуск в режиме разработки
python manage.py runserver 8001
```

### Railway (Рекомендуется для портфолио)

**Бесплатное развертывание с минимальными ресурсами:**

```bash
# Автоматический скрипт - всё настроит сам!
./scripts/railway-deploy.sh    # Linux/Mac
scripts\railway-deploy.bat     # Windows

# Или вручную (3 команды)
npm install -g @railway/cli
railway login && railway init
railway up
```

**Особенности:**
- ✅ SQLite база данных (бесплатно, быстро)
- ✅ Минимальное потребление ресурсов (~50MB RAM)
- ✅ Идеально для демонстрации в портфолио
- ✅ 500 часов бесплатно в месяц

Подробнее: [docs/RAILWAY_SIMPLE.md](docs/RAILWAY_SIMPLE.md)

### Docker

```bash
# Простой запуск
docker-compose up -d

# Тестирование
./scripts/test-docker.sh    # Linux/Mac
scripts\test-docker.bat     # Windows
```

### Традиционный сервер

1. **Настройте переменные окружения**:
```bash
export DEBUG=False
export SECRET_KEY=your-secret-key
export ALLOWED_HOSTS=your-domain.com,your-ip
```

2. **Используйте WSGI сервер**:
```bash
# Gunicorn
pip install gunicorn
gunicorn Tracker33.wsgi:application --bind 0.0.0.0:8001

# Или используйте готовые скрипты
chmod +x scripts/start_server.sh
./scripts/start_server.sh
```

3. **Настройте systemd service** (Linux):
```bash
sudo cp config/Tracker33.service /etc/systemd/system/
sudo systemctl enable Tracker33
sudo systemctl start Tracker33
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
python manage.py test

# Тестирование конкретного приложения
python manage.py test tracking

# Тестирование с покрытием
pip install coverage
coverage run manage.py test
coverage report
```

## 📈 Мониторинг

Система включает встроенный мониторинг производительности:

- Логирование медленных запросов
- Отслеживание времени выполнения
- Алерты при превышении порогов
- Детальные логи активности

Логи сохраняются в папке `logs/`:
- `activity.log` - логи активности пользователей
- `performance.log` - логи производительности
- `error.log` - логи ошибок

## 🔧 Конфигурация

### Основные настройки

- `SECRET_KEY` - секретный ключ Django (обязательно)
- `DEBUG` - режим отладки (по умолчанию False)
- `ALLOWED_HOSTS` - разрешенные хосты
- `CORS_ALLOWED_ORIGINS` - разрешенные CORS источники

### Мониторинг

- `SLOW_REQUEST_THRESHOLD` - порог медленных запросов (сек)
- `SLOW_QUERY_THRESHOLD` - порог медленных запросов к БД (сек)

### Email уведомления

- `EMAIL_HOST_USER` - email для отправки
- `EMAIL_HOST_PASSWORD` - пароль email

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 🆘 Поддержка

Если у вас возникли проблемы или вопросы:

1. Проверьте [документацию](docs/)
2. Создайте [Issue](https://github.com/your-username/tracker33/issues)
3. Свяжитесь с командой разработки

## 📞 Контакты

- **Разработчик**: Ваше имя
- **Email**: your-email@example.com
- **GitHub**: https://github.com/your-username

---

⭐ Если проект был полезен, поставьте звездочку!