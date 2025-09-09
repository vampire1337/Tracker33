# 🚀 Руководство по развертыванию Tracker33

## Обзор

Tracker33 - это веб-приложение Django с десктопным клиентом. Данное руководство покрывает различные сценарии развертывания.

## 📋 Предварительные требования

### Системные требования

- **OS**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **Python**: 3.10+
- **RAM**: минимум 2GB, рекомендуется 4GB+
- **Диск**: минимум 10GB свободного места
- **Сеть**: доступ к интернету для установки зависимостей

### Необходимое ПО

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git nginx supervisor

# CentOS/RHEL
sudo yum install python3 python3-pip git nginx supervisor
```

## 🔧 Настройка окружения

### 1. Подготовка пользователя

```bash
# Создание пользователя для приложения
sudo useradd -m -s /bin/bash tracker33
sudo usermod -aG www-data tracker33

# Переключение на пользователя
sudo su - tracker33
```

### 2. Клонирование и настройка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/tracker33.git
cd tracker33

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
pip install gunicorn psycopg2-binary  # для PostgreSQL
```

### 3. Настройка переменных окружения

```bash
# Создание .env файла
cp env.example .env

# Редактирование настроек
nano .env
```

Пример `.env` для продакшена:

```env
# Django settings
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-server-ip

# Database (PostgreSQL рекомендуется для продакшена)
DATABASE_URL=postgresql://tracker33:password@localhost:5432/tracker33

# Performance monitoring
SLOW_REQUEST_THRESHOLD=2.0
SLOW_QUERY_THRESHOLD=0.5

# CORS settings
CORS_ALLOWED_ORIGINS=https://your-domain.com

# Email settings
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=your-email-password
```

### 4. Подготовка базы данных

#### SQLite (для тестирования)
```bash
python manage.py migrate
python manage.py createsuperuser
```

#### PostgreSQL (рекомендуется)
```bash
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Создание базы данных и пользователя
sudo -u postgres psql
CREATE DATABASE tracker33;
CREATE USER tracker33 WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE tracker33 TO tracker33;
\q

# Применение миграций
python manage.py migrate
python manage.py createsuperuser
```

### 5. Сбор статических файлов

```bash
python manage.py collectstatic --noinput
```

## 🌐 Настройка веб-сервера

### Nginx конфигурация

Создайте файл `/etc/nginx/sites-available/tracker33`:

```nginx
server {
    listen 80;
    server_name your-domain.com your-server-ip;

    # Редирект на HTTPS (рекомендуется)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com your-server-ip;

    # SSL сертификаты (используйте Let's Encrypt)
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Настройки SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Основные настройки
    client_max_body_size 100M;
    keepalive_timeout 65;

    # Статические файлы
    location /static/ {
        alias /home/tracker33/tracker33/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Медиа файлы
    location /media/ {
        alias /home/tracker33/tracker33/media/;
        expires 7d;
    }

    # Основное приложение
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Логи
    access_log /var/log/nginx/tracker33_access.log;
    error_log /var/log/nginx/tracker33_error.log;
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/tracker33 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔄 Настройка Supervisor

Создайте файл `/etc/supervisor/conf.d/tracker33.conf`:

```ini
[program:tracker33]
command=/home/tracker33/tracker33/venv/bin/gunicorn Tracker33.wsgi:application
directory=/home/tracker33/tracker33
user=tracker33
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/tracker33/tracker33/logs/gunicorn.log
stderr_logfile=/home/tracker33/tracker33/logs/gunicorn_error.log
environment=PATH="/home/tracker33/tracker33/venv/bin"

[program:tracker33-worker]
command=/home/tracker33/tracker33/venv/bin/python manage.py runserver 0.0.0.0:8001
directory=/home/tracker33/tracker33
user=tracker33
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/tracker33/tracker33/logs/django.log
stderr_logfile=/home/tracker33/tracker33/logs/django_error.log
environment=PATH="/home/tracker33/tracker33/venv/bin"
```

Активируйте Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start tracker33
sudo supervisorctl status
```

## 🐧 Systemd Service (альтернатива)

Скопируйте и настройте systemd service:

