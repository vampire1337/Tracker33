"""
Утилиты для обработки данных приложений и активности пользователей
"""

import re
from typing import Dict, List, Tuple

# Черный список системных процессов и технических приложений
SYSTEM_PROCESSES_BLACKLIST = {
    'python.exe', 'python3.exe', 'pythonw.exe',
    'cmd.exe', 'powershell.exe', 'bash.exe',
    'explorer.exe', 'dwm.exe', 'winlogon.exe',
    'csrss.exe', 'smss.exe', 'lsass.exe',
    'services.exe', 'svchost.exe', 'spoolsv.exe',
    'taskhostw.exe', 'conhost.exe', 'dllhost.exe',
    'rundll32.exe', 'msiexec.exe', 'setup.exe',
    'installer.exe', 'updater.exe', 'launcher.exe',
    'node.exe', 'npm.exe', 'pip.exe',
    'git.exe', 'ssh.exe', 'curl.exe',
    'system', 'idle', 'system idle process',
    'registry', 'memory compression',
    'windows security health service',
    'windows defender', 'antimalware service executable'
}

# Правила группировки приложений
APP_GROUPING_RULES = {
    # Браузеры
    'chrome.exe': 'Google Chrome',
    'msedge.exe': 'Microsoft Edge', 
    'firefox.exe': 'Mozilla Firefox',
    'opera.exe': 'Opera',
    'brave.exe': 'Brave Browser',
    'vivaldi.exe': 'Vivaldi',
    'safari.exe': 'Safari',
    'iexplore.exe': 'Internet Explorer',
    'browser.exe': 'Yandex Browser',
    
    # Офисные приложения
    'word.exe': 'Microsoft Word',
    'winword.exe': 'Microsoft Word',
    'excel.exe': 'Microsoft Excel',
    'powerpnt.exe': 'Microsoft PowerPoint',
    'outlook.exe': 'Microsoft Outlook',
    
    # Редакторы кода
    'code.exe': 'Visual Studio Code',
    'devenv.exe': 'Visual Studio',
    'pycharm64.exe': 'PyCharm',
    'idea64.exe': 'IntelliJ IDEA',
    'sublime_text.exe': 'Sublime Text',
    'notepad++.exe': 'Notepad++',
    'atom.exe': 'Atom',
    
    # Мессенджеры
    'telegram.exe': 'Telegram',
    'discord.exe': 'Discord',
    'slack.exe': 'Slack',
    'teams.exe': 'Microsoft Teams',
    'whatsapp.exe': 'WhatsApp',
    'skype.exe': 'Skype',
    'zoom.exe': 'Zoom',
    
    # Медиа
    'spotify.exe': 'Spotify',
    'vlc.exe': 'VLC Media Player',
    'wmplayer.exe': 'Windows Media Player',
    'itunes.exe': 'iTunes',
    
    # Графика
    'photoshop.exe': 'Adobe Photoshop',
    'illustrator.exe': 'Adobe Illustrator',
    'figma.exe': 'Figma',
    'canva.exe': 'Canva',
    
    # Игры
    'steam.exe': 'Steam',
    'epicgameslauncher.exe': 'Epic Games',
    
    # Файлы
    'notepad.exe': 'Notepad',
    'winrar.exe': 'WinRAR',
    '7z.exe': '7-Zip',
}

# Продуктивные приложения по умолчанию
PRODUCTIVE_APPS_DEFAULT = {
    'Visual Studio Code', 'PyCharm', 'IntelliJ IDEA', 'Visual Studio',
    'Sublime Text', 'Notepad++', 'Atom',
    'Microsoft Word', 'Microsoft Excel', 'Microsoft PowerPoint',
    'Microsoft Outlook', 'Slack', 'Microsoft Teams', 'Zoom',
    'Adobe Photoshop', 'Adobe Illustrator', 'Figma', 'Canva',
    'Notepad'
}


