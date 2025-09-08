# Tracker33 Installation Guide

This guide will walk you through installing and setting up Tracker33 for development and production environments.

## 📋 System Requirements

### Minimum Requirements
- Python 3.8 or higher
- 4 GB RAM
- 10 GB free disk space
- Internet connection

### Recommended Requirements
- Python 3.11+
- 8 GB RAM
- 20 GB free disk space
- PostgreSQL 13+
- Redis 6.0+

### Supported Operating Systems
- **Server**: Linux, Windows Server, macOS
- **Desktop Client**: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.14+

## 🔧 Development Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/tracker33.git
cd tracker33
```

### Step 2: Python Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 3: Install Dependencies
```bash
# Install backend dependencies
pip install -r requirements.txt

# Install development tools (optional)
pip install -r requirements-dev.txt
```

### Step 4: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env
```

**Required environment variables for development:**
```env
SECRET_KEY=django-insecure-your-development-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Step 5: Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata fixtures/sample_data.json
```

### Step 6: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 7: Run Development Server
```bash
# Start Django development server
python manage.py runserver 8000

# In another terminal, start desktop client
cd desktop_app
python main.py
```

## 🏭 Production Installation

### Step 1: Server Setup (Ubuntu 20.04 LTS)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv nginx postgresql redis-server
sudo apt install -y python3-dev libpq-dev build-essential

# Create application user
sudo useradd -m -s /bin/bash tracker33
sudo usermod -aG www-data tracker33
```

### Step 2: PostgreSQL Setup
```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
createdb tracker33
createuser tracker33
psql -c "ALTER USER tracker33 WITH PASSWORD 'secure_password_here';"
psql -c "ALTER USER tracker33 CREATEDB;"
psql -c "GRANT ALL PRIVILEGES ON DATABASE tracker33 TO tracker33;"

# Exit postgres user
exit
```

### Step 3: Application Setup
```bash
# Switch to application user
sudo su - tracker33

# Clone repository
git clone https://github.com/your-username/tracker33.git
cd tracker33

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Step 4: Production Configuration
```bash
# Create production environment file
cp .env.example .env.production
```

**Production environment variables:**
```env
SECRET_KEY=your-very-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://tracker33:secure_password_here@localhost:5432/tracker33

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security settings
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Step 5: Database Migration
```bash
# Set environment
export DJANGO_SETTINGS_MODULE=Tracker33.settings

# Run migrations
python manage.py migrate --settings=Tracker33.settings

# Create superuser
python manage.py createsuperuser --settings=Tracker33.settings

# Collect static files
python manage.py collectstatic --noinput --settings=Tracker33.settings
```

### Step 6: Gunicorn Configuration
```bash
# Create gunicorn configuration
sudo mkdir -p /etc/tracker33
sudo cp deployment/gunicorn.conf.py /etc/tracker33/

# Create systemd service
sudo cp deployment/tracker33.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tracker33
sudo systemctl start tracker33
```

### Step 7: Nginx Configuration
```bash
# Copy nginx configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/tracker33
sudo ln -s /etc/nginx/sites-available/tracker33 /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### Step 8: SSL Certificate (Optional but Recommended)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

## 💻 Desktop Client Installation

### Development Setup
```bash
cd desktop_app

# Install dependencies
pip install -r requirements.txt

# Run client
python main.py
```

### Production Distribution
```bash
cd desktop_app

# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed --icon=tracker33_icon.ico main.py

# Executable will be in dist/main.exe
```

### Windows Installer Creation
```bash
# Install NSIS (Nullsoft Scriptable Install System)
# Download from: https://nsis.sourceforge.io/

# Use the installer script
makensis installer.nsi
```

## 🔍 Verification

### Backend Verification
```bash
# Check if Django server is running
curl http://localhost:8000/health/

# Check API endpoint
curl http://localhost:8000/api/health/

# Check admin interface
# Visit: http://localhost:8000/admin/
```

### Database Verification
```bash
# Connect to database
python manage.py dbshell

# Check tables
\dt

# Exit
\q
```

### Desktop Client Verification
1. Launch the desktop application
2. Check system tray for the Tracker33 icon
3. Try logging in with your credentials
4. Verify activity tracking is working

## 🔧 Troubleshooting

### Common Issues

**Django server won't start:**
```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check for port conflicts
netstat -an | grep :8000
```

**Database connection errors:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
python manage.py dbshell
```

**Desktop client login issues:**
```bash
# Check server URL in config
cat desktop_app/config.ini

# Check network connectivity
ping localhost
```

**Static files not loading:**
```bash
# Collect static files again
python manage.py collectstatic --noinput

# Check nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

### Log Files
- **Django logs**: `logs/error.log`, `logs/performance.log`
- **Nginx logs**: `/var/log/nginx/error.log`
- **PostgreSQL logs**: `/var/log/postgresql/postgresql-13-main.log`
- **Desktop client logs**: `desktop_app/tracker33_client.log`

## 📊 Performance Optimization

### Database Optimization
```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_useractivity_user_start_time ON tracking_useractivity(user_id, start_time);
CREATE INDEX idx_useractivity_application_start_time ON tracking_useractivity(application_id, start_time);
```

### Caching Setup
```bash
# Install Redis
sudo apt install redis-server

# Update settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## 🔒 Security Hardening

### Server Security
```bash
# Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS

# Configure fail2ban
sudo apt install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

### Application Security
- Change default secret key
- Enable HTTPS in production
- Configure proper CORS settings
- Regular security updates
- Monitor access logs

## 📞 Support

If you encounter issues during installation:
1. Check the troubleshooting section above
2. Review log files for error messages
3. Search existing GitHub issues
4. Create a new issue with detailed error information

---

For additional help, contact: support@tracker33.local