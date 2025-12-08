# Calendar Scheduling - JSON File Format Specification

This document describes the exact JSON structure used for calendar schedule files.

## File Location and Naming

All schedule JSON files are stored in a single directory:

```
data/calendar/schedule/theme/2025.json
data/calendar/schedule/recipe/2025.json
data/calendar/schedule/profile_product/2025.json
data/calendar/schedule/profile_surname/2025.json
data/calendar/schedule/weekly_word/2025.json
data/calendar/schedule/weekly_phrase/2025.json
data/calendar/schedule/weekly_insult/2025.json
```

Each category/year file is named (directory layout):

```
data/calendar/schedule/{category}/{year}.json
```

The system also supports a flat layout for backward compatibility:

```
data/calendar/schedule/{category}_{year}.json
```

## Categories

Supported categories:
- `theme`
- `recipe`
- `profile_product`
- `profile_surname`
- `weekly_word`
- `weekly_phrase`
- `weekly_insult`

---

## Standard JSON Structure

Each JSON file contains metadata and a `weeks` object mapping week numbers to items.

### Root Structure

```json
{
  "category": "theme",
  "year": 2025,
  "generated_at": "2025-01-01T12:34:56Z",
  "weeks": {
    "1": { "id": 5, "position": 1, "title": "Festive Music & Ceilidhs" },
    "2": { "id": 103, "position": 2, "title": "All Saints' / Samhain Continuation" },
    ...
  }
}
```

### Metadata Fields

- `category` (string, required): Category name (theme, recipe, profile_product, etc.)
- `year` (integer, required): ISO year
- `generated_at` (string, required): ISO 8601 timestamp of when the file was generated
- `weeks` (object, required): Mapping of week numbers (as strings) to item objects

### Week Object Structure

Each week entry in the `weeks` object contains:

- `id` (integer, required): Item ID (category-specific)
- `position` (integer, required): Position in the base cyclic list
- `title` (string, optional): Display title (not available for profiles)

### Category-Specific Examples

#### Theme – `data/calendar/schedule/theme_2025.json`

```json
{
  "category": "theme",
  "year": 2025,
  "generated_at": "2025-01-01T12:34:56Z",
  "weeks": {
    "1": { "id": 5, "position": 1, "title": "Festive Music & Ceilidhs" },
    "2": { "id": 103, "position": 2, "title": "All Saints' / Samhain Continuation" }
  }
}
```

- `id`: ID from `calendar_themes` table
- `title`: `theme_title` from database
- `position`: Position in theme list

#### Recipe – `data/calendar/schedule/recipe_2025.json`

```json
{
  "category": "recipe",
  "year": 2025,
  "generated_at": "2025-01-01T12:34:56Z",
  "weeks": {
    "1": { "id": 48, "position": 1, "title": "Hogmanay Sausage Rolls" },
    "2": { "id": 5, "position": 2, "title": "Rumbledethumps" }
  }
}
```

- `id`: ID from `calendar_recipes` table
- `title`: `recipe_title` from database
- `position`: Position in recipe list

#### Profile Product – `data/calendar/schedule/profile_product_2025.json`

```json
{
  "category": "profile_product",
  "year": 2025,
  "generated_at": "2025-01-01T12:34:56Z",
  "weeks": {
    "1": { "id": 55, "position": 22 },
    "2": { "id": 56, "position": 23 }
  }
}
```

