# Tracker33 - Система отслеживания времени и активности

Tracker33 - это полноценная система мониторинга рабочего времени и активности пользователя, состоящая из клиентского десктопного приложения и серверной части.

## Быстрый запуск

### Linux/Mac:
```bash
# Клонировать репозиторий
git clone https://your-repo-url/Tracker33.git
cd Tracker33

# Настроить .env файл (скопировать из примера и отредактировать)
cp .env.example .env
nano .env  # Отредактируйте настройки SMTP для работы функции восстановления пароля

# Запустить сервер
./start_server.sh
```

### Windows:
```cmd
# Клонировать репозиторий
git clone https://your-repo-url/Tracker33.git
cd Tracker33

# Настроить .env файл (скопировать из примера и отредактировать)
copy .env.example .env
# Отредактируйте .env файл в текстовом редакторе

# Запустить сервер
start_server.bat
```

## Настройка восстановления пароля

Для корректной работы функции восстановления пароля необходимо настроить параметры SMTP-сервера в файле `.env`:

```ini
# Email configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com
```

При использовании Gmail, вам потребуется создать пароль приложения в настройках безопасности аккаунта Google: https://myaccount.google.com/apppasswords

## Запуск клиентской части

### На Windows:
1. Скачайте клиентское приложение по ссылке: http://server-address:8000/users/download-tracker/
2. Распакуйте архив и запустите `TimeTracker.exe`
3. При первом запуске введите адрес сервера, логин и пароль

### На Linux:
1. Клонируйте репозиторий на локальную машину
2. Перейдите в директорию desktop_app
3. Установите зависимости: `pip install -r requirements.txt`
4. Запустите приложение: `python main.py`

## Подробные инструкции

### Структура системы

- **Серверная часть**: Django приложение для хранения и обработки данных
- **Клиентское приложение**: Десктопное приложение на PyQt для отслеживания активности пользователя
- **Веб-интерфейс**: Интерфейс для просмотра статистики и логов

### Требования

- Python 3.8+
- pip (менеджер пакетов Python)
- Доступ к SMTP-серверу для отправки писем (необходимо для восстановления пароля)

### Расширенная настройка сервера

Для продакшн-среды рекомендуется настроить:

1. **База данных PostgreSQL** вместо SQLite:
   ```python
   # В .env файле
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=tracker33
   DB_USER=tracker33_user
   DB_PASSWORD=your_strong_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

2. **Настройка веб-сервера Nginx + Gunicorn**:
   ```bash
   # Установка Gunicorn
   pip install gunicorn

   # Запуск через Gunicorn
   gunicorn --workers 3 --bind 0.0.0.0:8000 Tracker33.wsgi:application
   ```

3. **Настройка HTTPS** с Let's Encrypt:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### Решение проблем

#### Восстановление пароля не работает
1. Проверьте настройки EMAIL_* в файле `.env`
2. Убедитесь, что ваш SMTP-сервер разрешает отправку писем с вашего сервера
3. Для Gmail: создайте пароль приложения, обычный пароль не будет работать
4. Проверьте логи на предмет ошибок: `logs/error.log`

#### Ошибки подключения клиента к серверу
1. Убедитесь, что сервер запущен и доступен по сети
2. Проверьте настройки CORS в `settings.py`
3. Убедитесь, что в файле конфигурации клиента указан правильный адрес сервера

### Дополнительные функции

- **Мониторинг производительности**: Настройте пороги в `.env` файле:
  ```
  SLOW_REQUEST_THRESHOLD=1.0
  SLOW_QUERY_THRESHOLD=0.1
  ```

- **Логирование**: Все логи сохраняются в директории `logs/` 