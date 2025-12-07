# Calendar Week Assignment System - Audit & Recommendations

**Date**: 2025-12-01  
**Purpose**: Audit current system for assigning themes, recipes, profiles, words, and phrases to weeks, and recommend a robust framework

---

## Executive Summary

The current calendar week assignment system has **fundamental architectural issues** that prevent reliable week-to-item associations. The system lacks:
1. **Guaranteed one-item-per-week-per-category** - No constraints ensure each week has exactly one item
2. **Sequential ordering enforcement** - Items can be assigned to any week without maintaining order
3. **Persistent week associations** - Items recalculate based on current week instead of maintaining fixed assignments

**Recommendation**: Implement a **Sequential Assignment Framework** with explicit week-to-item mappings that persist across years and can be reordered via drag-and-drop.

---

## Current System Analysis

### 1. Themes (`calendar_themes`)

**Storage**:
- Table: `calendar_themes`
- Key field: `week_number` (1-52) - **UNIQUE constraint** ✅
- Structure: 11 themes currently, not all 52 weeks covered

**Assignment**:
- Assigned via `calendar_week_items` with `item_type='theme'` and `is_selected=TRUE`
- Multiple themes can exist for same week_number, but only one can be `is_selected=TRUE`
- **Problem**: No guarantee that every week (1-52) has a theme assigned

**Current State**:
- ✅ Has UNIQUE constraint on `week_number` in source table
- ❌ Not all 52 weeks have themes
- ❌ Assignment to specific year/week is separate from source `week_number`

### 2. Recipes (`calendar_recipes`)

**Storage**:
- Table: `calendar_recipes`
- Key field: `week_number` (1-52) - **UNIQUE constraint** ✅
- Structure: 52 recipes (one per week) ✅

**Assignment**:
- Assigned via `calendar_week_items` with `item_type='recipe'`
- **Problem**: Previously calculated based on current week (FIXED in recent change)
- **Problem**: No guarantee that every week has a recipe assigned

**Current State**:
- ✅ Has UNIQUE constraint on `week_number` in source table
- ✅ All 52 weeks have recipe definitions
- ❌ Not all weeks have recipes assigned in `calendar_week_items`
- ❌ Assignment is year-specific, breaking the "perpetual" nature

### 3. Profiles (`post` table)

**Storage**:
- Table: `post` with `profile_type IN ('product', 'category')`
- **No sequential ordering table** ❌
- **No week_number field** ❌

**Assignment**:
- Assigned via `calendar_week_items` with `item_type='profile'`
- **Problem**: No source table with sequential ordering
- **Problem**: No way to know which profile "should" be in which week
- **Problem**: Multiple profiles can be assigned to same week, or weeks can have none

**Current State**:
- ❌ No sequential ordering mechanism
- ❌ No guarantee of one profile per week
- ❌ Profiles are assigned ad-hoc without structure

### 4. Weekly Words (`calendar_ideas`)

**Storage**:
- Table: `calendar_ideas` with `item_classification='weekly_word'`
- Key field: `week_number` (1-52) - **NO UNIQUE constraint** ❌
- Structure: 52 words currently

**Assignment**:
- Assigned via `calendar_week_items` with `item_type='weekly_word'`
- **Problem**: Multiple words can have same `week_number` in source table
- **Problem**: Assignment to year/week is separate from source `week_number`

**Current State**:
- ❌ No UNIQUE constraint on `week_number` in source table
- ✅ 52 words exist (one per week)
- ❌ Assignment is year-specific, breaking the "perpetual" nature

### 5. Weekly Phrases (`calendar_ideas`)

**Storage**:
- Table: `calendar_ideas` with `item_classification='weekly_phrase'`
- Key field: `week_number` (1-52) - **NO UNIQUE constraint** ❌
- Structure: 52 phrases currently

**Assignment**:
- Assigned via `calendar_week_items` with `item_type='weekly_phrase'`
- **Problem**: Multiple phrases can have same `week_number` in source table
- **Problem**: Assignment to year/week is separate from source `week_number`

**Current State**:
- ❌ No UNIQUE constraint on `week_number` in source table
- ✅ 52 phrases exist (one per week)
- ❌ Assignment is year-specific, breaking the "perpetual" nature

