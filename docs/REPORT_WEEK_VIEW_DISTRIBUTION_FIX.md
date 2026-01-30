# Fix Week-View Distribution to Approved Matrix — Report

**Date:** 2026-01-29

---

## 1) Diagnosis (§1.1)

### Query A — posting_queue for 2026-W5 (2026-01-26 → 2026-02-01)

Excerpt (one row per distinct date/type where many rows exist):

| scheduled_date | scheduled_time | role | content_type | status | id | idea_id | culture_library_id | heritage_library_id | product_id |
|----------------|----------------|------|--------------|--------|-----|---------|--------------------|---------------------|------------|
| 2026-01-26 | 00:03:53 | CULTURE | weekly_phrase | cancelled | 10722 | 1188 | NULL | NULL | NULL |
| 2026-01-26 | 00:03:53 | CULTURE | weekly_insult | cancelled | 10723 | 1295 | NULL | NULL | NULL |
| 2026-01-26 | 09:00 | CULTURE | weekly_word | published | 3143 | 1093 | NULL | NULL | NULL |
| 2026-01-27 | 00:02:20 | CULTURE | weekly_phrase | ready | 12159 | 1188 | NULL | NULL | NULL |
| … (8 language rows for 2026-01-27) | | | | | | | | | |
| 2026-01-28 | 14:30 | REASSURANCE | message | published | 4631 | NULL | NULL | NULL | NULL |
| 2026-01-29 | 15:00 | HERITAGE | heritage_fact | published | 21085 | NULL | NULL | 147 | NULL |
| 2026-01-30 | 15:00 | AUTHORITY_SHORT | authority_short | ready | 15505 | NULL | NULL | NULL | NULL |
| 2026-01-31 | 15:00 | COMMERCE | product | ready | 656 | NULL | NULL | NULL | 965 |
| … (4 more product rows for 2026-01-31) | | | | | | | | | |
| 2026-02-01 | 15:00 | DEPTH_LONG | depth_long | scheduled | 11823 | NULL | NULL | NULL | NULL |

**Total rows in week:** 333 (before backfill). After backfill: Monday 2026-01-26 has one additional culture_fact row (id 21247).

### Query B — Monday 2026-01-26 culture_fact

**Before fix:** 0 rows.  
**After backfill:** 1 row:

| id | status | scheduled_date | scheduled_time | culture_library_id |
|----|--------|----------------|----------------|--------------------|
| 21247 | ready | 2026-01-26 | 15:00:00 | 181 |

### Query C — Tuesday 2026-01-27 language (weekly_word / weekly_phrase / weekly_insult)

**Count:** 8 rows (all status `ready`). Example ids: 12159, 12160, 12161, 12162, 12163, 12164, 12165, 12166.

### Report-back format (§1.2)

- **For 2026-W5, posting_queue contains:** 333+ rows across the week; Mon had no culture_fact before backfill; Tue had 8 language rows; Wed–Sun had message, heritage_fact, authority_short, product (5), depth_long.
- **Monday culture_fact rows (before fix):** 0. **Root cause:** Culture creator (a) only looked ahead from “today”, so 2026-01-26 was already in the past, and (b) used “any CULTURE post exists” (role = 'CULTURE') so Mondays with legacy weekly_* (role CULTURE) were treated as “slot filled” and no culture_fact was created.
- **Tuesday language rows:** 8. **Why schedule API returned none for the grid:** The API did return one Tuesday language item, but the week-view card lacked `scheduled_date` and `scheduled_time`. The UI groups by day using those fields, so the Tuesday card had no date and did not appear on the Tuesday column. So the issue was **missing date/time on the Tuesday schedule item**, not missing data in posting_queue.

---

## 2) Fix class #1: Missing Monday CULTURE

### 2.1 Backfill

- **Action:** Ran culture creator with a window that includes 2026-01-26:  
  `python3 scripts/automated_culture_creator.py --start-date 2026-01-01 --weeks-ahead 8`
- **Result:** Monday 2026-01-26 now has exactly one culture_fact row: id 21247, status ready, scheduled_time 15:00, culture_library_id 181.

### 2.2 Logic and “don’t miss weeks” going forward

- **culture_post_exists()** now checks **content_type = 'culture_fact'** (not role = 'CULTURE'). So legacy weekly_* rows on Monday no longer block creation of Monday culture_fact.
- **--start-date** added to the culture creator so backfills can target past weeks (e.g. `--start-date 2026-01-01 --weeks-ahead 8`).
- **Default lookahead** increased from 4 to **12 weeks** for both culture and heritage creators.

### 2.3 Who runs the culture creator and lookahead

- **Script:** `scripts/automated_culture_creator.py`. No dedicated cron or monitor was found in the repo that runs it; it is intended to be run by an operator or a separate scheduler.
- **Current lookahead:** 12 weeks (default). With default `today`, that covers the next 12 Mondays.
- **Recommendation:** Ensure whichever process runs the culture creator uses at least 8–12 weeks lookahead (e.g. `--weeks-ahead 12`). Same for heritage creator (`scripts/automated_heritage_creator.py`, now also default 12 weeks).

