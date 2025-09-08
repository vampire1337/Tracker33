#!/bin/bash

# Tracker33 Production Setup Script
# This script sets up the production environment for Tracker33

set -e

echo "🏭 Setting up Tracker33 for production..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Update system
log_info "Updating system packages..."
apt update && apt upgrade -y

# Install system dependencies
log_info "Installing system dependencies..."
apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    libpq-dev \
    build-essential \
    git \
    curl \
    fail2ban \
    ufw \
    certbot \
    python3-certbot-nginx

# Create application user
log_info "Creating application user..."
if ! id "tracker33" &>/dev/null; then
    useradd -m -s /bin/bash tracker33
    usermod -aG www-data tracker33
    log_success "User 'tracker33' created"
else
    log_info "User 'tracker33' already exists"
fi

# Setup PostgreSQL
log_info "Setting up PostgreSQL..."
sudo -u postgres createdb tracker33 2>/dev/null || log_info "Database already exists"
sudo -u postgres createuser tracker33 2>/dev/null || log_info "Database user already exists"

# Generate secure password for database
DB_PASSWORD=$(openssl rand -base64 32)
sudo -u postgres psql -c "ALTER USER tracker33 WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "ALTER USER tracker33 CREATEDB;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE tracker33 TO tracker33;"

log_success "PostgreSQL configured"

# Setup Redis
log_info "Configuring Redis..."
systemctl enable redis-server
systemctl start redis-server

# Configure firewall
log_info "Configuring firewall..."
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS

# Setup fail2ban
log_info "Configuring fail2ban..."
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Create application directories
log_info "Creating application directories..."
mkdir -p /var/log/tracker33
mkdir -p /var/run/tracker33
mkdir -p /etc/tracker33
chown -R tracker33:www-data /var/log/tracker33
chown -R tracker33:www-data /var/run/tracker33

# Clone repository as tracker33 user
log_info "Cloning application repository..."
sudo -u tracker33 bash -c '
cd /home/tracker33
if [ ! -d "tracker33" ]; then
    git clone https://github.com/your-username/tracker33.git
    cd tracker33
else
    cd tracker33
    git pull origin main
fi

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
'

# Create production environment file
log_info "Creating production environment file..."
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

cat > /home/tracker33/tracker33/.env.production << EOF
# Production Environment Configuration
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost,127.0.0.1

# Database Configuration
DATABASE_ENGINE=postgresql
DATABASE_NAME=tracker33
DATABASE_USER=tracker33
DATABASE_PASSWORD=$DB_PASSWORD
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/1

# Email Configuration (configure as needed)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security Settings
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Performance Settings
SLOW_REQUEST_THRESHOLD=2.0
SLOW_QUERY_THRESHOLD=0.5
EOF

chown tracker33:tracker33 /home/tracker33/tracker33/.env.production
chmod 600 /home/tracker33/tracker33/.env.production

# Run Django setup
log_info "Running Django setup..."
sudo -u tracker33 bash -c '
cd /home/tracker33/tracker33
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=Tracker33.settings

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create superuser (interactive)
echo "Creating Django superuser..."
python manage.py createsuperuser
'

# Copy deployment configurations
log_info "Installing deployment configurations..."
cp /home/tracker33/tracker33/deployment/gunicorn.conf.py /etc/tracker33/
cp /home/tracker33/tracker33/deployment/tracker33.service /etc/systemd/system/
cp /home/tracker33/tracker33/deployment/nginx.conf /etc/nginx/sites-available/tracker33

# Enable nginx site
ln -sf /etc/nginx/sites-available/tracker33 /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Start and enable services
log_info "Starting services..."
systemctl daemon-reload
systemctl enable tracker33
systemctl start tracker33
systemctl enable nginx
systemctl restart nginx

# Verify services are running
if systemctl is-active --quiet tracker33; then
    log_success "Tracker33 service is running"
else
    log_error "Tracker33 service failed to start"
    systemctl status tracker33
fi

if systemctl is-active --quiet nginx; then
    log_success "Nginx service is running"
else
    log_error "Nginx service failed to start"
    systemctl status nginx
fi

# Setup log rotation
log_info "Setting up log rotation..."
cat > /etc/logrotate.d/tracker33 << EOF
/var/log/tracker33/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 tracker33 www-data
    postrotate
        systemctl reload tracker33
    endscript
}
EOF

log_success "🎉 Production setup completed!"
echo
echo "📋 Next steps:"
echo "1. Update domain name in /etc/nginx/sites-available/tracker33"
echo "2. Update ALLOWED_HOSTS in /home/tracker33/tracker33/.env.production"
echo "3. Configure email settings in .env.production"
echo "4. Obtain SSL certificate: sudo certbot --nginx -d yourdomain.com"
echo "5. Test the application at http://your-server-ip/"
echo
echo "🔐 Database password: $DB_PASSWORD"
echo "📁 Application directory: /home/tracker33/tracker33"
echo "📝 Logs directory: /var/log/tracker33"