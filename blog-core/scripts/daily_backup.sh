#!/bin/bash

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$DIR" )"

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Run backup with compression
cd "$PROJECT_ROOT"
python3 scripts/db_backup.py

# Log the backup
echo "$(date): Backup completed" >> "$HOME/.blog_backups/backup.log" 