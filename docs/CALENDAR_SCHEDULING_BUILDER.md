# Calendar Scheduling - Builder Documentation

This document explains how to use the calendar schedule builder to generate and maintain JSON schedule files.

## Overview

The builder is responsible for creating the JSON schedule files (Layer 3) from the base database lists (Layer 1). It applies cyclic logic to generate 52-week plans for each category and year.

## Components

### Builder Module
**File**: `utils/calendar_schedule_builder.py`

Core logic for:
- Reading base database lists
- Applying cyclic scheduling logic
- Generating 52-week schedules
- Writing JSON files

### Management Script
**File**: `scripts/build_calendar_schedules.py` (or Flask CLI equivalent)

Command-line interface for:
- Building schedules for specific years
- Building schedules for specific categories
- Rebuilding multiple years
- Batch operations

## Usage

### Basic Commands

#### Build All Categories for a Year
```bash
python scripts/build_calendar_schedules.py --year 2025
```

This will:
1. Read all base lists from the database
2. Generate 52-week schedules for all 6 categories
3. Write 6 JSON files to `data/calendar/schedule/`:
   - `theme_2025.json`
   - `recipe_2025.json`
   - `profile_product_2025.json`
   - `profile_surname_2025.json`
   - `weekly_word_2025.json`
   - `weekly_phrase_2025.json`

#### Build One Category for a Year
```bash
python scripts/build_calendar_schedules.py --year 2025 --category theme
```

This will:
1. Read the `theme` base list from the database
2. Generate a 52-week schedule for `theme` in 2025
3. Write `theme_2025.json` to `data/calendar/schedule/`

#### Rebuild Multiple Years
```bash
python scripts/build_calendar_schedules.py --year 2025 --extra-years 2
```

This will:
1. Build all categories for years 2025, 2026, and 2027
2. Provide progress feedback
3. Handle errors gracefully (continue with other years if one fails)

### Command Options

- `--year` (required): Base ISO year to build (e.g., 2025)
- `--category` (optional): Single category to build (if omitted, builds all categories)
- `--extra-years` (optional, default 0): Number of additional years to build beyond base year
- `--base-dir` (optional): Override base directory for JSON files (useful for dev/test)

## When to Run the Builder

### Initial Setup
When first implementing the new system:
1. Build current year: `build-year --year 2025`
2. Build next year: `build-year --year 2026`
3. Optionally build 2-3 years ahead for buffer

### After Base List Changes
When items are added, removed, or reordered in base lists (Layer 1):

**Option A - Manual Rebuild**:
```bash
# After adding a new theme
python scripts/build_calendar_schedules.py --year 2025 --category theme

# After reordering recipes
python scripts/build_calendar_schedules.py --year 2025 --category recipe
```

**Option B - Automatic Trigger** (Future):
The list management API (`planning_api_calendar_cyclic.py`) could automatically trigger rebuilds:
- After `POST /planning/api/calendar/list/add`
- After `POST /planning/api/calendar/list/delete`
- After `POST /planning/api/calendar/list/reorder`

### Scheduled Regeneration
Set up a cron job or scheduled task to:
- Rebuild current year weekly (to catch any missed changes)
- Pre-generate next year's schedules in December
- Rebuild all years quarterly (to ensure consistency)

**Example Cron**:
```bash
# Rebuild current year every Sunday at 2 AM
0 2 * * 0 cd /path/to/blog && python scripts/build_calendar_schedules.py --year $(date +%Y)

# Pre-generate next year in December
0 3 1 12 * cd /path/to/blog && python scripts/build_calendar_schedules.py --year $(date -d "+1 year" +%Y)
```

## How It Works

### Step 1: Read Base List
The builder reads the base cyclic list from the database:
- For `theme`: `SELECT * FROM calendar_themes ORDER BY position`
- For `recipe`: `SELECT * FROM calendar_recipes ORDER BY position`
- For `profile_product`: `SELECT * FROM calendar_profile_sequence WHERE type = 'product' ORDER BY position`
- For `profile_surname`: `SELECT * FROM calendar_profile_sequence WHERE type = 'surname' ORDER BY position`
- For `weekly_word`: `SELECT * FROM calendar_ideas WHERE type = 'word' ORDER BY position`
- For `weekly_phrase`: `SELECT * FROM calendar_ideas WHERE type = 'phrase' ORDER BY position`

### Step 2: Determine Cycle Start
The builder determines where the cycle should start for the given year:
- Reads `cycle_start_week` from `calendar_category_cycles` table
- Or uses a default (e.g., week 1 of the year)
- This determines which item appears in week 1

### Step 3: Apply Cyclic Logic
For each of the 52 weeks:
1. Calculate which position in the base list should appear
2. Account for cycle start week
3. Handle wrapping (if position exceeds list length, wrap around)
4. Select the item at that position

