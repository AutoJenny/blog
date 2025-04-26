#!/bin/bash
set -e
BACKUP_DIR="$HOME/.blog_pg_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/blog_backup_$TIMESTAMP.sql"
pg_dump -U postgres -d blog > "$BACKUP_FILE"
find "$BACKUP_DIR" -type f -name 'blog_backup_*.sql' -mtime +14 -delete 