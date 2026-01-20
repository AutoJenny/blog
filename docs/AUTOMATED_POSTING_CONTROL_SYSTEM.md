# Automated Posting Control System

**Date:** 2026-01-20  
**Status:** ✅ **IMPLEMENTED**

---

## Overview

The Automated Posting Control System provides a master switch to enable/disable all automated posting across all platforms and channels. This system ensures that automated publishing can be safely paused without modifying code or stopping background processes.

---

## Key Features

1. **Master Switch**: Single toggle to control all automated posting
2. **Manual Trigger**: Ability to manually publish when automation is disabled
3. **UI Control**: Visual control panel on homepage Calendar & Planning section
4. **Database-Driven**: State stored in `system_config` table
5. **Failsafe Protection**: All automated scripts respect the switch

---

## System Architecture

### Database Schema

**Table:** `system_config`

```sql
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(100)
);
```

**Key:** `automated_posting_enabled`
- **Values:** `'true'` (enabled) or `'false'` (disabled)
- **Default:** `'true'` (enabled)
- **Purpose:** Master switch for all automated posting

### Core Components

1. **Scheduled Posting Executor** (`scripts/scheduled_posting_executor.py`)
   - Centralized date-sensitive scheduler
   - Checks `automated_posting_enabled` before publishing
   - Returns early with all posts marked as 'skipped' when disabled

2. **API Endpoints** (`blueprints/automated_posting_api.py`)
   - `GET /api/automated-posting/status` - Get current state
   - `POST /api/automated-posting/toggle` - Toggle on/off
   - `POST /api/automated-posting/trigger` - Manual publish (bypasses switch)

3. **UI Controls** (`templates/index.html`, `templates/planning/calendar/shared_calendar_header.html`)
   - Toggle switch
   - Status indicator
   - Manual trigger button

---

## How It Works

### When Automation is ENABLED (default)

1. `background_posting_monitor.sh` runs every 5 minutes
2. Calls `scheduled_posting_executor.py`
3. Executor checks `is_automated_posting_enabled()` → returns `True`
4. Proceeds with normal publishing flow
5. Posts are published to their scheduled platforms

### When Automation is DISABLED

1. `background_posting_monitor.sh` runs every 5 minutes
2. Calls `scheduled_posting_executor.py`
3. Executor checks `is_automated_posting_enabled()` → returns `False`
4. **Early return** - logs "Automated posting is DISABLED - skipping all publishing"
5. All due posts are marked as 'skipped' in stats
6. **No posts are published**

### Manual Trigger (Bypass Mode)

1. User clicks "Publish Now" button (only visible when automation is off)
2. API endpoint calls `scheduled_posting_executor.py` with `--bypass-switch` flag
3. Executor sets `_bypass_switch = True`
4. Bypasses the switch check and publishes due posts immediately
5. Useful for testing or one-off publishing when automation is disabled

---

## Code Flow

### Scheduled Posting Executor

```python
def process_due_posts(self) -> Dict[str, int]:
    # CRITICAL: Check if automated posting is enabled (unless bypassed)
    if not self._bypass_switch and not self.is_automated_posting_enabled():
        logger.info("Automated posting is DISABLED - skipping all publishing")
        due_posts = self.get_due_posts()
        stats['total_found'] = len(due_posts)
        stats['skipped'] = len(due_posts)
        return stats  # ← Returns early, NO publishing
    
    # Normal publishing flow continues...
```

### Switch Check Method

```python
def is_automated_posting_enabled(self) -> bool:
    """Check if automated posting is enabled in system_config."""
    with self.db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT config_value
            FROM system_config
            WHERE config_key = 'automated_posting_enabled'
        """)
        result = cursor.fetchone()
        
        if result:
            value = result.get('config_value', 'true').lower()
            return value == 'true' or value == '1'
        
        # Default to enabled if not found (safer - allows posting)
        return True
```

---

## API Endpoints

### GET `/api/automated-posting/status`

Get the current automated posting status.

**Response:**
```json
{
  "success": true,
  "enabled": false
}
```

### POST `/api/automated-posting/toggle`

Toggle automated posting on/off.

**Request:**
```json
{
  "enabled": false
}
```

**Response:**
```json
{
  "success": true,
  "enabled": false,
  "message": "Automated posting disabled"
}
```

### POST `/api/automated-posting/trigger`

Manually trigger publishing (bypasses switch).

**Response:**
```json
{
  "success": true,
  "message": "Manual publishing triggered successfully",
  "output": "..."
}
```

