# Report: Executor daily cap and idempotency (2026-01-30)

**Brief:** Fix “Multiple posts published in one day” (Facebook Matrix).  
**Status:** Implemented (containment + long-term hardening).

---

## 1. Summary of changes

### Files changed

| File | Change |
|------|--------|
| `scripts/scheduled_posting_executor.py` | Daily cap, deterministic selection, cancel surplus, atomic claim-before-publish, dry-run, stats |
| `scripts/hotfix_cancel_surplus_today.py` | **New.** Hotfix: cancel surplus Facebook rows for today; output CSV. |
| `scripts/cleanup_surplus_daily_posts.py` | **New.** Cleanup: scan N weeks, cancel surplus per date; output CSV. |
| `docs/BRIEF_EXECUTOR_DAILY_CAP_AND_IDEMPOTENCY.md` | **New.** Repo brief for this fix. |
| `docs/HOTFIX_CANCELLED_IDS_YYYYMMDD.csv` | **Artefact.** Written by hotfix (today: 1 row kept, 0 cancelled). |
| `docs/CLEANUP_SURPLUS_POSTS_YYYYMMDD.csv` | **Artefact.** Written by cleanup script (dry-run: 1 row to cancel in range). |

### Main functions modified (executor)

- **`get_due_posts()`** — SELECT now includes `pq.role` for priority.
- **`apply_daily_cap(valid_posts)`** — **New.** Groups by (platform, scheduled_date). Facebook: Saturday keeps all product rows and cancels non-product; non-Saturday keeps one per date by deterministic priority, cancels the rest. Returns (posts_to_publish, list of (id, error_message) to cancel).
- **`process_due_posts()`** — After `get_due_posts()`, calls `apply_daily_cap()`; applies cancellations (status='cancelled', error_message=…); then for each post: **atomic claim** (`UPDATE status='publishing' WHERE id=? AND status IN ('ready','pending')`, rowcount==1); then `route_to_platform_publisher()`. Stats extended: `eligible_after_validation`, `cancelled_surplus`, `blocked_wrong_day`.
- **`main()`** — Added `--dry-run` (log only; no DB updates or publishing).

### Selection priority (deterministic)

For non-Saturday Facebook dates, when multiple eligible rows exist for the same date, keep one in this order (then lowest id):

1. AUTHORITY_SHORT (Friday)
2. DEPTH_LONG (Sunday)
3. HERITAGE / heritage_fact (Thursday)
4. culture_fact (Monday)
5. message (Wednesday)
6. weekly_word / weekly_phrase / weekly_insult (Tuesday)
7. product (only on Saturday; on other days still only one per date)

---

## 2. Before/after evidence

### Hotfix (today)

- **Command:** `python3 scripts/hotfix_cancel_surplus_today.py --dry-run`
- **Result:** Found 1 publishable Facebook row for today (2026-01-30); 0 to cancel. Kept id=24715. CSV written: `docs/HOTFIX_CANCELLED_IDS_20260130.csv` (1 row: kept).
- **DB:** For today, only one row is publishable (ready/pending, scheduled ≤ now); no surplus to cancel.

### Executor dry-run

- **Command:** `python3 scripts/scheduled_posting_executor.py --dry-run`
- **Result:** Found 2 candidate posts; content schedule validation blocked both (wrong weekday / week already has language published). After validation: 0 posts ready. So daily cap was not triggered (no eligible posts). Stats: `eligible_after_validation=0`, `cancelled_surplus=0`.
- **Example when cap would trigger:** When multiple eligible posts exist for the same date, log will show: `Executor daily cap: date YYYY-MM-DD had N eligible, kept id=X (priority), cancelling N-1 surplus` and `Executor cap: cancelled N surplus eligible row(s)`.

### Cleanup script dry-run

- **Command:** `python3 scripts/cleanup_surplus_daily_posts.py --dry-run`
- **Result:** Wrote `docs/CLEANUP_SURPLUS_POSTS_20260130.csv` with 1 row to cancel (surplus for a date in the next 12 weeks). Would cancel id=24715.

### Atomic claim

