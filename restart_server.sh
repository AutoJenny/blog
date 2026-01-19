#!/bin/bash
#
# Server Restart Script
# Restarts the Flask application server
#

set -euo pipefail

# Absolute project root
ROOT_DIR="/Users/autojenny/Documents/projects/blog"
cd "$ROOT_DIR"

echo "=========================================="
echo "Restarting Blog Server"
echo "=========================================="

# Ensure blog_core import works (symlink for blog-core → blog_core)
if [ -d "blog-core" ] && [ ! -e "blog_core" ]; then
  echo "Creating blog_core symlink..."
  ln -s "blog-core" "blog_core"
fi

# Environment
export PYTHONUNBUFFERED=1
export FLASK_ENV=development
export PYTHONPATH="$ROOT_DIR:$ROOT_DIR/blog-core:${PYTHONPATH:-}"

# Load environment variables from .env if present
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT_DIR/.env"
  set +a
  echo "Loaded environment variables from .env"
fi

# Stop existing server processes
echo ""
echo "Stopping existing server processes..."
pkill -f "python.*unified_app.py" || echo "  No unified_app.py process found"
pkill -f "flask.*run" || echo "  No flask run process found"

# Kill any process on port 5000
PORT_PID=$(lsof -ti:5000 2>/dev/null || true)
if [ -n "$PORT_PID" ]; then
  echo "  Killing process on port 5000 (PID: $PORT_PID)..."
  kill -9 $PORT_PID 2>/dev/null || true
  sleep 1
else
  echo "  Port 5000 is free"
fi

# Wait a moment for processes to fully stop
sleep 2

# Check if port is now free
if lsof -ti:5000 >/dev/null 2>&1; then
  echo "  ⚠️  Warning: Port 5000 still in use, trying to force kill..."
  lsof -ti:5000 | xargs kill -9 2>/dev/null || true
  sleep 1
fi

# Start server
echo ""
echo "Starting server..."
nohup python3 "$ROOT_DIR/unified_app.py" > "$ROOT_DIR/unified_app.out" 2>&1 &
SERVER_PID=$!
echo "  Started unified_app.py (PID: $SERVER_PID)"
echo "  Logs: $ROOT_DIR/unified_app.out"

# Wait a moment for server to initialize
sleep 2

# Health check
echo ""
echo "Checking server health..."
MAX_ATTEMPTS=40
ATTEMPT=0
HEALTHY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  if curl -fsS http://localhost:5000/health >/dev/null 2>&1; then
    HEALTHY=true
    break
  fi
  ATTEMPT=$((ATTEMPT + 1))
  sleep 0.25
done

if [ "$HEALTHY" = true ]; then
  echo ""
  echo "✅ Server is healthy!"
  echo "   URL: http://localhost:5000"
  echo "   PID: $SERVER_PID"
  echo "   Logs: $ROOT_DIR/unified_app.out"
  echo ""
  exit 0
else
  echo ""
  echo "❌ Server failed to start or become healthy"
  echo "   Check logs: $ROOT_DIR/unified_app.out"
  echo ""
  echo "Last 20 lines of log:"
  echo "----------------------------------------"
  tail -20 "$ROOT_DIR/unified_app.out" 2>/dev/null || echo "  (log file not found or empty)"
  echo "----------------------------------------"
  echo ""
  exit 1
fi
