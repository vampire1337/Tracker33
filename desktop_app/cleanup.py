#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для очистки временных файлов и подготовки приложения к обновлению.
Работает на Windows и Linux.
"""

import os
import sys
import shutil
import logging
import platform
import argparse
from pathlib import Path
import tempfile
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TimeTrackerCleanup")

def get_app_data_dir(app_name="TimeTracker") -> Path:
    """
    Получает директорию данных приложения в зависимости от ОС.
    
    Args:
        app_name: Имя приложения
    
    Returns:
        Path: Путь к директории данных приложения
    """
    system = platform.system()
    
    if system == 'Windows':
        # На Windows используем %APPDATA%
        base_dir = os.environ.get('APPDATA')
        if not base_dir:
            base_dir = os.path.expanduser('~\\AppData\\Roaming')
    elif system == 'Linux':
        # На Linux используем ~/.config
        base_dir = os.path.expanduser('~/.config')
    elif system == 'Darwin':  # macOS
        # На macOS используем ~/Library/Application Support
        base_dir = os.path.expanduser('~/Library/Application Support')
    else:
        # Для других ОС используем локальную директорию
        base_dir = os.path.expanduser('~/.local/share')
    
    return Path(os.path.join(base_dir, app_name))

def get_program_dir(app_name="TimeTracker") -> Path:
    """
    Получает директорию установки приложения в зависимости от ОС.
    
    Args:
        app_name: Имя приложения
    
    Returns:
        Path: Путь к директории установки приложения
    """
    system = platform.system()
    
    if system == 'Windows':
        # На Windows используем %LOCALAPPDATA%
        base_dir = os.environ.get('LOCALAPPDATA')
        if not base_dir:
            base_dir = os.path.expanduser('~\\AppData\\Local')
    elif system == 'Linux':
        # На Linux используем ~/.local/share
        base_dir = os.path.expanduser('~/.local/share')
    elif system == 'Darwin':  # macOS
        # На macOS используем ~/Applications
        base_dir = os.path.expanduser('~/Applications')
    else:
        # Для других ОС используем локальную директорию
        base_dir = os.path.expanduser('~/.local/share')
    
    return Path(os.path.join(base_dir, app_name))

def cleanup_temp_files(dirs_to_clean=None):
    """
    Очищает временные файлы приложения.
    
    Args:
        dirs_to_clean: Список директорий для очистки
    """
    logger.info("Очистка временных файлов...")
    
    # Если директории не указаны, используем стандартные
    if not dirs_to_clean:
        app_data_dir = get_app_data_dir()
        dirs_to_clean = [
            app_data_dir / "logs",
            app_data_dir / "temp",
            Path(tempfile.gettempdir()) / "TimeTracker"
        ]
    
    # Список файлов для удаления (по маске)
    file_patterns = [
        "*.tmp",
        "*.log.*",
        "*.bak",
        "*.old"
    ]
    
    # Очищаем каждую директорию
    for directory in dirs_to_clean:
        if not directory.exists():
            logger.debug(f"Директория {directory} не существует, пропускаем")
            continue
        
        logger.info(f"Очистка директории: {directory}")
        
        # Удаляем файлы по маске
        for pattern in file_patterns:
            for file_path in directory.glob(pattern):
                try:
                    file_path.unlink()
                    logger.debug(f"Удален файл: {file_path}")
                except Exception as e:
                    logger.warning(f"Не удалось удалить файл {file_path}: {e}")
        
        # Очищаем файлы логов, которые старше 7 дней
        if "logs" in str(directory):
            logger.info("Очистка старых файлов логов...")
            now = time.time()
            for file_path in directory.glob("*.log"):
                if file_path.name == "tracker.log":
                    continue  # Не удаляем текущий лог
                
                file_age = now - file_path.stat().st_mtime
                if file_age > 7 * 24 * 60 * 60:  # 7 дней в секундах
                    try:
                        file_path.unlink()
                        logger.debug(f"Удален устаревший лог: {file_path}")
                    except Exception as e:
                        logger.warning(f"Не удалось удалить устаревший лог {file_path}: {e}")

def prepare_for_update():
    """
    Подготавливает приложение к обновлению.
    """
    logger.info("Подготовка к обновлению приложения...")
    
    # Очищаем временные файлы
    cleanup_temp_files()
    
    # Создаем резервную копию конфигурации
    app_data_dir = get_app_data_dir()
    config_file = app_data_dir / "config.ini"
    
    if config_file.exists():
        logger.info("Создание резервной копии конфигурации...")
        backup_file = app_data_dir / "config.ini.bak"
        try:
            shutil.copy2(config_file, backup_file)
            logger.info(f"Резервная копия создана: {backup_file}")
        except Exception as e:
            logger.error(f"Не удалось создать резервную копию конфигурации: {e}")
    
    logger.info("Приложение готово к обновлению.")

def remove_app():
    """
    Удаляет приложение с компьютера.
    """
    logger.info("Удаление приложения...")
    
    app_data_dir = get_app_data_dir()
    program_dir = get_program_dir()
    
    # Спрашиваем подтверждение
    confirm = input(f"Вы уверены, что хотите удалить приложение из {program_dir}? (y/n): ")
    if confirm.lower() != 'y':
        logger.info("Удаление отменено.")
        return
    
    # Удаляем файлы программы
    if program_dir.exists():
        logger.info(f"Удаление директории программы: {program_dir}")
        try:
            shutil.rmtree(program_dir)
            logger.info("Директория программы удалена.")
        except Exception as e:
            logger.error(f"Не удалось удалить директорию программы: {e}")
    
    # Спрашиваем, удалять ли данные приложения
    confirm_data = input(f"Удалить все данные приложения из {app_data_dir}? (y/n): ")
    if confirm_data.lower() == 'y':
        if app_data_dir.exists():
            logger.info(f"Удаление данных приложения: {app_data_dir}")
            try:
                shutil.rmtree(app_data_dir)
                logger.info("Данные приложения удалены.")
            except Exception as e:
                logger.error(f"Не удалось удалить данные приложения: {e}")
    else:
        logger.info("Данные приложения сохранены.")
    
    # Удаляем ярлыки в зависимости от ОС
    system = platform.system()
    
    if system == 'Windows':
        # Удаляем ярлык из меню Пуск
        start_menu_dir = Path(os.path.expanduser('~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs'))
        shortcut_path = start_menu_dir / "TimeTracker.lnk"
        
        if shortcut_path.exists():
            try:
                shortcut_path.unlink()
                logger.info("Ярлык из меню Пуск удален.")
            except Exception as e:
                logger.error(f"Не удалось удалить ярлык из меню Пуск: {e}")
        
        # Удаляем ярлык из автозагрузки
        startup_dir = Path(os.path.expanduser('~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup'))
        startup_shortcut = startup_dir / "TimeTracker.lnk"
        
        if startup_shortcut.exists():
            try:
                startup_shortcut.unlink()
                logger.info("Ярлык из автозагрузки удален.")
            except Exception as e:
                logger.error(f"Не удалось удалить ярлык из автозагрузки: {e}")
                
        # Удаляем запись из реестра
        logger.info("Для полного удаления рекомендуется вручную удалить запись TimeTracker из реестра Windows.")
        logger.info("Путь в реестре: HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run")
    
    elif system == 'Linux':
        # Удаляем desktop-файл из меню приложений
        desktop_dir = Path(os.path.expanduser('~/.local/share/applications'))
        desktop_file = desktop_dir / "TimeTracker.desktop"
        
        if desktop_file.exists():
            try:
                desktop_file.unlink()
                logger.info("Ярлык из меню приложений удален.")
            except Exception as e:
                logger.error(f"Не удалось удалить ярлык из меню приложений: {e}")
        
        # Удаляем файл автозапуска
        autostart_dir = Path(os.path.expanduser('~/.config/autostart'))
        autostart_file = autostart_dir / "TimeTracker.desktop"
        
        if autostart_file.exists():
            try:
                autostart_file.unlink()
                logger.info("Файл автозапуска удален.")
            except Exception as e:
                logger.error(f"Не удалось удалить файл автозапуска: {e}")
    
    logger.info("Удаление завершено.")

def main():
    """
    Основная функция скрипта.
    """
    parser = argparse.ArgumentParser(description='Утилита для обслуживания TimeTracker')
    parser.add_argument('--cleanup', action='store_true', help='Очистить временные файлы')
    parser.add_argument('--prepare-update', action='store_true', help='Подготовить к обновлению')
    parser.add_argument('--uninstall', action='store_true', help='Удалить приложение')
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_temp_files()
    elif args.prepare_update:
        prepare_for_update()
    elif args.uninstall:
        remove_app()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 