---

## 3) Fix class #2: Tuesday Language in schedule

### 3.1 Creation

- Tuesday already had 8 language rows in posting_queue for 2026-01-27. The approved behaviour is “one language post per week” (rotating word/phrase/insult). The schedule API is required to **pick exactly one** for the grid; it does not require the creator to insert only one row per Tuesday. No change was made to the weekly language creator; the schedule API now selects one and surfaces it with a date.

### 3.2 Schedule API Tuesday selection (deterministic)

**Predicate used for Tuesday language in the schedule API:**

- **Table:** `posting_queue` (alias `pq`).
- **Filters:**  
  - `pq.platform = 'facebook'`  
  - `pq.content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')`  
  - `pq.scheduled_date = <that week’s Tuesday date>`  
  - `pq.status IN ('ready', 'pending', 'generated', 'published', 'scheduled')`
- **Order:** Prefer `ready`, then `published`, then others; within that, newest first:  
  `ORDER BY CASE WHEN pq.status = 'ready' THEN 0 WHEN pq.status = 'published' THEN 1 ELSE 2 END, pq.id DESC`
- **Limit:** 1 row.

**Additional change:** The Tuesday schedule item now includes **scheduled_date** and **scheduled_time** from the selected queue row (or, when using the cyclic resolver fallback, `scheduled_date` = that Tuesday and `scheduled_time` = 09:00:00) so the week-view can place the card on Tuesday.

---

## 4) Fix class #3: Saturday Commerce (Option A)

- **Choice implemented:** **Option A** — Schedule API caps Saturday Commerce to **one visible card** in the week-view grid.
- **Implementation:** In `blueprints/planning_api_calendar_schedule.py`, after fetching product posts for the week, the list is capped to the first one: `filtered_product_posts = product_posts[:1]`. All product rows for that Saturday remain in posting_queue and can be used in detail views / queue list; only the grid shows one card.

---

## 5) Verification pack

### 5.1 Schedule API for 2026-W5 (excerpt)

After fixes, `GET /planning/api/calendar/schedule/2026/5` returns one item per day as intended:

| Date | Type | Role | Title (excerpt) |
|------|------|------|------------------|
| 2026-01-26 | culture | CULTURE | Why 'Ness' appears in river names |
| 2026-01-27 | weekly_insult | CULTURE | Ye're a richt haverel |
| 2026-01-28 | message | REASSURANCE | You don't need a clan connection to wear a kilt. |
| 2026-01-29 | heritage | HERITAGE | How tartan design balances tradition and choice |
| 2026-01-30 | authority_short | AUTHORITY_SHORT | Here is a short authoritative statement about Scot… |
| 2026-01-31 | product | COMMERCE | Celtic Oval Belt Buckle |
| 2026-02-01 | depth_long | DEPTH_LONG | When it comes to garments like the kilt, size can… |

Monday and Tuesday are no longer blank. Saturday shows one product card.

### 5.2 posting_queue rows for Mon and Tue

**Monday 2026-01-26 culture_fact:**  
id=21247, status=ready, scheduled_date=2026-01-26, scheduled_time=15:00:00, culture_library_id=181, role=CULTURE, content_type=culture_fact.

**Tuesday 2026-01-27 language (one selected for schedule):**  
id=12166, status=ready, scheduled_date=2026-01-27, scheduled_time=00:02:20, content_type=weekly_insult, idea_id=1297.

### 5.3 Executor compatibility

No code changes were made to the executor. Weekday validation already allows:

- **culture_fact** → Monday (1)  
- **heritage_fact** → Thursday (4)  
- **weekly_word / weekly_phrase / weekly_insult** → Tuesday (2)  
- message → Wednesday (3), authority_short → Friday (5), product → Saturday (6), depth_long → Sunday (7).

**Statement:** Executor weekday validation allows these content types on these days.

---

## 6) What was sent back (summary)

1. **SQL outputs (§1.1):** Summarised in §1 above (Query A excerpt, Query B before/after, Query C count).
2. **Root causes:** Monday blank = no culture_fact row (creator didn’t create for that week; logic treated “any CULTURE” as filled). Tuesday blank = Tuesday item was returned but without scheduled_date/scheduled_time, so the week-view could not place it.
3. **Files changed:**  
   - `scripts/automated_culture_creator.py`: culture_post_exists checks content_type='culture_fact'; added --start-date; default --weeks-ahead 12.  
   - `scripts/automated_heritage_creator.py`: default --weeks-ahead 12.  
   - `blueprints/planning_api_calendar_schedule.py`: Tuesday language query now selects scheduled_date/scheduled_time, filters by status IN (ready, pending, generated, published, scheduled), prefers ready then published then newest; Tuesday schedule item now includes scheduled_date and scheduled_time; Saturday product list capped to one for the grid (Option A).
4. **Schedule API excerpt:** See §5.1 (table by date).
5. **Saturday:** Option A implemented (cap in schedule grid; queue unchanged).
