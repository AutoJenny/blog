# Audit: Facebook Auto-Posting Duplicates and Wrong-Day Language Posts

**Date:** 2026-01-29  
**Scope:** Explain why (1) language posts were published on Thursday, (2) duplicates appeared (word twice, two phrases each twice), (3) posts went to both Facebook pages. No behavioural changes or fixes—audit only.

---

## 1. Executive Summary

- **What happened:** The automated system published language posts (word/phrase/insult) on **Thursday**, and produced **duplicates** (word of the day twice; two different phrase posts, each twice), across **both** Facebook pages.
- **Wrong-day cause:** The **queue** contains many language rows with `scheduled_date` = Thursday (weekday 4). These are **legacy** rows (old Matrix: word Mon, phrase Wed, insult Fri; or an older creator that scheduled language on multiple days). The **centralized executor** (`scheduled_posting_executor.py`) **does** block Thursday language (it enforces word=Mon, phrase=Wed, insult=Fri). So either an **older executor** (without that validation) ran and published them, or another **publish path** (e.g. `execute_publish_to_facebook`, manual publish, or another host) ran **without** weekday validation.
- **Duplicate cause:** (1) **Dual-page design:** `publish_to_facebook()` intentionally posts to **both** pages (Page A and Page B) for each queue row—so one row → two Facebook posts. (2) **Duplicate queue rows:** Historical duplicate-creation (see `docs/CRITICAL_DUPLICATE_POST_BUG.md`) left multiple `posting_queue` rows for the same content (same idea_id/content_type/scheduled_date). Each such row is published once and sent to both pages → same “word” or “phrase” appears multiple times (per row × per page).
- **Code path responsible:** Primary publish path is `scripts/scheduled_posting_executor.py` → `utils/platform_publishers.publish_to_facebook(queue_id)`. Legacy path: `blueprints/automation_execute.execute_publish_to_facebook()` (no weekday check). Manual path: `blueprints/posts.api_publish_post()` (no weekday check). **Both-pages** behaviour is in `utils/platform_publishers.py`: it builds a list of two pages from `platform_credentials` (`page_id`/`page_access_token` and `page_id_2`/`page_access_token_2`) and loops over them.

---

## 2. Reproduction and Timeline (Log-Backed)

### 2.1 Log sources

- **Executor:** `logs/scheduled_posting_executor.log`  
- **Monitor:** `scripts/background_posting_monitor.sh` runs every 5 minutes; step 7 runs `scheduled_posting_executor.py`.  
- **Monitoring API:** `blueprints/monitoring.py` reads `scheduled_posting_executor.log` (among others) for events.

### 2.2 Timeline (2026-01-29)

| Time (UTC/local) | Process | What happened |
|------------------|--------|----------------|
| 2026-01-29 00:02 – 10:44 (and every ~5 min) | scheduled_posting_executor | Runs; in recent runs either “Automated posting is DISABLED” or 0 posts published. |
| 2026-01-29 10:44:00 | scheduled_posting_executor | **Found many candidate posts** (language with `scheduled_date` = Thursday). **All blocked** by `validate_weekly_content_schedule`: “BLOCKED: Post N (weekly_word/weekly_phrase/weekly_insult) scheduled for weekday 4 (expected 1/3/5)”. Affected IDs include 17146–17714+ (hundreds of language rows). |
| (Exact time of actual publish TBD) | Unknown | User-observed posts went live. No entry in **this** log shows `successfully_published` > 0 on 2026-01-29. So either: (a) publish occurred via another path (e.g. automation_execute, manual, or old script), (b) on another host/environment, or (c) before the current validation was in place in the running process. |

**Conclusion:** The **current** centralized executor, when it runs, **does not** publish Thursday language; it blocks it. The wrong-day and duplicate behaviour are consistent with: (1) legacy or duplicate queue rows with Thursday dates, and (2) either an older executor run or a different code path that does not apply the weekday check, plus (3) intentional posting to both pages.

---

## 3. DB Evidence

### 3.1 Queries used (read-only)

Run these against your PostgreSQL DB (adjust connection per project convention). Results should be captured in `docs/AUDIT_SQL_DUMPS_20260129.sql` (or equivalent) and summarized below.