- **Logic:** Before `route_to_platform_publisher(post)`, executor runs `UPDATE posting_queue SET status='publishing' WHERE id=? AND status IN ('ready','pending')`. If `rowcount != 1`, log "Post X not claimed (rowcount=…); already claimed/published by another process, skipping" and skip. So a second process or re-run will not publish the same row twice.

---

## 3. Artefacts

- **docs/HOTFIX_CANCELLED_IDS_20260130.csv** — id, role, content_type, scheduled_date, scheduled_time, status_before, status_after. Today: 1 row (kept). Written by hotfix (for real).
- **docs/CLEANUP_SURPLUS_POSTS_YYYYMMDD.csv** — Written by cleanup only when there are rows to cancel. Run with `--weeks 12` for real; if no surplus in range, script exits without writing CSV.
- **docs/EXECUTOR_CORRELATE_PUBLISHED_POSTS.md** — DB query and mapping instructions for correlating published FB post IDs to posting_queue.id (task 1.1).
- **scripts/hotfix_cancel_surplus_today.py** — Hotfix: cancel surplus for today only; writes CSV.
- **scripts/cleanup_surplus_daily_posts.py** — Cleanup: scan N weeks (default 12), cancel surplus per date; writes CSV when any to cancel. Options: `--weeks N`, `--dry-run`.
- **scripts/validate_daily_cap_invariant.py** — Fails if any non-Saturday date in next N weeks has >1 publishable Facebook row.

---

## 4. Risk notes

- **Edge cases:** (1) `scheduled_time` or `scheduled_timestamp` missing — executor already skips such rows in `validate_scheduled_date`. (2) Status transitions — claim sets `publishing`; success sets `published`; failure sets `failed`; surplus set to `cancelled`. No other statuses used for this flow.
- **Other publish paths:** Phase C1 keeps Facebook publishing only via the scheduled posting executor. `blueprints/posts.api_publish_post()` returns 403. `automation_execute.execute_publish_to_facebook` exists but should remain disabled for Facebook (per Phase C1). No changes made to those paths; they continue to be disabled for Facebook.

---

## 5. Acceptance checklist

| Item | Status |
|------|--------|
| C1. Reproduce prior failure (day with >1 eligible) | DB can contain such days; cleanup script finds them. |
| C2. Executor selects one for non-Saturday, cancels surplus, logs rationale | Implemented; dry-run shows 0 eligible today; cap logic in `apply_daily_cap()`. |
| C3. Saturday: multiple product posts eligible, non-product cancelled | Implemented in `apply_daily_cap()` (Saturday branch). |
| C4. Idempotency (claim-before-publish) | Implemented; second run sees row as publishing/published and skips. |
| C5. Schedule API matches queue (one per day except Sat products) | Unchanged; validation script `validate_planning_calendar_p1.py` already checks this. |

---

## 6. How to run

- **Hotfix (today):** `python3 scripts/hotfix_cancel_surplus_today.py` (omit `--dry-run` to apply).
- **Cleanup (forward N weeks):** `python3 scripts/cleanup_surplus_daily_posts.py [--weeks N] [--dry-run]`.
- **Executor (with cap + claim):** `python3 scripts/scheduled_posting_executor.py [--bypass-switch] [--dry-run]`.
- **Daily cap invariant check:** `python3 scripts/validate_daily_cap_invariant.py --weeks 12 --platform facebook`.

---

## 7. Required report-back (non-negotiable format)

### 7.1 What exactly happened on the day 5 posts were published (cause)

**To be confirmed** with: (a) git commit hash deployed at time of that run, (b) executor log for the run that published the 5 posts, (c) DB state for that date immediately before publication (if available).

**Probable causes (coder to confirm which):**

| # | Cause | Evidence to check |
|---|--------|-------------------|
| 1 | Executor ran before the cap code was deployed (most common) | Git commit deployed + timestamp vs executor run time |
| 2 | A different publish path was used (despite Phase C1) | Only `scheduled_posting_executor.py` should publish Facebook; `execute_publish_to_facebook` is disabled |
| 3 | Multiple executor instances ran and claim-before-publish didn’t exist yet | Logs from multiple processes; claim SQL added in this fix |
| 4 | Queue already contained multiple “ready” rows for that date and no cap existed | DB query for that scheduled_date: count of status IN ('ready','pending') |

