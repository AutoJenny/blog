# One-Click Publication Redesign Plan

**Date:** 2025-01-XX  
**Purpose:** Fix calendar sync, rename from "One-Click Blog" to "One-Click Publication", and support output channel-specific stages

**Note:** This system handles ALL output types (blog, Facebook, Instagram, Twitter, Newsletter), not just blog posts.

---

## Key Distinction: Dashboard vs One-Click Publication

### Publication Dashboard (`/publication/dashboard`)
**Role:** Overall schedule management and multi-item overview
- **Scope:** Week/month view of ALL scheduled items
- **Focus:** Schedule overview, publication queue, production summary
- **Actions:** High-level actions (approve, publish, reschedule)
- **Navigation:** Click item → goes to One-Click Publication for deep dive

### One-Click Publication (`/launchpad/one-click-publication`)
**Role:** Deep dive into SINGLE item's production pipeline for ANY output type
- **Scope:** ONE selected item's detailed production for a specific output channel
- **Focus:** Pipeline execution, substage details, individual controls
- **Actions:** Run substages, edit content, execute automation
- **Entry Point:** Accessed FROM dashboard when clicking an item
- **Output Support:** Blog, Facebook, Instagram, Twitter, Newsletter (each with different stages)

**Relationship:**
```
Dashboard (Overview) → Click Item → One-Click Publication (Detail)
```

**Key Insight:** One-Click Publication must handle:
- **Different Post Types** (themed, recipe, weekly_word, etc.) - already supported via `config/post_type_substages.py`
- **Different Output Channels** (blog, facebook, instagram, etc.) - **NEEDS NEW SYSTEM** for channel-specific stages

---

## Problem 1: System Naming & Scope

### Current Name: "One-Click Blog"
**Issue:** Name implies blog-only, but system should handle all output types

### Solution: Rename to "One-Click Publication"
- More accurately reflects multi-channel capability
- Supports blog, Facebook, Instagram, Twitter, Newsletter outputs
- Each output type may have different stages/substages

---

## Problem 2: Output Channel-Specific Stages

### Current System
- `config/post_type_substages.py` defines stages per **post type** only
- All pipelines assume **blog output**
- No mechanism for channel-specific stages

### The Problem
**Example:** `weekly_word` → Facebook needs different stages than `weekly_word` → Blog
- **Blog:** calendar → content → imaging → header (full pipeline)
- **Facebook:** content formatting → image optimization → publish (minimal pipeline)
- **Instagram:** content formatting → image optimization → carousel creation → publish

### Solution Needed
Create `config/output_channel_stages.py` that defines stages per **(post_type, output_channel)** combination.

**See:** `docs/ONE_CLICK_PUBLICATION_SYSTEM_ANALYSIS.md` for detailed analysis

---

## Problem 3: Calendar Sync Issue

### Current Problem

The `/launchpad/one-click-blog/api/next-up` endpoint uses **deprecated tables**:

**Current Implementation (WRONG):**
```python
# blueprints/automation_calendar.py - get_next_up()
- Queries `calendar_weeks_deprecated` table ❌
- Queries `calendar_ideas_deprecated` table ❌
- Queries `calendar_schedule_deprecated` table ❌
```

**New System (CORRECT):**
- Uses `utils/calendar_resolver.py` to resolve items for current ISO week ✅
- Uses JSON-backed schedule files ✅
- Uses cyclic position-based logic ✅

### Solution: Fix Calendar Sync

**File:** `blueprints/automation_calendar.py`

**Replace `get_next_up()` function:**

**Note:** This endpoint should be renamed to reflect publication scope, not just blog.