**Example**:
- Base list has 20 items (positions 1-20)
- Cycle starts at position 7 for year 2025
- Week 1 → item at position 7
- Week 2 → item at position 8
- ...
- Week 14 → item at position 20
- Week 15 → item at position 1 (wrapped)
- Week 16 → item at position 2
- ...

### Step 4: Generate JSON Structure
For each week, create the JSON structure with metadata:
```json
{
  "category": "theme",
  "year": 2025,
  "generated_at": "2025-01-01T12:34:56Z",
  "weeks": {
    "1": {
      "id": 5,
      "position": 1,
      "title": "Festive Music & Ceilidhs"
    },
    "2": {
      "id": 103,
      "position": 2,
      "title": "All Saints' / Samhain Continuation"
    },
    ...
  }
}
```

The `weeks` object maps week numbers (as strings) to item objects containing `id`, `position`, and `title`.

### Step 5: Write JSON File
Write the complete structure to:
```
data/calendar/schedule/{category}_{year}.json
```

Example: `data/calendar/schedule/theme_2025.json`

## Error Handling

### Missing Base List
If a category has no items in the database:
- Builder logs a warning
- Generates an empty JSON file (empty array `[]`)
- The display API will handle empty files gracefully

### Invalid Cycle Configuration
If `cycle_start_week` is missing or invalid:
- Use a sensible default (e.g., week 1)
- Log a warning
- Continue with the build

### File Write Errors
If the JSON file cannot be written:
- Check directory permissions
- Ensure `data/calendar/schedule/` exists (builder creates directory automatically)
- Log the error and fail gracefully

## Troubleshooting

### Problem: Generated JSON is missing weeks
**Solution**: Check that the base list has items. Empty lists will cause issues.

### Problem: Schedule doesn't match expected pattern
**Solution**: 
1. Verify `cycle_start_week` in `calendar_category_cycles` table
2. Check base list order (positions should be sequential and dense 1..N)
3. Rebuild the affected category/year

### Problem: Builder is slow
**Solution**: 
- This is expected - builder hits the database
- It's only run occasionally, not on page load
- Consider caching base lists if rebuilding frequently

### Problem: JSON files are out of sync with database
**Solution**: 
- Rebuild affected categories/years
- Set up automatic rebuild triggers (future)
- Add validation to detect stale files (future)

## Integration with List Management

When base lists are modified via the API:

### Current Behavior (Phase 1)
- List changes are saved to database
- JSON files are **not** automatically updated
- Manual rebuild required

### Future Behavior (Phase 2)
- List changes trigger automatic rebuild
- Or mark JSON files as "stale"
- Background job rebuilds stale files
- Or queue rebuild for next page load (with fallback to old JSON)

## Override Handling (Future Phase)

When override/reassignment system is implemented:

### Option A: Apply Overrides During Build
- Builder reads override rules
- Applies them when generating schedules
- Overrides are "baked into" the JSON files

### Option B: Apply Overrides at Read Time
- JSON files contain base cyclic schedule
- API endpoint applies overrides when reading
- Overrides stored separately (DB or separate JSON)

**Recommendation**: Start with Option B for flexibility, move to Option A later for performance.

## Best Practices

1. **Pre-generate schedules** for current year + next 2 years
2. **Rebuild after any list changes** (manual or automatic)
3. **Validate JSON files** after generation (check for 52 weeks, valid structure)
4. **Version control JSON files** for audit trail
5. **Monitor file modification dates** to detect stale files
6. **Test builder** with small lists before running on production data

## Related Documentation

- `CALENDAR_SCHEDULING_NEW_PARADIGM.md` - Overall architecture
- `CALENDAR_SCHEDULING_JSON_FORMAT.md` - JSON file structure
- `CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md` - Component reference

---

## Implementation Details

### Builder Module (`utils/calendar_schedule_builder.py`)

The builder module provides:
- `build_category_year(category, year)` - Builds in-memory schedule structure
- `write_category_year_json(category, year)` - Builds and writes JSON file
- `build_year_all_categories(year)` - Builds all categories for a year
- `build_multiple_years(years)` - Builds multiple years

### Database Tables Used

- `calendar_themes` - Theme items with `id`, `theme_title`, `position`
- `calendar_recipes` - Recipe items with `id`, `recipe_title`, `position`
- `calendar_profile_sequence` - Profile items with `post_id`, `profile_type`, `position`
- `calendar_ideas` - Word/phrase items with `id`, `idea_title`, `item_classification`, `position`
- `calendar_category_cycles` - Cycle configuration with `category`, `cycle_start_week`

### Cyclic Algorithm

For each week `w` (1-52):
```
pos = ((w - cycle_start_week) mod N) + 1
```

Where:
- `w` = ISO week number (1-52)
- `cycle_start_week` = from `calendar_category_cycles` table (defaults to 1)
- `N` = number of items in base list
- `pos` = position in base list (1-based)

The modulo operation handles wrapping correctly (e.g., if list has 20 items and we're at week 25, we wrap back to position 5).

---

*Document created: 2025-01-XX*
*Status: Builder documentation - Implementation complete*