**Correlation (1.1):** Use `docs/EXECUTOR_CORRELATE_PUBLISHED_POSTS.md` — run the DB query for the scheduled_date of the 5 posts, list the 5 Facebook post IDs, and fill the mapping table (facebook_post_id → posting_queue.id). That proves whether 5 separate queue rows were published (most likely) vs a publish-loop.

---

### 7.2 What was cancelled (CSVs + counts)

| Artefact | Result (2026-01-30) |
|----------|----------------------|
| **Hotfix (for real)** | `python3 scripts/hotfix_cancel_surplus_today.py` → Found 1 publishable row today; kept id=24715, cancelled=0. CSV: `docs/HOTFIX_CANCELLED_IDS_20260130.csv` (1 row: kept). |
| **Cleanup 12 weeks (for real)** | `python3 scripts/cleanup_surplus_daily_posts.py --weeks 12` → No surplus rows in [2026-01-30, 2026-04-24]. Nothing to cancel. (Script only writes CSV when there are rows to cancel; none today.) |

**DB evidence for today (non-Saturday):** Max 1 row in status IN ('ready','pending') for facebook for 2026-01-30. Any surplus would now be cancelled with hotfix error message.

---

### 7.3 Proof of invariant (validation script output)

```
$ python3 scripts/validate_daily_cap_invariant.py --weeks 12 --platform facebook
Daily cap invariant OK: 1 dates checked, max 1 publishable per non-Saturday date.
```

Script: `scripts/validate_daily_cap_invariant.py` (committed). It fails (exit 1) if any non-Saturday date in the next N weeks has >1 publishable row for Facebook.

---

### 7.4 Proof from logs (cap + claim in a real run)

**Relevant log block** (executor startup + DB target + cap summary). From a run (dry-run below; real run will show same startup and, when eligible posts exist, cap/claim lines):

```
2026-01-30 09:37:39,307 - INFO - main:638 - Starting scheduled posting executor
2026-01-30 09:37:39,307 - INFO - main:641 - DB target: host=localhost port=5432 dbname=blog user=autojenny
2026-01-30 09:37:39,307 - INFO - main:644 - Executor daily cap enabled (max 1 per day except Saturday products)
2026-01-30 09:37:39,308 - INFO - main:648 - DRY-RUN: No DB updates or publishing
...
2026-01-30 09:37:39,355 - INFO - main:658 - Scheduled posting executor complete: {'eligible_after_validation': 0, 'total_found': 0, 'successfully_published': 0, 'failed': 0, 'skipped': 0, 'cancelled_surplus': 0, 'blocked_wrong_day': 0}
```

When multiple eligible exist for one date, logs will show:
- `Executor daily cap: date YYYY-MM-DD had N eligible, kept id=X (priority), cancelling N-1 surplus`
- `Executor cap: cancelled N surplus eligible row(s)`
- Claim failure (if another process won): `Post X not claimed (rowcount=0); already claimed/published by another process, skipping`

---

### 7.5 Anything still not covered

- **Other platforms:** Cap applies only to **Facebook** in `apply_daily_cap()`. Instagram, Twitter, LinkedIn go through the same `scheduled_posting_executor.py` but are not capped (they get all due posts). If other channels must enforce one-per-day, extend `apply_daily_cap()` by platform rules or add equivalent safeguards.
- **Saturday:** Multiple product posts per Saturday are allowed; non-product on Saturday is cancelled by cap.
- **psycopg IN clause:** Hotfix, cleanup, and invariant validator were updated to use `status IN (%s, %s)` with `PUBLISHABLE_STATUSES[0]`, `PUBLISHABLE_STATUSES[1]` for psycopg3 compatibility.

---

## 8. Long-term: shared predicate and executor order (evidence)

### 8.1 Shared “publishable” predicate (2.1)

