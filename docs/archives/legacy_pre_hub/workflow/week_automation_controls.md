# Week-Level Automation Controls (W2-FIX-9.2)

**Date:** 2026-02-23  
**Status:** Implemented  
**Source:** `utils/calendar/week_controls.py`, `utils/automation/calendar_driver.py`

---

## Overview

Week-level automation controls allow per-week toggling of automation and locking. Automation "what to run next" respects these controls and selects posts from the calendar (calendar-driven work selection).

---

## Storage

**Table:** `calendar_week_controls` (migration: `migrations/20260223_create_calendar_week_controls.sql`)

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| year | INT | — | ISO year (PK) |
| week_number | INT | — | ISO week 1–53 (PK) |
| automation_enabled | BOOLEAN | TRUE | If false, automation skips this week silently |
| locked | BOOLEAN | FALSE | If true, automation must not modify posts (409 week_locked) |
| created_at, updated_at | TIMESTAMPTZ | NOW | Timestamps |

---

## API

### `get_week_controls(year, week)` — `utils.calendar.week_controls`

Returns `{ automation_enabled, locked, year, week_number }`. Defaults when no row: `automation_enabled=True`, `locked=False`.

### `set_week_controls(year, week, automation_enabled=None, locked=None)` — `utils.calendar.week_controls`

Upserts controls. Pass `None` to leave a field unchanged.

### `get_posts_for_week(year, week, only_automation_enabled=True)` — `utils.automation.calendar_driver`

Returns posts seeded to the week, ordered by workflow stage. Sources: `calendar_week_items` (recipe, profile) and `post.extra_settings.calendar_seed` with matching year/week. Filters by `post.extra_settings.automation.enabled` when `only_automation_enabled=True`.

---

## HTTP Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/planning/api/calendar/week-controls/<year>/<week>` | Get week controls |
| PUT | `/planning/api/calendar/week-controls/<year>/<week>` | Set automation_enabled and/or locked |
| GET | `/launchpad/one-click-publication/api/week-worklist?year=&week=` | Get worklist for week (409 if locked) |
| POST | `/launchpad/one-click-publication/api/run-week-automation` | Run automation for week (returns worklist; 409 if locked) |

---

## Safety Rules (Part D)

- **Week locked:** `execute_substage` with `target_year`/`target_week` → **409** `week_locked`
- **Week automation disabled:** `week-worklist` and `run-week-automation` return empty `posts` with `skipped: true`
- **Post calendar_seed missing:** Blocked by W2-FIX-9.1 `verify_calendar_seed_for_automation` (409 `calendar_mismatch`)

---

## UI

Week view (`templates/planning/calendar/includes/week_view_content.html`) includes:

- **Automation** toggle — `automation_enabled`
- **Lock** toggle — `locked`

Schedule API response includes `week_controls`; toggles sync on load and PUT on change.

---

## Related Documentation

- `docs/ARCHITECTURE_V2_OVERVIEW.md` — Automation control layers
- `docs/workflow/calendar_seed_model.md` — calendar_seed traceability (W2-FIX-9.1)
