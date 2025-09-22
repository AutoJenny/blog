
#!/bin/bash

# Restart Projects Script
# This script stops all processes on ports 5001, 5002, and 5003, then restarts the respective projects
# All output is logged to avoid hanging terminal issues

LOG_DIR="/Users/autojenny/Documents/projects/blog/logs"
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/restart.log"
}

# Function to stop processes on a port
stop_port() {
    local port=$1
    log_message "Stopping processes on port $port..."
    
    # Get PIDs using the port
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [ -n "$pids" ]; then
        log_message "Found processes on port $port: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null
        sleep 2
        
        # Verify they're stopped
        local remaining_pids=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            log_message "WARNING: Some processes still running on port $port: $remaining_pids"
            echo "$remaining_pids" | xargs kill -9 2>/dev/null
        else
            log_message "Successfully stopped all processes on port $port"
        fi
    else
        log_message "No processes found on port $port"
    fi
}

# Function to start a project
start_project() {
    local project_name=$1
    local port=$2
    local project_path=$3
    local startup_cmd=$4
    
    log_message "Starting $project_name on port $port..."
    
    # Change to project directory
    cd "$project_path" || {
        log_message "ERROR: Could not change to directory $project_path"
        return 1
    }
    
    # Start the project in background with logging
    log_message "Running: $startup_cmd"
    nohup bash -c "$startup_cmd" > "$LOG_DIR/${project_name}.log" 2>&1 &
    local pid=$!
    
    log_message "$project_name started with PID $pid"
    echo $pid > "$LOG_DIR/${project_name}.pid"
    
    # Wait for server to start
    sleep 5
    
    # Test if the server is responding
    local test_url="http://localhost:$port"
    if [ "$project_name" = "blog-core" ]; then
        test_url="http://localhost:$port/"
    fi
    
    log_message "Testing $project_name at $test_url..."
    
    # Use curl with timeout to avoid hanging
    if curl -s --max-time 10 "$test_url" > /dev/null 2>&1; then
        log_message "✅ $project_name is running successfully on port $port"
        return 0
    else
        log_message "❌ $project_name failed to respond on port $port"
        log_message "Check logs: $LOG_DIR/${project_name}.log"
        return 1
    fi
}

# Main execution
log_message "=== Starting project restart process ==="

# Stop all processes on target ports
log_message "Stopping existing processes..."
stop_port 5000
stop_port 5001
stop_port 5002
stop_port 5003
stop_port 5004
stop_port 5005
stop_port 5006

# Additional cleanup - kill any remaining Python/Flask processes that might interfere
log_message "Performing additional cleanup..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*run.py" 2>/dev/null || true
pkill -f "flask" 2>/dev/null || true
sleep 2

# Start projects (updated paths for new directory structure)
log_message "Starting projects..."

# Start blog-core project (port 5000)
start_project "blog-core" 5000 "/Users/autojenny/Documents/projects/blog/blog-core" "PORT=5000 /usr/local/bin/python3 app.py"

# Start blog-launchpad microservice (port 5001)
start_project "blog-launchpad" 5001 "/Users/autojenny/Documents/projects/blog/blog-launchpad" "PORT=5001 /usr/local/bin/python3 app.py"

# Start blog-llm-actions microservice (port 5002)
start_project "blog-llm-actions" 5002 "/Users/autojenny/Documents/projects/blog/blog-llm-actions" "PORT=5002 /usr/local/bin/python3 app.py"

# Start the blog-post-sections microservice (port 5003)
start_project "blog-post-sections" 5003 "/Users/autojenny/Documents/projects/blog/blog-post-sections" "/usr/local/bin/python3 app.py"

# Start the blog-post-info microservice (port 5004)
start_project "blog-post-info" 5004 "/Users/autojenny/Documents/projects/blog/blog-post-info" "PORT=5004 /usr/local/bin/python3 app.py"

# Start the blog-images microservice (port 5005)
start_project "blog-images" 5005 "/Users/autojenny/Documents/projects/blog/blog-images" "PORT=5005 /usr/local/bin/python3 app.py"

# Final status check
log_message "=== Final status check ==="
sleep 3

# Check if all ports are responding
if curl -s --max-time 5 http://localhost:5000/ > /dev/null 2>&1; then
    log_message "✅ Port 5000 (blog-core) is responding"
else
    log_message "❌ Port 5000 (blog-core) is not responding"
fi

if curl -s --max-time 5 http://localhost:5001/health > /dev/null 2>&1; then
    log_message "✅ Port 5001 (blog-launchpad) is responding"
else
    log_message "❌ Port 5001 (blog-launchpad) is not responding"
fi

if curl -s --max-time 5 http://localhost:5002/health > /dev/null 2>&1; then
    log_message "✅ Port 5002 (blog-llm-actions) is responding"
else
    log_message "❌ Port 5002 (blog-llm-actions) is not responding"
fi

if curl -s --max-time 5 http://localhost:5003/health > /dev/null 2>&1; then
    log_message "✅ Port 5003 (blog-post-sections) is responding"
else
    log_message "❌ Port 5003 (blog-post-sections) is not responding"
fi

if curl -s --max-time 5 http://localhost:5004/health > /dev/null 2>&1; then
    log_message "✅ Port 5004 (blog-post-info) is responding"
else
    log_message "❌ Port 5004 (blog-post-info) is not responding"
fi

if curl -s --max-time 5 http://localhost:5005/health > /dev/null 2>&1; then
    log_message "✅ Port 5005 (blog-images) is responding"
else
    log_message "❌ Port 5005 (blog-images) is not responding"
fi

log_message "=== Restart process complete ==="
log_message "Logs available in: $LOG_DIR"
log_message "Blog core: http://localhost:5000"
log_message "Blog Launchpad: http://localhost:5001"
log_message "Blog LLM Actions: http://localhost:5002"
log_message "Blog Post Sections: http://localhost:5003"
log_message "Blog Post Info: http://localhost:5004"
log_message "Blog Images: http://localhost:5005" 