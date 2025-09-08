#!/bin/bash

# Tracker33 Backup Script
# Creates backups of database, media files, and configuration

set -e

echo "🔄 Starting Tracker33 backup process..."

# Configuration
APP_NAME="tracker33"
APP_DIR="/home/tracker33/tracker33"
BACKUP_DIR="/home/tracker33/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${APP_NAME}_backup_${DATE}"

# Database configuration (load from environment)
source "$APP_DIR/.env.production"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

log_info "Creating database backup..."
if [ "$DATABASE_ENGINE" = "postgresql" ]; then
    pg_dump "$DATABASE_NAME" > "$BACKUP_DIR/$BACKUP_NAME/database.sql"
elif [ "$DATABASE_ENGINE" = "sqlite3" ]; then
    cp "$APP_DIR/db.sqlite3" "$BACKUP_DIR/$BACKUP_NAME/database.sqlite3"
else
    log_warning "Unsupported database engine: $DATABASE_ENGINE"
fi

log_info "Backing up media files..."
if [ -d "$APP_DIR/media" ] && [ "$(ls -A $APP_DIR/media)" ]; then
    cp -r "$APP_DIR/media" "$BACKUP_DIR/$BACKUP_NAME/"
else
    log_info "No media files to backup"
fi

log_info "Backing up configuration files..."
cp "$APP_DIR/.env.production" "$BACKUP_DIR/$BACKUP_NAME/"
cp -r "$APP_DIR/deployment" "$BACKUP_DIR/$BACKUP_NAME/"

log_info "Backing up static files..."
if [ -d "$APP_DIR/staticfiles" ]; then
    cp -r "$APP_DIR/staticfiles" "$BACKUP_DIR/$BACKUP_NAME/"
fi

log_info "Creating backup information file..."
cat > "$BACKUP_DIR/$BACKUP_NAME/backup_info.txt" << EOF
Tracker33 Backup Information
============================
Backup Date: $(date)
Application Version: $(cd $APP_DIR && git rev-parse HEAD)
Database Engine: ${DATABASE_ENGINE:-unknown}
Backup Size: $(du -sh "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)

Files included:
- Database dump
- Media files
- Configuration files
- Static files
- Deployment configurations

To restore this backup, use the restore.sh script.
EOF

log_info "Compressing backup..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

log_success "Backup created: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"

# Clean up old backups (keep last 7 days)
log_info "Cleaning up old backups..."
find "$BACKUP_DIR" -name "${APP_NAME}_backup_*.tar.gz" -type f -mtime +7 -delete

# Display backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
log_success "Backup completed successfully! Size: $BACKUP_SIZE"

echo
echo "📁 Available backups:"
ls -lah "$BACKUP_DIR"/${APP_NAME}_backup_*.tar.gz 2>/dev/null || echo "No backups found"