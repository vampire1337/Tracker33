#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с иконками на разных операционных системах
"""

import os
import sys
import platform
import logging
from pathlib import Path
from typing import Optional
from PyQt5.QtGui import QIcon, QPixmap

logger = logging.getLogger('TimeTracker')

def get_icon_path() -> Path:
    """
    Получает путь к иконке приложения с учетом особенностей ОС.
    
    Returns:
        Path: Путь к файлу иконки
    """
    # Список возможных мест расположения иконки
    icon_locations = [
        Path('icon.png'),                         # В текущей директории
        Path('desktop_app/icon.png'),             # В директории desktop_app
        Path(__file__).parent / 'icon.png',       # В директории скрипта
        get_app_data_path() / 'icon.png',         # В директории данных приложения
    ]
    
    # Добавляем специфические для каждой ОС пути
    system = platform.system()
    if system == 'Windows':
        # Для Windows проверяем в Program Files и AppData
        icon_locations.extend([
            Path(os.environ.get('LOCALAPPDATA', '')) / 'TimeTracker' / 'icon.png',
            Path(os.environ.get('APPDATA', '')) / 'TimeTracker' / 'icon.png',
            Path(os.environ.get('PROGRAMFILES', '')) / 'TimeTracker' / 'icon.png',
            Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'TimeTracker' / 'icon.png',
        ])
    elif system == 'Linux':
        # Для Linux проверяем в стандартных директориях иконок и приложений
        icon_locations.extend([
            Path('/usr/share/icons/hicolor/128x128/apps/timetracker.png'),
            Path('/usr/share/pixmaps/timetracker.png'),
            Path('/usr/local/share/timetracker/icon.png'),
            Path(os.path.expanduser('~/.local/share/TimeTracker/icon.png')),
        ])
    elif system == 'Darwin':  # macOS
        # Для macOS проверяем в директории приложений и ресурсов
        icon_locations.extend([
            Path('/Applications/TimeTracker.app/Contents/Resources/icon.png'),
            Path(os.path.expanduser('~/Applications/TimeTracker.app/Contents/Resources/icon.png')),
            Path(os.path.expanduser('~/Library/Application Support/TimeTracker/icon.png')),
        ])
        
    # Проверяем наличие иконки в указанных местах
    for icon_path in icon_locations:
        if icon_path.exists():
            logger.debug(f"Найдена иконка: {icon_path}")
            return icon_path
            
    # Если иконка не найдена, возвращаем путь в текущей директории
    # (даже если файл не существует - его нужно будет создать)
    default_icon_path = Path(__file__).parent / 'icon.png'
    logger.warning(f"Иконка не найдена. Будет использован путь по умолчанию: {default_icon_path}")
    return default_icon_path

def get_app_data_path(app_name: str = "TimeTracker") -> Path:
    """
    Получает путь к директории данных приложения для текущей ОС.
    
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
            base_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
    elif system == 'Linux':
        # На Linux используем ~/.config
        base_dir = os.path.join(os.path.expanduser('~'), '.config')
    elif system == 'Darwin':  # macOS
        # На macOS используем ~/Library/Application Support
        base_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        # Для других ОС используем временную директорию
        base_dir = os.path.join(os.path.expanduser('~'), '.local', 'share')
        
    return Path(os.path.join(base_dir, app_name))

def create_app_icon() -> QIcon:
    """
    Создает QIcon для приложения. Если иконка не найдена, использует стандартную.
    
    Returns:
        QIcon: Иконка приложения
    """
    # Получаем путь к файлу иконки
    icon_path = get_icon_path()
    
    # Проверяем, существует ли файл
    if icon_path.exists():
        try:
            # Пробуем загрузить иконку из файла
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                logger.debug(f"Успешно загружена иконка из {icon_path}")
                return icon
        except Exception as e:
            logger.error(f"Ошибка при загрузке иконки из {icon_path}: {e}")
    
    # Если иконка не найдена или не удалось загрузить, используем встроенную иконку Qt
    try:
        # Пробуем использовать стандартную иконку из темы
        system_icon = QIcon.fromTheme("utilities-system-monitor")
        if not system_icon.isNull():
            logger.debug("Используется системная иконка 'utilities-system-monitor'")
            return system_icon
            
        # Пробуем другие иконки из темы
        for icon_name in ["application-x-executable", "utilities-terminal", "preferences-system", "applications-system"]:
            system_icon = QIcon.fromTheme(icon_name)
            if not system_icon.isNull():
                logger.debug(f"Используется системная иконка '{icon_name}'")
                return system_icon
    except Exception as e:
        logger.error(f"Ошибка при загрузке системной иконки: {e}")
    
    # Если не удалось найти ни одной подходящей иконки, создаем пустую
    logger.warning("Не удалось найти подходящую иконку. Используется пустая иконка.")
    return QIcon()

def ensure_icon_exists() -> Optional[Path]:
    """
    Убеждается, что файл иконки существует. Если нет - создает пустую иконку.
    
    Returns:
        Optional[Path]: Путь к файлу иконки или None, если не удалось создать
    """
    icon_path = get_icon_path()
    
    # Если иконка уже существует, просто возвращаем путь
    if icon_path.exists():
        return icon_path
        
    # Иначе пытаемся создать директорию для иконки
    try:
        icon_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Создаем минимальную иконку (пустой пиксель)
        pixmap = QPixmap(64, 64)
        pixmap.fill()  # Заполняем прозрачным цветом
        
        # Сохраняем в файл
        if pixmap.save(str(icon_path), 'PNG'):
            logger.info(f"Создан файл иконки по умолчанию: {icon_path}")
            return icon_path
        else:
            logger.error(f"Не удалось сохранить иконку в {icon_path}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при создании файла иконки: {e}")
        return None 