# 🚂 Развертывание Tracker33 на Railway

## Обзор

Railway - это современная платформа для развертывания приложений с автоматическим CI/CD. Данное руководство покрывает полное развертывание Tracker33 на Railway.

## 🚀 Быстрый старт

### Вариант 1: Автоматический скрипт

```bash
# Linux/Mac
./scripts/railway-deploy.sh

# Windows
scripts\railway-deploy.bat
```

### Вариант 2: Ручное развертывание

#### 1. Установка Railway CLI

```bash
# NPM
npm install -g @railway/cli

# Или скачать с https://railway.app/cli
```

#### 2. Авторизация

```bash
railway login
```

#### 3. Инициализация проекта

```bash
railway init
```

#### 4. Добавление PostgreSQL

```bash
railway add postgresql
```

#### 5. Настройка переменных окружения

```bash
# Генерация SECRET_KEY
SECRET_KEY=$(python -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
print(''.join(secrets.choice(alphabet) for i in range(50)))
")

# Установка переменных
railway variables set SECRET_KEY="$SECRET_KEY"
railway variables set DEBUG="False"
railway variables set DJANGO_SETTINGS_MODULE="Tracker33.settings"
railway variables set ALLOWED_HOSTS="*.railway.app"
```

#### 6. Развертывание

```bash
railway up
```

## ⚙️ Конфигурация

### railway.toml

Файл `railway.toml` содержит конфигурацию для Railway:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn Tracker33.wsgi:application --bind 0.0.0.0:$PORT"
healthcheckPath = "/api/health/"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[environments.production.variables]
DEBUG = "False"
DJANGO_SETTINGS_MODULE = "Tracker33.settings"
```

### Procfile

Альтернативная конфигурация через Procfile:

```
release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn Tracker33.wsgi:application --bind 0.0.0.0:$PORT
```

## 🔧 Переменные окружения

### Обязательные переменные

| Переменная | Описание | Пример |
|------------|----------|--------|
| `SECRET_KEY` | Django секретный ключ | `django-secret-key-here` |
| `DEBUG` | Режим отладки | `False` |
| `DATABASE_URL` | URL базы данных | Автоматически от Railway |

### Опциональные переменные

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `ALLOWED_HOSTS` | Разрешенные хосты | `*.railway.app` |
| `CORS_ALLOWED_ORIGINS` | CORS источники | `https://yourdomain.railway.app` |
| `DJANGO_SETTINGS_MODULE` | Модуль настроек | `Tracker33.settings` |

### Настройка переменных через CLI

```bash
# Просмотр всех переменных
railway variables

# Установка переменной
railway variables set KEY="value"

# Удаление переменной
railway variables delete KEY
```

## 🗄️ База данных

### PostgreSQL

Railway автоматически предоставляет PostgreSQL базу данных:

```bash
# Добавление PostgreSQL
railway add postgresql

# Подключение к базе данных
railway connect postgres
```

### Миграции

Миграции запускаются автоматически при каждом развертывании через `startCommand` в `railway.toml`.

Ручной запуск миграций:

```bash
railway run python manage.py migrate
```

### Создание суперпользователя

```bash
railway run python manage.py createsuperuser
```

## 📁 Статические файлы

Статические файлы обрабатываются через WhiteNoise:

- Автоматический сбор при развертывании
- Сжатие и кэширование
- CDN доставка

## 🔍 Мониторинг и логи

### Просмотр логов

```bash
# Просмотр логов в реальном времени
railway logs

# Логи с фильтром
railway logs --filter="ERROR"
```

### Health Check

Приложение имеет встроенный health check:

```bash
curl https://your-app.railway.app/api/health/
```

Ответ:
```json
{
  "status": "healthy",
  "timestamp": 1694123456.789,
  "version": "2.0.0",
  "environment": "production",
  "database": "connected",
  "cache": "connected"
}
```

### Метрики

Railway предоставляет встроенные метрики:
- CPU использование
- Память
- Сетевой трафик
- Время ответа

## 🚨 Устранение неполадок

### Частые проблемы

#### 1. Ошибки миграции

```bash
# Проверка состояния миграций
railway run python manage.py showmigrations

# Принудительное применение
railway run python manage.py migrate --fake-initial
```

#### 2. Проблемы со статическими файлами

```bash
# Ручной сбор статики
railway run python manage.py collectstatic --clear --noinput
```

#### 3. Ошибки переменных окружения

```bash
# Проверка переменных
railway variables

# Проверка настроек Django
railway run python manage.py check --deploy
```

#### 4. Проблемы с базой данных

```bash
# Проверка подключения к БД
railway run python manage.py dbshell

# Сброс базы данных (ОСТОРОЖНО!)
railway run python manage.py flush
```

### Логи и отладка

```bash
# Детальные логи
railway logs --tail 100

# Подключение к контейнеру
railway shell

# Проверка переменных окружения внутри контейнера
railway run env
```

## 🔄 CI/CD

### Автоматическое развертывание

Railway автоматически развертывает при пуше в основную ветку GitHub.

### Настройка GitHub интеграции

1. Подключите GitHub репозиторий в Railway Dashboard
2. Выберите ветку для автодеплоя
3. Настройте переменные окружения
4. Railway будет автоматически развертывать при каждом пуше

### Webhook уведомления

Настройте webhook для уведомлений о развертывании:

```bash
railway webhooks create --url="https://your-webhook-url.com"
```

## 📊 Производительность

### Оптимизация

1. **Используйте connection pooling** для базы данных
2. **Настройте кэширование** с Redis
3. **Оптимизируйте статические файлы** через WhiteNoise
4. **Мониторьте метрики** через Railway Dashboard

### Масштабирование

Railway автоматически масштабирует приложение на основе нагрузки:

- Автоматическое вертикальное масштабирование
- Горизонтальное масштабирование (на платных планах)
- Load balancing

## 💰 Стоимость

### Бесплатный план

- 500 часов выполнения в месяц
- 1GB RAM
- 1GB диск
- Автоматический sleep при неактивности

### Платные планы

- Больше ресурсов
- Кастомные домены
- Приоритетная поддержка
- Расширенная аналитика

## 📞 Поддержка

### Ресурсы

- [Railway Documentation](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [GitHub Issues](https://github.com/railwayapp/railway/issues)

### Команды Railway CLI

```bash
railway help           # Справка по командам
railway status         # Статус развертывания
railway open           # Открыть приложение в браузере
railway domain         # Управление доменами
railway environment    # Управление окружениями
```

## 🎯 Чек-лист развертывания

- [ ] Установлен Railway CLI
- [ ] Выполнена авторизация
- [ ] Создан проект
- [ ] Добавлена PostgreSQL база данных
- [ ] Настроены переменные окружения
- [ ] Приложение успешно развернуто
- [ ] Health check возвращает 200
- [ ] Создан суперпользователь
- [ ] Протестированы основные функции
- [ ] Настроен мониторинг
- [ ] Документирован процесс

---

**Готово! Ваше приложение Tracker33 теперь работает на Railway! 🎉**