```sql
-- (1) Facebook posting_queue for Thursday 2026-01-29 and nearby
SELECT id, platform, content_type, status, scheduled_date, scheduled_time,
       idea_id, role, platform_post_id, updated_at
FROM posting_queue
WHERE platform = 'facebook'
  AND scheduled_date >= '2026-01-27' AND scheduled_date <= '2026-01-30'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult', 'message', 'product', 'culture_fact', 'authority_short', 'depth_long')
ORDER BY scheduled_date, id;

-- (2) Counts by content_type and status for that window
SELECT content_type, status, scheduled_date, COUNT(*) AS cnt
FROM posting_queue
WHERE platform = 'facebook'
  AND scheduled_date >= '2026-01-27' AND scheduled_date <= '2026-01-30'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult', 'message', 'product', 'culture_fact', 'authority_short', 'depth_long')
GROUP BY content_type, status, scheduled_date
ORDER BY scheduled_date, content_type, status;

-- (3) Duplicate candidates: same idea_id, content_type, scheduled_date (language)
SELECT idea_id, content_type, scheduled_date, COUNT(*) AS cnt, array_agg(id ORDER BY id) AS queue_ids
FROM posting_queue
WHERE platform = 'facebook'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  AND scheduled_date = '2026-01-29'
GROUP BY idea_id, content_type, scheduled_date
HAVING COUNT(*) > 1
ORDER BY cnt DESC;

-- (4) Rows actually published (status = 'published') on 2026-01-29
SELECT id, content_type, idea_id, scheduled_date, platform_post_id, updated_at
FROM posting_queue
WHERE platform = 'facebook'
  AND status = 'published'
  AND (updated_at::date = '2026-01-29' OR scheduled_date = '2026-01-29')
ORDER BY id;
```

### 3.2 Summarized results (to be filled from your run)

- **Counts by content_type/status/scheduled_date:** Run query (2) and paste or summarize (e.g. “N weekly_word ready on 2026-01-29”, “M weekly_phrase published on 2026-01-29”).
- **Duplicate queue rows:** Query (3) will show whether multiple rows exist for the same (idea_id, content_type, scheduled_date). If yes, that supports “duplicate queue rows” as a cause of duplicate Facebook posts (each row published once → both pages).
- **Actually posted rows:** Query (4) lists rows that were marked published on 2026-01-29; correlate with user-observed “word twice, two phrases each twice” and platform_post_id if needed.

---

## 4. System Map

### 4.1 Creators (what generates queue entries)

| File | Entrypoint | Days targeted | Invoked by |
|------|------------|---------------|------------|
| `scripts/automated_weekly_content_creator.py` | `WeeklyContentCreator.create_weekly_content_posts()` | **Tuesday only** (CULTURE v1.1); rotating weekly_word → weekly_phrase → weekly_insult by week | `background_posting_monitor.sh` (step 1) |
| `blueprints/automation_core.py` | (workflow: social-only weekly) | No fixed day; creates **draft** rows with **no** scheduled_date/scheduled_time when using `create_weekly_social_post(..., cursor=cursor)` | User/workflow when choosing Facebook + weekly format |
| Legacy / historical | (e.g. old creator, backfills) | Previously Mon/Wed/Fri or other patterns; many Thursday rows still in DB | N/A (data left in queue) |

Only the automated weekly content creator is currently scheduled by the monitor; it creates **Tuesday-only** language. Thursday language in the queue is from **legacy data** or from workflow-created drafts that were later dated.

### 4.2 Schedulers / executors (what publishes)

| File | Role | Weekday validation? | Invoked by |
|------|------|---------------------|------------|
| `scripts/scheduled_posting_executor.py` | **Central** executor: gets due posts, validates date + weekly schedule, calls platform publisher | **Yes:** weekly_word=Mon(1), weekly_phrase=Wed(3), weekly_insult=Fri(5). Thursday (4) **blocked**. | `background_posting_monitor.sh` (step 7); or `posting_executor.py` (wrapper) |
| `scripts/posting_executor.py` | Thin wrapper: loads and runs `scheduled_posting_executor.main()` | Same as above | Monitor or legacy cron |
| `scripts/automated_posting.py` | **Does not publish;** only sets `scheduled_timestamp` and status `pending` (schedules for later) | N/A | Monitor step 6 |
| `blueprints/automation_execute.execute_publish_to_facebook()` | Legacy publish path | **No** weekday validation; delegates to `publish_to_facebook(queue_id)` | Workflow when substage = `publish_to_facebook` |
| `blueprints/posts.api_publish_post()` | Manual publish for one queue_id | **No** weekday validation | UI / API call |

