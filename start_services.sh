#!/bin/bash

# Simple service starter - no complex logging to avoid hangs
echo "Starting blog services..."

# Kill any existing processes
echo "Stopping existing processes..."
pkill -f "python.*app.py" 2>/dev/null || true
sleep 2

# Start blog-core
echo "Starting blog-core on port 5000..."
cd /Users/autojenny/Documents/projects/blog/blog-core
nohup PORT=5000 /opt/homebrew/bin/python3 app.py > /dev/null 2>&1 &
echo "blog-core started"

# Start blog-launchpad
echo "Starting blog-launchpad on port 5001..."
cd /Users/autojenny/Documents/projects/blog/blog-launchpad
nohup PORT=5001 /opt/homebrew/bin/python3 app.py > /dev/null 2>&1 &
echo "blog-launchpad started"

# Start blog-llm-actions
echo "Starting blog-llm-actions on port 5002..."
cd /Users/autojenny/Documents/projects/blog/blog-llm-actions
nohup PORT=5002 /opt/homebrew/bin/python3 app.py > /dev/null 2>&1 &
echo "blog-llm-actions started"

# Start blog-post-sections
echo "Starting blog-post-sections on port 5003..."
cd /Users/autojenny/Documents/projects/blog/blog-post-sections
nohup /opt/homebrew/bin/python3 app.py > /dev/null 2>&1 &
echo "blog-post-sections started"

# Start blog-post-info
echo "Starting blog-post-info on port 5004..."
cd /Users/autojenny/Documents/projects/blog/blog-post-info
nohup PORT=5004 /opt/homebrew/bin/python3 app.py > /dev/null 2>&1 &
echo "blog-post-info started"

echo "All services started!"
echo "Blog core: http://localhost:5000"
echo "Blog Launchpad: http://localhost:5001"
echo "Blog LLM Actions: http://localhost:5002"
echo "Blog Post Sections: http://localhost:5003"
echo "Blog Post Info: http://localhost:5004"

