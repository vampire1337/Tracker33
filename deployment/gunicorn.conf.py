"""
Gunicorn configuration file for Tracker33 production deployment
"""
import os
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1200
max_requests_jitter = 50

# Preload application for faster worker spawn times
preload_app = True

# Server mechanics
daemon = False
pidfile = '/var/run/tracker33/gunicorn.pid'
user = 'tracker33'
group = 'www-data'
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Logging
accesslog = '/var/log/tracker33/gunicorn-access.log'
errorlog = '/var/log/tracker33/gunicorn-error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'tracker33'

# Environment variables
raw_env = [
    'DJANGO_SETTINGS_MODULE=Tracker33.settings',
]

# Worker timeout
timeout = 60
graceful_timeout = 30

# Memory optimization
worker_tmp_dir = '/dev/shm'