So: the **only** path that enforces “no language on Thursday” is the centralized executor. Any other path that calls `publish_to_facebook(queue_id)` will publish whatever is in the row, including Thursday language.

### 4.3 Page targeting configuration

- **Source:** `platform_credentials` (platform = Facebook): keys `page_id`, `page_access_token`, `page_id_2`, `page_access_token_2`.
- **Code:** `utils/platform_publishers.publish_to_facebook()`:
  - Reads all active Facebook credentials.
  - Builds `pages_to_post`: first page from `page_id` + `page_access_token`, second from `page_id_2` + `page_access_token_2` **only if** `page_id_2 != page_id`.
  - Loops over `pages_to_post` and posts the **same** message/image to each page (Graph API feed or photos endpoint).
- **Definitive statement:** Posts were sent to **both** Page A and Page B because `publish_to_facebook()` is implemented to post to **both** configured pages in a single call. There are not “two runs with different page configs”—there is **one** call per queue row that intentionally targets two pages.

---

## 5. Root Causes

### 5.1 Wrong-day language posting (Thursday)

- **Cause:** Queue contains language rows with `scheduled_date` = Thursday. The **current** `scheduled_posting_executor` **blocks** these (weekday 4 ≠ 1, 3, 5). So either:
  1. An **older** version of the executor (without `validate_weekly_content_schedule`) ran and published them, or  
  2. Another **publish path** ran (e.g. `execute_publish_to_facebook`, manual publish, or another environment) and that path does **not** perform weekday validation.

- **Evidence:** Log lines on 2026-01-29 10:44: “BLOCKED: Post … (weekly_* ) scheduled for weekday 4 (expected 1/3/5)”. Hundreds of Thursday language rows are present and blocked by the current executor.

### 5.2 Duplicate posting

- **Cause (1) – Two pages:** By design, each call to `publish_to_facebook(queue_id)` posts to **both** Facebook pages. So “same content twice” (once per page) is expected for a **single** queue row.
- **Cause (2) – Duplicate queue rows:** Past duplicate-creation (see `docs/CRITICAL_DUPLICATE_POST_BUG.md`) left multiple `posting_queue` rows for the same (idea_id, content_type, scheduled_date). If the executor (or another path) published **each** of those rows, and each row is sent to **both** pages, the user would see:
  - “Word of the day” twice: e.g. 1 word row × 2 pages, or 2 word rows × 2 pages.
  - “Two different phrase posts, each posted twice”: 2 phrase rows × 2 pages = 4 phrase posts (two distinct phrases, each on both pages).

- **Evidence:** Query (3) above will show whether duplicate (idea_id, content_type, scheduled_date) exist for 2026-01-29. Historical doc confirms mass duplicate creation on 2026-01-18.

### 5.3 Dual-page targeting

- **Cause:** Not a misconfiguration; it is **intentional** in `utils/platform_publishers.publish_to_facebook()`. Both `page_id` and `page_id_2` (when different) are used in one go.
- **Evidence:** Code at `utils/platform_publishers.py` (message and image branches) builds `pages_to_post` and iterates with the same payload.

---

## 6. Risk Assessment (What Could Repeat)

- **Tomorrow / next Thursday:** If the **same** executor or another path runs without weekday validation, any remaining **Thursday** language rows (ready/pending) could be published again. Duplicate queue rows would again produce multiple posts per content type across both pages.
- **Tuesday:** The **current** creator only adds **Tuesday** language. The **current** executor allows only Mon (word), Wed (phrase), Fri (insult)—so it does **not** allow Tuesday language either unless the executor’s expected weekdays are updated to match CULTURE v1.1 (Tuesday-only language). So there is a **mismatch**: creator = Tuesday only; executor = Mon/Wed/Fri only. That needs a fix so that (a) only Tuesday language is valid at publish time, and (b) Thursday is CULTURE (e.g. culture_fact), not language.
- **Dual-page:** Will repeat every time `publish_to_facebook()` is called until code or config is changed to target a single page or to make dual-page optional.