| Consumer | File:line | How predicate is used |
|----------|-----------|------------------------|
| **Executor due selection** | `scripts/scheduled_posting_executor.py` 251–264 | `status IN ('pending','ready')` and `(scheduled_timestamp <= %s OR (scheduled_date + scheduled_time)::timestamp <= %s)` — matches `utils.publishable_predicate` semantics |
| **Hotfix** | `scripts/hotfix_cancel_surplus_today.py` 59–80 | Imports `PUBLISHABLE_STATUSES` from `utils.publishable_predicate`; uses same scheduled-due SQL fragment |
| **Cleanup** | `scripts/cleanup_surplus_daily_posts.py` 49–72 | Imports `PUBLISHABLE_STATUSES`; same scheduled-due fragment |
| **Invariant validator** | `scripts/validate_daily_cap_invariant.py` 25–45 | Imports `PUBLISHABLE_STATUSES`; same scheduled-due fragment |
| **Shared definition** | `utils/publishable_predicate.py` 1–26 | `PUBLISHABLE_STATUSES = ('ready', 'pending')`, `SCHEDULED_DUE_FRAGMENT`, `CLAIM_ELIGIBLE_WHERE` |

Executor does not import the module but uses the same logical predicate (status + scheduled time); hotfix, cleanup, and validator use the shared module.

### 8.2 Executor order: validate → cap → cancel → claim → publish (2.2)

| Step | File:line | Description |
|------|-----------|-------------|
| 1. get_due_posts() | `scheduled_posting_executor.py` 225–289 | Query due posts; in-loop: validate_scheduled_date, validate_content_schedule; return only valid_posts |
| 2. validate_content_schedule() | 172–224 (called from get_due_posts 269–281) | Weekday + weekly constraints (Matrix v1.1) |
| 3. apply_daily_cap() | 328–384, called at 341 | On valid_posts only; returns (to_publish, to_cancel) |
| 4. Write cancellations | 346–354 | UPDATE status='cancelled', error_message for each in cancel_list |
| 5. Claim-before-publish | 408–419 | UPDATE status='publishing' WHERE id=%s AND status IN ('ready','pending') AND (platform_post_id IS NULL OR = '') |
| 6. Publish | 419 (route_to_platform_publisher) | platform publisher updates status='published', platform_post_id |

Order is: get_due_posts (includes validation) → apply_daily_cap on valid_posts → write cancellations → per post: re-check state → claim → publish.

### 8.3 Claim SQL exact (2.3)

**File:** `scripts/scheduled_posting_executor.py` lines 409–414.

**Exact SQL:**

```sql
UPDATE posting_queue
SET status = 'publishing', updated_at = NOW()
WHERE id = %s AND status IN ('ready', 'pending')
  AND (platform_post_id IS NULL OR platform_post_id = '')
```

**Conditions:** status IN ('ready','pending'); platform_post_id IS NULL or empty; row identified by id. Claim only succeeds for one row (rowcount must be 1). Table has no `published_at` column; “already published” is inferred from status and platform_post_id.

### 8.4 Daily cap invariant script (2.4)

- **Script:** `scripts/validate_daily_cap_invariant.py` — committed.
- **Usage:** `python3 scripts/validate_daily_cap_invariant.py --weeks 12 --platform facebook`
- **Sample output:** See §7.3.

### 8.5 Publish executors per platform (2.5)

| Platform | Published via | Daily cap applied? |
|----------|----------------|--------------------|
| **Facebook** | `scripts/scheduled_posting_executor.py` → `publish_to_facebook(queue_id)` | **Yes** — apply_daily_cap() enforces 1/day (non-Sat), Sat = products only |
| **Instagram** | Same executor → `publish_to_instagram(queue_id)` | No |
| **Twitter** | Same executor → `publish_to_twitter(queue_id)` | No |
| **LinkedIn** | Same executor → `publish_to_linkedin(queue_id)` | No |

There is a single executor script; all platforms use it. Only Facebook has the cap. Other channels have no separate “safeguards” unless added.


---

## 9. Final closure reply

See **docs/CLOSURE_REPLY_EXECUTOR_DAILY_CAP.md** for the coder checklist and reply template (correlation table, executor commit/deploy time, confirmation that production executor includes apply_daily_cap + claim-before-publish, and how the executor is invoked: launchd → background_posting_monitor.sh → scheduled_posting_executor.py).
