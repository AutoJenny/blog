#!/usr/bin/env bash
set -euo pipefail

# One-click supervisor for the local "AI Hub + BlogForge" cockpit.
# - Kills anything listening on: 9000, 5000, 3001, 8000
# - Starts AI Hub (9000) + BlogForge UI (5000) using the master venv
# - Opens AI Hub dashboard in the foreground

ROOT_DIR="/Users/autojenny/Documents/projects/blog"
AIHUB_DIR="/Users/autojenny/Documents/ai-hub"

MASTER_VENV="${ROOT_DIR}/master_venv"
if [ ! -d "${MASTER_VENV}" ]; then
  MASTER_VENV="${ROOT_DIR}/venv"
fi

if [ ! -x "${MASTER_VENV}/bin/python" ] || [ ! -x "${MASTER_VENV}/bin/uvicorn" ]; then
  echo "Master venv is missing required binaries. Expected: ${MASTER_VENV}/bin/python and ${MASTER_VENV}/bin/uvicorn" >&2
  exit 1
fi

cleanup_port() {
  local port="$1"
  local pids
  pids="$(lsof -nP -iTCP:${port} -sTCP:LISTEN -t 2>/dev/null || true)"
  if [ -n "${pids}" ]; then
    echo "Stopping listeners on :${port} -> ${pids}"
    kill -9 ${pids} >/dev/null 2>&1 || true
  fi
}

echo "== Ignition: cleanup =="
for port in 9000 5000 3001 8000; do
  cleanup_port "${port}"
done

# Extra belt-and-suspenders: uvicorn's reload can leave a watcher/binder around.
pkill -f "uvicorn app.main:app" >/dev/null 2>&1 || true
pkill -f "app.main:app" >/dev/null 2>&1 || true
pkill -f "unified_app.py" >/dev/null 2>&1 || true

echo "== Ignition: launch =="
export PYTHONUNBUFFERED=1

# Start AI Hub on :9000
cd "${AIHUB_DIR}"
nohup "${MASTER_VENV}/bin/uvicorn" app.main:app --port 9000 \
  > "${ROOT_DIR}/ai-hub_9000.out" 2>&1 &
AIHUB_PID=$!
echo "Started AI Hub (pid: ${AIHUB_PID})"

# Start BlogForge on :5000
cd "${ROOT_DIR}"
if [ ! -e "blog_core" ] && [ -d "blog-core" ]; then
  ln -s "blog-core" "blog_core"
fi

nohup "${MASTER_VENV}/bin/python" "./unified_app.py" \
  > "${ROOT_DIR}/blogforge_5000.out" 2>&1 &
BLOG_PID=$!
echo "Started BlogForge (pid: ${BLOG_PID})"

echo "== Ignition: verify =="

wait_for() {
  local url="$1"
  local label="$2"
  for i in {1..60}; do
    if curl -fsS --max-time 1 "${url}" >/dev/null 2>&1; then
      echo "${label} is up: ${url}"
      return 0
    fi
    sleep 0.25
  done
  echo "Timed out waiting for ${label}: ${url}" >&2
  return 1
}

wait_for "http://127.0.0.1:9000/dashboard" "AI Hub dashboard"
wait_for "http://127.0.0.1:5000/planning/calendar" "BlogForge /planning/calendar"

echo "== Ignition: handoff =="
open "http://localhost:9000/" >/dev/null 2>&1 || true

echo "Ignition complete."

