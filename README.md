# Tracker33 - Employee Activity Monitoring System

![Tracker33 Logo](desktop_app/tracker33_icon.png)

## 🚀 Overview

Tracker33 is a comprehensive employee activity monitoring system that tracks desktop application usage, generates productivity reports, and provides insights into work patterns. The system consists of a Django web application backend and a PyQt5 desktop client.

## ✨ Features

### Web Application
- **User Management**: Secure user registration and authentication
- **Dashboard**: Real-time activity overview and productivity metrics  
- **Statistics**: Detailed reports with charts and graphs
- **Admin Panel**: Comprehensive administration tools
- **Activity Tracking**: Detailed logs of application usage
- **QR Code Authentication**: Secure desktop client authentication

### Desktop Client
- **Automatic Activity Tracking**: Monitor application usage and keyboard activity
- **Background Operation**: Runs silently in system tray
- **Secure Communication**: Encrypted data transmission to server
- **Cross-platform**: Windows support with Linux/macOS compatibility

## 🛠 Technology Stack

### Backend
- **Django 5.0+**: Web framework
- **Django REST Framework**: API development
- **SQLite/PostgreSQL**: Database
- **Redis**: Caching (optional)
- **JWT**: Token-based authentication

### Desktop Client
- **PyQt5**: GUI framework
- **Requests**: HTTP client
- **psutil**: System monitoring
- **pynput**: Input monitoring
- **OpenCV**: Image processing

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend development)
- PostgreSQL (production) or SQLite (development)
- Redis (optional, for caching)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/tracker33.git
cd tracker33
```

### 2. Set up Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
```

### 3. Install Dependencies
```bash
# Backend dependencies
pip install -r requirements.txt

# Development dependencies (optional)
pip install -r requirements-dev.txt

# Desktop client dependencies
pip install -r desktop_app/requirements.txt
```

### 4. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Setup Database
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 6. Run the Development Server
```bash
python manage.py runserver 8000
```

### 7. Launch Desktop Client
```bash
cd desktop_app
python main.py
```

## 📖 Documentation

### Project Structure
```
tracker33/
├── Tracker33/           # Django project settings
├── users/               # User management app
├── tracking/            # Activity tracking app
├── admin_panel/         # Administration interface
├── templates/           # HTML templates
├── static/              # Static files (CSS, JS, images)
├── desktop_app/         # Desktop client application
├── scripts/             # Deployment and utility scripts
├── docs/                # Documentation and diagrams
├── logs/                # Application logs
└── requirements.txt     # Python dependencies
```

### API Endpoints

#### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/register/` - User registration
- `GET /api/auth/qr/` - Generate QR code for desktop client

#### Activity Tracking
- `POST /api/tracking/activity/` - Submit activity data
- `GET /api/tracking/statistics/` - Get user statistics
- `GET /api/tracking/applications/` - List tracked applications

#### User Management
- `GET /api/users/profile/` - Get user profile
- `PUT /api/users/profile/` - Update user profile
- `GET /api/users/dashboard/` - Dashboard data

### Desktop Client Configuration

The desktop client can be configured via `desktop_app/config.ini`:

```ini
[Server]
host = localhost
port = 8000
use_https = false

[Client]
tracking_interval = 5
screenshot_enabled = false
keyboard_logging = true

[Security]
auto_login = false
remember_token = true
```

## 🔧 Development

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test tracking

# Run with coverage
pytest --cov=./ --cov-report=html
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .

# Security scan
bandit -r .
```

### Database Migrations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

## 🚀 Deployment

### Production Environment Setup

1. **Environment Variables**
```bash
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:password@localhost:5432/tracker33
```

2. **Database Setup**
```bash
# PostgreSQL setup
python manage.py migrate --settings=Tracker33.settings_production
```

3. **Static Files**
```bash
python manage.py collectstatic --noinput
```

4. **Web Server Configuration**

See `deployment/nginx.conf` and `deployment/gunicorn.conf` for example configurations.

### Desktop Client Distribution

Build executable for distribution:
```bash
cd desktop_app
pyinstaller --onefile --windowed --icon=tracker33_icon.ico main.py
```

## 📊 Monitoring and Logging

### Application Logs
- `logs/activity.log` - User activity events
- `logs/performance.log` - Performance metrics
- `logs/error.log` - Error messages

### Performance Monitoring
The system includes built-in performance monitoring:
- Request/response times
- Database query performance
- Cache hit ratios
- Memory usage

### Health Checks
- `/health/` - Application health status
- `/api/health/` - API health status

## 🔒 Security

### Security Features
- CSRF protection
- SQL injection prevention
- XSS protection
- Secure authentication tokens
- Input validation and sanitization
- Rate limiting

### Security Considerations
- Regular security updates
- Strong password policies
- Secure communication (HTTPS)
- Data encryption at rest
- Access logging and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write comprehensive tests
- Update documentation
- Use meaningful commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Support

For support and questions:
- Create an issue on GitHub
- Contact: support@tracker33.local
- Documentation: [docs/](docs/)

## 🏆 Acknowledgments

- Django community for the excellent framework
- PyQt5 for the desktop application framework
- All contributors who helped improve this project

---

**Tracker33** - Monitoring productivity, one activity at a time. 📈