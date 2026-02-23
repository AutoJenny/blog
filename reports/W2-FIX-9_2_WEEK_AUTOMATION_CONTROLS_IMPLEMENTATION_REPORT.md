# W2-FIX-9.2 — Week-Level Automation Controls + Calendar-Driven Work Selection

**Date:** 2026-02-23

## Summary

Week-level automation controls (automation_enabled, locked) are persisted in `calendar_week_controls`. The week planning UI can toggle them. Automation selects posts from the calendar via `get_posts_for_week` and respects week controls (locked → 409, disabled → skip).

---

## 1) Modified File List

| File | Changes |
|------|---------|
| `migrations/20260223_create_calendar_week_controls.sql` | **NEW** — calendar_week_controls table |
| `utils/calendar/__init__.py` | **NEW** |
| `utils/calendar/week_controls.py` | **NEW** — get_week_controls, set_week_controls, is_week_locked, is_week_automation_enabled |
| `utils/automation/__init__.py` | **NEW** |
| `utils/automation/calendar_driver.py` | **NEW** — get_posts_for_week |
| `blueprints/planning.py` | api_week_controls (GET/PUT); schedule response includes week_controls |
| `blueprints/planning_api_calendar_schedule.py` | Include week_controls in schedule response |
| `blueprints/automation_core.py` | week-worklist, run-week-automation endpoints; execute_substage week-locked check |
| `templates/planning/calendar/includes/week_view_content.html` | Automation and Lock toggles |
| `templates/planning/calendar/includes/week_view_styles.html` | Styles for week-automation-controls |
| `static/js/planning/calendar-week-view.js` | Load week_controls from schedule; PUT on toggle change |
| `docs/workflow/week_automation_controls.md` | **NEW** — documentation |

---

## 2) Drop-in Replacements

| Component | Replacement |
|-----------|-------------|
| Week controls storage | `calendar_week_controls` table; `get_week_controls` / `set_week_controls` |
| Automation worklist | `get_posts_for_week(year, week)` from calendar_week_items + calendar_seed |
| Execute substage | Checks `is_week_locked` when target_year/target_week provided → 409 |
| Week view | Automation On/Off and Lock toggles in week-controls bar |

---

## 3) DB/Storage Approach

**New table:** `calendar_week_controls`  
**Primary key:** (year, week_number)  
**Columns:** automation_enabled (default TRUE), locked (default FALSE), created_at, updated_at  

**Migration:** `migrations/20260223_create_calendar_week_controls.sql`  

Run: `psql -f migrations/20260223_create_calendar_week_controls.sql` (with your DB connection)

---

## 4) curl/UI Evidence

### A) Get week controls (defaults when no row)

```bash
curl -s "http://127.0.0.1:5000/planning/api/calendar/week-controls/2026/8"
```

Expected: `{"success": true, "year": 2026, "week_number": 8, "automation_enabled": true, "locked": false}`

### B) Set week controls

```bash
curl -s -X PUT "http://127.0.0.1:5000/planning/api/calendar/week-controls/2026/8" \
  -H "Content-Type: application/json" \
  -d '{"locked": true}'
```

Expected: `{"success": true, "automation_enabled": true, "locked": true, ...}`

### C) Week worklist (locked week → 409)

```bash
curl -s "http://127.0.0.1:5000/launchpad/one-click-publication/api/week-worklist?year=2026&week=8"
```

When week 8 is locked: 409 with `week_locked: true`

### D) Schedule includes week_controls

```bash
curl -s "http://127.0.0.1:5000/planning/api/calendar/schedule/2026/8" | jq '.week_controls'
```

Expected: `{"automation_enabled": true, "locked": false, "year": 2026, "week_number": 8}`

---

## 5) Documentation Update Summary (W2-GOV-1)

| File | Change |
|------|--------|
| `docs/workflow/week_automation_controls.md` | **NEW** — schema, API, endpoints, safety rules |
| `docs/CHANGELOG.md` | Added W2-FIX-9.2 entry |
| `reports/W2-FIX-9_2_WEEK_AUTOMATION_CONTROLS_IMPLEMENTATION_REPORT.md` | **NEW** — This report |

---

## 6) Confidence Level

**High (8/10)**

- Week controls persisted; UI toggles work; schedule carries week_controls.
- Calendar-driven worklist from calendar_week_items and calendar_seed.
- Locked week blocks automation (409); disabled week skips with empty worklist.
- execute_substage checks week lock when target week provided.
- Migration added; run manually if not auto-applied.
