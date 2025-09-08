# Tracker33 Makefile
# Convenient commands for development and deployment

.PHONY: help install dev test lint format clean deploy backup

# Default target
help:
	@echo "Tracker33 Development Commands"
	@echo "============================="
	@echo ""
	@echo "Development:"
	@echo "  make install     Install dependencies"
	@echo "  make dev         Start development server"
	@echo "  make test        Run tests"
	@echo "  make lint        Run linting"
	@echo "  make format      Format code"
	@echo "  make clean       Clean temporary files"
	@echo ""
	@echo "Database:"
	@echo "  make migrate     Run database migrations"
	@echo "  make superuser   Create Django superuser"
	@echo "  make resetdb     Reset database (development only)"
	@echo ""
	@echo "Production:"
	@echo "  make deploy      Deploy to production"
	@echo "  make backup      Create backup"
	@echo "  make logs        View production logs"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build    Build Docker image"
	@echo "  make docker-up       Start Docker containers"
	@echo "  make docker-down     Stop Docker containers"

# Development commands
install:
	python -m venv .venv
	.venv/Scripts/activate && pip install --upgrade pip
	.venv/Scripts/activate && pip install -r requirements.txt
	.venv/Scripts/activate && pip install -r requirements-dev.txt

dev:
	.venv/Scripts/activate && python manage.py runserver 8000

test:
	.venv/Scripts/activate && python manage.py test
	.venv/Scripts/activate && pytest --cov=./ --cov-report=html

lint:
	.venv/Scripts/activate && flake8 .
	.venv/Scripts/activate && mypy .
	.venv/Scripts/activate && bandit -r .

format:
	.venv/Scripts/activate && black .
	.venv/Scripts/activate && isort .

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

# Database commands
migrate:
	.venv/Scripts/activate && python manage.py makemigrations
	.venv/Scripts/activate && python manage.py migrate

superuser:
	.venv/Scripts/activate && python manage.py createsuperuser

resetdb:
	@echo "⚠️  This will delete all data in the development database!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f db.sqlite3; \
		.venv/Scripts/activate && python manage.py migrate; \
		echo "Database reset complete"; \
	else \
		echo "Database reset cancelled"; \
	fi

# Collect static files
collectstatic:
	.venv/Scripts/activate && python manage.py collectstatic --noinput

# Production commands (Linux only)
deploy:
	@echo "🚀 Deploying to production..."
	bash scripts/deploy.sh

backup:
	@echo "📦 Creating backup..."
	bash scripts/backup.sh

logs:
	@echo "📋 Production logs:"
	sudo tail -f /var/log/tracker33/gunicorn-error.log

# Docker commands
docker-build:
	docker-compose -f deployment/docker-compose.yml build

docker-up:
	docker-compose -f deployment/docker-compose.yml up -d

docker-down:
	docker-compose -f deployment/docker-compose.yml down

docker-logs:
	docker-compose -f deployment/docker-compose.yml logs -f

# Development utilities
shell:
	.venv/Scripts/activate && python manage.py shell

dbshell:
	.venv/Scripts/activate && python manage.py dbshell

check:
	.venv/Scripts/activate && python manage.py check

# Desktop client
client:
	cd desktop_app && python main.py

client-build:
	cd desktop_app && pyinstaller --onefile --windowed --icon=tracker33_icon.ico main.py

# Security
security-check:
	.venv/Scripts/activate && python manage.py check --deploy
	.venv/Scripts/activate && bandit -r .

# Documentation
docs:
	@echo "📚 Opening documentation..."
	@echo "README: file://$(PWD)/README.md"
	@echo "Installation Guide: file://$(PWD)/docs/INSTALLATION.md"

# Version info
version:
	@echo "Tracker33 Version Information"
	@echo "============================="
	@echo "Git commit: $(shell git rev-parse HEAD)"
	@echo "Git branch: $(shell git branch --show-current)"
	@echo "Python version: $(shell python --version)"
	@echo "Django version: $(shell .venv/Scripts/activate && python -c 'import django; print(django.get_version())')"