- `id`: `post_id` from `calendar_profile_sequence` table
- `position`: Position in profile product list
- Note: No `title` field (profiles don't have titles in sequence table)

#### Profile Surname – `data/calendar/schedule/profile_surname_2025.json`

```json
{
  "category": "profile_surname",
  "year": 2025,
  "generated_at": "2025-01-01T12:34:56Z",
  "weeks": {
    "1": { "id": 88, "position": 61 },
    "2": { "id": 89, "position": 62 }
  }
}
```

- `id`: `post_id` from `calendar_profile_sequence` table
- `position`: Position in profile surname list
- Note: No `title` field

#### Weekly Word – `data/calendar/schedule/weekly_word/2025.json`

```json
{
  "category": "weekly_word",
  "year": 2025,
  "generated_at": "2025-01-01T12:34:56Z",
  "weeks": {
    "1": { "id": 501, "position": 11, "title": "Dreich" },
    "2": { "id": 502, "position": 12, "title": "Haver" }
  }
}
```

- `id`: ID from `calendar_ideas` table
- `title`: `idea_title` from database
- `position`: Position in weekly word list

#### Weekly Phrase – `data/calendar/schedule/weekly_phrase/2025.json`

```json
{
  "category": "weekly_phrase",
  "year": 2025,
  "generated_at": "2025-01-01T12:34:56Z",
  "weeks": {
    "1": { "id": 620, "position": 44, "title": "Lang may yer lum reek" },
    "2": { "id": 621, "position": 45, "title": "Haud yer wheesht" }
  }
}
```

- `id`: ID from `calendar_ideas` table
- `title`: `idea_title` from database
- `position`: Position in weekly phrase list

#### Weekly Insult – `data/calendar/schedule/weekly_insult/2025.json`

```json
{
  "category": "weekly_insult",
  "year": 2025,
  "generated_at": "2025-01-01T12:34:56Z",
  "weeks": {
    "1": { "id": 1339, "position": 49, "title": "Ye'd argue wi a puddle" },
    "2": { "id": 1340, "position": 50, "title": "Ye're as subtle as a brick through a windae" }
  }
}
```

- `id`: ID from `calendar_ideas` table (with `item_classification = 'weekly_insult'`)
- `title`: `idea_title` from database
- `position`: Position in weekly insult list

### Week Numbers

- Week numbers in the `weeks` object are strings ("1", "2", ..., "52")
- Must be integers from 1 to 52
- All 52 weeks should be present (unless the base list is empty)

## Validation Rules

### Required Fields
- Root object must have `category`, `year`, `generated_at`, and `weeks`
- Each week entry must have `id` and `position`
- `title` is optional (not available for profiles)

### Week Numbers
- Week keys in `weeks` object must be strings representing integers 1-52
- All 52 weeks should be present (unless base list is empty)
- No duplicate week numbers

### Data Types
- `category`: string
- `year`: integer
- `generated_at`: string (ISO 8601 format)
- `weeks`: object (mapping string week numbers to item objects)
- `id`: integer (category-specific ID)
- `position`: integer (positive)
- `title`: string (optional, non-empty when present)

### File Completeness
- Fully built years should contain entries for all weeks 1–52 per category
- Empty base lists result in empty `weeks` object `{}`

## Invalid Examples

### Missing Week
```json
{
  "category": "theme",
  "year": 2025,
  "generated_at": "...",
  "weeks": {
    "1": {...},
    "3": {...}  // Missing week 2
  }
}
```
**Error**: Week 2 is missing

### Duplicate Week
```json
{
  "category": "theme",
  "year": 2025,
  "generated_at": "...",
  "weeks": {
    "1": {...},
    "1": {...}  // Duplicate
  }
}
```
**Error**: Week 1 appears twice

### Missing Required Field
```json
{
  "category": "theme",
  "year": 2025,
  "generated_at": "...",
  "weeks": {
    "1": { "id": 7, "title": "Theme Name" }  // Missing "position"
  }
}
```
**Error**: `position` is required in week entry

### Wrong Data Type
```json
{
  "category": "theme",
  "year": "2025",  // Should be integer
  "generated_at": "...",
  "weeks": {...}
}
```
**Error**: `year` must be an integer

## Frontend Consumption

The frontend does **not** need any extra metadata beyond this structure. The API endpoint will:
1. Load multiple category files for the requested year range
2. Merge them into a unified structure
3. Return weeks with all categories combined

The frontend receives data in this merged format (see API documentation for the exact response structure).

## File Generation

These files are generated by:
- `utils/calendar_schedule_builder.py` - Builder module
- `scripts/build_calendar_schedules.py` - CLI script

Configuration for paths and categories is defined in:
- `config/calendar_settings.py` - Centralized configuration

See `docs/CALENDAR_SCHEDULING_BUILDER.md` for generation details.

## File Modification

**Important**: These files should generally **not** be edited manually. They are:
- Generated from base database lists (Layer 1)
- Regenerated when base lists change
- May be patched by override/reassignment logic (Phase 2)

If manual editing is needed (e.g., for testing), ensure:
- JSON is valid
- All 52 weeks are present
- Week numbers are sequential
- All required fields are present

## Version Control

These files can be:
- Committed to version control (for tracking changes)
- Or excluded via `.gitignore` (if they're regenerated frequently)

Recommendation: Include them in version control for:
- Audit trail
- Rollback capability
- Debugging historical states

---

## Related Documentation

- `CALENDAR_SCHEDULING_NEW_PARADIGM.md` - Overall architecture
- `CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md` - Component reference
- `CALENDAR_SCHEDULING_BUILDER.md` - How to generate these files

---

*Document created: 2025-01-XX*
*Status: Format specification - Implementation pending*