---

## Current Assignment Mechanism (`calendar_week_items`)

### Table Structure
```sql
CREATE TABLE calendar_week_items (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(50) NOT NULL,  -- 'theme', 'recipe', 'profile', 'weekly_word', 'weekly_phrase'
    item_id INTEGER NOT NULL,         -- References source table
    year INTEGER NOT NULL,            -- Year-specific assignment
    week_number INTEGER NOT NULL,     -- Week number (1-52)
    is_selected BOOLEAN DEFAULT FALSE,  -- For themes only
    is_active BOOLEAN DEFAULT TRUE,
    -- ... other fields
    UNIQUE(year, week_number, item_type, item_id)  -- Prevents duplicates
);
```

### Problems Identified

1. **No "One Per Week" Constraint**
   - Constraint allows multiple items of same type per week
   - Constraint allows zero items of same type per week
   - No guarantee that each week has exactly one item in each category

2. **Year-Specific Assignments**
   - Items are assigned to specific `(year, week_number)` combinations
   - Breaks the "perpetual" nature of themes, recipes, words, phrases
   - Requires manual assignment for each year

3. **Disconnect from Source Ordering**
   - Source tables have `week_number` (1-52) for sequential ordering
   - `calendar_week_items` has `year + week_number` for actual assignment
   - No automatic mapping between source order and assignment

4. **No Reordering Mechanism**
   - Source `week_number` can be changed, but assignments don't update
   - Drag-and-drop would need to update both source and assignment
   - No atomic operation to maintain consistency

---

## Recommended Framework: Sequential List with Cycling

### Core Principles

1. **Sequential List**: Each category has an ordered list of items (any number, not limited to 52)
2. **Cycling Behavior**: Items cycle through weeks sequentially - when the list ends, it wraps back to the start
3. **Flexible Insertion**: Items can be inserted at any position, pushing later items back one week
4. **Drag-and-Drop Reordering**: Items can be reordered, automatically adjusting all subsequent items
5. **Perpetual Schedule**: The cycle continues across years (week 53 = week 1 of next cycle)

### Key Insight

Instead of assigning items to specific weeks (1-52), we maintain:
- **Ordered list** of items with `position` field (1, 2, 3, ... N)
- **Cycle start point** indicating which week position 1 begins at
- **Automatic calculation**: For any week W, item = ((W - cycle_start) % item_count) + 1

This allows:
- ✅ Any number of items (52, 100, 200+)
- ✅ Automatic cycling (item N+1 appears in week 1 of next cycle)
- ✅ Easy insertion (add at position X, all items X+1 shift down)
- ✅ Simple reordering (swap positions, all affected items update)

### Proposed Architecture: Sequential List with Position Tracking

**Core Design: Position-Based Sequential Lists**

Each category maintains an ordered list where items have a `position` field. The system calculates which item appears in which week using modular arithmetic.

#### Database Schema

**For each category, add `position` field to source table:**

```sql
-- Enhanced calendar_themes
ALTER TABLE calendar_themes ADD COLUMN position INTEGER;
CREATE UNIQUE INDEX idx_themes_position ON calendar_themes(position) WHERE position IS NOT NULL;

-- Enhanced calendar_recipes
ALTER TABLE calendar_recipes ADD COLUMN position INTEGER;
CREATE UNIQUE INDEX idx_recipes_position ON calendar_recipes(position) WHERE position IS NOT NULL;

-- New table for profiles sequential ordering
CREATE TABLE calendar_profile_sequence (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    profile_type VARCHAR(20) NOT NULL CHECK (profile_type IN ('product', 'category')),
    UNIQUE(position, profile_type),  -- One product profile and one category profile per position
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Enhanced calendar_ideas for words/phrases
ALTER TABLE calendar_ideas ADD COLUMN position INTEGER;
CREATE UNIQUE INDEX idx_ideas_position_word ON calendar_ideas(position) 
    WHERE item_classification = 'weekly_word' AND position IS NOT NULL;
CREATE UNIQUE INDEX idx_ideas_position_phrase ON calendar_ideas(position) 
    WHERE item_classification = 'weekly_phrase' AND position IS NOT NULL;
```

