# CULTURE v1.1 — Implementation and Verification

## Migration(s) summary

1. **`migrations/20260204_create_culture_library.sql`**
   - Creates table `culture_library` with: `id`, `category`, `title`, `body_text`, `source_note`, `active`, `created_at`.
   - Indexes: `idx_culture_library_active`, `idx_culture_library_category`.
   - Used for Mon/Thu CULTURE (culture_fact) posts; 90-day repeat avoidance via `posting_queue.culture_library_id`.

2. **`migrations/20260204_add_culture_library_id_to_posting_queue.sql`**
   - Adds nullable FK `posting_queue.culture_library_id` → `culture_library(id)` ON DELETE SET NULL.
   - Index: `idx_posting_queue_culture_library_id` (partial, WHERE culture_library_id IS NOT NULL).

**Run order:**
```bash
psql -d your_database -f migrations/20260204_create_culture_library.sql
psql -d your_database -f migrations/20260204_add_culture_library_id_to_posting_queue.sql
```

---

## Tuesday language rotation (3-week proof)

**Formula:** `language_type = ['weekly_word','weekly_phrase','weekly_insult'][(week_number - 1) % 3]`

| ISO week | (week_number - 1) % 3 | Type         |
|----------|------------------------|--------------|
| 1        | 0                      | weekly_word  |
| 2        | 1                      | weekly_phrase|
| 3        | 2                      | weekly_insult|
| 4        | 0                      | weekly_word  |
| …        | …                      | …            |

**Proof:** Call schedule API for three consecutive weeks (e.g. 2026-W1, 2026-W2, 2026-W3). The single Tuesday language slot must show:
- W1: type `weekly_word`
- W2: type `weekly_phrase`
- W3: type `weekly_insult`

**Code reference:** `blueprints/planning_api_calendar_schedule.py` — `language_type = language_types[(week_number - 1) % 3]`; `scripts/automated_weekly_content_creator.py` — `content_type = LANGUAGE_TYPES[(week_number - 1) % 3]`.

---

## Mon/Thu culture (2-week proof)

- **Monday (ISO weekday 1)** and **Thursday (ISO weekday 4)** only.
- One CULTURE (culture_fact) post per Mon and per Thu from `culture_library`; 90-day exclusion on planned schedule (`scheduled_date >= target_date - 90 days`).
- **Proof:** After seeding `culture_library` and running `scripts/automated_culture_creator.py --weeks-ahead 2 --dry-run` (then without `--dry-run`), call schedule API for a week that includes Mon and Thu. Role-based schedule must show two CULTURE entries for that week (one Mon, one Thu), with `content_type` effectively culture_fact and `scheduled_time` 15:00.

---

## Schedule API excerpt (Mon / Tue / Thu / Fri / Sun)

Expected pattern for one week:

- **Mon:** CULTURE (culture_fact from `culture_library`) — from role-based query, `scheduled_time` 15:00.
- **Tue:** CULTURE (language) — single slot from resolver or posting_queue; type rotates word → phrase → insult.
- **Thu:** CULTURE (culture_fact from `culture_library`) — from role-based query, 15:00.
- **Fri:** AUTHORITY_SHORT (unchanged; Matrix v1).
- **Sun:** DEPTH_LONG (unchanged; Matrix v1).

**How to capture excerpt:**  
GET the schedule API for a specific (year, week), e.g. `/api/planning/calendar/schedule/<year>/<week>`. Filter or inspect `schedule` for items by role and/or `scheduled_date` (or weekday derived from it) to confirm Mon/Tue/Thu CULTURE and Fri/Sun unchanged.

---

## 90-day repeat avoidance

- **Definition (option A):** Exclude any item (language `idea_id` or culture `culture_library_id`) that appears in `posting_queue` with `scheduled_date >= (target_date - 90 days)`. Planned schedule only; ignore `status = 'published'` for this rule.
- **Language:** `scripts/automated_weekly_content_creator.py` — `get_idea_ids_used_in_last_90_days()`; `pick_idea_for_tuesday()` uses cyclic resolver first, then eligible list with deterministic seed.
- **Culture:** `utils/content_roles/culture_generator.py` — `get_eligible_culture_ids()`; `pick_culture_for_slot()` uses deterministic seed `(rota_year, rota_week, weekday)`.

---

## Files touched

| Area | File(s) |
|------|--------|
| Migrations | `migrations/20260204_create_culture_library.sql`, `migrations/20260204_add_culture_library_id_to_posting_queue.sql` |
| Schedule API | `blueprints/planning_api_calendar_schedule.py` (Tue-only language; prefer posting_queue for Tue; role query already includes culture_fact) |
| Tuesday language creator | `scripts/automated_weekly_content_creator.py` (1/week, Tue only, 15:00, rotating type, 90-day, status ready) |
| Culture generator | `utils/content_roles/culture_generator.py` (new) |
| Culture automation | `scripts/automated_culture_creator.py` (new; Mon/Thu, 52–104 weeks, --weeks-ahead, --dry-run, --force) |

---

## No regression

- **Sunday DEPTH_LONG** and **Friday AUTHORITY_SHORT** logic and schedule API behaviour unchanged.
- Matrix structure (Mon: CULTURE, Tue: CULTURE Language, Thu: CULTURE) preserved; single post per day; role authority unchanged.
