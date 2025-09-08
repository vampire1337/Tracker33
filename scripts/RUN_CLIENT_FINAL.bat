@echo off
echo ============================
echo ФИНАЛЬНЫЙ ЗАПУСК КЛИЕНТА
echo ============================

echo [INFO] Проверяем сервер...
python manage.py check --deploy 2>nul
if errorlevel 1 (
    echo [СТАРТ] Запускаем сервер...
    start "Django Server" cmd /k "python manage.py runserver 127.0.0.1:8001"
    timeout /t 3 >nul
)

echo [КЛИЕНТ] Запускаем TimeTracker...
cd desktop_app
python main.py

pause 