# Calendar Schedule JSON Files

This directory contains the **JSON-backed calendar schedules** used by the planning system.

These files are the **source of truth for display** in the new JSON-centric scheduling paradigm.  
They are generated from database data (and later overrides) and are **not** edited by hand in normal operation.

---

## Directory Layout

Per-category, per-year files:

- `theme/YYYY.json`
- `recipe/YYYY.json`
- `profile_product/YYYY.json`
- `profile_surname/YYYY.json`
- `weekly_word/YYYY.json`
- `weekly_phrase/YYYY.json`

Per-year meta files:

- `meta/YYYY.json`

Example for 2025:

- `theme/2025.json`
- `recipe/2025.json`
- `profile_product/2025.json`
- `profile_surname/2025.json`
- `weekly_word/2025.json`
- `weekly_phrase/2025.json`
- `meta/2025.json`

---

## Category File Formats (Summary)

See `docs/CALENDAR_SCHEDULING_JSON_FORMAT.md` for the full formal specification.  
Below is a concise summary of the **on-disk structure** for each category.

### Theme – `theme/YYYY.json`

```json
[
  { "week": 1, "item_id": 14, "position": 14, "title": "Winter Traditions" }
]
```

- `week`: ISO week number (1–52)
- `item_id`: ID from `calendar_themes`
- `position`: Position in base theme list
- `title`: Theme title

### Recipe – `recipe/YYYY.json`

```json
[
  { "week": 1, "item_id": 302, "position": 92, "title": "Cullen Skink" }
]
```

- `week`: ISO week number (1–52)
- `item_id`: ID from `calendar_recipes`
- `position`: Position in base recipe list
- `title`: Recipe title

### Product Profiles – `profile_product/YYYY.json`

```json
[
  { "week": 1, "post_id": 55, "position": 22, "title": "Handmade Sporrans" }
]
```

- `week`: ISO week number (1–52)
- `post_id`: Product profile post ID
- `position`: Position in base product profile sequence
- `title`: Product profile title

### Surname Profiles – `profile_surname/YYYY.json`

```json
[
  { "week": 1, "post_id": 88, "position": 61, "surname": "Stewart" }
]
```

- `week`: ISO week number (1–52)
- `post_id`: Surname profile post ID
- `position`: Position in base surname profile sequence
- `surname`: Surname key used for display

### Weekly Word – `weekly_word/YYYY.json`

```json
[
  { "week": 1, "id": 501, "position": 11, "title": "Dreich", "description": "Bleak, grey weather" }
]
```

- `week`: ISO week number (1–52)
- `id`: Idea ID (`calendar_ideas`, type = 'word')
- `position`: Position in base weekly word list
- `title`: Word label (e.g. `Weekly Word: neep`)
- `description` (optional): Human-readable explanation

### Weekly Phrase – `weekly_phrase/YYYY.json`

```json
[
  { "week": 1, "id": 620, "position": 44, "title": "Lang may yer lum reek", "description": "May you live long" }
]
```

- `week`: ISO week number (1–52)
- `id`: Idea ID (`calendar_ideas`, type = 'phrase')
- `position`: Position in base weekly phrase list
- `title`: Phrase label (e.g. `Weekly Phrase: Nae bother.`)
- `description` (optional): Human-readable explanation

### Meta – `meta/YYYY.json`

```json
{
  "year": 2025,
  "categories": [
    "theme",
    "recipe",
    "profile_product",
    "profile_surname",
    "weekly_word",
    "weekly_phrase"
  ],
  "generated_at": "2025-01-14T12:00:00Z",
  "notes": "Generated from cache"
}
```

- `year`: Year for which schedules were generated
- `categories`: List of categories present
- `generated_at`: ISO8601 timestamp of generation
- `notes`: Free-form notes about provenance

---

## Generation and Maintenance

### Source of Data

The initial 2025 files are generated from:

- `data/calendar_scheduling_cache.json`

via the migration script:

- `scripts/migrate_calendar_cache_to_schedule_json.py`

This script:

- Reads the existing **cache** structure used by the old endpoint
- Extracts week-level assignments for:
  - themes (`theme_selection`)
  - recipes (`recipe`)
  - weekly words (`weekly_word`)
  - weekly phrases (`weekly_phrase`)
- Writes out per-category files under `data/schedule/...`
- Writes a `meta/YYYY.json` file per year

> Note: At present, **profile_product** and **profile_surname** arrays are empty because profile data is not present in the cache. They will be populated later from profile sources.

### Regeneration

- Rerun `python3 scripts/migrate_calendar_cache_to_schedule_json.py` whenever:
  - The contents of `data/calendar_scheduling_cache.json` change
  - You need to rebuild/refresh the JSON schedule for 2025 from the old cache
- Future phases will introduce a proper **builder** that reads directly from DB base lists instead of the legacy cache.

---

## Invariants and Expectations

- **Per-year completeness (target state)**:
  - Each category file should contain one entry per week (1–52) for that year.
  - Transitional or partial years may temporarily have fewer entries for some categories.
- **Week uniqueness**:
  - Within a given category/year file, `week` values must not be duplicated.
- **Category isolation**:
  - Each category is stored in its own file and has its own schema (as above).
- **Read-only at runtime**:
  - Frontend/API should treat these files as read-only.
  - Modifications happen via builders/migration scripts, not ad-hoc edits.

If a file is malformed (e.g. invalid JSON, duplicate weeks), the range-based API should treat that category as empty for the affected year and log diagnostics.

---

## Relationship to Documentation

For deeper detail and architectural context, see:

- `docs/CALENDAR_SCHEDULING_JSON_FORMAT.md` – Formal JSON schema and validation rules
- `docs/CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md` – Where these files fit in the 5-layer architecture
- `docs/CALENDAR_SCHEDULING_BUILDER.md` – Future builder flow (DB → JSON), replacing the one-off cache migration
- `docs/CALENDAR_SCHEDULING_NEW_PARADIGM.md` – High-level design of the JSON-centric scheduling system


