#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль с универсальными функциями для работы с путями на разных операционных системах.
"""

import os
import sys
import platform
import logging
from pathlib import Path
from typing import Optional, List, Union

logger = logging.getLogger('TimeTracker')

def get_base_path() -> Path:
    """
    Возвращает базовый путь к директории приложения.
    
    Returns:
        Path: Путь к директории приложения
    """
    # Если приложение запущено как замороженное (PyInstaller)
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        # Если запущено как скрипт
        base_path = Path(os.path.abspath(os.path.dirname(__file__)))
        
        # Проверяем, находится ли скрипт в поддиректории
        if base_path.name == 'desktop_app':
            base_path = base_path.parent
    
    logger.debug(f"Базовый путь приложения: {base_path}")
    return base_path

def get_app_data_dir(app_name: str = "TimeTracker") -> Path:
    """
    Возвращает путь к директории данных приложения в зависимости от ОС.
    
    Args:
        app_name: Имя приложения
        
    Returns:
        Path: Путь к директории данных приложения
    """
    system = platform.system()
    
    if system == 'Windows':
        # На Windows используем %APPDATA% (обычно C:\Users\<user>\AppData\Roaming)
        base_dir = os.environ.get('APPDATA')
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
    elif system == 'Linux':
        # На Linux используем ~/.config
        base_dir = os.path.join(os.path.expanduser('~'), '.config')
    elif system == 'Darwin':  # macOS
        # На macOS используем ~/Library/Application Support
        base_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        # Для других ОС используем ~/.local/share
        base_dir = os.path.join(os.path.expanduser('~'), '.local', 'share')
        
    return Path(os.path.join(base_dir, app_name))

def get_logs_dir(app_name: str = "TimeTracker") -> Path:
    """
    Возвращает путь к директории для хранения логов.
    
    Args:
        app_name: Имя приложения
        
    Returns:
        Path: Путь к директории логов
    """
    app_data_dir = get_app_data_dir(app_name)
    logs_dir = app_data_dir / "logs"
    
    # Создаем директорию, если она не существует
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    return logs_dir

def get_data_dir(app_name: str = "TimeTracker") -> Path:
    """
    Возвращает путь к директории для хранения данных приложения.
    
    Args:
        app_name: Имя приложения
        
    Returns:
        Path: Путь к директории данных
    """
    app_data_dir = get_app_data_dir(app_name)
    data_dir = app_data_dir / "data"
    
    # Создаем директорию, если она не существует
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir

def get_config_path(app_name: str = "TimeTracker") -> Path:
    """
    Возвращает путь к файлу конфигурации.
    
    Args:
        app_name: Имя приложения
        
    Returns:
        Path: Путь к файлу конфигурации
    """
    app_data_dir = get_app_data_dir(app_name)
    return app_data_dir / "config.ini"

def get_db_path(app_name: str = "TimeTracker") -> Path:
    """
    Возвращает путь к файлу локальной базы данных.
    
    Args:
        app_name: Имя приложения
        
    Returns:
        Path: Путь к файлу базы данных
    """
    data_dir = get_data_dir(app_name)
    return data_dir / "local.db"

def get_temp_dir(app_name: str = "TimeTracker") -> Path:
    """
    Возвращает путь к временной директории приложения.
    
    Args:
        app_name: Имя приложения
        
    Returns:
        Path: Путь к временной директории
    """
    system = platform.system()
    
    # Получаем системную временную директорию
    if system == 'Windows':
        temp_base = os.environ.get('TEMP')
        if not temp_base:
            temp_base = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp')
    else:
        temp_base = '/tmp'
    
    temp_dir = Path(temp_base) / app_name
    
    # Создаем директорию, если она не существует
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    return temp_dir

def get_executable_dir() -> Path:
    """
    Возвращает путь к директории, где находится исполняемый файл.
    
    Returns:
        Path: Путь к директории исполняемого файла
    """
    if getattr(sys, 'frozen', False):
        # Если приложение запущено как замороженное (PyInstaller)
        return Path(sys.executable).parent
    else:
        # Если запущено как скрипт
        return Path(sys.argv[0]).parent.absolute()

def normalize_path(path: Union[str, Path]) -> Path:
    """
    Нормализует путь для текущей ОС.
    
    Args:
        path: Путь для нормализации
        
    Returns:
        Path: Нормализованный путь
    """
    if isinstance(path, str):
        path = Path(path)
    
    return path.absolute()

def ensure_dir_exists(directory: Union[str, Path]) -> Path:
    """
    Создает директорию, если она не существует.
    
    Args:
        directory: Путь к директории
        
    Returns:
        Path: Путь к созданной директории
    """
    directory = normalize_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def join_paths(*paths: Union[str, Path]) -> Path:
    """
    Объединяет пути с учетом особенностей ОС.
    
    Args:
        *paths: Части пути для объединения
        
    Returns:
        Path: Объединенный путь
    """
    if not paths:
        return Path()
    
    result = Path(paths[0])
    for path in paths[1:]:
        result = result / path
    
    return result

def is_valid_path(path: Union[str, Path]) -> bool:
    """
    Проверяет, является ли путь допустимым для текущей ОС.
    
    Args:
        path: Путь для проверки
        
    Returns:
        bool: True, если путь допустимый, иначе False
    """
    try:
        normalize_path(path)
        return True
    except (ValueError, TypeError):
        return False 