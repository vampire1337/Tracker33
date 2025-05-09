@echo off
echo Starting Tracker33 server setup...

REM Создание виртуального окружения, если оно не существует
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Активация виртуального окружения
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Установка зависимостей
echo Installing dependencies...
pip install -r requirements.txt

REM Создание директории для логов, если она не существует
if not exist logs (
    echo Creating logs directory...
    mkdir logs
    REM Создание пустых файлов логов
    type nul > logs\activity.log
    type nul > logs\performance.log
    type nul > logs\error.log
)

REM Создание файла .env, если он не существует
if not exist .env (
    echo Creating .env file with default settings...
    (
        echo # Django settings
        echo DEBUG=True
        echo SECRET_KEY=django-insecure-^)hw&twianf%%f=wq&sb)89@4jf%%am1*4((&#(c#*xb)g4=yj_g
        echo.
        echo # Email configuration
        echo # Configure these settings for password reset functionality
        echo EMAIL_HOST=smtp.gmail.com
        echo EMAIL_PORT=587
        echo EMAIL_USE_TLS=True
        echo EMAIL_HOST_USER=
        echo EMAIL_HOST_PASSWORD=
        echo DEFAULT_FROM_EMAIL=noreply@tracker33.com
        echo.
        echo # CORS settings
        echo ALLOWED_HOSTS=localhost,127.0.0.1
        echo CORS_ALLOWED_ORIGINS=http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000
    ) > .env
    echo Please edit .env file to configure email settings for password reset
)

REM Применение миграций базы данных
echo Applying database migrations...
python manage.py migrate

REM Создание суперпользователя, если он еще не создан
echo Checking for superuser...
python -c "import django; django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); exit(0) if User.objects.filter(is_superuser=True).exists() else User.objects.create_superuser('admin', 'admin@example.com', 'admin') and print('Superuser created. Username: admin, Password: admin')"

REM Сбор статических файлов
echo Collecting static files...
python manage.py collectstatic --noinput

REM Запуск сервера
echo Starting Django server...
echo You can access the server at: http://127.0.0.1:8000/
echo Admin interface: http://127.0.0.1:8000/admin/
echo Login credentials: admin / admin
python manage.py runserver 0.0.0.0:8000 