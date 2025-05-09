#!/bin/bash

# Запускаем скрипт start_server.sh в фоновом режиме с перенаправлением вывода
echo "Starting Tracker33 server in background mode..."

# Активация виртуального окружения
source venv/bin/activate

# Применение миграций и сбор статических файлов
python manage.py migrate
python manage.py collectstatic --noinput

# Запуск сервера в фоновом режиме с помощью nohup
nohup python manage.py runserver 0.0.0.0:8000 > logs/server.log 2>&1 &

# Сохраняем PID процесса
echo $! > server.pid

echo "Server started in background mode. PID: $(cat server.pid)"
echo "Log output is redirected to logs/server.log"
echo "To stop the server, run: kill $(cat server.pid)"
echo "You can access the server at: http://0.0.0.0:8000/"
echo "Admin interface: http://0.0.0.0:8000/admin/" 