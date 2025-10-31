#!/usr/bin/env bash
set -euo pipefail

# Absolute project root
ROOT_DIR="/Users/autojenny/Documents/projects/blog"
cd "$ROOT_DIR"

# Ensure blog_core import works (symlink for blog-core → blog_core)
if [ -d "blog-core" ] && [ ! -e "blog_core" ]; then
  ln -s "blog-core" "blog_core"
fi

# Environment
export PYTHONUNBUFFERED=1
export FLASK_ENV=development
export PYTHONPATH="$ROOT_DIR:$ROOT_DIR/blog-core:${PYTHONPATH:-}"

# Stop existing server (port policy: always 5000)
pkill -f unified_app.py || true
sleep 1

# Start server
nohup python3 "$ROOT_DIR/unified_app.py" > "$ROOT_DIR/unified_app.out" 2>&1 &
SERVER_PID=$!
echo "Started unified_app.py (pid: $SERVER_PID)"

# Health check
for i in {1..40}; do
  if curl -fsS http://localhost:5000/health >/dev/null 2>&1; then
    echo "Server is healthy at http://localhost:5000"
    exit 0
  fi
  sleep 0.25
done

echo "Failed to verify server health. See unified_app.out for details." >&2
exit 1