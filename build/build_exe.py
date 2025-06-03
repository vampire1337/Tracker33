#!/usr/bin/env python3
"""
Скрипт сборки EXE файла для Tracker33
Создает готовый к распространению исполняемый файл
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Tracker33Builder:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.desktop_app_dir = self.project_root / "desktop_app"
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.icon_path = self.desktop_app_dir / "icon.ico"
        
        # Создаем иконку если её нет
        if not self.icon_path.exists():
            self.create_default_icon()
    
    def check_requirements(self):
        """Проверяем системные требования"""
        logger.info("🔍 Проверка системных требований...")
        
        # Проверяем Python версию
        if sys.version_info < (3, 8):
            raise RuntimeError("Требуется Python 3.8 или выше")
        
        # Проверяем ОС
        if platform.system() != "Windows":
            logger.warning("⚠️ Сборка оптимизирована для Windows")
        
        # Проверяем наличие PyInstaller
        try:
            import PyInstaller
            logger.info(f"✅ PyInstaller {PyInstaller.__version__} найден")
        except ImportError:
            logger.info("📦 Устанавливаем PyInstaller...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
        logger.info("✅ Системные требования выполнены")
    
    def install_dependencies(self):
        """Устанавливаем все зависимости"""
        logger.info("📦 Установка зависимостей...")
        
        requirements_file = self.desktop_app_dir / "requirements.txt"
        if requirements_file.exists():
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "-r", str(requirements_file)
            ])
        
        # Дополнительные зависимости для сборки
        build_deps = [
            "pyinstaller>=5.0",
            "pywin32",  # Для Windows
        ]
        
        for dep in build_deps:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            except subprocess.CalledProcessError:
                logger.warning(f"⚠️ Не удалось установить {dep}")
        
        logger.info("✅ Зависимости установлены")
    
    def create_default_icon(self):
        """Создаем иконку по умолчанию"""
        logger.info("🎨 Создание иконки...")
        
        try:
            from PIL import Image, ImageDraw
            
            # Создаем простую иконку 256x256
            size = 256
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Рисуем круг
            margin = 20
            draw.ellipse([margin, margin, size-margin, size-margin], 
                        fill=(52, 152, 219, 255), outline=(41, 128, 185, 255), width=4)
            
            # Рисуем текст "T33"
            from PIL import ImageFont
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                font = ImageFont.load_default()
            
            text = "T33"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (size - text_width) // 2
            y = (size - text_height) // 2
            
            draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
            
            # Сохраняем в разных размерах для ICO
            img.save(str(self.icon_path), format='ICO', sizes=[(16,16), (32,32), (48,48), (256,256)])
            logger.info(f"✅ Иконка создана: {self.icon_path}")
            
        except ImportError:
            logger.warning("⚠️ PIL не найден, создаем простую иконку")
            # Создаем минимальную иконку
            icon_data = b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x08\x00\x68\x05\x00\x00\x16\x00\x00\x00'
            self.icon_path.write_bytes(icon_data)
    
    def build_exe(self):
        """Собираем EXE файл"""
        logger.info("🔨 Сборка EXE файла...")
        
        # Очищаем предыдущие сборки
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        
        build_temp = self.build_dir / "build"
        if build_temp.exists():
            shutil.rmtree(build_temp)
        
        # Запускаем PyInstaller с параметрами
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            f"--icon={self.icon_path}",
            f"--name=Tracker33",
            "--clean",
            "--noconfirm",
            "--add-data", f"{self.desktop_app_dir / 'config.ini'};.",
            "--hidden-import", "PyQt5.QtCore",
            "--hidden-import", "PyQt5.QtGui", 
            "--hidden-import", "PyQt5.QtWidgets",
            "--hidden-import", "PyQt5.QtNetwork",
            "--hidden-import", "pynput",
            "--hidden-import", "pynput.keyboard",
            "--hidden-import", "pynput.mouse",
            "--hidden-import", "psutil",
            "--hidden-import", "requests",
            "--hidden-import", "win32gui",
            "--hidden-import", "win32process",
            "--hidden-import", "win32con",
            "--hidden-import", "win32api",
            "--exclude-module", "tkinter",
            "--exclude-module", "matplotlib",
            str(self.desktop_app_dir / "main.py")
        ]
        
        logger.info(f"Команда сборки: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=str(self.project_root), capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ Ошибка сборки: {result.stderr}")
            raise RuntimeError("Сборка завершилась с ошибкой")
        
        logger.info("✅ EXE файл успешно собран!")
    
    def create_installer_script(self):
        """Создаем скрипт установки"""
        logger.info("📦 Создание скрипта установки...")
        
        installer_script = '''@echo off
echo.
echo ===============================================
echo   Tracker33 - Установка системы мониторинга
echo ===============================================
echo.

REM Проверяем права администратора
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Права администратора подтверждены
) else (
    echo [ERROR] Требуются права администратора!
    echo Пожалуйста, запустите от имени администратора
    pause
    exit /b 1
)

REM Создаем директорию программы
set INSTALL_DIR=%ProgramFiles%\\Tracker33
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [INFO] Копирование файлов в %INSTALL_DIR%...
copy "Tracker33.exe" "%INSTALL_DIR%\\" >nul
if exist "config.ini" copy "config.ini" "%INSTALL_DIR%\\" >nul

REM Создаем ярлык на рабочем столе
echo [INFO] Создание ярлыка на рабочем столе...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\Tracker33.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\Tracker33.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Tracker33 - Система мониторинга активности'; $Shortcut.Save()"

REM Создаем ярлык в меню пуск
echo [INFO] Создание ярлыка в меню пуск...
set START_MENU=%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs
if not exist "%START_MENU%\\Tracker33" mkdir "%START_MENU%\\Tracker33"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%\\Tracker33\\Tracker33.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\Tracker33.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Tracker33 - Система мониторинга активности'; $Shortcut.Save()"

REM Добавляем в автозагрузку (опционально)
echo [INFO] Добавление в автозагрузку...
reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "Tracker33" /t REG_SZ /d "%INSTALL_DIR%\\Tracker33.exe" /f >nul

REM Настройка брандмауэра
echo [INFO] Настройка брандмауэра...
netsh advfirewall firewall add rule name="Tracker33" dir=out action=allow program="%INSTALL_DIR%\\Tracker33.exe" >nul 2>&1

echo.
echo [SUCCESS] Установка завершена успешно!
echo.
echo [INFO] Программа установлена в: %INSTALL_DIR%
echo [INFO] Ярлыки созданы на рабочем столе и в меню пуск
echo [INFO] Автозапуск настроен
echo.
echo Запустите Tracker33 с рабочего стола или из меню пуск
echo.
pause
'''
        
        installer_file = self.dist_dir / "install.bat"
        installer_file.write_text(installer_script, encoding='utf-8')
        logger.info(f"✅ Скрипт установки создан: {installer_file}")
    
    def create_readme(self):
        """Создаем README для пользователей"""
        logger.info("📝 Создание README...")
        
        readme_content = '''# Tracker33 - Система мониторинга активности ПК

## Быстрая установка

1. **Скачайте** Tracker33.exe
2. **Запустите** файл **ОТ ИМЕНИ АДМИНИСТРАТОРА**
3. **Следуйте** инструкциям на экране

## Что делать после установки:

1. Запустите Tracker33 с рабочего стола
2. При первом запуске введите данные для входа:
   - Сервер: http://147.45.153.16:8000/
   - Логин и пароль (получите у администратора)
3. Программа начнет автоматически отслеживать активность

## Основные функции:

- Автоматическое отслеживание всех приложений
- Подсчет клавиатурной активности
- Мониторинг времени работы
- Веб-интерфейс для просмотра статистики
- Работа в фоновом режиме

## Системные требования:

- Windows 10 (версия 1903+) или Windows 11
- 512 МБ свободной памяти
- 50 МБ места на диске
- Подключение к интернету

## Важно:

- Обязательно запускайте программу **ОТ ИМЕНИ АДМИНИСТРАТОРА**
- Добавьте Tracker33.exe в исключения антивируса
- Программа работает в фоновом режиме (иконка в трее)

## Поддержка:

- Веб-интерфейс: http://147.45.153.16:8000/
- Техподдержка: support@tracker33.com

---
© 2024 Tracker33. Все права защищены.
'''
        
        readme_file = self.dist_dir / "README.txt"
        readme_file.write_text(readme_content, encoding='utf-8')
        logger.info(f"✅ README создан: {readme_file}")
    
    def create_uninstaller(self):
        """Создаем деинсталлятор"""
        logger.info("🗑️ Создание деинсталлятора...")
        
        uninstaller_script = '''@echo off
echo.
echo ===============================================
echo   Tracker33 - Удаление программы
echo ===============================================
echo.

REM Проверяем права администратора
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Права администратора подтверждены
) else (
    echo [ERROR] Требуются права администратора!
    pause
    exit /b 1
)

echo [WARNING] Это действие удалит Tracker33 с вашего компьютера
set /p confirm=Продолжить? (y/N): 
if /i "%confirm%" neq "y" (
    echo Отмена удаления
    pause
    exit /b 0
)

echo [INFO] Остановка процесса...
taskkill /f /im "Tracker33.exe" >nul 2>&1

echo [INFO] Удаление файлов...
set INSTALL_DIR=%ProgramFiles%\\Tracker33
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"

echo [INFO] Удаление ярлыков...
del "%USERPROFILE%\\Desktop\\Tracker33.lnk" >nul 2>&1
rmdir /s /q "%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs\\Tracker33" >nul 2>&1

echo [INFO] Удаление из автозагрузки...
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "Tracker33" /f >nul 2>&1

echo [INFO] Удаление правил брандмауэра...
netsh advfirewall firewall delete rule name="Tracker33" >nul 2>&1

echo.
echo [SUCCESS] Удаление завершено!
pause
'''
        
        uninstaller_file = self.dist_dir / "uninstall.bat"
        uninstaller_file.write_text(uninstaller_script, encoding='utf-8')
        logger.info(f"✅ Деинсталлятор создан: {uninstaller_file}")
    
    def optimize_exe(self):
        """Оптимизируем EXE файл"""
        logger.info("⚡ Оптимизация EXE файла...")
        
        exe_file = self.dist_dir / "Tracker33.exe"
        if not exe_file.exists():
            logger.error("❌ EXE файл не найден!")
            return
        
        # Проверяем размер
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        logger.info(f"📏 Размер EXE файла: {size_mb:.1f} МБ")
        
        if size_mb > 100:
            logger.warning("⚠️ EXE файл достаточно большой, рассмотрите оптимизацию зависимостей")
    
    def create_package(self):
        """Создаем итоговый пакет"""
        logger.info("📦 Создание итогового пакета...")
        
        # Копируем дополнительные файлы
        config_src = self.desktop_app_dir / "config.ini"
        if config_src.exists():
            shutil.copy2(config_src, self.dist_dir / "config.ini")
        
        # Создаем все дополнительные файлы
        self.create_installer_script()
        self.create_readme()
        self.create_uninstaller()
        
        # Показываем содержимое
        logger.info("📁 Содержимое пакета:")
        for item in self.dist_dir.iterdir():
            if item.is_file():
                size = item.stat().st_size
                if size > 1024*1024:
                    size_str = f"{size/(1024*1024):.1f} МБ"
                elif size > 1024:
                    size_str = f"{size/1024:.1f} КБ"
                else:
                    size_str = f"{size} байт"
                logger.info(f"  📄 {item.name} ({size_str})")
        
        logger.info(f"✅ Пакет готов в: {self.dist_dir}")
    
    def run(self):
        """Основная функция сборки"""
        try:
            logger.info("🚀 Начинаем сборку Tracker33...")
            
            self.check_requirements()
            self.install_dependencies()
            self.build_exe()
            self.optimize_exe()
            self.create_package()
            
            logger.info("🎉 Сборка завершена успешно!")
            logger.info(f"📦 Готовый пакет: {self.dist_dir}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сборки: {e}")
            sys.exit(1)

if __name__ == "__main__":
    builder = Tracker33Builder()
    builder.run() 