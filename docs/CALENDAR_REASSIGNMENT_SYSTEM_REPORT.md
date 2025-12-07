# Calendar Reassignment System - Technical Report

## Executive Summary

This document describes the requirements, current implementation, and issues with the calendar item reassignment system. The goal is to allow users to move items (themes, recipes, profiles, words, phrases) from one week to another in a calendar scheduling interface.

**Status**: System is partially working but unreliable. Reassignments sometimes work, sometimes don't, and items appear in incorrect weeks.

---

## Business Requirements

### What We're Trying to Achieve

1. **Calendar Scheduling Interface**: A table showing 52 weeks with columns for:
   - Theme
   - Recipe
   - Product Profile
   - Surname Profile
   - Weekly Word
   - Weekly Phrase

2. **Reassignment Functionality**: 
   - User clicks an item in a week
   - Modal opens showing current week and allowing selection of target week
   - User selects target week and clicks "Reassign"
   - Item should move from source week to target week
   - Change should persist and be visible immediately

3. **Constraints**:
   - Each week must have exactly one item per category (no gaps)
   - Items can be reassigned to any week (current or future years)
   - The sequential list order should be maintained for cycling
   - Overrides should take precedence over the cycle formula

---

## Current Architecture

### Database Schema

#### `calendar_week_items` (Override Table)
Primary table for week-specific overrides. Takes precedence over cycle formula.

```sql
CREATE TABLE calendar_week_items (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,  -- 'theme', 'recipe', 'profile', 'weekly_word', 'weekly_phrase'
    item_id INTEGER NOT NULL,         -- ID of item in source table
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,     -- ISO week 1-52
    weekday INTEGER,                  -- NULL for week-level items
    scheduled_date DATE,
    is_selected BOOLEAN DEFAULT FALSE,
    priority VARCHAR(20) DEFAULT 'normal',
    position INTEGER DEFAULT 0,
    metadata JSONB,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE (year, week_number, item_type, item_id)
);
```

#### `calendar_themes` (Sequential List)
Contains themes with positions for cycling.