def is_system_process(process_name: str) -> bool:
    """
    Проверяет, является ли процесс системным
    """
    if not process_name:
        return True
    
    process_lower = process_name.lower().strip()
    return process_lower in SYSTEM_PROCESSES_BLACKLIST


def normalize_app_name(process_name: str, window_title: str = "") -> Tuple[str, bool]:
    """
    Нормализует название приложения и определяет продуктивность
    
    Returns:
        Tuple[str, bool]: (normalized_name, is_productive)
    """
    if not process_name:
        return "Неизвестное приложение", False
    
    process_lower = process_name.lower().strip()
    
    # Проверяем системные процессы
    if is_system_process(process_lower):
        return None, False  # None означает, что процесс нужно игнорировать
    
    # Применяем правила группировки
    if process_lower in APP_GROUPING_RULES:
        normalized_name = APP_GROUPING_RULES[process_lower]
        is_productive = normalized_name in PRODUCTIVE_APPS_DEFAULT
        return normalized_name, is_productive
    
    # Пытаемся извлечь читаемое имя из названия процесса
    clean_name = process_name.replace('.exe', '').replace('_', ' ').title()
    
    # Особые случаи
    if 'code' in process_lower and 'visual' not in clean_name:
        return 'Visual Studio Code', True
    
    return clean_name, False


def group_applications_by_name(applications_data: List[Dict]) -> List[Dict]:
    """
    Группирует приложения по названию, суммируя время использования
    """
    grouped = {}
    
    for app_data in applications_data:
        # Нормализуем название
        process_name = app_data.get('process_name', '')
        window_title = app_data.get('window_title', '')
        
        normalized_result = normalize_app_name(process_name, window_title)
        if normalized_result[0] is None:  # Системный процесс - игнорируем
            continue
            
        normalized_name, default_productive = normalized_result
        
        if normalized_name in grouped:
            # Суммируем время
            grouped[normalized_name]['total_seconds'] += app_data.get('total_seconds', 0)
            grouped[normalized_name]['activities_count'] += app_data.get('activities_count', 1)
        else:
            # Создаем новую запись
            grouped[normalized_name] = {
                'name': normalized_name,
                'process_name': process_name,  # Сохраняем оригинальное имя для справки
                'total_seconds': app_data.get('total_seconds', 0),
                'activities_count': app_data.get('activities_count', 1),
                'is_productive': app_data.get('is_productive', default_productive),
                'id': app_data.get('id')  # Берем ID одного из приложений
            }
    
    # Сортируем по времени использования
    return sorted(grouped.values(), key=lambda x: x['total_seconds'], reverse=True)


def filter_user_applications(applications_queryset):
    """
    Фильтрует приложения, исключая системные процессы
    """
    filtered_apps = []
    
    for app in applications_queryset:
        normalized_result = normalize_app_name(app.process_name)
        if normalized_result[0] is not None:  # Не системный процесс
            normalized_name, default_productive = normalized_result
            app.normalized_name = normalized_name
            app.default_productive = default_productive
            filtered_apps.append(app)
    
    return filtered_apps


def format_duration(total_seconds: int) -> str:
    """
    Форматирует длительность в читаемый вид
    """
    if not total_seconds:
        return "00:00:00"
    
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def calculate_productivity_stats(applications_data: List[Dict]) -> Dict:
    """
    Рассчитывает статистику продуктивности
    """
    total_seconds = sum(app.get('total_seconds', 0) for app in applications_data)
    productive_seconds = sum(
        app.get('total_seconds', 0) for app in applications_data 
        if app.get('is_productive', False)
    )
    
    productivity_percent = 0
    if total_seconds > 0:
        productivity_percent = round((productive_seconds / total_seconds) * 100, 1)
    
    return {
        'total_seconds': total_seconds,
        'total_time': format_duration(total_seconds),
        'productive_seconds': productive_seconds,
        'productive_time': format_duration(productive_seconds),
        'productivity_percent': productivity_percent,
        'apps_count': len(applications_data)
    } 