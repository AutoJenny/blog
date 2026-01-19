# Monitor Troubleshooting Guide

**Purpose:** Diagnose and fix issues with the background posting monitor stopping

---

## Quick Diagnosis

### Check Monitor Status
```bash
curl http://localhost:5000/monitoring/status
```

### Check if Process is Running
```bash
ps aux | grep background_posting_monitor | grep -v grep
```

### Check PID File
```bash
cat logs/background_posting.pid
ps -p $(cat logs/background_posting.pid)  # Check if PID is actually running
```

### Check Recent Logs
```bash
tail -50 logs/background_posting.log
```

---

## Common Reasons Monitor Stops

### 1. **PostgreSQL Not Running** (Most Common)

**Symptoms:**
- Log shows: `connection failed: connection to server at "127.0.0.1", port 5432 failed: Connection refused`
- Monitor stops after database connection errors

**Solution:**
- Start PostgreSQL: `brew services start postgresql@14` (or your version)
- Verify: `ps aux | grep postgres`
- Restart monitor after PostgreSQL is running

### 2. **Process Killed by System**

**Symptoms:**
- PID file exists but process is not running
- No "stopped" message in logs

**Possible Causes:**
- System shutdown/restart
- Out of memory (OOM killer)
- Manual kill (`kill -9`)

**Solution:**
- Restart monitor manually
- Check system logs for OOM kills: `dmesg | grep -i oom`

### 3. **Script Error/Crash**

**Symptoms:**
- Error messages in logs
- Monitor stops mid-execution

**Solution:**
- Check logs for Python errors
- Fix underlying issue
- Restart monitor

### 4. **No Auto-Restart Mechanism**

**Current State:**
- Monitor runs as a simple bash script
- No system service (launchd/cron) to auto-restart
- Must be manually started after crashes

---

## Solutions

### Option 1: Manual Start (Current)

**Start via UI:**
1. Go to `http://localhost:5000/monitoring/report`
2. Click "Start Monitor" button

**Start via API:**
```bash
curl -X POST http://localhost:5000/monitoring/start
```

**Start via Command Line:**
```bash
./scripts/background_posting_monitor.sh
```

### Option 2: Launchd Service (Recommended for Auto-Restart)

Create a launchd plist file to automatically start and restart the monitor:

**File:** `~/Library/LaunchAgents/com.blog.automated-posting.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.blog.automated-posting</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/autojenny/Documents/projects/blog/scripts/background_posting_monitor.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/autojenny/Documents/projects/blog</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/autojenny/Documents/projects/blog/logs/launchd_monitor.out</string>
    <key>StandardErrorPath</key>
    <string>/Users/autojenny/Documents/projects/blog/logs/launchd_monitor.err</string>
</dict>
</plist>
```

**Install:**
```bash
launchctl load ~/Library/LaunchAgents/com.blog.automated-posting.plist
```

**Uninstall:**
```bash
launchctl unload ~/Library/LaunchAgents/com.blog.automated-posting.plist
```

### Option 3: Enhanced Monitor Script (Error Recovery)

Add error handling to the monitor script to:
- Catch database connection errors
- Retry with backoff
- Continue running even if one script fails

---

## Current Status

**Monitor Type:** Manual start (no auto-restart)  
**PID File:** `logs/background_posting.pid`  
**Log File:** `logs/background_posting.log`  
**Launchd Services:** Registered but may not be active

---

## Immediate Fix

If monitor is stopped:

**Quick Start (Recommended):**
```bash
./start_monitor.sh
```

**Or via API:**
```bash
curl -X POST http://localhost:5000/monitoring/start
```

**Or manually:**
1. **Check PostgreSQL is running:**
   ```bash
   brew services list | grep postgresql
   ```

2. **Start PostgreSQL if needed:**
   ```bash
   brew services start postgresql@14  # Adjust version as needed
   ```

3. **Start monitor:**
   ```bash
   ./scripts/background_posting_monitor.sh &
   ```

4. **Verify:**
   ```bash
   curl http://localhost:5000/monitoring/status
   ```

---

## Prevention

To prevent monitor from stopping:

1. **Ensure PostgreSQL auto-starts:**
   ```bash
   brew services start postgresql@14
   ```

2. **Use launchd service** (Option 2 above) for auto-restart

3. **Monitor script now has error handling** - continues running even if individual scripts fail

4. **Use restart script** - `./start_monitor.sh` to easily restart

---

## Quick Reference Scripts

**Start Monitor:**
```bash
./start_monitor.sh
```

**Stop Monitor:**
```bash
./stop_monitor.sh
```

**Check Status:**
```bash
curl http://localhost:5000/monitoring/status
```

---

*Last updated: 2026-01-19*
