# Launchd Service Permissions Fix

**Issue:** Launchd service shows "Operation not permitted" errors

---

## Problem

When launchd tries to start the monitor, you may see errors like:
```
/bin/bash: /Users/autojenny/Documents/projects/blog/scripts/background_posting_monitor.sh: Operation not permitted
```

This is a macOS security feature that restricts what launchd can access.

---

## Solution: Grant Full Disk Access

macOS requires "Full Disk Access" permission for launchd to run scripts in certain directories.

### Steps:

1. **Open System Settings:**
   - Apple Menu → System Settings
   - Go to **Privacy & Security**
   - Click **Full Disk Access**

2. **Add Terminal (or your terminal app):**
   - Click the **+** button
   - Navigate to `/Applications/Utilities/Terminal.app` (or your terminal app)
   - Add it to the list
   - **Enable the toggle** next to Terminal

3. **Reload the service:**
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.blog.automated-posting.plist
   launchctl load ~/Library/LaunchAgents/com.blog.automated-posting.plist
   launchctl start com.blog.automated-posting
   ```

### Alternative: Use Manual Start Script

If you prefer not to grant Full Disk Access, you can use the manual start script instead:

```bash
./start_monitor.sh
```

The monitor will still run, but won't auto-start on login.

---

## Verify It's Working

After granting permissions:

```bash
# Check service status
launchctl list com.blog.automated-posting

# Check if monitor is running
curl http://localhost:5000/monitoring/status

# Check process
ps aux | grep background_posting_monitor
```

---

## Why This Happens

macOS Catalina and later versions restrict what system services can access, even for user-owned files. Launchd needs explicit permission to execute scripts in your Documents folder.

---

*Last updated: 2026-01-19*
