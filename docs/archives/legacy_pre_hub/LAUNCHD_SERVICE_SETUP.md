# Launchd Service Setup for Background Posting Monitor

**Purpose:** Automatically start and keep the background posting monitor running

---

## Overview

The launchd service ensures the monitor:
- **Starts automatically** when you log in
- **Restarts automatically** if it crashes or stops
- **Runs in the background** without manual intervention

---

## Service Details

**Service Name:** `com.blog.automated-posting`  
**Plist File:** `~/Library/LaunchAgents/com.blog.automated-posting.plist`  
**Monitor Script:** `scripts/background_posting_monitor.sh`

---

## Installation

The service is already installed and loaded. To verify:

```bash
launchctl list com.blog.automated-posting
```

You should see the service listed.

---

## Management Commands

### Check Service Status
```bash
launchctl list com.blog.automated-posting
```

### Start Service (if stopped)
```bash
launchctl start com.blog.automated-posting
```

### Stop Service
```bash
launchctl stop com.blog.automated-posting
```

### Unload Service (disable auto-start)
```bash
launchctl unload ~/Library/LaunchAgents/com.blog.automated-posting.plist
```

### Reload Service (after editing plist)
```bash
launchctl unload ~/Library/LaunchAgents/com.blog.automated-posting.plist
launchctl load ~/Library/LaunchAgents/com.blog.automated-posting.plist
```

---

## Service Configuration

The plist file includes:

- **`RunAtLoad`**: Starts immediately when loaded
- **`KeepAlive`**: Automatically restarts if the process exits
- **`WorkingDirectory`**: Sets project root as working directory
- **`StandardOutPath`**: Logs stdout to `logs/launchd_monitor.out`
- **`StandardErrorPath`**: Logs stderr to `logs/launchd_monitor.err`
- **`Nice`**: Runs with lower priority (nice value 1)

---

## Logs

**Monitor Logs:**
- `logs/background_posting.log` - Main monitor log (from script)
- `logs/launchd_monitor.out` - Launchd stdout
- `logs/launchd_monitor.err` - Launchd stderr

**Check logs:**
```bash
tail -f logs/background_posting.log
tail -f logs/launchd_monitor.out
tail -f logs/launchd_monitor.err
```

---

## Troubleshooting

### Service Not Starting

1. **Check service status:**
   ```bash
   launchctl list com.blog.automated-posting
   ```

2. **Check launchd logs:**
   ```bash
   tail -50 logs/launchd_monitor.err
   ```

3. **Permission Issues (Most Common):**
   If you see "Operation not permitted" errors, you need to grant Full Disk Access:
   - System Settings → Privacy & Security → Full Disk Access
   - Add Terminal.app and enable it
   - See `docs/LAUNCHD_PERMISSIONS_FIX.md` for detailed instructions

4. **Verify script is executable:**
   ```bash
   ls -lah scripts/background_posting_monitor.sh
   chmod +x scripts/background_posting_monitor.sh
   ```

5. **Test script manually:**
   ```bash
   ./scripts/background_posting_monitor.sh
   ```

### Service Keeps Restarting

If `KeepAlive` is causing issues (restart loop), you can temporarily disable it:

1. Edit plist:
   ```bash
   open ~/Library/LaunchAgents/com.blog.automated-posting.plist
   ```

2. Change `<true/>` to `<false/>` under `<key>KeepAlive</key>`

3. Reload service (see commands above)

### Remove Service

To completely remove the launchd service:

```bash
launchctl unload ~/Library/LaunchAgents/com.blog.automated-posting.plist
rm ~/Library/LaunchAgents/com.blog.automated-posting.plist
```

---

## Integration with Manual Scripts

The launchd service works alongside the manual scripts:

- **`start_monitor.sh`**: Still works, but will detect if service is running
- **`stop_monitor.sh`**: Stops the monitor, but service will restart it (due to KeepAlive)

To stop permanently, unload the service first:
```bash
launchctl unload ~/Library/LaunchAgents/com.blog.automated-posting.plist
./stop_monitor.sh
```

---

## Benefits

✅ **Automatic startup** - No manual intervention needed  
✅ **Auto-restart** - Survives crashes and errors  
✅ **Background operation** - Runs independently  
✅ **System integration** - Uses macOS native service management  

---

*Last updated: 2026-01-19*
