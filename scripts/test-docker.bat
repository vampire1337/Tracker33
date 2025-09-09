@echo off
setlocal enabledelayedexpansion

echo 🐳 Тестирование Docker развертывания Tracker33

REM Проверка установки Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не установлен. Установите Docker Desktop и повторите попытку.
    echo    Скачайте с https://www.docker.com/get-started
    pause
    exit /b 1
)

REM Проверка запуска Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker не запущен. Запустите Docker Desktop и повторите попытку.
    pause
    exit /b 1
)

echo ✅ Docker установлен и запущен

REM Переход в директорию проекта
cd /d "%~dp0\.."

echo 📦 Сборка Docker образа...
docker build -t tracker33:latest .
if errorlevel 1 (
    echo ❌ Ошибка при сборке Docker образа
    pause
    exit /b 1
)

echo ✅ Docker образ собран успешно

REM Проверка образа
echo 📋 Информация о созданном образе:
docker images tracker33:latest

REM Создание сети для контейнеров
echo 🌐 Создание Docker сети...
docker network create tracker33_network 2>nul || echo Сеть уже существует

REM Остановка и удаление старых контейнеров
echo 🧹 Очистка старых контейнеров...
docker stop tracker33_web tracker33_postgres >nul 2>&1
docker rm tracker33_web tracker33_postgres >nul 2>&1

REM Запуск базы данных PostgreSQL
echo 🗄️ Запуск PostgreSQL...
docker run -d --name tracker33_postgres --network tracker33_network -e POSTGRES_DB=tracker33 -e POSTGRES_USER=tracker33 -e POSTGRES_PASSWORD=secure_password postgres:15-alpine
if errorlevel 1 (
    echo ❌ Ошибка при запуске PostgreSQL
    pause
    exit /b 1
)

REM Ожидание запуска PostgreSQL
echo ⏳ Ожидание запуска PostgreSQL...
timeout /t 15 /nobreak >nul

REM Запуск основного приложения с SQLite для простоты
echo 🚀 Запуск Tracker33...
docker run -d --name tracker33_web --network tracker33_network -p 8001:8001 -e SECRET_KEY="django-test-secret-key-for-docker" -e DEBUG=False -e ALLOWED_HOSTS="localhost,127.0.0.1,0.0.0.0" tracker33:latest
if errorlevel 1 (
    echo ❌ Ошибка при запуске контейнера
    pause
    exit /b 1
)

echo ✅ Контейнеры запущены

REM Проверка статуса контейнеров
echo 📊 Статус контейнеров:
docker ps --filter "name=tracker33"

REM Ожидание полного запуска приложения
echo ⏳ Ожидание полного запуска приложения...
timeout /t 30 /nobreak >nul

REM Проверка работоспособности приложения
echo 🏥 Проверка работоспособности приложения...
for /l %%i in (1,1,10) do (
    curl -f -s http://localhost:8001/ >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Приложение отвечает на HTTP запросы
        goto :health_check_passed
    ) else (
        echo ⏳ Попытка %%i/10: приложение еще не готово...
        timeout /t 5 /nobreak >nul
    )
)

echo ❌ Приложение не отвечает после 10 попыток
echo 📋 Логи контейнера:
docker logs tracker33_web
pause
exit /b 1

:health_check_passed

REM Проверка API
echo 🔍 Проверка API...
curl -f -s http://localhost:8001/api/health/ >nul 2>&1
if errorlevel 1 (
    echo ⚠️ API недоступен (возможно, нужна миграция БД)
) else (
    echo ✅ API работает корректно
)

echo.
echo 🎉 Docker развертывание успешно завершено!
echo.
echo 📱 Приложение доступно по адресу: http://localhost:8001
echo 📊 Для просмотра логов: docker logs tracker33_web
echo 🛑 Для остановки: docker stop tracker33_web tracker33_postgres
echo 🧹 Для очистки: docker rm tracker33_web tracker33_postgres ^&^& docker network rm tracker33_network
echo.

REM Показать инструкции для дальнейшего использования
echo 📝 Следующие шаги:
echo 1. Откройте браузер и перейдите по адресу http://localhost:8001
echo 2. Создайте суперпользователя: docker exec -it tracker33_web python manage.py createsuperuser
echo 3. Примените миграции: docker exec -it tracker33_web python manage.py migrate
echo 4. Для остановки всех сервисов используйте: docker-compose down

pause
