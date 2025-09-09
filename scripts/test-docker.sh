#!/bin/bash

# Скрипт для тестирования Docker развертывания Tracker33

set -e

echo "🐳 Тестирование Docker развертывания Tracker33"

# Проверка установки Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    echo "   Скачайте с https://www.docker.com/get-started"
    exit 1
fi

# Проверка запуска Docker
if ! docker info &> /dev/null; then
    echo "❌ Docker не запущен. Запустите Docker Desktop и повторите попытку."
    exit 1
fi

echo "✅ Docker установлен и запущен"

# Переход в директорию проекта
cd "$(dirname "$0")/.."

echo "📦 Сборка Docker образа..."
docker build -t tracker33:latest . || {
    echo "❌ Ошибка при сборке Docker образа"
    exit 1
}

echo "✅ Docker образ собран успешно"

# Проверка образа
echo "📋 Информация о созданном образе:"
docker images tracker33:latest

# Создание сети для контейнеров
echo "🌐 Создание Docker сети..."
docker network create tracker33_network 2>/dev/null || echo "Сеть уже существует"

# Запуск базы данных PostgreSQL (для продакшена)
echo "🗄️ Запуск PostgreSQL..."
docker run -d \
    --name tracker33_postgres \
    --network tracker33_network \
    -e POSTGRES_DB=tracker33 \
    -e POSTGRES_USER=tracker33 \
    -e POSTGRES_PASSWORD=secure_password \
    -v tracker33_postgres_data:/var/lib/postgresql/data \
    postgres:15-alpine 2>/dev/null || echo "PostgreSQL уже запущен"

# Ожидание запуска PostgreSQL
echo "⏳ Ожидание запуска PostgreSQL..."
sleep 10

# Запуск основного приложения
echo "🚀 Запуск Tracker33..."
docker run -d \
    --name tracker33_web \
    --network tracker33_network \
    -p 8001:8001 \
    -e SECRET_KEY="django-test-secret-key-for-docker" \
    -e DEBUG=False \
    -e ALLOWED_HOSTS="localhost,127.0.0.1,0.0.0.0" \
    -e DATABASE_URL="postgresql://tracker33:secure_password@tracker33_postgres:5432/tracker33" \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/media:/app/media" \
    tracker33:latest || {
    echo "❌ Ошибка при запуске контейнера"
    exit 1
}

echo "✅ Контейнеры запущены"

# Проверка статуса контейнеров
echo "📊 Статус контейнеров:"
docker ps --filter "name=tracker33"

# Ожидание полного запуска приложения
echo "⏳ Ожидание полного запуска приложения..."
sleep 30

# Проверка здоровья приложения
echo "🏥 Проверка работоспособности приложения..."
for i in {1..10}; do
    if curl -f -s http://localhost:8001/ > /dev/null; then
        echo "✅ Приложение отвечает на HTTP запросы"
        break
    else
        echo "⏳ Попытка $i/10: приложение еще не готово..."
        sleep 5
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ Приложение не отвечает после 10 попыток"
        echo "📋 Логи контейнера:"
        docker logs tracker33_web
        exit 1
    fi
done

# Проверка API
echo "🔍 Проверка API..."
if curl -f -s http://localhost:8001/api/health/ > /dev/null; then
    echo "✅ API работает корректно"
else
    echo "⚠️ API недоступен (возможно, нужна миграция БД)"
fi

echo ""
echo "🎉 Docker развертывание успешно завершено!"
echo ""
echo "📱 Приложение доступно по адресу: http://localhost:8001"
echo "📊 Для просмотра логов: docker logs tracker33_web"
echo "🛑 Для остановки: docker stop tracker33_web tracker33_postgres"
echo "🧹 Для очистки: docker rm tracker33_web tracker33_postgres && docker network rm tracker33_network"
echo ""

# Показать инструкции для дальнейшего использования
echo "📝 Следующие шаги:"
echo "1. Откройте браузер и перейдите по адресу http://localhost:8001"
echo "2. Создайте суперпользователя: docker exec -it tracker33_web python manage.py createsuperuser"
echo "3. Примените миграции: docker exec -it tracker33_web python manage.py migrate"
echo "4. Для остановки всех сервисов используйте: docker-compose down"
