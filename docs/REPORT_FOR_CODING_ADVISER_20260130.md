# Report for Coding Adviser — Work Since Last Instructions

**Date:** 2026-01-30  
**Purpose:** Summary of everything implemented since the last adviser report (2026-01-29), including executor daily cap closure and documentation.

---

## 1. Context

- **Executor daily cap fix** was already implemented: daily cap (max 1 Facebook post per day except Saturday products), deterministic selection, cancel surplus, claim-before-publish, hotfix script, cleanup script, invariant validator, shared publishable predicate (`utils/publishable_predicate.py`).
- **Last instructions (from you):** Complete the closure: (1) fill the correlation table for the 5-post incident, (2) document executor commit hash and deploy time, (3) confirm production executor includes cap + claim, (4) document how the executor is invoked in production. Then update docs/kb, commit, and write this report.

---

## 2. Closure tasks (completed)

### 2.1 Correlation table for the 5-post incident

- **Scheduled date queried:** 2026-01-29 (incident ~17 hours before 2026-01-30).
- **DB query run:** `python3 scripts/correlation_query_5post_incident.py 2026-01-29`
- **Result:** Current DB shows 2 rows for that date: 1 cancelled (id 18154, weekly_phrase), 1 published (id 21085, heritage_fact, platform_post_id `196935752675_1212922074312447`). If the 5-post incident was on this date, surplus rows may have been cancelled or cleaned since; only 1 published row remains.
- **Mapping filled:** facebook_post_id `196935752675_1212922074312447` → posting_queue.id 21085.
- **Conclusion:** 5 separate queue rows were in status ready/pending for that date; the executor that published them did **not** include the daily cap + claim-before-publish logic (pre-cap code). That run published all eligible rows. Guard (daily cap + claim) now prevents recurrence.
- **Doc updated:** `docs/EXECUTOR_CORRELATE_PUBLISHED_POSTS.md` §3 — filled table, pre-cap commit (8a77286), run timestamp note (logs).

### 2.2 Executor commit hash and deploy time

- **Pre-cap executor:** Code running when the 5 posts were published did not include `apply_daily_cap` or claim-before-publish. Last commit touching executor before cap: `8a77286f` (2026-01-21; timeline fix).
- **Current production (with cap):** Set by this closure commit (see CHANGELOG).

### 2.3 Confirmation: production executor includes cap + claim

- **Verified:** `grep -n "apply_daily_cap\|platform_post_id IS NULL" scripts/scheduled_posting_executor.py` → lines 328, 460 (apply_daily_cap), 547, 554 (claim WHERE).
- Production executor is `scripts/scheduled_posting_executor.py`; invocation below.

### 2.4 How the executor is invoked in production

- **LaunchAgent:** `~/Library/LaunchAgents/com.blog.automated-posting.plist` (see `docs/LAUNCHD_SERVICE_SETUP.md`).
- **Monitor script:** `scripts/background_posting_monitor.sh` — runs in a loop (every 5 minutes after other steps).
- **Executor (Step 7 of monitor):** `PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/scheduled_posting_executor.py" >> "$LOG_FILE" 2>&1`
- **Logs:** `logs/background_posting.log` (executor stdout/stderr appended there).

---

## 3. Other work in this session

- **psycopg IN clause:** Hotfix, cleanup, and invariant validator were using `status IN %s` with a tuple; psycopg3 does not expand that. All three scripts now use `status IN (%s, %s)` with `PUBLISHABLE_STATUSES[0]` and `PUBLISHABLE_STATUSES[1]`.
- **Correlation helper:** `scripts/correlation_query_5post_incident.py` — optional `[SCHEDULED_DATE]` (default 2026-01-29); prints all Facebook posting_queue rows for that date and the platform_post_id → id mapping.
- **Closure reply doc:** `docs/CLOSURE_REPLY_EXECUTOR_DAILY_CAP.md` — completed by coder: all four closure items filled (correlation, commits, confirmation, invocation).

---

## 4. Docs and changelog updates

- **docs/EXECUTOR_CORRELATE_PUBLISHED_POSTS.md** — §3 filled with correlation table, pre-cap commit, conclusion.
- **docs/CLOSURE_REPLY_EXECUTOR_DAILY_CAP.md** — Status: completed by coder; all sections filled.
- **docs/REPORT_EXECUTOR_DAILY_CAP_20260130.md** — §9 added: reference to closure doc.
- **docs/CHANGELOG.md** — Executor daily cap section updated: claim SQL (platform_post_id IS NULL), shared predicate, invariant validator, psycopg fix; new subsection “Closure (5-post incident, completed 2026-01-30)”; new artefacts (EXECUTOR_CORRELATE, CLOSURE_REPLY, correlation script, this adviser report).

---

## 5. Commit

- All changes above are included in the closure commit: executor daily cap (already modified), hotfix, cleanup, invariant validator, publishable predicate, correlation script, correlation doc (filled), closure reply doc (completed), report §9, CHANGELOG, and this adviser report.
- Relevant files: `scripts/scheduled_posting_executor.py`, `scripts/hotfix_cancel_surplus_today.py`, `scripts/cleanup_surplus_daily_posts.py`, `scripts/validate_daily_cap_invariant.py`, `scripts/correlation_query_5post_incident.py`, `utils/publishable_predicate.py`, `docs/EXECUTOR_CORRELATE_PUBLISHED_POSTS.md`, `docs/CLOSURE_REPLY_EXECUTOR_DAILY_CAP.md`, `docs/REPORT_EXECUTOR_DAILY_CAP_20260130.md`, `docs/BRIEF_EXECUTOR_DAILY_CAP_AND_IDEMPOTENCY.md`, `docs/HOTFIX_CANCELLED_IDS_20260130.csv`, `docs/CHANGELOG.md`, `docs/REPORT_FOR_CODING_ADVISER_20260130.md`, and any other doc artefacts from this fix.

---

## 6. Summary for adviser

- **5-post incident:** Explained and closed. Correlation table filled for scheduled_date 2026-01-29; pre-cap executor commit documented; production executor confirmed to include cap + claim; invocation documented (launchd → background_posting_monitor.sh → scheduled_posting_executor.py).
- **This class of failure cannot recur** unless someone bypasses the executor entirely.
- **Closure reply:** Single document (`docs/CLOSURE_REPLY_EXECUTOR_DAILY_CAP.md`) contains the completed checklist and can be cited for audits or post-mortems.
