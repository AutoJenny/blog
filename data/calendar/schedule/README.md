# Calendar Schedule JSON Files

This directory contains the **JSON-backed calendar schedules** used by the planning system.

These files are the **source of truth for display** in the new JSON-centric scheduling paradigm.  
They are generated from database data (and later overrides) and are **not** edited by hand in normal operation.

---

## Directory Layout

Per-category, per-year files in a single flat directory:

- `theme_YYYY.json`
- `recipe_YYYY.json`
- `profile_product_YYYY.json`
- `profile_surname_YYYY.json`
- `weekly_word_YYYY.json`
- `weekly_phrase_YYYY.json`

Example for 2025:

- `theme_2025.json`
- `recipe_2025.json`
- `profile_product_2025.json`
- `profile_surname_2025.json`
- `weekly_word_2025.json`
- `weekly_phrase_2025.json`

---

## File Format

Each JSON file contains metadata and a `weeks` object mapping week numbers to items:

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

See `docs/CALENDAR_SCHEDULING_JSON_FORMAT.md` for the full formal specification.

---

## Generation and Maintenance

### Builder Script

Files are generated using:

```bash
python scripts/build_calendar_schedules.py --year 2025
```

This script:
- Reads base lists from database tables (`calendar_themes`, `calendar_recipes`, etc.)
- Applies cyclic logic using `cycle_start_week` from `calendar_category_cycles`
- Generates 52-week schedules per category/year
- Writes JSON files to this directory

### Regeneration

Rebuild files whenever:
- Base lists change (items added, removed, or reordered)
- Cycle start weeks are modified
- New years need to be generated

See `docs/CALENDAR_SCHEDULING_BUILDER.md` for detailed usage.

---

## Invariants and Expectations

- **Per-year completeness**:
  - Each category file should contain entries for all 52 weeks (unless base list is empty)
  - Week keys in `weeks` object are strings "1" through "52"
- **Week uniqueness**:
  - Within a given category/year file, week numbers must not be duplicated
- **Category isolation**:
  - Each category is stored in its own file
- **Read-only at runtime**:
  - Frontend/API should treat these files as read-only
  - Modifications happen via builder script, not ad-hoc edits

If a file is malformed (e.g. invalid JSON, duplicate weeks), the range-based API treats that category as empty for the affected year and logs diagnostics.

---

## Relationship to Documentation

For deeper detail and architectural context, see:

- `docs/CALENDAR_SCHEDULING_JSON_FORMAT.md` – Formal JSON schema and validation rules
- `docs/CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md` – Where these files fit in the 5-layer architecture
- `docs/CALENDAR_SCHEDULING_BUILDER.md` – Builder usage and maintenance
- `docs/CALENDAR_SCHEDULING_NEW_PARADIGM.md` – High-level design of the JSON-centric scheduling system

