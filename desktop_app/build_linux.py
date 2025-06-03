#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сборки приложения TimeTracker для Linux
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

def check_requirements():
    """Проверяет необходимые зависимости для сборки"""
    print("Проверка зависимостей...")
    
    # Проверяем, что мы на Linux
    if platform.system() != "Linux":
        print(f"Ошибка: Этот скрипт должен выполняться на Linux, а не на {platform.system()}")
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

def create_desktop_file(build_path, version="1.0"):
    """Создает .desktop файл для запуска приложения из меню Linux"""
    desktop_file_content = f"""[Desktop Entry]
Name=TimeTracker
Comment=Приложение для отслеживания активности на компьютере
Exec={build_path}/TimeTracker
Icon={build_path}/icon.png
Terminal=false
Type=Application
Categories=Utility;
Version={version}
"""
    
    # Создаем директорию для .desktop файла, если её нет
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    # Путь к .desktop файлу
    desktop_file_path = desktop_dir / "timetracker.desktop"
    
    # Сохраняем файл
    with open(desktop_file_path, "w", encoding="utf-8") as file:
        file.write(desktop_file_content)
    
    # Делаем файл исполняемым
    os.chmod(desktop_file_path, 0o755)
    
    print(f"Создан файл запуска в меню: {desktop_file_path}")
    return desktop_file_path

def create_autostart_file(desktop_file_path):
    """Создает ссылку на .desktop файл в автозапуске"""
    # Директория автозапуска
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    
    # Путь к файлу автозапуска
    autostart_file_path = autostart_dir / "timetracker.desktop"
    
    # Копируем .desktop файл в директорию автозапуска
    shutil.copy2(desktop_file_path, autostart_file_path)
    
    print(f"Создан файл автозапуска: {autostart_file_path}")
    return autostart_file_path

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
        "--add-data=icon.png:.",
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

def create_installation_script(build_path):
    """Создает скрипт установки для Linux"""
    install_script_content = f"""#!/bin/bash
# Скрипт установки TimeTracker

echo "Установка TimeTracker..."

# Создаем директорию для приложения
install_dir="$HOME/.local/share/TimeTracker"
mkdir -p "$install_dir"

# Копируем файлы
cp -r "{build_path}/"* "$install_dir/"

# Делаем исполняемым
chmod +x "$install_dir/TimeTracker"

# Создаем .desktop файл
desktop_file="$HOME/.local/share/applications/timetracker.desktop"
cat > "$desktop_file" << EOL
[Desktop Entry]
Name=TimeTracker
Comment=Приложение для отслеживания активности на компьютере
Exec=$install_dir/TimeTracker
Icon=$install_dir/icon.png
Terminal=false
Type=Application
Categories=Utility;
Version=1.0
EOL

chmod +x "$desktop_file"

# Создаем файл автозапуска
mkdir -p "$HOME/.config/autostart"
cp "$desktop_file" "$HOME/.config/autostart/"

echo "TimeTracker успешно установлен!"
echo "Вы можете запустить его из меню приложений или командой: $install_dir/TimeTracker"
"""
    
    # Путь к скрипту установки
    install_script_path = Path(build_path) / "install.sh"
    
    # Сохраняем скрипт
    with open(install_script_path, "w", encoding="utf-8") as file:
        file.write(install_script_content)
    
    # Делаем скрипт исполняемым
    os.chmod(install_script_path, 0o755)
    
    print(f"Создан скрипт установки: {install_script_path}")
    return install_script_path

def main():
    """Основная функция сборки и установки"""
    print("=== Сборка TimeTracker для Linux ===")
    
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
    create_installation_script(build_path)
    
    print("\nСборка успешно завершена!")
    print(f"Исполняемый файл: {build_path}/TimeTracker")
    print(f"Запустите скрипт {build_path}/install.sh для установки приложения")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 