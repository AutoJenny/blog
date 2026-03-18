# Server Restart Guide

**Purpose:** Quick reference for restarting the Flask application server

---

## Quick Restart

**Use this script:**
```bash
./restart_server.sh
```

This script:
- Stops any existing server processes
- Clears port 5000 if needed
- Starts the server with proper environment
- Verifies server health
- Shows logs location

---

## Manual Restart

If you prefer to restart manually:

```bash
# Stop existing server
pkill -f unified_app.py
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# Start server
cd /Users/autojenny/Documents/projects/blog
export PYTHONUNBUFFERED=1
export FLASK_ENV=development
export PYTHONPATH="$PWD:$PWD/blog-core:${PYTHONPATH:-}"
nohup python3 unified_app.py > unified_app.out 2>&1 &

# Check if running
curl http://localhost:5000/health
```

---

## Server Files

- **Main Application:** `unified_app.py`
- **Start Script:** `start_blog.sh` (original)
- **Restart Script:** `restart_server.sh` (recommended)
- **Log File:** `unified_app.out`
- **Port:** 5000

---

## Troubleshooting

### Server Won't Start

1. **Check if port 5000 is in use:**
   ```bash
   lsof -ti:5000
   ```
   If something is using it, kill it:
   ```bash
   lsof -ti:5000 | xargs kill -9
   ```

2. **Check logs:**
   ```bash
   tail -50 unified_app.out
   ```

3. **Check for Python errors:**
   ```bash
   python3 unified_app.py
   ```
   (Run directly to see errors immediately)

### Server Keeps Stopping

1. **Check for crashes in logs:**
   ```bash
   tail -100 unified_app.out | grep -i error
   ```

2. **Check system resources:**
   ```bash
   ps aux | grep unified_app
   ```

3. **Check for memory issues:**
   - Look for "Killed" messages in logs
   - Check system memory usage

### Common Issues

- **Port 5000 in use:** Another process is using the port
- **Database connection:** Check PostgreSQL is running
- **Import errors:** Check PYTHONPATH is set correctly
- **Environment variables:** Check `.env` file exists and is valid

---

## Health Check

After restarting, verify the server is healthy:

```bash
curl http://localhost:5000/health
```

Should return: `{"status": "healthy"}` or similar

---

## Logs

- **Server logs:** `unified_app.out`
- **Application logs:** `logs/` directory
- **View recent logs:**
  ```bash
  tail -f unified_app.out
  ```

---

## Background Processes

The server runs in the background using `nohup`. To see if it's running:

```bash
ps aux | grep unified_app.py
```

To stop it:

```bash
pkill -f unified_app.py
```

---

## Notes

- The server uses port 5000 (as per user rules)
- If port 5000 is busy, the script will kill the process using it
- Server logs to `unified_app.out` in the project root
- Environment variables are loaded from `.env` if present
