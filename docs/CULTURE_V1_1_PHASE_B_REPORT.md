# CULTURE v1.1 — Phase B Report

**Status:** Phase B implementation complete per instruction brief (2026-01-29)  
**Scope:** Generator, creator script, schedule API adjustments only. No execution, preview, schema, or other systems touched.

---

## 1. Implementation summary

| Component | File | Change |
|-----------|------|--------|
| Generator | `utils/content_roles/culture_generator.py` | Added `category` to return of `pick_culture_for_slot()`. 90-day eligibility and deterministic seed `(rota_year, rota_week, weekday)` unchanged. |
| Creator | `scripts/automated_culture_creator.py` | Default look-ahead set to 4 weeks (28 days). Mon/Thu only; `culture_fact`; `status='ready'`; `scheduled_time=15:00`; skip if non-failed post exists unless `--force`. |
| Schedule API | `blueprints/planning_api_calendar_schedule.py` | Comment added: Mon/Thu CULTURE (culture_fact) appear via role-based query; Tuesday language remains resolver-only. No logic change (role query already included `culture_fact`). |

---

## 2. Schedule API behaviour (CULTURE v1.1)

- **Tuesday:** One CULTURE (language) slot from resolver or posting_queue; type rotates `weekly_word` → `weekly_phrase` → `weekly_insult` by `(week_number - 1) % 3`. No language on Mon/Thu.
- **Monday & Thursday:** CULTURE (culture_fact) from posting_queue with `role='CULTURE'`, `content_type='culture_fact'`, `culture_library_id` set. Fetched by the existing role-based query (content_type NOT IN product, message, weekly_*). No duplication with Tuesday language.

**Schedule API excerpt (expected pattern for one week):**

| Day | Role | Source | content_type |
|-----|------|--------|--------------|
| Mon | CULTURE | culture_library | culture_fact |
| Tue | CULTURE | calendar_ideas (resolver) | weekly_word / weekly_phrase / weekly_insult (rotating) |
| Wed | REASSURANCE | message | message |
| Thu | CULTURE | culture_library | culture_fact |
| Fri | AUTHORITY_SHORT | (unchanged) | authority_short |
| Sat | COMMERCE | product | product |
| Sun | DEPTH_LONG | (unchanged) | depth_long |

---

## 3. Sample posting_queue rows (culture_fact)

After running `automated_culture_creator.py` (with `culture_library` seeded), Mon/Thu rows look like:

```text
platform='facebook'
role='CULTURE'
content_type='culture_fact'
culture_library_id=<id>
scheduled_date=<date>
scheduled_time='15:00'
status='ready'
generated_content='<title>\n\n<body_text>'
```

No `idea_id`; language posts use `idea_id` and `content_type` in (`weekly_word`,`weekly_phrase`,`weekly_insult`).

---

## 4. 90-day repeat avoidance

- **Logic:** `utils/content_roles/culture_generator.get_eligible_culture_ids(target_date)` excludes any `culture_library.id` that appears in `posting_queue` with `culture_library_id` set and `scheduled_date >= (target_date - 90 days)`. Planned schedule only; `status` is not used for exclusion.
- **Deterministic pick:** `pick_culture_for_slot(target_date, weekday, rota_year, rota_week)` uses seed `rota_year * 53 * 10 + rota_week * 10 + weekday` to choose from eligible IDs (stable ordering by id). Same (year, week, weekday) ⇒ same library item.
- **Proof:** Use an item once; it is excluded for the next 90 days; after 90 days it becomes eligible again. No LLM; selection is deterministic from seed and eligible list.

---

## 5. Acceptance criteria (brief 5.1–5.4)

| Criterion | Status |
|-----------|--------|
| 5.1 Behavioural: Mon 1 CULTURE (library), Tue 1 CULTURE (language rotating), Thu 1 CULTURE (library); no duplicate CULTURE cards; no language on Mon/Thu | Implemented: creator + schedule API align with this. |
| 5.2 Rotation: Three consecutive Tuesdays show word → phrase → insult; correct ISO week mapping | Implemented: `language_type = language_types[(week_number - 1) % 3]` in schedule API and weekly creator. |
| 5.3 Repeat-avoidance: Library item used once, excluded 90 days, then eligible again | Implemented: `get_eligible_culture_ids` and deterministic pick. |
| 5.4 Artifacts: Short report with schedule API excerpt, sample posting_queue rows, 90-day confirmation | This document. |

---

## 6. Non-scope (unchanged)

- Execution / scheduler logic  
- Preview renderer or templates  
- Facebook formatter  
- AUTHORITY_SHORT / DEPTH_LONG  
- Schema or migrations  
- Product / message logic  

No work done in these areas.

---

## 7. How to verify

1. **Seed `culture_library`** with at least a few rows (`active = TRUE`).
2. **Run creator (dry-run):**  
   `python3 scripts/automated_culture_creator.py --weeks-ahead 4 --dry-run`  
   Then without `--dry-run` to insert rows.
3. **Call schedule API** for a week that includes Mon/Thu, e.g. `GET /api/planning/calendar/schedule/<year>/<week>`.  
   Confirm: one Tuesday language item; Mon and Thu each have one CULTURE (culture_fact) from the role-based list.
4. **Check posting_queue:** Rows with `content_type='culture_fact'` have `culture_library_id`, `scheduled_time='15:00'`, `status='ready'`.

Phase B complete. Do not proceed beyond Phase B without new approval.
