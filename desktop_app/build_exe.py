#!/usr/bin/env python3
"""
🔨 Сборка EXE файла для Tracker33
Обновленная версия с поддержкой QR-аутентификации
"""

import sys
import os
import shutil
from pathlib import Path
import subprocess

def build_exe():
    """Сборка исполняемого файла"""
    
    print("🔨 Начинаем сборку Tracker33 с QR-аутентификацией...")
    
    # Проверяем наличие PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller найден: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller не найден. Устанавливаем...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Проверяем зависимости для QR
    required_packages = [
        'qrcode', 'cv2', 'pyzbar', 'PyQt6', 
        'requests', 'aiohttp', 'psutil', 'pynput'
    ]
    
    print("🔍 Проверяем зависимости...")
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} не найден")
            return False
    
    # Создаем иконку если её нет
    icon_path = Path("tracker33_icon.ico")
    if not icon_path.exists():
        print("🎨 Создаем иконку...")
        try:
            from create_icon import create_icon
            create_icon()
        except Exception as e:
            print(f"⚠️ Не удалось создать иконку: {e}")
    
    # Параметры сборки
    build_args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Один файл
        "--windowed",                   # Без консоли
        "--name=Tracker33",             # Имя файла
        "--distpath=../dist",           # Папка вывода
        "--workpath=../build",          # Рабочая папка
        "--specpath=../",               # Папка spec файла
        
        # Скрытые импорты для QR-аутентификации
        "--hidden-import=cv2",
        "--hidden-import=pyzbar",
        "--hidden-import=pyzbar.pyzbar",
        "--hidden-import=qrcode",
        "--hidden-import=qrcode.image.pil",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=numpy",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui", 
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=requests",
        "--hidden-import=aiohttp",
        "--hidden-import=psutil",
        "--hidden-import=pynput",
        "--hidden-import=json",
        "--hidden-import=threading",
        "--hidden-import=queue",
        "--hidden-import=datetime",
        "--hidden-import=platform",
        "--hidden-import=logging",
        
        # Основной файл
        "modern_client.py"
    ]
    
    # Убираем пустые аргументы
    build_args = [arg for arg in build_args if arg]
    
    print("🚀 Запускаем PyInstaller...")
    print(f"Команда: {' '.join(build_args)}")
    
    try:
        result = subprocess.run(build_args, check=True, capture_output=True, text=True)
        print("✅ Сборка завершена успешно!")
        
        # Проверяем результат
        exe_path = Path("../dist/Tracker33.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Создан файл: {exe_path}")
            print(f"📏 Размер: {size_mb:.1f} MB")
            
            # Создаем конфигурационный файл
            config_path = exe_path.parent / "config.json"
            if not config_path.exists():
                import json
                default_config = {
                    "server_url": "http://localhost:8000",
                    "api_url": "http://localhost:8000/api",
                    "username": "",
                    "password": "",
                    "auth_token": "",
                    "user_id": None,
                    "update_interval": 60,
                    "auto_start": False,
                    "minimize_to_tray": True,
                    "qr_auth_enabled": True,
                    "camera_index": 0
                }
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                print(f"⚙️ Создан config.json: {config_path}")
            
            return True
        else:
            print("❌ EXE файл не найден после сборки")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки: {e}")
        print(f"Вывод: {e.stdout}")
        print(f"Ошибки: {e.stderr}")
        return False

def clean_build():
    """Очистка временных файлов"""
    print("🧹 Очистка временных файлов...")
    
    paths_to_clean = [
        "../build",
        "../dist", 
        "../Tracker33.spec",
        "__pycache__"
    ]
    
    for path in paths_to_clean:
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.is_dir():
                shutil.rmtree(path_obj)
            else:
                path_obj.unlink()
            print(f"🗑️ Удален: {path}")

def main():
    """Главная функция"""
    print("=" * 60)
    print("�� СБОРКА TRACKER33 С QR-АУТЕНТИФИКАЦИЕЙ")
    print("=" * 60)
    
    # Переходим в папку desktop_app
    os.chdir(Path(__file__).parent)
    
    # Опционально очищаем старые файлы
    if "--clean" in sys.argv:
        clean_build()
    
    # Собираем EXE
    success = build_exe()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 СБОРКА ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 60)
        print("📦 Файл готов: ../dist/Tracker33.exe")
        print("⚙️ Конфигурация: ../dist/config.json")
        print("\n🚀 ИНСТРУКЦИИ ПО ЗАПУСКУ:")
        print("1. Запустите Django сервер: python manage.py runserver")
        print("2. Откройте браузер: http://localhost:8000/qr-connect/")
        print("3. Запустите Tracker33.exe")
        print("4. Выберите QR-аутентификацию")
        print("5. Сканируйте QR-код")
        print("\n✨ Готово к использованию!")
    else:
        print("\n❌ СБОРКА НЕУСПЕШНА")
        print("Проверьте ошибки выше и попробуйте снова")
        sys.exit(1)

if __name__ == "__main__":
    main() 