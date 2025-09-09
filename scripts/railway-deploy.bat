@echo off
setlocal enabledelayedexpansion

echo 🚂 Подготовка к развертыванию на Railway

REM Проверка Railway CLI
railway --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Railway CLI не установлен. Установите его:
    echo    npm install -g @railway/cli
    echo    Или скачайте с https://railway.app/cli
    pause
    exit /b 1
)

echo ✅ Railway CLI найден

REM Логин (если не залогинен)
echo 🔐 Проверка авторизации...
railway whoami >nul 2>&1
if errorlevel 1 (
    echo Необходимо войти в Railway:
    railway login
)

echo ✅ Авторизация прошла успешно

REM Создание проекта (если не существует)
echo 📦 Создание/подключение к проекту...
if not exist "railway.json" (
    echo Создание нового проекта на Railway...
    railway init
) else (
    echo Проект уже существует, используем его
)

REM Настройка переменных окружения
echo ⚙️ Настройка переменных окружения...

REM Генерация SECRET_KEY
for /f %%i in ('python -c "import secrets; import string; alphabet = string.ascii_letters + string.digits + '!@#$%%^&*(-_=+)'; print(''.join(secrets.choice(alphabet) for i in range(50)))"') do set SECRET_KEY=%%i

railway variables set SECRET_KEY="%SECRET_KEY%"
railway variables set DEBUG="False"
railway variables set DJANGO_SETTINGS_MODULE="Tracker33.settings"
railway variables set ALLOWED_HOSTS="*.railway.app,localhost,127.0.0.1"
railway variables set CORS_ALLOWED_ORIGINS="https://tracker33-production.up.railway.app"

echo ✅ Переменные окружения настроены

REM Добавление PostgreSQL базы данных
echo 🗄️ Добавление PostgreSQL базы данных...
railway add postgresql

echo ✅ PostgreSQL добавлен

REM Развертывание
echo 🚀 Развертывание приложения...
railway up --detach

echo ⏳ Ожидание завершения развертывания...
timeout /t 30 /nobreak >nul

echo.
echo 🎉 Развертывание запущено!
echo 📊 Панель управления: https://railway.app/dashboard
echo.
echo 📝 Следующие шаги:
echo 1. Откройте панель Railway и дождитесь завершения развертывания
echo 2. Создайте суперпользователя: railway run python manage.py createsuperuser
echo 3. Проверьте работу приложения в браузере
echo.
echo 🔧 Полезные команды Railway:
echo    railway logs        - просмотр логов
echo    railway shell       - подключение к контейнеру
echo    railway status      - статус развертывания
echo    railway variables   - просмотр переменных окружения

pause
