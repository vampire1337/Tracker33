#!/bin/bash

# Скрипт для развертывания на Railway

echo "🚂 Подготовка к развертыванию на Railway"

# Проверка Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI не установлен. Установите его:"
    echo "   npm install -g @railway/cli"
    echo "   Или скачайте с https://railway.app/cli"
    exit 1
fi

echo "✅ Railway CLI найден"

# Логин (если не залогинен)
echo "🔐 Проверка авторизации..."
if ! railway whoami &> /dev/null; then
    echo "Необходимо войти в Railway:"
    railway login
fi

echo "✅ Авторизация прошла успешно"

# Создание проекта (если не существует)
echo "📦 Создание/подключение к проекту..."
if [ ! -f "railway.json" ]; then
    echo "Создание нового проекта на Railway..."
    railway init
else
    echo "Проект уже существует, используем его"
fi

# Настройка переменных окружения
echo "⚙️ Настройка переменных окружения..."

# Генерация SECRET_KEY
SECRET_KEY=$(python -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
print(''.join(secrets.choice(alphabet) for i in range(50)))
")

railway variables set SECRET_KEY="$SECRET_KEY"
railway variables set DEBUG="False"
railway variables set DJANGO_SETTINGS_MODULE="Tracker33.settings"
railway variables set ALLOWED_HOSTS="*.railway.app,localhost,127.0.0.1"
railway variables set CORS_ALLOWED_ORIGINS="https://tracker33-production.up.railway.app"

echo "✅ Переменные окружения настроены"

# Добавление PostgreSQL базы данных
echo "🗄️ Добавление PostgreSQL базы данных..."
railway add postgresql

echo "✅ PostgreSQL добавлен"

# Развертывание
echo "🚀 Развертывание приложения..."
railway up --detach

echo "⏳ Ожидание завершения развертывания..."
sleep 30

# Получение URL приложения
APP_URL=$(railway status --json | jq -r '.deployments[0].url // empty')

if [ -n "$APP_URL" ]; then
    echo ""
    echo "🎉 Развертывание завершено успешно!"
    echo "📱 URL приложения: $APP_URL"
    echo "📊 Панель управления: https://railway.app/dashboard"
    echo ""
    echo "📝 Следующие шаги:"
    echo "1. Откройте $APP_URL в браузере"
    echo "2. Создайте суперпользователя: railway run python manage.py createsuperuser"
    echo "3. Проверьте работу API: curl $APP_URL/api/health/"
else
    echo "⚠️ Не удалось получить URL приложения. Проверьте статус в панели Railway:"
    echo "   https://railway.app/dashboard"
fi

echo ""
echo "🔧 Полезные команды Railway:"
echo "   railway logs        - просмотр логов"
echo "   railway shell       - подключение к контейнеру"
echo "   railway status      - статус развертывания"
echo "   railway variables   - просмотр переменных окружения"
