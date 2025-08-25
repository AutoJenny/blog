#!/bin/bash

# Exit on error, but allow for proper error handling
set -eo pipefail

# Configuration
BACKUP_DIR="$HOME/.blog_pg_backups"
LOG_FILE="$BACKUP_DIR/restore.log"
DB_NAME="blog"
DB_USER="postgres"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $1"
    exit 1
}

# Check if PostgreSQL is running
if ! pg_isready -q; then
    error "PostgreSQL is not running"
fi

# List available backups
echo "Available backups:"
echo "-----------------"
ls -lt "$BACKUP_DIR"/*.sql | awk '{print NR") " $9 " (" $5 " bytes)"}' || error "No backups found"

# Get user selection
read -p "Enter the number of the backup to restore (or 'q' to quit): " selection

[[ "$selection" == "q" ]] && exit 0

# Validate selection
backup_file=$(ls -t "$BACKUP_DIR"/*.sql | sed -n "${selection}p")
if [[ ! -f "$backup_file" ]]; then
    error "Invalid selection"
fi

# Verify backup file is not empty
if [[ ! -s "$backup_file" ]]; then
    error "Selected backup file is empty"
fi

# Confirm restore
echo "WARNING: This will overwrite the current '$DB_NAME' database!"
read -p "Are you sure you want to proceed? (y/N): " confirm
[[ "$confirm" != "y" ]] && exit 0

log "Starting restore from: $backup_file"

# Create a new backup before restore
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PRE_RESTORE_BACKUP="$BACKUP_DIR/pre_restore_${TIMESTAMP}.sql"
log "Creating pre-restore backup: $PRE_RESTORE_BACKUP"

if pg_dump -U "$DB_USER" -d "$DB_NAME" > "$PRE_RESTORE_BACKUP" 2>/dev/null; then
    log "Pre-restore backup created successfully"
else
    log "Warning: Could not create pre-restore backup (database might not exist)"
fi

# Drop and recreate database
log "Dropping existing database..."
dropdb -U "$DB_USER" --if-exists "$DB_NAME" || error "Failed to drop database"

log "Creating fresh database..."
createdb -U "$DB_USER" "$DB_NAME" || error "Failed to create database"

# Restore from backup
log "Restoring from backup..."
if psql -U "$DB_USER" -d "$DB_NAME" < "$backup_file"; then
    log "Restore completed successfully"
else
    error "Restore failed"
fi

# Verify database is accessible
if psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" >/dev/null 2>&1; then
    log "Database verification successful"
else
    error "Database verification failed"
fi

log "Restore process completed successfully"
echo "Database has been restored successfully!" 