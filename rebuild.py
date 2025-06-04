#!/usr/bin/env python3
import os
import shutil
import subprocess

def rebuild_client():
    """Пересобирает клиент с актуальными настройками"""
    
    # Очищаем старые файлы сборки
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('TimeTracker.spec'):
        os.remove('TimeTracker.spec')
    
    # Переходим в папку с клиентом
    os.chdir('desktop_app')
    
    # Собираем EXE
    cmd = [
        'python', '-m', 'PyInstaller',
        '--onefile',
        '--noconsole', 
        '--icon=icon.ico',
        '--add-data', 'config.ini:.',
        '--name', 'TimeTracker',
        'main.py'
    ]
    
    print("Собираю клиент...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Сборка успешна!")
        
        # Копируем в static
        os.chdir('..')
        if os.path.exists('desktop_app/dist/TimeTracker.exe'):
            shutil.copy2('desktop_app/dist/TimeTracker.exe', 'static/TimeTracker.exe')
            shutil.copy2('desktop_app/dist/TimeTracker.exe', 'staticfiles/downloads/TimeTracker.exe')
            print("✅ Файл скопирован в static/ и staticfiles/downloads/")
        
        # Показываем размер файла
        if os.path.exists('static/TimeTracker.exe'):
            size = os.path.getsize('static/TimeTracker.exe') / (1024*1024)
            print(f"📦 Размер файла: {size:.1f} МБ")
    else:
        print("❌ Ошибка сборки:")
        print(result.stderr)

if __name__ == '__main__':
    rebuild_client() 