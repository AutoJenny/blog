# Monitoring System - Technical Reference

**Date:** 2026-01-18  
**Status:** ✅ **PRODUCTION READY** - Full monitoring system with status indicator and reporting

---

## Overview

The monitoring system provides real-time visibility into automation processes, specifically focusing on automated social media postings. It includes:

1. **Status Indicator** - Traffic light icon in header (top right) showing if monitoring is running
2. **Monitoring Report Page** - Detailed view of all automation events with filtering
3. **Start/Stop Controls** - Ability to control the background monitoring script from the UI

---

## Features

### 1. Status Indicator (Header Module)

**Location:** Top right of every page, next to navigation links

**Visual Indicators:**
- 🟢 **Green Circle** - Monitoring is running
- 🔴 **Red Circle** (pulsing) - Monitoring is stopped

**Functionality:**
- Auto-updates every 30 seconds
- Click to view full monitoring report
- "Start" button appears when monitoring is stopped

**Implementation:**
- `templates/shared/header.html` - Monitoring module HTML
- `static/js/shared/monitoring-module.js` - Status updates and controls

---

### 2. Monitoring Report Page

**URL:** `http://localhost:5000/monitoring/report`

**Features:**
- **Filter Tabs:**
  - **All Events** - Shows everything
  - **Automated Postings** - Only actual publication events
  - **Administrative** - Infrastructure/monitoring messages only

- **Event Display:**
  - Timestamp (most recent first)
  - Script name
  - Message with full context
  - Result icon (✅ success, ❌ error, ⚠️ warning)

- **Status Controls:**
  - Current status indicator
  - Start/Stop buttons
  - Real-time status updates

**Auto-refresh:**
- Status: Every 30 seconds
- Events: Every 60 seconds

---

### 3. API Endpoints

#### Get Monitoring Status
```
GET /monitoring/status
```

**Response:**
```json
{
  "success": true,
  "is_running": true,
  "pid": 33050
}
```

#### Start Monitoring
```
POST /monitoring/start
```

**Response:**
```json
{
  "success": true,
  "message": "Monitoring started successfully",
  "pid": 33050
}
```

#### Stop Monitoring
```
POST /monitoring/stop
```

**Response:**
```json
{
  "success": true,
  "message": "Monitoring stopped successfully"
}
```

#### Get Events
```
GET /monitoring/api/events?type=posting
```

**Query Parameters:**
- `type` - Filter: `all`, `posting`, or `admin` (default: `all`)

**Response:**
```json
{
  "success": true,
  "events": [
    {
      "timestamp": "2026-01-18T02:20:07",
      "script": "automated_weekly_content_workflow",
      "level": "INFO",
      "message": "Published to Facebook (2 page(s)): queue_id 1014 (weekly_insult) - Och, we've a' said it...",
      "result": "success",
      "category": "posting"
    }
  ],
  "total": 1,
  "filter": "posting"
}
```

---

## Event Categories

### Automated Postings

**What it shows:**
- Actual publication events to social media platforms
- Successful posts with details (queue_id, content_type, pages, content preview)
- Failed posts with error messages
- Publication attempts

**Scripts monitored:**
- `automated_weekly_content_creator` - Creates weekly content posts
- `automated_weekly_content_workflow` - Processes and publishes weekly content
- `posting_executor` - Executes scheduled posts
- `automated_posting` - Schedules product posts

**Message format:**
```
Published to Facebook (2 page(s)): queue_id 1014 (weekly_insult) - Och, we've a' said it...
```

**Filtered out:**
- Debug messages
- Internal workflow steps (format, caption generation, image creation)
- Database connection messages
- Status checks and queries
- Intermediate API responses

---

### Administrative

**What it shows:**
- Background monitor infrastructure messages
- System orchestration events
- Monitoring script status

**Scripts monitored:**
- `background_posting_monitor` - The monitoring script itself

**Message examples:**
- "Starting background posting monitor"
- "Checking for due posts..."
- "Running automated posting scheduler..."
- "Running posting executor..."
- "Waiting 5 minutes until next check..."