```sql
CREATE TABLE calendar_themes (
    id SERIAL PRIMARY KEY,
    theme_title VARCHAR(255),
    theme_description TEXT,
    week_number INTEGER,              -- Legacy field, may be NULL
    position INTEGER UNIQUE,          -- Sequential position (1, 2, 3, ...)
    seasonal_context TEXT,
    priority VARCHAR(20),
    tags TEXT[],
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### `calendar_recipes` (Sequential List)
Similar structure to themes.

```sql
CREATE TABLE calendar_recipes (
    id SERIAL PRIMARY KEY,
    recipe_title VARCHAR(255),
    recipe_description TEXT,
    week_number INTEGER,              -- Legacy field
    position INTEGER UNIQUE,          -- Sequential position
    ...
);
```

#### `calendar_category_cycles` (Cycle Configuration)
Stores cycle start week for each category.

```sql
CREATE TABLE calendar_category_cycles (
    category VARCHAR(50) PRIMARY KEY, -- 'theme', 'recipe', etc.
    cycle_start_week INTEGER DEFAULT 1
);
```

#### `calendar_profile_sequence` (Profile Sequential List)
For product/surname profiles.

```sql
CREATE TABLE calendar_profile_sequence (
    post_id INTEGER PRIMARY KEY,      -- References post.id
    profile_type VARCHAR(20),        -- 'product', 'category', 'surname'
    position INTEGER NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE (profile_type, position)
);
```

#### `calendar_ideas` (Words/Phrases Sequential List)
For weekly words and phrases.

```sql
CREATE TABLE calendar_ideas (
    id SERIAL PRIMARY KEY,
    idea_title VARCHAR(255),
    item_classification VARCHAR(50),  -- 'weekly_word' or 'weekly_phrase'
    position INTEGER,
    ...
    UNIQUE (item_classification, position)
);
```

### Resolution Priority

The system uses this priority order (in `utils/calendar_sequential_resolver.py`):

1. **Override Check**: Look for `calendar_week_items` entry for the specific week
2. **Cycle Formula**: If no override, calculate position using: `position = ((absolute_week - cycle_start_week) % item_count) + 1`
3. **Get Item**: Return item at that position from the sequential list

### Current Implementation Files

1. **`blueprints/planning_api_calendar_reassign.py`** (NEW - Simple approach)
   - Endpoint: `POST /planning/api/calendar/reassign`
   - Creates `calendar_week_items` override for target week
   - Removes override from source week
   - **Status**: Just created, may have bugs

2. **`blueprints/planning_api_calendar_reorder.py`** (OLD - Complex approach)
   - Endpoint: `POST /planning/api/calendar/reorder`
   - Tries to swap positions in sequential lists
   - Uses temporary positions to avoid unique constraint violations
   - **Status**: Partially working but unreliable

3. **`templates/planning/calendar/scheduling.html`**
   - Frontend JavaScript
   - Opens modal on item click
   - Calls reassign API
   - Reloads page after success

4. **`utils/calendar_sequential_resolver.py`**
   - Core logic for resolving which item appears in a week
   - Checks overrides first, then uses cycle formula

5. **`blueprints/planning_api_calendar_scheduling_cache.py`**
   - Generates scheduling data for all 52 weeks
   - Caches in `data/calendar_scheduling_cache.json`
   - Uses `resolve_item_for_week()` from sequential resolver

---

## Problems Identified

### Problem 1: Position Swapping Doesn't Work for Week-Specific Assignment

**Issue**: The cycle formula makes each position appear in multiple weeks (every N weeks where N = item_count). When we swap positions, the item appears in ALL weeks where that position cycles, not just the target week.

**Example**: 
- 11 themes, position 5 appears in weeks 5, 16, 27, 38, 49, 60...
- Moving item to position 5 makes it appear in ALL those weeks
- User wants it ONLY in week 49

**Attempted Fix**: Created override system, but implementation may be incomplete.

### Problem 2: Unique Constraint Violations

**Issue**: When swapping positions, we can't set two items to the same position simultaneously.

**Attempted Fix**: Used temporary position (99999) in three-step process:
1. Move item A to temp position
2. Move item B to item A's old position
3. Move item A to target position

**Status**: Works but creates gaps in sequential list.

### Problem 3: Cache Invalidation Issues

**Issue**: After reassignment, cache may not be invalidated properly, showing stale data.

**Current Fix**: `invalidate_scheduling_cache()` deletes cache file, but timing issues may occur.

### Problem 4: Item ID Mapping Confusion

**Issue**: Different categories use different ID systems:
- Themes: `calendar_themes.id`
- Recipes: `calendar_recipes.id`
- Profiles: `post.id` (stored in `calendar_profile_sequence.post_id`)
- Words/Phrases: `calendar_ideas.id`

**Current Fix**: `get_item_id_from_category()` function, but may have bugs.

### Problem 5: Override Removal Not Working

**Issue**: When reassigning, we need to remove the override from the source week, but this may not be happening correctly.

**Current Code**: `remove_week_override()` function exists but may not be called correctly.

### Problem 6: Frontend-Backend Mismatch

**Issue**: Frontend may be calling wrong endpoint or passing incorrect data.

**Current State**: Frontend calls `/planning/api/calendar/reassign` with:
```json
{
  "category": "theme",
  "item_id": 131,
  "source_week": {"year": 2025, "week": 51},
  "target_week": {"year": 2025, "week": 49}
}
```

---

## Current Code Flow

### Reassignment Flow (New System)

1. User clicks item in week 51
2. `openReassignModal()` called with item data
3. User selects week 49 in dropdown
4. User clicks "Reassign"
5. `submitReassign()` called
6. Frontend calls `POST /planning/api/calendar/reassign`
7. Backend:
   - Maps category to item_type
   - Gets actual item_id
   - Removes override from source week (if exists)
   - Creates override for target week
   - Invalidates cache
8. Frontend reloads page
9. New data should show item in week 49

### Resolution Flow (When Displaying Schedule)

1. `api_calendar_scheduling_all()` called
2. For each week (1-52):
   - For each category:
     - Call `resolve_item_for_week(category, year, week)`
     - `resolve_item_for_week()` checks:
       1. `get_calendar_week_item_override()` - looks in `calendar_week_items`
       2. If no override, calculates position using cycle formula
       3. Gets item at that position
     - Adds item to schedule
3. Returns all weeks with schedules
4. Frontend renders table

---

## Specific Issues to Fix

### Issue 1: Override Creation May Fail Silently

**Location**: `blueprints/planning_api_calendar_reassign.py`, `create_week_item()` call

**Problem**: If override creation fails, error may not be properly handled or reported.

**Evidence**: User reports reassignments "not working" - could be silent failures.

### Issue 2: Source Week Override Not Removed

**Location**: `remove_week_override()` function

**Problem**: Function may not be finding/removing the correct override, or may not be called when item wasn't originally an override.

**Evidence**: Items may appear in both source and target weeks.

### Issue 3: Cache Not Refreshing

**Location**: Cache invalidation and frontend cache-busting

**Problem**: Even after invalidating cache, frontend may be using cached data, or cache may be regenerated before override is committed.

**Evidence**: Changes not visible immediately after reassignment.

### Issue 4: Item ID Resolution

**Location**: `get_item_id_from_category()` function

**Problem**: May not correctly map item_id for all categories, especially profiles.

**Evidence**: Reassignments failing for certain categories.

### Issue 5: Frontend Week Detection

**Location**: `openReassignModal()` - how it determines current week

**Problem**: May not correctly identify which week the item is currently in, especially if item appears in multiple weeks due to cycling.

**Evidence**: Source week may be incorrect in API call.

---

## Recommended Solution Approach

### Option 1: Pure Override System (Recommended)

**Principle**: Use `calendar_week_items` overrides exclusively for reassignments. Don't modify sequential list positions.

**Flow**:
1. User reassigns item from week A to week B
2. Create override in `calendar_week_items` for week B
3. Remove override for week A (if exists)
4. Don't touch sequential list positions
5. Resolution always checks overrides first

**Pros**: Simple, clear, predictable
**Cons**: Requires maintaining override table, but that's already the design

### Option 2: Hybrid System (Current Attempt)

**Principle**: Use overrides for reassignments, but also maintain sequential list order.

**Flow**:
1. Create override for target week
2. Also swap positions in sequential list
3. Resolution checks overrides first

**Pros**: Maintains list order for future cycling
**Cons**: More complex, two operations that can get out of sync

---

## Database Queries for Debugging

```sql
-- Check overrides for a specific week
SELECT * FROM calendar_week_items 
WHERE year = 2025 AND week_number = 49 AND is_active = TRUE;

