#!/bin/bash

# Kill any existing processes
pkill -f flask

# Ensure logs directory exists
mkdir -p logs

# Start Flask in the background
echo "Server starting on http://127.0.0.1:8080"
echo "Check logs/flask.log for details"
nohup python3 run.py > logs/flask.log 2>&1 &
sleep 2
tail -n 10 logs/flask.log 