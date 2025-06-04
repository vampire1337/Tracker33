#!/bin/bash

# Creating a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activating virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Installing dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Creating logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    echo "Creating logs directory..."
    mkdir -p logs
    touch logs/activity.log
    touch logs/performance.log
    touch logs/error.log
fi

# Creating .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file with default settings..."
    cat > .env << EOF
# Django settings
DEBUG=True
SECRET_KEY=django-insecure-^)hw&twianf%f=wq&sb)89@4jf%am1*4((&#(c#*xb)g4=yj_g

# Email configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@tracker33.com

# CORS settings
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000
EOF
    echo "Please edit .env file to configure email settings for password reset"
fi

# Loading environment variables
echo "Loading environment variables..."
export $(grep -v '^#' .env | xargs)

# Applying database migrations
echo "Applying database migrations..."
python manage.py migrate

# Creating superuser if needed
echo "Checking for superuser..."
python -c "
import django; django.setup();
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...');
    User.objects.create_superuser('admin', 'admin@example.com', 'admin');
    print('Superuser created. Username: admin, Password: admin');
else:
    print('Superuser already exists.');
"

# Collecting static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Copying service file to systemd directory
echo "Installing systemd service..."
sudo cp tracker33.service /etc/systemd/system/

# Reloading systemd to recognize the new service
sudo systemctl daemon-reload

# Enabling and starting the service
sudo systemctl enable tracker33.service
sudo systemctl start tracker33.service

echo "Service setup complete. Check status with: sudo systemctl status tracker33.service"