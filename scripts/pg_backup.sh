#!/bin/bash

# Exit on error, but allow for proper error handling
set -eo pipefail

# Configuration
BACKUP_DIR="$HOME/.blog_pg_backups"
LOG_FILE="$BACKUP_DIR/backup.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/blog_backup_$TIMESTAMP.sql"
RETENTION_DAYS=14
DB_NAME="blog"
DB_USER="postgres"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $1"
    exit 1
}

verify_database() {
    # Try to connect and verify key tables exist
    if ! psql -U "$DB_USER" -d "$DB_NAME" -c "\dt post" >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

initialize_schema() {
    log "Initializing database schema..."
    cd "$PROJECT_DIR"
    if ! flask db upgrade; then
        error "Failed to initialize database schema"
    fi
    log "Schema initialization completed"
}

# Check if PostgreSQL is running
if ! pg_isready -q; then
    error "PostgreSQL is not running"
fi

# Check if database exists and initialize if needed
if ! psql -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    log "Database '$DB_NAME' does not exist. Attempting to create..."
    if createdb -U "$DB_USER" "$DB_NAME"; then
        log "Successfully created database '$DB_NAME'"
        initialize_schema
    else
        error "Failed to create database '$DB_NAME'"
    fi
elif ! verify_database; then
    log "Database exists but schema is missing. Initializing schema..."
    initialize_schema
fi

# Verify database is healthy
if ! verify_database; then
    error "Database verification failed after initialization"
fi

# Perform backup
log "Starting backup of database '$DB_NAME'"
if pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"; then
    # Verify backup is not empty
    if [ -s "$BACKUP_FILE" ]; then
        log "Backup completed successfully: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
    else
        rm "$BACKUP_FILE"
        error "Backup file is empty"
    fi
else
    rm -f "$BACKUP_FILE"
    error "Backup failed"
fi

# Clean up old backups
log "Cleaning up backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -type f -name 'blog_backup_*.sql' -mtime "+$RETENTION_DAYS" -delete

# Verify we have at least one valid backup
if ! ls "$BACKUP_DIR"/blog_backup_*.sql >/dev/null 2>&1; then
    error "No valid backups found after cleanup"
fi

log "Backup process completed successfully" 