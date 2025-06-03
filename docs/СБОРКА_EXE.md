# 🔨 Инструкция по сборке EXE файла Tracker33

## 📋 Подготовка к сборке

### Системные требования для сборки
- **ОС**: Windows 10/11 (рекомендуется)
- **Python**: 3.8 или выше
- **RAM**: минимум 4 ГБ
- **Место на диске**: 2 ГБ свободного места
- **Интернет**: для загрузки зависимостей

### Предварительная установка
```bash
# Обновляем pip
python -m pip install --upgrade pip

# Устанавливаем основные зависимости
pip install pyinstaller>=5.0
pip install pywin32
```

## 🚀 Автоматическая сборка

### Простой способ
```bash
# Переходим в папку проекта
cd Tracker33

# Запускаем автоматическую сборку
cd build
python build_exe.py
```

### Что происходит при автоматической сборке:
1. ✅ Проверка системных требований
2. 📦 Установка всех зависимостей
3. 🎨 Создание иконки приложения
4. 🔨 Сборка EXE файла с PyInstaller
5. 📁 Создание установочных файлов
6. 📝 Генерация документации
7. 🗑️ Создание деинсталлятора

## 🔧 Ручная сборка (для продвинутых пользователей)

### Шаг 1: Установка зависимостей
```bash
cd desktop_app
pip install -r requirements.txt
```

### Шаг 2: Создание иконки (опционально)
```bash
# Если у вас есть PIL/Pillow
pip install Pillow

# Иконка создастся автоматически при сборке
```

### Шаг 3: Сборка с PyInstaller
```bash
pyinstaller --onefile --windowed \
    --icon=icon.ico \
    --name=Tracker33 \
    --add-data "config.ini;." \
    --hidden-import PyQt5.QtCore \
    --hidden-import PyQt5.QtGui \
    --hidden-import PyQt5.QtWidgets \
    --hidden-import pynput \
    --hidden-import psutil \
    --hidden-import requests \
    --exclude-module tkinter \
    main.py
```

## 📁 Структура готового пакета

После успешной сборки в папке `dist/` будут созданы:

```
dist/
├── Tracker33.exe          # Основной исполняемый файл
├── config.ini             # Файл конфигурации
├── install.bat            # Скрипт установки
├── uninstall.bat          # Скрипт удаления
└── README.txt             # Инструкция для пользователя
```

## 🎯 Параметры сборки

### Основные флаги PyInstaller
- `--onefile` - создает один EXE файл
- `--windowed` - скрывает консоль (для GUI приложений)
- `--icon=icon.ico` - добавляет иконку
- `--name=Tracker33` - имя итогового файла
- `--clean` - очищает кэш перед сборкой
- `--noconfirm` - не запрашивает подтверждения

### Скрытые импорты
Добавляем модули, которые PyInstaller может не обнаружить автоматически:
```bash
--hidden-import PyQt5.QtCore
--hidden-import PyQt5.QtGui
--hidden-import PyQt5.QtWidgets
--hidden-import pynput.keyboard
--hidden-import pynput.mouse
--hidden-import win32gui
--hidden-import win32process
```

### Исключения
Исключаем ненужные модули для уменьшения размера:
```bash
--exclude-module tkinter
--exclude-module matplotlib
--exclude-module numpy
--exclude-module pandas
```

## 🔍 Устранение проблем

### Проблема: "Module not found"
**Решение**: Добавьте модуль в `--hidden-import`
```bash
--hidden-import имя_модуля
```

### Проблема: Большой размер EXE
**Решение**: Добавьте исключения
```bash
--exclude-module ненужный_модуль
```

### Проблема: Антивирус блокирует EXE
**Решение**: 
1. Добавьте папку сборки в исключения антивируса
2. Используйте цифровую подпись для EXE файла

### Проблема: Ошибка при запуске EXE
**Решение**: Проверьте логи
```bash
# Запустите EXE из командной строки для просмотра ошибок
Tracker33.exe
```

## 🛡️ Цифровая подпись (опционально)

### Для корпоративного использования рекомендуется подписать EXE:
```bash
# Используйте signtool.exe из Windows SDK
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com Tracker33.exe
```

## 📊 Оптимизация размера

### Способы уменьшения размера EXE:
1. **Исключение ненужных модулей**
2. **Использование UPX компрессии**
3. **Удаление отладочной информации**

### UPX компрессия:
```bash
# Установите UPX
# Скачайте с https://upx.github.io/

# Сжимайте EXE после сборки
upx --best Tracker33.exe
```

## 🔄 Автоматизация сборки

### GitHub Actions (для CI/CD):
```yaml
name: Build EXE
on: [push]
jobs:
  build:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r desktop_app/requirements.txt
        pip install pyinstaller
    - name: Build EXE
      run: python build/build_exe.py
    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: Tracker33-EXE
        path: dist/
```

## 📝 Чек-лист перед релизом

- [ ] ✅ Все тесты пройдены
- [ ] 🔧 Конфигурация обновлена
- [ ] 🎨 Иконка создана
- [ ] 📦 EXE собран без ошибок
- [ ] 🧪 EXE протестирован на чистой системе
- [ ] 📝 Документация обновлена
- [ ] 🛡️ Антивирусы не блокируют
- [ ] 📊 Размер файла приемлемый
- [ ] 🔍 Нет утечек памяти
- [ ] 🚀 Готов к распространению

## 📞 Поддержка

При возникновении проблем со сборкой:
1. Проверьте версии Python и зависимостей
2. Убедитесь что все файлы на месте
3. Запустите сборку с флагом `--debug`
4. Проверьте логи в папке `build/`

---

**Успешной сборки!** 🎉 