**Filtered out:**
- Script output from posting processes (those go to "Automated Postings")
- Python logging format messages (only shows monitor's own messages)

---

## Log Files

The monitoring system reads from these log files:

### Automated Postings
- `logs/automated_weekly_content_creator.log`
- `logs/automated_weekly_content_workflow.log`
- `logs/posting_executor.log`
- `logs/automated_posting.log`

### Administrative
- `logs/background_posting.log`

**Note:** The system reads the last 200 lines from each log file to show recent events.

---

## Technical Implementation

### Blueprint
**File:** `blueprints/monitoring.py`

**Routes:**
- `/monitoring/status` - Get status
- `/monitoring/start` - Start monitoring (POST)
- `/monitoring/stop` - Stop monitoring (POST)
- `/monitoring/report` - Report page
- `/monitoring/api/events` - Get events (with filtering)

### Templates
- `templates/monitoring/report.html` - Full monitoring report page
- `templates/shared/header.html` - Status indicator module

### JavaScript
- `static/js/shared/monitoring-module.js` - Header status updates

### Background Monitor
**File:** `scripts/background_posting_monitor.sh`

**What it does:**
- Runs continuously, checking every 5 minutes
- Executes automation scripts in order:
  1. `automated_weekly_content_creator.py` - Create posts
  2. `automated_weekly_content_workflow.py` - Execute workflows
  3. `automated_posting.py` - Product post scheduling
  4. `posting_executor.py` - Publish due posts

**PID File:** `logs/background_posting.pid`

**Log File:** `logs/background_posting.log`

---

## Usage

### Starting Monitoring

**Via UI:**
1. Check status indicator in header (top right)
2. If red, click "Start" button
3. Status updates automatically

**Via API:**
```bash
curl -X POST http://localhost:5000/monitoring/start
```

**Via Command Line:**
```bash
./scripts/background_posting_monitor.sh
```

### Viewing Events

**Via UI:**
1. Click "Monitor" link in header (or go to `/monitoring/report`)
2. Select filter tab (All Events, Automated Postings, Administrative)
3. Events auto-refresh every 60 seconds

**Via API:**
```bash
# All events
curl http://localhost:5000/monitoring/api/events

# Only posting events
curl http://localhost:5000/monitoring/api/events?type=posting

# Only administrative events
curl http://localhost:5000/monitoring/api/events?type=admin
```

### Stopping Monitoring

**Via UI:**
1. Go to `/monitoring/report`
2. Click "Stop Monitor" button
3. Confirm action

**Via API:**
```bash
curl -X POST http://localhost:5000/monitoring/stop
```

**Via Command Line:**
```bash
kill $(cat logs/background_posting.pid)
```

---

## Event Message Format

### Publication Events

**Success:**
```
Published to Facebook (2 page(s)): queue_id 1014 (weekly_insult) - Och, we've a' said it...
```

**Failure:**
```
❌ publish_to_facebook failed for queue_id 1014 (weekly_insult): {error details}
```

**Components:**
- Platform: Facebook (or Instagram, Twitter, etc. when implemented)
- Pages count: Number of pages posted to
- Queue ID: Internal post identifier
- Content type: weekly_word, weekly_phrase, or weekly_insult
- Content preview: First 30 characters of Scots text

---

## Troubleshooting

### Status Indicator Not Updating

1. Check browser console for JavaScript errors
2. Verify `/monitoring/status` endpoint is accessible
3. Check that `monitoring-module.js` is loaded

### No Events Showing

1. Verify log files exist in `logs/` directory
2. Check log file permissions
3. Verify scripts are actually running and logging
4. Check filter - try "All Events" tab

### Events Not Filtering Correctly

1. Check event category assignment in `blueprints/monitoring.py`
2. Verify message format matches filter patterns
3. Check log file parsing logic

### Monitoring Won't Start

1. Check if already running: `ps aux | grep background_posting`
2. Check PID file: `cat logs/background_posting.pid`
3. Verify script exists: `ls -la scripts/background_posting_monitor.sh`
4. Check script permissions: `chmod +x scripts/background_posting_monitor.sh`

---

## Related Documentation

- `docs/WEEKLY_CONTENT_AUTOMATION_COMPLETE.md` - Weekly content automation details
- `docs/WEEKLY_CONTENT_SYSTEM_TECHNICAL_REFERENCE.md` - Weekly content system reference
- `scripts/background_posting_monitor.sh` - Background monitor script

---

**Last Updated:** 2026-01-18  
**Version:** 1.0