**Cycle Configuration Table:**

```sql
CREATE TABLE calendar_category_cycles (
    category VARCHAR(50) PRIMARY KEY CHECK (category IN ('theme', 'recipe', 'profile_product', 'profile_category', 'weekly_word', 'weekly_phrase')),
    cycle_start_week INTEGER NOT NULL DEFAULT 1 CHECK (cycle_start_week >= 1 AND cycle_start_week <= 52),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Assignment Calculation Logic:**

```python
def get_item_for_week(category: str, year: int, week_number: int):
    """
    Calculate which item appears in a specific week.
    
    Formula: position = ((week_number - cycle_start_week) % item_count) + 1
    
    Example:
    - 60 items in list
    - cycle_start_week = 1
    - Week 1: position = ((1 - 1) % 60) + 1 = 1
    - Week 52: position = ((52 - 1) % 60) + 1 = 52
    - Week 53: position = ((53 - 1) % 60) + 1 = 53
    - Week 60: position = ((60 - 1) % 60) + 1 = 60
    - Week 61: position = ((61 - 1) % 60) + 1 = 1 (wraps around!)
    """
    # Get cycle configuration
    cycle_start = get_cycle_start_week(category)
    
    # Get item count for category
    item_count = get_item_count(category)
    
    if item_count == 0:
        return None
    
    # Calculate position using modular arithmetic
    # Handle year boundaries: week_number can be > 52
    # For year Y, week W: absolute_week = (Y - base_year) * 52 + W
    base_year = 2025  # Or current year
    absolute_week = (year - base_year) * 52 + week_number
    
    position = ((absolute_week - cycle_start) % item_count) + 1
    
    # Get item at this position
    return get_item_by_position(category, position)
