#!/bin/bash

# Change to the project directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Run dependency check
./scripts/check_dependencies.py

# Check exit code
if [ $? -eq 1 ]; then
    # Send notification (modify this based on your notification system)
    if [ -n "$ADMIN_EMAIL" ]; then
        echo "Dependency check found issues. Check logs/dependency_check.json for details." | \
        mail -s "Blog Dependencies Warning" "$ADMIN_EMAIL"
    fi
fi

# Deactivate virtual environment
deactivate 