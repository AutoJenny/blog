#!/bin/bash

# Exit on error, but allow for proper error handling
set -eo pipefail

# Configuration
MONITOR_DIR="$HOME/.blog_monitoring"
LOG_FILE="$MONITOR_DIR/health.log"
DB_NAME="blog"
DB_USER="postgres"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_URL="http://localhost:5000"  # Adjust if different

# Ensure monitoring directory exists
mkdir -p "$MONITOR_DIR"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $1"
    # Here you could add email notification or other alerting mechanisms
    exit 1
}

# Check if PostgreSQL is running
if ! pg_isready -q; then
    error "PostgreSQL is not running"
fi

# Check if database exists and is accessible
if ! psql -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    error "Database '$DB_NAME' does not exist"
fi

# Check if key tables exist and are accessible
tables=("post" "post_development" "post_section" "llm_action")
for table in "${tables[@]}"; do
    if ! psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1 FROM $table LIMIT 1" >/dev/null 2>&1; then
        error "Table '$table' is not accessible"
    fi
done

# Check if application is running
if ! curl -s "$APP_URL" >/dev/null; then
    error "Application is not responding"
fi

# Check if we can create a test post (optional)
if ! psql -U "$DB_USER" -d "$DB_NAME" -c "
    INSERT INTO post (title, slug, created_at, updated_at) 
    VALUES ('Test Post', 'test-post-$(date +%s)', NOW(), NOW())
    ON CONFLICT DO NOTHING
    RETURNING id" >/dev/null 2>&1; then
    error "Cannot write to database"
fi

# Log successful health check
log "Health check completed successfully" 