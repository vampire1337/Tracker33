#!/bin/bash

echo "Starting Tracker33 server setup..."

# Создание виртуального окружения, если оно не существует
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "Activating virtual environment..."
source venv/bin/activate

# Установка зависимостей
echo "Installing dependencies..."
pip install -r requirements.txt

# Создание директории для логов, если она не существует
if [ ! -d "logs" ]; then
    echo "Creating logs directory..."
    mkdir -p logs
    # Создание пустых файлов логов
    touch logs/activity.log
    touch logs/performance.log
    touch logs/error.log
fi

# Создание файла .env, если он не существует
if [ ! -f ".env" ]; then
    echo "Creating .env file with default settings..."
    cat > .env << EOF
# Django settings
DEBUG=True
SECRET_KEY=django-insecure-^)hw&twianf%f=wq&sb)89@4jf%am1*4((&#(c#*xb)g4=yj_g

# Email configuration
# Configure these settings for password reset functionality
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@tracker33.com

# CORS settings
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000
EOF
    echo "Please edit .env file to configure email settings for password reset"
fi

# Загрузка переменных окружения
echo "Loading environment variables..."
export $(grep -v '^#' .env | xargs)

# Применение миграций базы данных
echo "Applying database migrations..."
python manage.py migrate

# Создание суперпользователя, если он еще не создан
echo "Checking for superuser..."
python -c "
import django; django.setup();
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...');
    User.objects.create_superuser('admin', 'admin@example.com', 'admin');
    print('Superuser created. Username: admin, Password: admin');
else:
    print('Superuser already exists.');
"

# Сбор статических файлов
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Запуск сервера
echo "Starting Django server..."
echo "You can access the server at: http://0.0.0.0:8000/"
echo "Admin interface: http://0.0.0.0:8000/admin/"
echo "Login credentials: admin / admin"
python manage.py runserver 0.0.0.0:8000 