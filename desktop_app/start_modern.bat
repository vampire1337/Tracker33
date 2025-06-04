@echo off
echo 🚀 Tracker33 Modern Client
echo =====================================
echo.

REM Проверяем, установлен ли Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python с python.org
    pause
    exit /b 1
)

REM Проверяем зависимости
echo 🔍 Проверка зависимостей...
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo 📥 Установка зависимостей...
    pip install -r requirements_modern.txt
    if errorlevel 1 (
        echo ❌ Ошибка установки зависимостей!
        pause
        exit /b 1
    )
    echo ✅ Зависимости установлены!
)

REM Запуск клиента
echo 🚀 Запуск Tracker33 Modern Client...
python modern_client.py

REM Если программа закрылась с ошибкой
if errorlevel 1 (
    echo.
    echo ❌ Программа завершилась с ошибкой!
    echo 📝 Проверьте лог выше для диагностики
    pause
) 