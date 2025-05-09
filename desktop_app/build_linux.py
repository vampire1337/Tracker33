import PyInstaller.__main__
import os
import shutil
from pathlib import Path
import site
import sys

def build_app():
    # Пути к файлам
    current_dir = Path(__file__).parent
    main_script = current_dir / 'main.py'
    icon_file = current_dir / 'icon.png'
    config_file = current_dir / 'config.ini'
    
    # Проверим структуру PyQt5
    pyqt5_path = None
    for site_packages in site.getsitepackages():
        pyqt5_candidate = Path(site_packages) / 'PyQt5'
        if pyqt5_candidate.exists():
            pyqt5_path = pyqt5_candidate
            break
    
    if not pyqt5_path:
        raise RuntimeError("PyQt5 не найден в site-packages")
    
    print(f"PyQt5 найден в: {pyqt5_path}")
    
    # Проверим существование директорий с плагинами Qt
    qt_platform_path = None
    qt_styles_path = None
    qt_imageformats_path = None
    
    # Проверяем различные возможные пути для Linux
    possible_paths = [
        pyqt5_path / 'Qt5' / 'plugins',
        pyqt5_path / 'Qt' / 'plugins',
        pyqt5_path / 'plugins',
        Path('/usr/lib/qt5/plugins'),
        Path('/usr/lib/x86_64-linux-gnu/qt5/plugins')
    ]
    
    # Ищем существующие пути для плагинов
    for base_path in possible_paths:
        if (base_path / 'platforms').exists():
            qt_platform_path = base_path / 'platforms'
            print(f"Найдены платформенные плагины: {qt_platform_path}")
        
        if (base_path / 'styles').exists():
            qt_styles_path = base_path / 'styles'
            print(f"Найдены плагины стилей: {qt_styles_path}")
            
        if (base_path / 'imageformats').exists():
            qt_imageformats_path = base_path / 'imageformats'
            print(f"Найдены плагины форматов изображений: {qt_imageformats_path}")
    
    # Создаем директорию для сборки
    build_dir = current_dir / 'build'
    dist_dir = current_dir / 'dist'
    
    # Очищаем предыдущие сборки
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Базовые параметры сборки
    params = [
        str(main_script),  # Основной скрипт
        '--name=TimeTracker',  # Имя приложения
        '--onefile',  # Собираем в один файл
        '--windowed',  # Без консоли
        f'--add-data={icon_file}:.',  # Добавляем иконку
        f'--add-data={config_file}:.',  # Добавляем конфиг
        '--clean',  # Очистка перед сборкой
        '--noconfirm',  # Без подтверждений
        
        # PyQt5 специфичные параметры
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtNetwork',
        '--hidden-import=PyQt5.sip',
    ]
    
    # Добавляем плагины только если они существуют
    if qt_platform_path:
        params.append(f'--add-binary={qt_platform_path}/*:platforms')
    
    if qt_styles_path:
        params.append(f'--add-binary={qt_styles_path}/*:styles')
    
    if qt_imageformats_path:
        params.append(f'--add-binary={qt_imageformats_path}/*:imageformats')
    
    # Отключаем ненужные модули Qt
    params.extend([
        '--exclude-module=PyQt5.Qt3DCore',
        '--exclude-module=PyQt5.Qt3DRender',
        '--exclude-module=PyQt5.Qt3DInput',
        '--exclude-module=PyQt5.Qt3DLogic',
        '--exclude-module=PyQt5.Qt3DAnimation',
        '--exclude-module=PyQt5.Qt3DExtras',
        '--exclude-module=PyQt5.QtWebEngine',
        '--exclude-module=PyQt5.QtMultimedia',
        '--exclude-module=PyQt5.QtQuick',
    ])
    
    # Если нам не удалось найти плагины Qt, попробуем собрать версию без них
    if not qt_platform_path and not qt_styles_path and not qt_imageformats_path:
        print("ВНИМАНИЕ: Не найдены плагины Qt. Сборка может быть неполной и несовместимой с Windows.")
    
    # Запускаем сборку
    print("Запуск PyInstaller со следующими параметрами:")
    for param in params:
        print(f"  {param}")
        
    PyInstaller.__main__.run(params)
    
    # Создаем директории для логов и данных в dist
    dist_dir = current_dir / 'dist'
    if dist_dir.exists():
        (dist_dir / 'logs').mkdir(exist_ok=True)
        (dist_dir / 'data').mkdir(exist_ok=True)
        
        # Для Linux сборки файл не будет иметь .exe расширение
        dist_exe = dist_dir / 'TimeTracker'
        
        # Переименовываем в .exe для совместимости с Windows
        if dist_exe.exists():
            target_exe = dist_dir / 'TimeTracker.exe'
            shutil.copy2(dist_exe, target_exe)
            print(f"Скопирован {dist_exe} в {target_exe}")
            
            # Копируем исполняемый файл в корневой каталог dist/ сервера
            server_dist = Path(current_dir.parent, 'dist')
            server_dist.mkdir(exist_ok=True)
            server_target = server_dist / 'TimeTracker.exe'
            shutil.copy2(dist_exe, server_target)
            print(f"Скопирован {dist_exe} в {server_target}")
    
    print("Сборка завершена!")

if __name__ == '__main__':
    build_app() 