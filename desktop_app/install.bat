@echo off
:: Скрипт установки TimeTracker для Windows
:: Запускать от имени администратора

echo ==== Установка TimeTracker ====
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Ошибка: Этот скрипт должен быть запущен от имени администратора.
    echo Пожалуйста, закройте окно и запустите скрипт от имени администратора.
    pause
    exit /b 1
)

:: Проверка наличия PowerShell
where powershell >nul 2>&1
if %errorLevel% neq 0 (
    echo Ошибка: PowerShell не найден.
    echo Установка невозможна. Пожалуйста, установите PowerShell.
    pause
    exit /b 1
)

:: Запускаем PowerShell скрипт установки
echo Запуск установки...
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"

if %errorLevel% neq 0 (
    echo Ошибка при установке. См. сообщения выше для деталей.
    pause
    exit /b 1
)

echo.
echo Установка завершена успешно!
echo.
echo Нажмите любую клавишу для выхода...
pause >nul 