---

## 7. Fix Plan (Proposal Only — No Code Yet)

1. **Align executor with Matrix (Tuesday-only language; Thursday = CULTURE):**  
   - In `scheduled_posting_executor.validate_weekly_content_schedule()`, change expected weekday for **all** three language types to **Tuesday (2)**.  
   - Optionally restrict to “at most one language post per week” (e.g. by week number) to match “one rotating type per Tuesday”.

2. **Clean up legacy Thursday language in queue:**  
   - Identify and cancel or delete (or reschedule) `posting_queue` rows with `content_type IN ('weekly_word','weekly_phrase','weekly_insult')` and `scheduled_date` on Thursday (or any non-Tuesday).  
   - Prevent future creation of language on non-Tuesday (creator already does Tuesday-only; ensure no other code path creates language on other days).

3. **Duplicate queue rows:**  
   - Run a one-off dedupe: for (platform, content_type, idea_id, scheduled_date), keep one row (e.g. lowest id) and cancel or delete the rest.  
   - Harden the weekly content creator with a **unique constraint** or transactional “check then insert” with locking so duplicate (idea_id, content_type, platform, scheduled_date) cannot be created (see `CRITICAL_DUPLICATE_POST_BUG.md`).

4. **Idempotency / locking at publish:**  
   - Before calling `publish_to_facebook(queue_id)`, **claim** the row (e.g. status → `in_progress` or use a row lock) and only then call the publisher; on success set `published` and `platform_post_id`; on failure set `failed`.  
   - Re-check status and `platform_post_id` immediately before publish (executor already does a re-check; ensure no other path publishes without the same guard).  
   - This reduces the chance that two runs or two processes publish the same row twice.

5. **Single-page targeting (optional):**  
   - If the product requirement is to post to **one** page only, add config (e.g. “primary page only” or a single token set) and in `publish_to_facebook()` only add that page to `pages_to_post`.  
   - If both pages are required, document that “duplicate” in the sense of “same post on two pages” is by design; focus fixes on duplicate **queue rows** and wrong-day validation.

---

## 8. Hypotheses — Confirmed or Denied

| # | Hypothesis | Result |
|---|------------|--------|
| 1 | Language creator still generating 3× weekly language and scheduling on Thu | **Denied.** Current `automated_weekly_content_creator.py` is Tuesday-only, one type per week. Thursday language in queue is legacy. |
| 2 | Two publishing processes running (monitor + cron; or two hosts) | **Unconfirmed from logs.** Single log shows only one executor run every ~5 min. Possible on other host or cron; not proven here. |
| 3 | Publish claim non-atomic → race causes duplicates | **Plausible.** Executor re-checks status/platform_post_id before publish but does not lock. Duplicate **queue rows** (same content) are confirmed historically; those alone cause “same content posted multiple times” when each row is published to both pages. |
| 4 | Two page tokens / page IDs configured → cross-posting | **Confirmed by design.** One call to `publish_to_facebook()` posts to both pages. |
| 5 | Legacy module still calls publish directly (bypassing centralized executor) | **Confirmed.** `execute_publish_to_facebook()` and `api_publish_post()` call `publish_to_facebook()` with no weekday validation. |

---

## 9. Supporting Artefacts

- **SQL:** `docs/AUDIT_SQL_DUMPS_20260129.sql` — exact queries (same as in §3.1); run locally and append result excerpts if desired.  
- **Log excerpts:** `docs/AUDIT_LOG_EXCERPTS_20260129.txt` — sample executor log lines showing BLOCKED Thursday language and completion stats.  
- **Config snapshot:** `docs/AUDIT_CONFIG_SNAPSHOT_20260129.txt` — optional; list of relevant config keys (e.g. `automated_posting_enabled`) and **redacted** credential keys (e.g. `page_id`, `page_id_2` present/absent). No secret values.

---

*End of audit report.*