-- Check theme positions
SELECT id, theme_title, position FROM calendar_themes ORDER BY position;

-- Check what position appears in a week (manual calculation)
-- For themes: position = ((week - 1) % 11) + 1
SELECT 49 as week, ((49 - 1) % 11) + 1 as calculated_position;

-- Find all overrides for a specific item
SELECT * FROM calendar_week_items 
WHERE item_type = 'theme' AND item_id = 131 AND is_active = TRUE;
```

---

## Test Cases

1. **Basic Reassignment**: Move theme from week 51 to week 49
   - Expected: Theme appears in week 49, not in week 51
   - Actual: Sometimes works, sometimes doesn't

2. **Reassignment to Different Year**: Move item to week 5 of 2026
   - Expected: Item appears in 2026-W5
   - Actual: Untested

3. **Remove Override**: Reassign item that was previously overridden
   - Expected: Old override removed, new override created
   - Actual: May leave item in both weeks

4. **Multiple Reassignments**: Reassign same item multiple times
   - Expected: Item only appears in latest target week
   - Actual: May accumulate overrides

5. **Category Variations**: Test with themes, recipes, profiles, words, phrases
   - Expected: All work the same way
   - Actual: Some categories may fail

---

## Files to Review

1. `blueprints/planning_api_calendar_reassign.py` - New reassign endpoint
2. `utils/calendar_week_items.py` - Override creation/removal
3. `utils/calendar_sequential_resolver.py` - Resolution logic
4. `blueprints/planning_api_calendar_scheduling_cache.py` - Schedule generation
5. `templates/planning/calendar/scheduling.html` - Frontend JavaScript
6. `blueprints/planning_api_calendar_reorder.py` - Old reorder endpoint (may conflict)

---

## Key Questions for New Implementation

1. Should reassignments modify sequential list positions, or only create overrides?
2. How should we handle items that appear in multiple weeks due to cycling?
3. Should we allow removing overrides to return to cycle-based assignment?
4. How do we ensure cache invalidation happens at the right time?
5. How do we handle concurrent reassignments?
6. Should the UI show which items are overrides vs. cycle-based?

---

## Conclusion

The system has the right architecture (overrides + cycle formula), but the implementation has multiple failure points. The new `/planning/api/calendar/reassign` endpoint is a step in the right direction but needs thorough testing and debugging.

**Recommended Next Steps**:
1. Add comprehensive logging to track each step of reassignment
2. Add database transaction handling to ensure atomicity
3. Add validation to ensure overrides are created correctly
4. Test each category type separately
5. Add UI feedback to show when reassignment succeeds/fails
6. Consider adding a "Remove Override" option to return items to cycle-based assignment