```python
@bp.route('/next-up', methods=['GET'])
def get_next_up():
    """
    Get next scheduled item from NEW calendar system.
    
    This endpoint is used by One-Click Blog to show what item to work on.
    It should return a SINGLE item (not all items - that's dashboard's job).
    """
    try:
        from utils.calendar_resolver import resolve_item_for_week
        from datetime import date
        
        # Get current ISO week
        today = date.today()
        year, week_number, _ = today.isocalendar()
        
        # Priority order for selecting which item to show:
        # 1. Items that need work (not_started or in_progress)
        # 2. Items scheduled for today
        # 3. First item in week
        
        categories = ['theme', 'recipe', 'profile_product', 'profile_surname', 
                     'weekly_word', 'weekly_phrase', 'weekly_insult']
        
        # Get all items for current week
        items_with_status = []
        for category in categories:
            item = resolve_item_for_week(category, year, week_number)
            if item:
                post_id = _get_post_id_for_item(category, item['id'])
                status = _get_production_status(post_id, category)
                items_with_status.append({
                    'category': category,
                    'item': item,
                    'post_type': _get_post_type_from_category(category),
                    'post_id': post_id,
                    'status': status
                })
        
        # Select priority item (needs work > scheduled today > first)
        selected_item = _select_priority_item(items_with_status, year, week_number)
        
        if not selected_item:
            return jsonify({
                "success": False,
                "error": "No scheduled items found for current week"
            }), 404
        
        # Get publication info
        publication_info = _get_publication_info(selected_item['category'], year, week_number)
        
        return jsonify({
            "success": True,
            "data": {
                "current_week": {
                    "week_number": week_number,
                    "year": year,
                    "start_date": _get_week_start_date(year, week_number).strftime('%Y-%m-%d'),
                    "end_date": _get_week_end_date(year, week_number).strftime('%Y-%m-%d')
                },
                "selected_item": {
                    "category": selected_item['category'],
                    "post_type": selected_item['post_type'],
                    "id": selected_item['item']['id'],
                    "title": _get_item_title(selected_item['item']),
                    "description": _get_item_description(selected_item['item']),
                    "position": selected_item['item'].get('position')
                },
                "production_status": selected_item['status'],
                "scheduled_date": publication_info['date'],
                "scheduled_relative": publication_info['relative'],
                "post_id": selected_item['post_id'],
                "channels": _get_channels_for_post_type(selected_item['post_type'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_next_up: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
```

**Key Changes:**
- ✅ Uses `utils/calendar_resolver.py` (new system)
- ✅ Returns SINGLE item (not all items)
- ✅ Focuses on production status (not schedule overview)
- ✅ Removed "alternative ideas" (dashboard shows all items)

---

## Problem 4: UI Redesign - Focused on Single Item Production with Output Channel Support

### Current UI Issues

1. **Shows "Next Up" panel** - This duplicates dashboard functionality
2. **Shows "alternative ideas"** - Dashboard shows all items
3. **No clear entry point from dashboard** - Should be linked from dashboard

### Revised UI Design

**One-Click Blog should be:**
- **Single Item Focus** - Shows ONE item's production pipeline
- **Deep Dive** - Detailed substage execution and controls
- **Production Tool** - Run automation, edit content, execute substages
- **Entry from Dashboard** - Accessed via "Work on This" button from dashboard

### New UI Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  Header: One-Click Publication                                   │
│  [← Back to Dashboard] [Item: Theme - "Hogmanay Traditions"]    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Selected Item Card                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Theme: "Hogmanay Traditions"                             │  │
│  │  Post Type: Themed                                        │  │
│  │  Output Channel: [Blog ▼] [Facebook] [Newsletter]        │  │
│  │  Status: 🟡 In Progress (60% complete)                    │  │
│  │  Scheduled: Dec 10, 2025 14:00                            │  │
│  │  [View in Dashboard] [Change Item]                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Production Pipeline (Single Item + Output Channel)             │
│                                                                  │
│  Output: Blog | [Switch to: Facebook] [Instagram] [Newsletter] │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Stage        Substage              Status    Run   Mode │  │
│  │  Calendar     Week Ideas            ✅ Done   [Run] Auto│  │
│  │  Planning     Taxonomy              ✅ Done   [Run] Auto│  │
│  │  Planning     Topic Brainstorming   🟡 In Prog [Run] Auto│  │
│  │  Authoring    Drafting              ⏸ Paused  [Run] Auto│  │
│  │  Imaging      Image Generation      ⏳ Waiting [Run] Auto│  │
│  │  Header       Title & Summary        ⏳ Waiting [Run] Auto│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Note: Stages shown are for "Blog" output. Switching to         │
│  "Facebook" would show different stages (e.g., Syndication).    │
│                                                                  │
│  [Run All Uncompleted] [Pause Automation] [View Full Status]   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Publication Status (Single Item)                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Channel      Status        Scheduled    Actions         │  │
│  │  Blog         🟡 Scheduled  Dec 10 14:00 [Preview] [Edit]│  │
│  │  Facebook     ⏳ Pending    Dec 10 16:00 [Preview] [Edit]│  │
│  │  Newsletter   ⏳ Pending    Dec 10 14:00 [Preview] [Edit]│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  [Publish Now] [Schedule] [View All Channels]                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Differences from Dashboard

