# Инструкции по сборке TimeTracker для Windows

## Проблема
Клиент собрался на Linux, но нужен Windows EXE.

## Решение 1: Сборка на Windows машине

### Шаги:
1. Скопируйте папку `desktop_app/` на Windows машину
2. Установите Python 3.10+ и зависимости:
   ```cmd
   pip install -r desktop_app/requirements.txt
   pip install pyinstaller
   ```
3. Соберите EXE:
   ```cmd
   cd desktop_app
   pyinstaller --onefile --noconsole --icon=icon.ico --add-data "config.ini;." --name TimeTracker main.py
   ```
4. Найдите готовый EXE в `desktop_app/dist/TimeTracker.exe`

## Решение 2: Использовать готовую конфигурацию

### Текущая правильная конфигурация в config.ini:
```ini
[API]
base_url = http://147.45.153.16:8001

[Server]  
base_url = http://147.45.153.16:8001

[Credentials]
api_base_url = http://147.45.153.16:8001/api/

[Settings]
update_interval = 5
log_level = INFO
auto_start = false
minimize_to_tray = true
idle_threshold_seconds = 300
send_interval_seconds = 10
max_send_batch_size = 20
demo_mode = false
```

### Тестовые данные для входа:
- **Логин**: client
- **Пароль**: 123456

## Решение 3: Автоматическая сборка (если есть GitHub Actions)

Можно настроить GitHub Actions для автоматической сборки Windows EXE при пуше в репозиторий.

## Важно!
Старый файл `static/TimeTracker.exe` (47MB от 3 июня) содержит localhost настройки и не будет работать с удаленным сервером. 