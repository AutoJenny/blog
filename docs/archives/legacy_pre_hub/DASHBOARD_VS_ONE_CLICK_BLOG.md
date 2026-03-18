# Dashboard vs One-Click Publication - Role Clarification

**Date:** 2025-01-XX  
**Purpose:** Clear separation of concerns between Publication Dashboard and One-Click Publication

**Note:** System renamed from "One-Click Blog" to "One-Click Publication" to reflect multi-channel capability (blog, Facebook, Instagram, Twitter, Newsletter).

---

## Core Distinction

### Publication Dashboard (`/publication/dashboard`)
**Role:** **Schedule Management & Multi-Item Overview**

**What it does:**
- Shows ALL scheduled items for a week/month
- Provides week overview (7-day grid)
- Shows publication queue (what needs to be published)
- Shows production pipeline summary (what's in progress)
- Provides high-level actions (approve, publish, reschedule)
- Links to One-Click Publication for detailed work

**What it does NOT do:**
- ❌ Execute individual substages
- ❌ Show detailed pipeline for single item
- ❌ Provide production automation controls

---

### One-Click Publication (`/launchpad/one-click-publication`)
**Role:** **Single Item Production Deep Dive for Any Output Type**

**What it does:**
- Shows ONE selected item's detailed production pipeline
- **Supports multiple output channels** (blog, Facebook, Instagram, Twitter, Newsletter)
- **Dynamically shows stages/substages** based on (post_type, output_channel) combination
- Provides substage execution controls (Run buttons)
- Shows detailed status for each substage
- Provides automation controls (Run All, Pause, Resume)
- Shows publication status for that item's channels
- Allows editing and content creation

**What it does NOT do:**
- ❌ Show week overview (dashboard's job)
- ❌ Show all scheduled items (dashboard's job)
- ❌ Show publication queue (dashboard's job)
- ❌ Provide schedule management (dashboard's job)

---

## User Flow

```
1. User opens Dashboard
   → Sees all scheduled items for the week
   → Sees what's in progress, what's ready, what needs attention

2. User clicks "Work on This" button for an item
   → Navigates to One-Click Publication with item context
   → URL: /launchpad/one-click-publication?post_id=X&category=theme&item_id=Y&output=blog

3. User works on item in One-Click Publication
   → Selects output channel (Blog, Facebook, Instagram, etc.)
   → Sees channel-specific stages/substages
   → Executes substages
   → Edits content
   → Runs automation

4. User clicks "Back to Dashboard"
   → Returns to overview
   → Sees updated status
```

---

## Feature Comparison

| Feature | Dashboard | One-Click Publication |
|---------|-----------|----------------------|
| **Week Overview** | ✅ 7-day grid | ❌ |
| **All Items View** | ✅ All scheduled | ❌ |
| **Single Item Focus** | ❌ | ✅ Selected item |
| **Output Channel Selection** | ❌ Shows all channels | ✅ Select specific channel |
| **Pipeline Summary** | ✅ High-level | ❌ |
| **Pipeline Details** | ❌ | ✅ Full substages (channel-specific) |
| **Substage Execution** | ❌ | ✅ Run buttons |
| **Publication Queue** | ✅ All items | ❌ |
| **Publication Status** | ✅ Summary | ✅ Single item + channel |
| **Schedule Management** | ✅ | ❌ |
| **Production Controls** | High-level | ✅ Detailed |
| **Automation Controls** | ❌ | ✅ Run All, Pause |

---

## Data Flow

### Dashboard Data
```
GET /api/publication/dashboard?year=2025&week=50
→ Returns: All scheduled items, status summary, publication queue
```

### One-Click Publication Data
```
GET /launchpad/one-click-publication/api/item/theme/123?year=2025&week=50&output=blog
→ Returns: Single item details, full pipeline status (channel-specific), publication status

GET /launchpad/one-click-publication/api/pipeline/<post_id>?output=facebook
→ Returns: Pipeline stages/substages for (post_type, output_channel) combination
```

---

## Implementation Status

### Deprecated Tables Renamed ✅
- `calendar_weeks` → `calendar_weeks_deprecated`
- `calendar_ideas` → `calendar_ideas_deprecated`
- `calendar_schedule` → `calendar_schedule_deprecated`
- `calendar_week_items` → `calendar_week_items_deprecated`

### Next Steps
1. ✅ Fix `/next-up` endpoint to use new calendar system
2. ✅ Add weekly content types to `config/post_type_substages.py`
3. ✅ Create `config/output_channel_stages.py` for channel-specific stages
4. ✅ Update One-Click Publication to accept item + output channel from URL params
5. ✅ Add output channel selector to UI
6. ✅ Remove duplicate features (week overview, all items)
7. ✅ Add "Back to Dashboard" navigation
8. ✅ Add "Work on This" buttons in Dashboard
9. ✅ Rename system throughout codebase (One-Click Blog → One-Click Publication)

---

## Summary

**Dashboard = Manager View** (What needs to be done, overview of all items)  
**One-Click Publication = Worker View** (How to do it, detailed work on one item for specific output channel)

Clear separation ensures:
- ✅ No feature duplication
- ✅ Each tool has focused purpose
- ✅ Better user experience
- ✅ Easier maintenance