| Feature | Dashboard | One-Click Publication |
|---------|-----------|----------------------|
| **Scope** | All items in week | Single selected item |
| **Week Overview** | ✅ 7-day grid | ❌ Removed |
| **Item Selection** | ✅ Multiple items | ✅ Single item (from URL param) |
| **Output Channel Selection** | ❌ Shows all channels | ✅ Select specific channel |
| **Pipeline Detail** | Summary only | ✅ Full substage details |
| **Substage Execution** | ❌ No | ✅ Yes (Run buttons) |
| **Publication Queue** | ✅ All items | ❌ Removed (dashboard's job) |
| **Production Controls** | High-level | ✅ Detailed controls |
| **Channel-Specific Stages** | ❌ | ✅ Dynamic based on output channel |

---

## Implementation Plan

### Phase 1: Add Weekly Content Types
1. Add `weekly_word`, `weekly_phrase`, `weekly_insult` to `config/post_type_substages.py`
2. Define minimal pipelines for blog output
3. Test pipeline display for weekly content

### Phase 2: Create Output Channel Stage System
1. Create `config/output_channel_stages.py`
2. Define social media pipelines for weekly content
3. Define syndication pipelines for themed posts
4. Create helper functions to resolve stages per (post_type, output_channel)

### Phase 3: Fix Calendar Sync
1. Update `get_next_up()` to use `utils/calendar_resolver.py`
2. Remove queries to deprecated tables
3. Return single item (not all items)
4. Test with current week data

### Phase 4: Update Entry Point & Rename
1. Rename route from `/launchpad/one-click-blog` to `/launchpad/one-click-publication`
2. Update all references in codebase
3. Dashboard adds "Work on This" button for each item
4. Button links to `/launchpad/one-click-publication?post_id=X&category=theme&item_id=Y&output=blog`
5. One-Click Publication reads URL params to load specific item and output channel

### Phase 5: Add Output Channel Selector
1. Add output channel selector to UI (Blog, Facebook, Instagram, etc.)
2. Dynamically load stages based on (post_type, output_channel)
3. Update pipeline display to show channel-specific stages
4. Handle channel switching (show different stages)

### Phase 6: Simplify UI
1. Remove "Next Up" panel (dashboard's job)
2. Remove "alternative ideas" (dashboard shows all)
3. Add "Back to Dashboard" button
4. Focus on single item pipeline with output channel support

### Phase 7: Enhance Production Controls
1. Keep detailed pipeline table (this is the core feature)
2. Add publication status panel (for this item + output channel)
3. Add approval status (if required)
4. Add "Run All" automation controls
5. Support executing stages for specific output channels

---

## API Changes

### Updated Endpoints

**`GET /launchpad/one-click-publication/api/next-up`** (renamed)
- **Change:** Now accepts optional query params: `?post_id=X&category=Y&item_id=Z&output=blog`
- **If params provided:** Load that specific item and output channel
- **If no params:** Use priority selection (needs work > scheduled today > first)
- **Response:** Single item (not all items) with available output channels

**`GET /launchpad/one-click-publication/api/item/<category>/<item_id>?year=X&week=Y&output=blog`**
- Returns single item details
- Includes production status for specified output channel
- Includes publication status
- Used when coming from dashboard

### New Endpoints

**`GET /launchpad/one-click-publication/api/pipeline/<post_id>?output=<channel>`**
- Returns pipeline stages/substages for (post_type, output_channel) combination
- Dynamically loads from `config/output_channel_stages.py`
- Falls back to `config/post_type_substages.py` if no channel-specific config

**`GET /launchpad/one-click-publication/api/output-channels/<post_type>`**
- Returns available output channels for a post type
- Uses `post_type_channel_config` table
- Used to populate output channel selector

---

## Summary

✅ **System Rename:** "One-Click Blog" → "One-Click Publication" (handles all output types)  
✅ **Output Channel Support:** New system for channel-specific stages (`config/output_channel_stages.py`)  
✅ **Weekly Content Types:** Add to `config/post_type_substages.py`  
✅ **Calendar Sync Fix:** Use new calendar system, remove deprecated table queries  
✅ **Role Clarification:** Dashboard = overview, One-Click Publication = single item deep dive  
✅ **UI Enhancement:** Add output channel selector, dynamically show channel-specific stages  
✅ **Entry Point:** Dashboard links to One-Click Publication for detailed work  
✅ **No Overlap:** Clear separation of concerns  

**Status:** Architecture supports this redesign. Implementation requires:
1. Adding weekly content types to config
2. Creating output channel stage system
3. Updating UI to support output channel selection
4. Renaming system throughout codebase
