#!/bin/bash

# Tracker33 Deployment Script
# This script automates the deployment process for production

set -e  # Exit on any error

echo "🚀 Starting Tracker33 deployment..."

# Configuration
APP_NAME="tracker33"
APP_USER="tracker33"
APP_DIR="/home/$APP_USER/$APP_NAME"
VENV_DIR="$APP_DIR/.venv"
LOG_DIR="/var/log/$APP_NAME"
RUN_DIR="/var/run/$APP_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root"
   exit 1
fi

# Check if environment file exists
if [ ! -f "$APP_DIR/.env.production" ]; then
    log_error "Production environment file not found at $APP_DIR/.env.production"
    log_info "Please create the environment file first"
    exit 1
fi

# Load environment variables
source "$APP_DIR/.env.production"

log_info "Updating application code..."
cd "$APP_DIR"

# Pull latest changes
git pull origin main

log_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install/update dependencies
log_info "Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
log_info "Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
log_info "Running database migrations..."
python manage.py migrate --noinput

# Check for any issues
log_info "Running system checks..."
python manage.py check --deploy

# Create log directories if they don't exist
log_info "Setting up log directories..."
sudo mkdir -p "$LOG_DIR"
sudo mkdir -p "$RUN_DIR"
sudo chown -R "$APP_USER:www-data" "$LOG_DIR"
sudo chown -R "$APP_USER:www-data" "$RUN_DIR"

# Restart services
log_info "Restarting application services..."

# Restart Gunicorn
sudo systemctl restart "$APP_NAME"
if systemctl is-active --quiet "$APP_NAME"; then
    log_success "Gunicorn service restarted successfully"
else
    log_error "Failed to restart Gunicorn service"
    sudo systemctl status "$APP_NAME"
    exit 1
fi

# Restart Nginx
sudo systemctl reload nginx
if systemctl is-active --quiet nginx; then
    log_success "Nginx reloaded successfully"
else
    log_error "Failed to reload Nginx"
    sudo systemctl status nginx
    exit 1
fi

# Health check
log_info "Performing health check..."
sleep 5  # Wait for services to start

if curl -f -s http://localhost/health/ > /dev/null; then
    log_success "Health check passed"
else
    log_error "Health check failed"
    exit 1
fi

# Clean up old logs (keep last 30 days)
log_info "Cleaning up old log files..."
find "$LOG_DIR" -name "*.log" -type f -mtime +30 -delete

# Display final status
echo
log_success "🎉 Deployment completed successfully!"
log_info "Application is running at: $(curl -s http://localhost/)"
log_info "Admin panel: http://yourdomain.com/admin/"
log_info "API health check: http://yourdomain.com/health/"
echo

# Show service status
echo "📊 Service Status:"
systemctl status "$APP_NAME" --no-pager -l
echo
systemctl status nginx --no-pager -l