# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Создаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .
COPY env.example .env

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем пользователя для приложения
RUN useradd --create-home --shell /bin/bash tracker33

# Копируем код приложения
COPY . .

# Создаем необходимые директории
RUN mkdir -p logs media staticfiles

# Устанавливаем права доступа
RUN chown -R tracker33:tracker33 /app

# Переключаемся на пользователя приложения
USER tracker33

# Собираем статические файлы
RUN python manage.py collectstatic --noinput

# Открываем порт
EXPOSE 8001

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/health/ || exit 1

# Команда запуска
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]