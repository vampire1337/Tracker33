import PyInstaller.__main__
import os
import shutil
from pathlib import Path
import site

def build_app():
    # Пути к файлам
    current_dir = Path(__file__).parent
    main_script = current_dir / 'main.py'
    icon_file = current_dir / 'icon.png'
    config_file = current_dir / 'config.ini'
    
    # Получаем путь к PyQt5 из site-packages
    pyqt5_path = None
    for site_packages in site.getsitepackages():
        pyqt5_candidate = Path(site_packages) / 'PyQt5'
        if pyqt5_candidate.exists():
            pyqt5_path = pyqt5_candidate
            break
    
    if not pyqt5_path:
        raise RuntimeError("PyQt5 не найден в site-packages")
    
    # Создаем директорию для сборки
    build_dir = current_dir / 'build'
    dist_dir = current_dir / 'dist'
    
    # Очищаем предыдущие сборки
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Параметры сборки
    params = [
        str(main_script),  # Основной скрипт
        '--name=TimeTracker',  # Имя приложения
        '--onefile',  # Собираем в один файл
        '--windowed',  # Без консоли
        f'--icon={icon_file}',  # Иконка приложения
        f'--add-data={icon_file};.',  # Добавляем иконку
        f'--add-data={config_file};.',  # Добавляем конфиг
        '--clean',  # Очистка перед сборкой
        '--noconfirm',  # Без подтверждений
        
        # PyQt5 специфичные параметры
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtNetwork',
        '--hidden-import=PyQt5.sip',
        '--collect-all=PyQt5.sip',  # Собираем все файлы sip
        
        # Добавляем необходимые Qt плагины
        f'--add-binary={pyqt5_path}/Qt5/plugins/platforms/*;platforms',
        f'--add-binary={pyqt5_path}/Qt5/plugins/styles/*;styles',
        f'--add-binary={pyqt5_path}/Qt5/plugins/imageformats/*;imageformats',
        
        # Отключаем ненужные модули Qt
        '--exclude-module=PyQt5.Qt3DCore',
        '--exclude-module=PyQt5.Qt3DRender',
        '--exclude-module=PyQt5.Qt3DInput',
        '--exclude-module=PyQt5.Qt3DLogic',
        '--exclude-module=PyQt5.Qt3DAnimation',
        '--exclude-module=PyQt5.Qt3DExtras',
        '--exclude-module=PyQt5.QtWebEngine',
        '--exclude-module=PyQt5.QtMultimedia',
        '--exclude-module=PyQt5.QtQuick',
    ]
    
    # Запускаем сборку
    PyInstaller.__main__.run(params)
    
    # Копируем дополнительные файлы
    dist_app = dist_dir / 'TimeTracker'
    if dist_app.exists():
        shutil.copy2(config_file, dist_app)
        shutil.copy2(icon_file, dist_app)
        
        # Создаем директории для логов и данных
        (dist_app / 'logs').mkdir(exist_ok=True)
        (dist_app / 'data').mkdir(exist_ok=True)
    
    print("Сборка завершена!")

if __name__ == '__main__':
    build_app() 