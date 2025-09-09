#!/bin/bash

# Скрипт развертывания Tracker33
# Использование: ./scripts/deploy.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
PROJECT_DIR="/home/tracker33/tracker33"
BACKUP_DIR="/home/tracker33/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Начало развертывания Tracker33 в режиме: $ENVIRONMENT"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Создание резервных копий
create_backup() {
    log "📦 Создание резервной копии..."
    mkdir -p $BACKUP_DIR
    
    # Резервная копия базы данных
    if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
        cp "$PROJECT_DIR/db.sqlite3" "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
        log "✅ База данных скопирована"
    fi
    
    # Резервная копия медиа файлов
    if [ -d "$PROJECT_DIR/media" ]; then
        tar -czf "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" -C "$PROJECT_DIR" media
        log "✅ Медиа файлы скопированы"
    fi
}

# Обновление кода
update_code() {
    log "📥 Обновление кода из репозитория..."
    cd $PROJECT_DIR
    
    # Сохранение текущих изменений
    git stash push -m "Auto stash before deployment $TIMESTAMP"
    
    # Получение последних изменений
    git fetch origin
    git checkout main
    git pull origin main
    
    log "✅ Код обновлен"
}

# Обновление зависимостей
update_dependencies() {
    log "📚 Обновление зависимостей..."
    cd $PROJECT_DIR
    source venv/bin/activate
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log "✅ Зависимости обновлены"
}

# Применение миграций
apply_migrations() {
    log "🗃️ Применение миграций базы данных..."
    cd $PROJECT_DIR
    source venv/bin/activate
    
    python manage.py migrate --noinput
    
    log "✅ Миграции применены"
}

# Сбор статических файлов
collect_static() {
    log "🎨 Сбор статических файлов..."
    cd $PROJECT_DIR
    source venv/bin/activate
    
    python manage.py collectstatic --noinput --clear
    
    log "✅ Статические файлы собраны"
}

# Проверка конфигурации
check_config() {
    log "🔍 Проверка конфигурации Django..."
    cd $PROJECT_DIR
    source venv/bin/activate
    
    if [ "$ENVIRONMENT" = "production" ]; then
        python manage.py check --deploy --fail-level WARNING
    else
        python manage.py check
    fi
    
    log "✅ Конфигурация проверена"
}

# Перезапуск сервисов
restart_services() {
    log "🔄 Перезапуск сервисов..."
    
    # Проверка и перезапуск через supervisor
    if command -v supervisorctl > /dev/null; then
        sudo supervisorctl restart tracker33
        log "✅ Supervisor сервис перезапущен"
    fi
    
    # Проверка и перезапуск через systemd
    if systemctl is-active --quiet Tracker33; then
        sudo systemctl restart Tracker33
        log "✅ Systemd сервис перезапущен"
    fi
    
    # Перезапуск Nginx
    if systemctl is-active --quiet nginx; then
        sudo systemctl reload nginx
        log "✅ Nginx перезагружен"
    fi
}

# Проверка здоровья приложения
health_check() {
    log "🏥 Проверка здоровья приложения..."
    
    sleep 10  # Ждем запуска сервисов
    
    # Проверка HTTP ответа
    if curl -f -s http://localhost:8001/api/health/ > /dev/null; then
        log "✅ Приложение работает корректно"
    else
        log "❌ Приложение не отвечает на запросы"
        exit 1
    fi
}

# Очистка старых резервных копий
cleanup_backups() {
    log "🧹 Очистка старых резервных копий (старше 30 дней)..."
    find $BACKUP_DIR -name "*.sqlite3" -mtime +30 -delete 2>/dev/null || true
    find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true
    log "✅ Очистка завершена"
}

# Отправка уведомления
send_notification() {
    local status=$1
    local message="Развертывание Tracker33 [$ENVIRONMENT]: $status"
    
    # Slack уведомление (если настроено)
    if [ -n "${SLACK_WEBHOOK_URL}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
    
    log "📨 Уведомление отправлено: $message"
}

# Основная функция развертывания
main() {
    log "🎯 Начало развертывания в режиме: $ENVIRONMENT"
    
    # Проверка прав доступа
    if [ ! -w "$PROJECT_DIR" ]; then
        log "❌ Нет прав записи в директорию проекта"
        exit 1
    fi
    
    # Проверка окружения
    if [ "$ENVIRONMENT" = "production" ] && [ -z "${SECRET_KEY}" ]; then
        log "❌ Не установлен SECRET_KEY для продакшена"
        exit 1
    fi
    
    # Выполнение этапов развертывания
    create_backup
    update_code
    update_dependencies
    apply_migrations
    collect_static
    check_config
    restart_services
    health_check
    cleanup_backups
    
    log "🎉 Развертывание успешно завершено!"
    send_notification "УСПЕХ"
}

# Обработка ошибок
trap 'log "❌ Развертывание прервано из-за ошибки"; send_notification "ОШИБКА"; exit 1' ERR

# Запуск основной функции
main

log "✨ Развертывание Tracker33 завершено успешно!"