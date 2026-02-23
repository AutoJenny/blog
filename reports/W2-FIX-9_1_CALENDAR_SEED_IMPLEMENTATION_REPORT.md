# W2-FIX-9.1 — Calendar Seed Traceability & Week Integrity

**Date:** 2026-02-23

## Summary

Calendar is the canonical driver for automated blog posts: posts record `calendar_seed` in `extra_settings`, automation verifies seed and week match before advancing, theme uniqueness is enforced per week, and orphan auto-posts are prevented.

---

## 1) Modified File List

| File | Changes |
|------|---------|
| `utils/posts/calendar_seed.py` | **NEW** — `set_calendar_seed`, `get_calendar_seed`, `ensure_manual_seed`, `verify_calendar_seed_for_automation` |
| `blueprints/planning_api_posts.py` | `confirm_calendar_idea`: set_calendar_seed(theme); theme uniqueness guard (409 if >1 selected) |
| `blueprints/planning_api_calendar_schedule.py` | `api_select_theme_idea`: theme uniqueness guard (409 if >1 selected for week) |
| `blueprints/automation_core.py` | `execute_substage`: verify_calendar_seed_for_automation before advance; `create_post_from_item`: require year/week for theme/weekly; set_calendar_seed; `create_post`: ensure_manual_seed |
| `blueprints/recipes.py` | Recipe create-post: set_calendar_seed(recipe) |
| `blueprints/content_generation_api.py` | After create_post: ensure_manual_seed |

---

## 2) Drop-in Replacements

| Component | Replacement |
|-----------|-------------|
| Post creation (confirm_idea) | Calls `set_calendar_seed` with type=theme, year, week_number, item_id |
| Post creation (recipe) | Calls `set_calendar_seed` with type=recipe |
| Post creation (automation create_post_from_item) | Requires year/week for theme/weekly; sets calendar_seed |
| Post creation (generic create_post) | Calls `ensure_manual_seed` |
| Automation advance | `verify_calendar_seed_for_automation` before substage execution → 409 on mismatch |
| Theme selection | Rejects if >1 selected for week → 409 calendar_conflict |

---

## 3) Seed Schema Example

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

Manual post:

```json
{
  "type": "manual",
  "created_at": "2026-02-23T14:00:00.000000Z",
  "actor": "create_post"
}
```

---

## 4) curl Evidence

### A) confirm_calendar_idea sets calendar_seed

```bash
# 1) Select theme for week first
curl -s -X POST "http://127.0.0.1:5000/planning/api/calendar/select-theme" \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "week_number": 8, "theme_id": 42}'

# 2) Confirm idea (uses selected theme from step 1)
curl -s -X POST "http://127.0.0.1:5000/planning/api/calendar/confirm-idea" \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "week_number": 8, "topic": "Test topic"}'
```

Expected: `{"success": true, "post_id": <id>}`. Then:

```bash
# Verify seed
curl -s "http://127.0.0.1:5000/planning/api/posts/<post_id>" | jq '.extra_settings.calendar_seed'
```

Expected: `{"type": "theme", "year": 2026, "week_number": 8, "item_id": 42, ...}`

### B) create_post_from_item requires year/week for theme

```bash
curl -s -X POST "http://127.0.0.1:5000/launchpad/one-click-publication/api/create-post-from-item" \
  -H "Content-Type: application/json" \
  -d '{"item_id": 1, "category": "theme"}'
```

Expected: 400 with `calendar_seed_required: true` (year/week missing)

Actual (verified):
```json
{"calendar_seed_required":true,"error":"year and week are required for calendar-driven post creation. Provide year and week to link post to calendar.","success":false}
```

### C) Theme uniqueness — 409 on second selection

```bash
# After selecting theme A for week 8, try to select theme B for same week
curl -s -X POST "http://127.0.0.1:5000/planning/api/calendar/select-theme" \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "week_number": 8, "theme_id": 99}'
```

Expected (when week already has selected theme): 409 with `calendar_conflict`

### D) Automation advance with calendar_mismatch

When post has seed year=2025/week=1 and automation targets year=2026/week=8:

Expected: 409 with `calendar_mismatch`

---

## 5) Documentation Update Summary (W2-GOV-1)

| File | Change |
|------|--------|
| `docs/workflow/calendar_seed_model.md` | **NEW** — Schema, API, guards, integration points |
| `docs/CHANGELOG.md` | Added W2-FIX-9.1 entry |
| `reports/W2-FIX-9_1_CALENDAR_SEED_IMPLEMENTATION_REPORT.md` | **NEW** — This report |

---

## 6) Confidence Level

**High (8/10)**

- All creation paths instrumented with set_calendar_seed or ensure_manual_seed.
- Automation advance guarded; backfill for legacy posts.
- Theme uniqueness enforced at application layer (DB constraint deferred).
- Orphan prevention in create_post_from_item for theme/weekly types.
- Recipe and manual paths covered.
- DB migration for UNIQUE(year, week, selected) on `calendar_week_items` not added; logical enforcement in place.
