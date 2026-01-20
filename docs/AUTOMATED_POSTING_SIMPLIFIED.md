# Automated Posting System - Simplified Explanation

## Overview

The automated posting system takes content from the **calendar** and publishes it to Facebook at the right time. Think of it like a production line:

**Calendar** → **Posting Queue** → **Published**

---

## The Calendar: The Source of Truth

The calendar stores **what** should be published and **when**:

### Calendar Content Types:
- **Weekly Words/Phrases/Insults** - Stored in `calendar_ideas` table
- **Themes** - Blog post themes (stored in calendar JSON files)
- **Recipes** - Blog post recipes (stored in calendar JSON files)
- **Product Posts** - Products to promote (stored in `posting_queue` directly)

### How Calendar Works:
- Calendar uses **ISO week numbers** (Week 1-52 per year)
- Each week has scheduled items (e.g., "Week 3 has word 'dreich', phrase 'haud yer wheesht'")
- Calendar is **perpetual** - Week 1 of next year cycles back to same content

---

## The Posting Queue: The Working Queue

The `posting_queue` table is where posts wait to be published. It's like a to-do list.

### Post Status Flow:
```
draft → ready → pending → published
```

1. **draft** - Post created, needs preparation
2. **ready** - Post prepared, ready to schedule
3. **pending** - Post scheduled, waiting for time
4. **published** - Post sent to Facebook ✅

---

## How Automated Posting Works (Every 5 Minutes)

A background monitor runs every 5 minutes and does 4 steps:

### Step 1: Create Posts from Calendar
**Script:** `automated_weekly_content_creator.py`

**What it does:**
- Looks at calendar for upcoming weeks (next 7 days)
- For each week, finds what content is scheduled (words, phrases, insults)
- Creates **draft** posts in `posting_queue` table
- Sets scheduled date/time (e.g., Monday 9 AM)

**Example:**
- Calendar says: "Week 3 has word 'dreich'"
- Creates: `posting_queue` entry with `content_type='weekly_word'`, `status='draft'`, `scheduled_date='2026-01-20'`

---

### Step 2: Prepare Posts
**Script:** `automated_weekly_content_workflow.py`

**What it does:**
- Finds **draft** posts in `posting_queue`
- Prepares them for Facebook:
  - Formats content
  - Generates caption
  - Adds hashtags
  - Creates square image (1080×1080)
- Updates status to **ready**

**Example:**
- Draft post → Generate image → Add caption → Status = **ready**

---

### Step 3: Schedule Posts
**Script:** `automated_posting.py`

**What it does:**
- Finds **ready** posts in `posting_queue`
- Checks if their scheduled time is coming up (within 30 minutes)
- Sets exact `scheduled_timestamp` (adds random delay for natural distribution)
- Updates status to **pending**

**Example:**
- Ready post scheduled for "2026-01-20 09:00"
- Sets `scheduled_timestamp = '2026-01-20 09:05'` (with small random delay)
- Status = **pending**

---

### Step 4: Actually Post
**Script:** `scheduled_posting_executor.py` (replaces old `posting_executor.py`)

**What it does:**
- **Checks automated posting switch** (master control - see below)
- Finds **pending** or **ready** posts where `scheduled_timestamp <= now()`
- Validates scheduled dates (failsafe protection)
- Posts them to Facebook
- Updates status to **published**
- Stores Facebook post ID

**Example:**
- Post scheduled for "2026-01-20 09:05"
- Current time is "2026-01-20 09:06"
- Automated posting switch is ON
- → Post to Facebook → Status = **published** ✅

**⚠️ Important:** If the automated posting switch is OFF, this step will skip all publishing and mark posts as 'skipped'. See [Automated Posting Control System](../docs/AUTOMATED_POSTING_CONTROL_SYSTEM.md) for details.

---

## How It Finds What to Publish

The system doesn't look at the calendar directly when posting. Instead:

1. **Calendar** → Creates posts in `posting_queue` (Step 1)
2. **Posting Queue** → Contains all posts waiting to be published
3. **Posting Executor** → Queries `posting_queue` for posts where:
   - Status is `pending` or `ready`
   - `scheduled_timestamp <= now()`

**Key Point:** The calendar is the **source**, but `posting_queue` is the **working queue**. Once a post is in `posting_queue`, the calendar is no longer checked - everything happens from the queue.

---

## Relationship to Calendar

### Calendar's Role:
- **Planning** - Shows what content is scheduled for each week
- **Creation** - Used to create draft posts in `posting_queue`
- **Display** - Shows in calendar UI what's coming up

### Posting Queue's Role:
- **Execution** - Actually publishes posts
- **Status Tracking** - Tracks if post is draft/ready/pending/published
- **Timing** - Stores exact timestamp for when to post

### The Flow:
```
Calendar (Week 3: word "dreich")
    ↓
automated_weekly_content_creator.py
    ↓
posting_queue (draft, scheduled_date=2026-01-20)
    ↓
automated_weekly_content_workflow.py
    ↓
posting_queue (ready, has image & caption)
    ↓
automated_posting.py
    ↓
posting_queue (pending, scheduled_timestamp=2026-01-20 09:05)
    ↓
scheduled_posting_executor.py (checks automated posting switch)
    ↓
Facebook (published!)
    ↓
posting_queue (published, platform_post_id=12345)
```

---

## Summary

**Calendar** = "What should be published when" (the plan)  
**Posting Queue** = "What's actually being published" (the execution)

The automated system:
1. Reads calendar → Creates draft posts
2. Prepares drafts → Makes them ready
3. Schedules ready posts → Sets exact time
4. Posts when time comes → Sends to Facebook

All happens automatically every 5 minutes!
