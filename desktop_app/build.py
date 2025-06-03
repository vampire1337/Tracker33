#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сборки приложения TimeTracker для Windows
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path
import winreg

def check_requirements():
    """Проверяет необходимые зависимости для сборки"""
    print("Проверка зависимостей...")
    
    # Проверяем, что мы на Windows
    if platform.system() != "Windows":
        print(f"Ошибка: Этот скрипт должен выполняться на Windows, а не на {platform.system()}")
        return False
    
    # Проверяем наличие PyInstaller
    try:
        subprocess.run(["pyinstaller", "--version"], capture_output=True, check=True)
        print("PyInstaller найден")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Ошибка: PyInstaller не установлен. Установите его командой: pip install pyinstaller")
        return False
    
    # Проверяем наличие необходимых пакетов
    required_packages = ["PyQt5", "pynput", "psutil", "requests", "PyJWT"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Ошибка: Следующие пакеты не установлены: {', '.join(missing_packages)}")
        print("Установите их командой: pip install " + " ".join(missing_packages))
        return False
    
    print("Все зависимости установлены")
    return True

def create_windows_shortcut(target_path, shortcut_path, icon_path=None, description="TimeTracker Application"):
    """Создает ярлык Windows (.lnk)"""
    try:
        import win32com.client
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        if icon_path:
            shortcut.IconLocation = icon_path
        shortcut.Description = description
        shortcut.save()
        print(f"Создан ярлык: {shortcut_path}")
        return True
    except Exception as e:
        print(f"Ошибка при создании ярлыка: {e}")
        return False

def add_to_startup(executable_path, app_name="TimeTracker"):
    """Добавляет приложение в автозапуск Windows"""
    try:
        # Путь к реестру автозапуска
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        # Открываем ключ реестра
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        
        # Добавляем приложение в автозапуск
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, executable_path)
        
        # Закрываем ключ
        winreg.CloseKey(key)
        
        print(f"Приложение добавлено в автозапуск: {executable_path}")
        return True
    except Exception as e:
        print(f"Ошибка при добавлении в автозапуск: {e}")
        return False

def build_application():
    """Выполняет сборку приложения с помощью PyInstaller"""
    print("Начинаем сборку приложения...")
    
    # Путь к директории сборки
    dist_dir = Path("dist")
    build_dir = Path("build")
    
    # Очищаем предыдущие сборки
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Параметры для PyInstaller
    pyinstaller_args = [
        "pyinstaller",
        "--name=TimeTracker",
        "--onefile",
        "--windowed",
        "--add-data=icon.png;.",
        "--icon=icon.png",
        "main.py"
    ]
    
    try:
        # Запускаем PyInstaller
        subprocess.run(pyinstaller_args, check=True)
        print("Сборка успешно выполнена")
        
        # Создаем каталог для дополнительных файлов
        build_path = dist_dir / "TimeTracker"
        if not build_path.exists():
            build_path = dist_dir  # Для onefile сборки
        
        # Копируем конфигурационный файл, если он существует
        config_file = Path("config.ini")
        if config_file.exists():
            shutil.copy2(config_file, build_path)
            print(f"Конфигурационный файл скопирован в {build_path / 'config.ini'}")
        
        # Копируем иконку
        icon_file = Path("icon.png")
        if icon_file.exists():
            shutil.copy2(icon_file, build_path)
            print(f"Файл иконки скопирован в {build_path / 'icon.png'}")
        
        return str(build_path.absolute())
    except subprocess.SubprocessError as e:
        print(f"Ошибка при сборке: {e}")
        return None

def create_installation_batch(build_path):
    """Создает batch-файл для установки приложения на Windows"""
    install_batch_content = f"""@echo off
echo Установка TimeTracker...

set "INSTALL_DIR=%LOCALAPPDATA%\\TimeTracker"
set "STARTUP_DIR=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
set "STARTMENU_DIR=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"

:: Создаем директорию для установки
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Копируем файлы
xcopy /y /e "{build_path}\\*" "%INSTALL_DIR%\\"

:: Создаем ярлык в меню Пуск
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTMENU_DIR%\\TimeTracker.lnk');$s.TargetPath='%INSTALL_DIR%\\TimeTracker.exe';$s.IconLocation='%INSTALL_DIR%\\icon.png';$s.Save()"

:: Создаем ярлык в автозапуске
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP_DIR%\\TimeTracker.lnk');$s.TargetPath='%INSTALL_DIR%\\TimeTracker.exe';$s.IconLocation='%INSTALL_DIR%\\icon.png';$s.Save()"

echo TimeTracker успешно установлен!
echo Вы можете запустить его из меню Пуск или выполнив: %INSTALL_DIR%\\TimeTracker.exe

pause
"""
    
    # Путь к batch-файлу установки
    install_batch_path = Path(build_path) / "install.bat"
    
    # Сохраняем файл
    with open(install_batch_path, "w", encoding="utf-8") as file:
        file.write(install_batch_content)
    
    print(f"Создан установочный batch-файл: {install_batch_path}")
    return install_batch_path

def main():
    """Основная функция сборки и установки"""
    print("=== Сборка TimeTracker для Windows ===")
    
    # Проверяем зависимости
    if not check_requirements():
        print("Сборка прервана из-за отсутствия необходимых зависимостей")
        return 1
    
    # Собираем приложение
    build_path = build_application()
    if not build_path:
        print("Сборка не удалась")
        return 1
    
    # Создаем файлы для установки
    create_installation_batch(build_path)
    
    print("\nСборка успешно завершена!")
    print(f"Исполняемый файл: {build_path}\\TimeTracker.exe")
    print(f"Запустите скрипт {build_path}\\install.bat для установки приложения")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 