---

## UI Controls

### Homepage Calendar & Planning Panel

**Location:** Top right of "Calendar & Planning" panel on homepage (`/`)

**Components:**
- **Toggle Switch**: Enable/disable automated posting
- **Status Indicator**: 
  - Green dot + "Enabled" when on
  - Red dot + "Disabled" when off
- **Manual Trigger Button**: "Publish Now" (only visible when disabled)

### Calendar Page Header

**Location:** Top right of calendar header (`/planning/calendar`)

**Same components as homepage panel**

---

## Background Monitor Integration

The `background_posting_monitor.sh` script calls `scheduled_posting_executor.py` every 5 minutes. The executor respects the switch:

```bash
# Step 6: Run the scheduled posting executor
PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/scheduled_posting_executor.py"
```

**Behavior:**
- If switch is ON: Normal publishing proceeds
- If switch is OFF: Executor returns early, no posts published
- Monitor continues running (doesn't stop)

---

## Migration

**File:** `migrations/add_automated_posting_control.sql`

**What it does:**
1. Creates `system_config` table (if not exists)
2. Inserts default: `automated_posting_enabled = 'true'`
3. Adds index for fast lookups

**To apply:**
```bash
psql -U autojenny -d blog -f migrations/add_automated_posting_control.sql
```

---

## Testing

### Verify Switch is Working

```python
from scripts.scheduled_posting_executor import ScheduledPostingExecutor

executor = ScheduledPostingExecutor()
enabled = executor.is_automated_posting_enabled()
print(f"Automated posting enabled: {enabled}")
```

### Test Disabled State

1. Turn switch OFF via UI
2. Check database: `SELECT config_value FROM system_config WHERE config_key = 'automated_posting_enabled';`
3. Run executor manually: `python3 scripts/scheduled_posting_executor.py`
4. Check logs for: "Automated posting is DISABLED - skipping all publishing"
5. Verify no posts were published

### Test Manual Trigger

1. Turn switch OFF
2. Click "Publish Now" button
3. Verify posts are published (bypasses switch)
4. Check logs for bypass confirmation

---

## Related Systems

### Scheduled Posting Executor

**File:** `scripts/scheduled_posting_executor.py`

- Centralized date-sensitive scheduler
- Replaces old `posting_executor.py`
- Implements failsafe date validation
- Routes to platform-specific publishers

### Platform Publishers

**File:** `utils/platform_publishers.py`

- Simplified platform-specific publishing functions
- Assumes date validation already occurred
- Does NOT check the automation switch (that's the executor's job)

### Background Monitor

**File:** `scripts/background_posting_monitor.sh`

- Orchestrates all automation scripts
- Calls `scheduled_posting_executor.py` every 5 minutes
- Continues running regardless of switch state

---

## Troubleshooting

### Switch Not Working

1. **Check database:**
   ```sql
   SELECT * FROM system_config WHERE config_key = 'automated_posting_enabled';
   ```

2. **Check logs:**
   ```bash
   tail -f logs/scheduled_posting_executor.log
   ```
   Look for: "Automated posting is DISABLED - skipping all publishing"

3. **Verify executor is being called:**
   ```bash
   tail -f logs/background_posting_monitor.log
   ```

### Posts Still Publishing When Disabled

1. Check if manual trigger was used (bypasses switch)
2. Verify `_bypass_switch` is False in executor
3. Check for other code paths that might publish directly

### UI Not Reflecting State

1. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
2. Check browser console for JavaScript errors
3. Verify API endpoint is accessible: `curl http://localhost:5000/api/automated-posting/status`

---

## Security Considerations

1. **Default State**: System defaults to ENABLED (safer - allows posting)
2. **Error Handling**: On database errors, defaults to ENABLED (safer)
3. **Bypass Flag**: Only set via manual API trigger (intentional)
4. **No Authentication**: Currently no auth required (consider adding if needed)

---

## Future Enhancements

1. **Per-Platform Control**: Individual switches for Facebook, Instagram, etc.
2. **Scheduled Enable/Disable**: Auto-enable at specific times
3. **Audit Log**: Track who changed the switch and when
4. **Notifications**: Alert when switch is toggled
5. **Authentication**: Require login to toggle switch

---

## Changelog

**2026-01-20:**
- Initial implementation
- Added `system_config` table
- Created API endpoints
- Added UI controls to homepage and calendar
- Updated `scheduled_posting_executor.py` to check switch
- Added manual trigger functionality
