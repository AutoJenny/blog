#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Create a database backup before starting
echo "Creating database backup..."
./scripts/db_backup.py

# Start the Flask development server
echo "Server starting on http://127.0.0.1:3000"
echo "Check logs/flask.log for details"

# Start the server with the specified port
FLASK_APP=app FLASK_DEBUG=1 python3 -m flask run --port 3000 2>&1 | tee logs/flask.log

# Check if server started successfully
if [ $? -eq 0 ]; then
    echo "Server started successfully!"
else
    echo "Failed to start server. Check logs/flask.log for details."
    exit 1
fi 