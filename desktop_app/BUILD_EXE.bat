@echo off
title Tracker33 EXE Builder
echo.
echo 🔨 TRACKER33 EXE BUILDER
echo ========================================
echo 🚀 Автоматическая сборка исполняемого файла
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python с python.org
    pause
    exit /b 1
)

REM Устанавливаем зависимости если нужно
echo 📦 Проверка зависимостей...
pip show PyQt6 pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 📥 Установка зависимостей для сборки...
    pip install pyinstaller PyQt6 aiohttp psutil pynput pygetwindow pywin32
)

REM Запускаем сборку
echo.
echo 🔨 Запуск автоматической сборки EXE...
echo.
python build_exe.py

REM Показываем результат
if exist "dist\Tracker33_Client.exe" (
    echo.
    echo 🎉 УСПЕХ! EXE файл создан!
    echo 📁 Расположение: dist\Tracker33_Client.exe
    echo.
    echo 🚀 Можете запускать Tracker33_Client.exe
    echo    Он не требует установки Python!
    echo.
) else (
    echo.
    echo ❌ Ошибка сборки! Проверьте логи выше.
    echo.
)

pause 