```bash
sudo cp config/Tracker33.service /etc/systemd/system/
sudo nano /etc/systemd/system/Tracker33.service

# Настройте пути в файле под ваше окружение
sudo systemctl daemon-reload
sudo systemctl enable Tracker33
sudo systemctl start Tracker33
sudo systemctl status Tracker33
```

## 🔒 SSL/TLS сертификаты

### Let's Encrypt (рекомендуется)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавьте строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Мониторинг и логи

### Настройка логирования

```bash
# Создание директории для логов
mkdir -p /home/tracker33/tracker33/logs

# Настройка ротации логов
sudo nano /etc/logrotate.d/tracker33
```

Содержимое файла ротации:

```
/home/tracker33/tracker33/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 tracker33 tracker33
    postrotate
        supervisorctl restart tracker33
    endscript
}
```

### Мониторинг системы

```bash
# Установка системы мониторинга
sudo apt install htop iotop nethogs

# Мониторинг процессов
htop
ps aux | grep tracker33

# Мониторинг логов
tail -f /home/tracker33/tracker33/logs/*.log
```

## 🔧 Обновление приложения

### Скрипт обновления

Создайте файл `scripts/update.sh`:

```bash
#!/bin/bash
set -e

echo "Начало обновления Tracker33..."

# Переход в директорию проекта
cd /home/tracker33/tracker33

# Активация виртуального окружения
source venv/bin/activate

# Создание резервной копии
echo "Создание резервной копии..."
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Получение обновлений
echo "Получение обновлений из Git..."
git pull origin main

# Обновление зависимостей
echo "Обновление зависимостей..."
pip install -r requirements.txt

# Применение миграций
echo "Применение миграций базы данных..."
python manage.py migrate

# Сбор статических файлов
echo "Сбор статических файлов..."
python manage.py collectstatic --noinput

# Перезапуск сервисов
echo "Перезапуск сервисов..."
sudo supervisorctl restart tracker33

echo "Обновление завершено успешно!"
```

Сделайте скрипт исполняемым:

```bash
chmod +x scripts/update.sh
```

## 📱 Настройка десктопного клиента

### Сборка клиента для Windows

На Windows машине:

```cmd
cd desktop_app
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --noconsole --icon=icon.ico --add-data "config.ini;." --name TimeTracker main.py
```

### Конфигурация клиента

Отредактируйте `desktop_app/config.ini`:

```ini
[API]
base_url = https://your-domain.com

[Server]
base_url = https://your-domain.com

[Credentials]
api_base_url = https://your-domain.com/api/

[Settings]
update_interval = 5
log_level = INFO
auto_start = true
minimize_to_tray = true
idle_threshold_seconds = 300
send_interval_seconds = 10
max_send_batch_size = 20
demo_mode = false
```

## 🛠️ Устранение неполадок

### Частые проблемы

1. **Сервер не запускается**
   ```bash
   # Проверка логов
   sudo supervisorctl tail tracker33
   # или
   systemctl status Tracker33
   journalctl -u Tracker33 -f
   ```

2. **Ошибки базы данных**
   ```bash
   # Проверка миграций
   python manage.py showmigrations
   python manage.py migrate --fake-initial
   ```

3. **Проблемы со статическими файлами**
   ```bash
   # Повторный сбор статики
   python manage.py collectstatic --clear --noinput
   ```

4. **Ошибки разрешений**
   ```bash
   # Исправление прав доступа
   sudo chown -R tracker33:www-data /home/tracker33/tracker33
   sudo chmod -R 755 /home/tracker33/tracker33
   ```

### Диагностика

```bash
# Проверка подключения к базе данных
python manage.py dbshell

# Проверка настроек Django
python manage.py check --deploy

# Тестирование API
curl -X GET https://your-domain.com/api/health/
```

## 📈 Оптимизация производительности

### Настройки базы данных

Для PostgreSQL в `/etc/postgresql/*/main/postgresql.conf`:

```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
```

### Кэширование

Добавьте Redis для кэширования:

```bash
sudo apt install redis-server
pip install django-redis
```

В `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи приложения
2. Убедитесь в правильности настроек
3. Проверьте системные ресурсы
4. Обратитесь к документации Django
5. Создайте issue в репозитории проекта
