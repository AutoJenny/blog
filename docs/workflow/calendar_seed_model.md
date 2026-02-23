# Calendar Seed Model

**Date:** 2026-02-23  
**Status:** Implemented (W2-FIX-9.1)  
**Source:** `utils/posts/calendar_seed.py`

---

## Overview

Calendar Seed provides traceability between posts and the calendar-driven context that created them. It answers: *"Where did this post come from in the calendar?"* and supports:

- **Orphan prevention** — automation cannot auto-drive posts without a valid calendar linkage
- **Week integrity** — automation cannot advance a post for a week that does not match its seed
- **Theme uniqueness** — at most one selected theme per (year, week)
- **Manual posts** — posts created outside calendar flows explicitly record `type: "manual"`

---

## Seed Schema

Stored in `post.extra_settings.calendar_seed` (JSONB):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | `"theme"`, `"recipe"`, `"weekly_word"`, `"weekly_phrase"`, `"weekly_insult"`, or `"manual"` |
| `year` | int | for calendar types | ISO year |
| `week_number` | int | for calendar types | ISO week number (1–53) |
| `item_id` | int | for calendar types | Source item ID (theme, recipe, weekly content) |
| `category` | string | optional | Human-readable category (e.g. `"theme"`, `"recipe"`) |
| `created_at` | string | auto | ISO timestamp |
| `actor` | string | auto | Who set it: `confirm_idea`, `recipe_create`, `create_post_from_item`, `create_post`, `content_generation` |

### Example (theme-based post)

```json
{
  "type": "theme",
  "year": 2026,
  "week_number": 8,
  "item_id": 42,
  "category": "theme",
  "created_at": "2026-02-23T14:00:00.000000Z",
  "actor": "confirm_idea"
}
```

### Example (manual post)

```json
{
  "type": "manual",
  "created_at": "2026-02-23T14:00:00.000000Z",
  "actor": "create_post"
}
```

---

## API

### `set_calendar_seed(post_id, seed_data, actor, cursor=None)`

Sets or overwrites `post.extra_settings.calendar_seed`. Merges into existing `extra_settings`.

- **cursor:** Optional. When provided, participates in caller's transaction; otherwise uses own connection and commits.

### `get_calendar_seed(post_id)`

Returns the `calendar_seed` dict or `None` if missing.

### `ensure_manual_seed(post_id, actor)`

Sets `calendar_seed.type = "manual"` for posts created without calendar context.

### `verify_calendar_seed_for_automation(post_id, target_year, target_week, backfill_missing=True)`

Before automation advances a post:

1. **Seed exists:** If missing and `backfill_missing=True` → sets `manual` seed, returns ok.
2. **Seed exists:** If missing and `backfill_missing=False` → returns (False, "calendar_seed_required").
3. **Week match:** If `target_year`/`target_week` provided and seed has year/week → must match; else returns (False, "calendar_mismatch").
4. **Manual seed:** `type="manual"` always passes (no week check).

Returns `(ok: bool, reason: str | None)`.

---

## Integration Points

| Creation Path | Seed Type | Actor |
|---------------|-----------|-------|
| `confirm_calendar_idea` | theme | confirm_idea |
| Recipe create-post | recipe | recipe_create |
| Automation `create_post_from_item` | theme, recipe, weekly_* | create_post_from_item |
| `create_post` (generic) | manual | create_post |
| `content_generation_api` create | manual | content_generation |

---

## Guards

### A) Automation advance guard (Part B)

In `execute_substage` (before routing to substage handlers):

- Calls `verify_calendar_seed_for_automation(post_id, target_year, target_week)`.
- If not ok → **409** with `calendar_mismatch` or `calendar_seed_required`.

### B) Orphan prevention (Part D)

In `create_post_from_item` (theme, weekly_word, weekly_phrase, weekly_insult):

- Requires `year` and `week` in request.
- If missing → **400** with `calendar_seed_required: true`.

### C) Theme uniqueness (Part C)

In `api_select_theme_idea` and `confirm_calendar_idea`:

- Count selected themes for (year, week).
- If > 1 → **409** with `calendar_conflict`.

---

## Rules

- **All posts have a seed** — creation paths either set calendar-specific seed or `manual`.
- **Backfill** — `verify_calendar_seed_for_automation` with `backfill_missing=True` ensures legacy posts without seed get `manual` and are not blocked.
- **Recipe** — uses `recipe_week_number` (perpetual week) when year/week not provided.

---

## Related Documentation

- `docs/ARCHITECTURE_V2_OVERVIEW.md` — Calendar-driven model summary
- `docs/workflow/workflow_stage_model.md` — workflow progression
- `docs/workflow/output_readiness_model.md` — output channel validation
- `reports/W2-FIX-9_1_CALENDAR_SEED_IMPLEMENTATION_REPORT.md` — implementation report