```

**Benefits:**
- ✅ Supports any number of items (52, 100, 200+)
- ✅ Automatic cycling (wraps around when list ends)
- ✅ Simple insertion (add at position X, increment all positions >= X)
- ✅ Easy reordering (swap positions, update affected items)
- ✅ Perpetual schedule (works across years)
- ✅ Flexible (can adjust cycle_start_week to shift entire schedule)

---

## Recommended Implementation: Sequential List System

### Phase 1: Database Schema Updates

1. **Create Cycle Configuration Table**
   ```sql
   CREATE TABLE calendar_category_cycles (
       category VARCHAR(50) PRIMARY KEY CHECK (category IN ('theme', 'recipe', 'profile_product', 'profile_category', 'weekly_word', 'weekly_phrase')),
       cycle_start_week INTEGER NOT NULL DEFAULT 1 CHECK (cycle_start_week >= 1 AND cycle_start_week <= 52),
       updated_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Initialize with default cycle_start_week = 1 for all categories
   INSERT INTO calendar_category_cycles (category) VALUES 
       ('theme'), ('recipe'), ('profile_product'), ('profile_category'), ('weekly_word'), ('weekly_phrase');
   ```

2. **Themes** (`calendar_themes`)
   ```sql
   -- Add position field (sequential order in list)
   ALTER TABLE calendar_themes ADD COLUMN position INTEGER;
   -- Initialize: use existing week_number as position, or assign sequential 1, 2, 3...
   UPDATE calendar_themes SET position = week_number WHERE week_number IS NOT NULL;
   -- Or if week_number is not sequential: assign positions 1, 2, 3... based on id
   -- UPDATE calendar_themes SET position = ROW_NUMBER() OVER (ORDER BY id);
   CREATE UNIQUE INDEX idx_themes_position ON calendar_themes(position) WHERE position IS NOT NULL;
   ```

3. **Recipes** (`calendar_recipes`)
   ```sql
   -- Add position field
   ALTER TABLE calendar_recipes ADD COLUMN position INTEGER;
   -- Initialize: use existing week_number as position
   UPDATE calendar_recipes SET position = week_number;
   ALTER TABLE calendar_recipes ALTER COLUMN position SET NOT NULL;
   CREATE UNIQUE INDEX idx_recipes_position ON calendar_recipes(position);
   ```

4. **Profiles** (New table)
   ```sql
   CREATE TABLE calendar_profile_sequence (
       id SERIAL PRIMARY KEY,
       post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
       position INTEGER NOT NULL,
       profile_type VARCHAR(20) NOT NULL CHECK (profile_type IN ('product', 'category')),
       UNIQUE(position, profile_type),
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );
   
   -- Populate from existing profile posts
   -- Assign positions 1, 2, 3... based on existing calendar_week_items or post creation date
   ```

5. **Words/Phrases** (`calendar_ideas`)
   ```sql
   -- Add position field
   ALTER TABLE calendar_ideas ADD COLUMN position INTEGER;
   -- Initialize: use existing week_number as position
   UPDATE calendar_ideas SET position = week_number 
       WHERE item_classification IN ('weekly_word', 'weekly_phrase') AND week_number IS NOT NULL;
   CREATE UNIQUE INDEX idx_ideas_position_word ON calendar_ideas(position) 
       WHERE item_classification = 'weekly_word' AND position IS NOT NULL;
   CREATE UNIQUE INDEX idx_ideas_position_phrase ON calendar_ideas(position) 
       WHERE item_classification = 'weekly_phrase' AND position IS NOT NULL;
   ```

### Phase 2: Assignment Resolution Logic

**New function: `resolve_item_for_week(category, year, week_number)`**

```python
def resolve_item_for_week(category: str, year: int, week_number: int):
    """
    Resolve which item appears in a specific week using sequential list cycling.
    
    Priority:
    1. Check calendar_week_items for year-specific override
    2. Calculate position using cycle formula
    3. Return item at that position
    
    Formula: position = ((absolute_week - cycle_start_week) % item_count) + 1
    """
    # Check for year-specific override first
    override = get_calendar_week_item(category, year, week_number)
    if override:
        return override
    
    # Get cycle configuration
    cycle_start = get_cycle_start_week(category)
    
    # Get item count for category
    item_count = get_item_count(category)
    if item_count == 0:
        return None
    
    # Calculate absolute week number (handles year boundaries)
    base_year = 2025  # Or use a fixed reference year
    absolute_week = (year - base_year) * 52 + week_number
    
    # Calculate position using modular arithmetic
    position = ((absolute_week - cycle_start) % item_count) + 1
    
    # Get item at this position
    return get_item_by_position(category, position)

def get_item_count(category: str) -> int:
    """Get total number of items in category's sequential list."""
    if category == 'theme':
        return count_items('calendar_themes', 'position IS NOT NULL')
    elif category == 'recipe':
        return count_items('calendar_recipes', 'position IS NOT NULL')
    elif category in ('profile_product', 'profile_category'):
        profile_type = 'product' if category == 'profile_product' else 'category'
        return count_items('calendar_profile_sequence', f"profile_type = '{profile_type}'")
    elif category == 'weekly_word':
        return count_items('calendar_ideas', "item_classification = 'weekly_word' AND position IS NOT NULL")
    elif category == 'weekly_phrase':
        return count_items('calendar_ideas', "item_classification = 'weekly_phrase' AND position IS NOT NULL")
    return 0

def get_item_by_position(category: str, position: int):
    """Get item at specific position in category's list."""
    # Implementation depends on category
    # Returns item dict with all relevant fields
    pass
```

### Phase 3: Reordering API

**New endpoint: `POST /api/calendar/reorder`**

```python
@bp.route('/api/calendar/reorder', methods=['POST'])
def api_reorder_item():
    """
    Reorder items within a category's sequential list.
    
    Request:
    {
        "category": "theme|recipe|profile_product|profile_category|weekly_word|weekly_phrase",
        "item_id": 123,
        "new_position": 5,  # Move item to position 5
        "insert_mode": true  # If true, insert at position (pushes others down)
    }
    
    Behavior:
    - If insert_mode=true: Insert at new_position, increment all positions >= new_position
    - If insert_mode=false: Swap with item at new_position
    """
    category = request.json['category']
    item_id = request.json['item_id']
    new_position = request.json['new_position']
    insert_mode = request.json.get('insert_mode', False)
    
    with db_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # Get current position of item
            current_position = get_item_position(category, item_id)
            
            if insert_mode:
                # Insert mode: move item to new_position, push others down
                if new_position < current_position:
                    # Moving earlier: increment positions from new_position to current_position-1
                    increment_positions(category, new_position, current_position - 1, +1)
                    update_item_position(category, item_id, new_position)
                elif new_position > current_position:
                    # Moving later: decrement positions from current_position+1 to new_position
                    decrement_positions(category, current_position + 1, new_position, -1)
                    update_item_position(category, item_id, new_position)
            else:
                # Swap mode: swap positions with item at new_position
                swap_positions(category, item_id, current_position, new_position)
            
            conn.commit()
    
    return jsonify({'success': True})

def increment_positions(category: str, start_pos: int, end_pos: int, amount: int):
    """Increment positions in range [start_pos, end_pos] by amount."""
    # Update all items with position in range
    # SQL: UPDATE table SET position = position + amount 
    #      WHERE position >= start_pos AND position <= end_pos
    pass

def decrement_positions(category: str, start_pos: int, end_pos: int, amount: int):
    """Decrement positions in range [start_pos, end_pos] by amount."""
    # Similar to increment_positions but with negative amount
    pass

def swap_positions(category: str, item_id: int, pos1: int, pos2: int):
    """Swap positions of two items."""
    # Get item at pos2
    # Update item_id to pos2
    # Update other item to pos1
    pass
```

**Reordering Logic:**
- **Insert Mode** (default for drag-and-drop):
  - Moving item from position 5 to position 2:
    - Item at position 5 moves to position 2
    - Items at positions 2, 3, 4 all increment to 3, 4, 5
    - All items after position 5 remain unchanged
  
- **Swap Mode**:
  - Swap item at position 5 with item at position 2
  - Only two items change positions
  
- **Atomic Operations**: All position updates happen in a single transaction

### Phase 4: Initial Population

**Script to populate assignments:**

1. **Themes**: Use existing `week_number` as `assigned_week_number`
2. **Recipes**: Already have `week_number` (1-52), use as-is
3. **Profiles**: 
   - Create `calendar_profile_sequence` entries for existing profile posts
   - Distribute across 52 weeks (may need multiple profiles per week initially)
   - Or create separate sequences for product vs category profiles
4. **Words/Phrases**: Use existing `week_number` as `assigned_week_number`

### Phase 5: UI Updates

**Scheduling View (`/planning/posts/0/calendar/scheduling`):**

- Display all 52 weeks in a grid
- For each week, show:
  - Theme (from `assigned_week_number`)
  - Recipe (from `assigned_week_number`)
  - Profile (from `assigned_week_number`)
  - Word (from `assigned_week_number`)
  - Phrase (from `assigned_week_number`)
- Enable drag-and-drop to reorder items
- Show year-specific overrides (if any) with visual indicator

---

## Migration Strategy

### Step 1: Add `assigned_week_number` Columns
- Add columns to source tables
- Populate from existing `week_number` or `calendar_week_items`

### Step 2: Create Profile Sequence Table
- Create `calendar_profile_sequence` table
- Populate from existing profile posts (distribute across 52 weeks)

### Step 3: Update Assignment Resolution
- Update `generate_scheduling_data()` to use new resolution logic
- Test with existing data

### Step 4: Add Reordering API
- Implement reorder endpoint
- Add validation and atomic updates

### Step 5: Update UI
- Update scheduling view to show all items
- Add drag-and-drop functionality (future phase)

---

## Benefits of Sequential List Framework

1. **Flexible Item Count**: Supports any number of items (52, 100, 200+), not limited to 52
2. **Automatic Cycling**: When list ends, automatically wraps to start (week 53 = item 1 if 52 items)
3. **Easy Insertion**: Insert item at any position, automatically pushes later items back one week
4. **Simple Reordering**: Drag-and-drop updates positions, all affected items adjust automatically
5. **Perpetual Schedule**: Works across years - week 53, 54, etc. automatically calculated
6. **Year Override Support**: `calendar_week_items` can still provide year-specific overrides
7. **Data Integrity**: Position uniqueness ensures no gaps or duplicates
8. **Query Performance**: Direct position lookups are fast
9. **Maintainability**: Clear sequential ordering, easy to understand and debug
10. **Scalability**: Can add items without restructuring (just append to end of list)

---

## Example Scenarios

### Scenario 1: 60 Items, Cycling Behavior
**Setup**: Category has 60 items, `cycle_start_week = 1`

**Year 2025 (Weeks 1-52)**:
- Week 1: position = ((1 - 1) % 60) + 1 = **1** → Item #1
- Week 2: position = ((2 - 1) % 60) + 1 = **2** → Item #2
- ...
- Week 52: position = ((52 - 1) % 60) + 1 = **52** → Item #52

**Year 2026 (Weeks 1-8)**:
- Week 1 (2026): absolute_week = (2026-2025)*52 + 1 = 53
  - position = ((53 - 1) % 60) + 1 = **53** → Item #53
- Week 2 (2026): absolute_week = 54
  - position = ((54 - 1) % 60) + 1 = **54** → Item #54
- ...
- Week 8 (2026): absolute_week = 60
  - position = ((60 - 1) % 60) + 1 = **60** → Item #60
- Week 9 (2026): absolute_week = 61
  - position = ((61 - 1) % 60) + 1 = **1** → Item #1 (wraps around!)

**Visual Representation**:
```
Items: [1, 2, 3, ..., 52, 53, 54, ..., 60]
        ↓   ↓   ↓        ↓   ↓   ↓        ↓
Weeks:  1   2   3  ...  52  53  54  ...  60  61  62  ...
        ↑                                    ↑   ↑
     Start                              Wrap  Item 1, 2...
```

### Scenario 2: 40 Items (Fewer than 52)
**Setup**: Category has 40 items, `cycle_start_week = 1`

**Year 2025**:
- Week 1: position = ((1 - 1) % 40) + 1 = **1** → Item #1
- Week 40: position = ((40 - 1) % 40) + 1 = **40** → Item #40
- Week 41: position = ((41 - 1) % 40) + 1 = **1** → Item #1 (wraps!)
- Week 52: position = ((52 - 1) % 40) + 1 = **12** → Item #12

**Year 2026**:
- Week 1: absolute_week = 53, position = ((53 - 1) % 40) + 1 = **13** → Item #13
- Week 2: absolute_week = 54, position = ((54 - 1) % 40) + 1 = **14** → Item #14

### Scenario 2: Insert Item at Position 10
- Current list: [1, 2, 3, ..., 9, 10, 11, 12, ..., 52]
- Insert new item at position 10
- Result: [1, 2, 3, ..., 9, **NEW**, 10, 11, 12, ..., 52]
- All items from position 10 onward shift down by 1
- Week assignments automatically adjust

### Scenario 3: Drag Item from Position 20 to Position 5
- Current: Item A at position 20, Item B at position 5
- Move Item A to position 5 (insert mode)
- Result: Item A at position 5, Item B at position 6, all items 6-19 shift down
- Week assignments automatically recalculate

## Open Questions

1. **Profiles**: Should product profiles and category profiles be separate sequences or combined?
   - **Recommendation**: Separate sequences (allows different counts for each type)

2. **Year Overrides**: How should year-specific overrides be managed?
   - **Recommendation**: Use `calendar_week_items` for overrides, with UI indicator showing "override" status

3. **Cycle Start Week**: Should users be able to adjust `cycle_start_week` to shift entire schedule?
   - **Recommendation**: Yes, but with clear UI indication of what this does

4. **Drag-and-Drop**: Should reordering update immediately or require confirmation?
   - **Recommendation**: Immediate update with undo capability

5. **Empty Positions**: What happens if a position has no item (NULL position)?
   - **Recommendation**: Skip empty positions in calculation, or show placeholder in UI

---

## Next Steps

1. **Review and approve** this framework
2. **Create migration scripts** for Phase 1 (database schema)
3. **Implement resolution logic** (Phase 2)
4. **Build reordering API** (Phase 3)
5. **Populate initial assignments** (Phase 4)
6. **Update UI** (Phase 5)

---

*This audit document should be updated as the implementation progresses.*

