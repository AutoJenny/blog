# BRIEF: Fix “Multiple posts published in one day” (Facebook Matrix)

**Objective:** Ensure that, for Facebook, the system publishes exactly one post per day (Mon–Fri + Sun), with Saturday explicitly allowed to publish multiple COMMERCE/product posts. Today’s failure shows the executor published multiple eligible ready rows for the same day. This must be prevented at publish/executor layer, not just at creation time.

---

## A) Short-term containment (same day / next run safety)

### A1. Immediate stopgap: block multi-publish for today

**Goal:** Prevent further repeats today even if executor runs again.

1. Identify all Facebook rows for today that are publishable (status='ready' or 'pending', scheduled <= now).
2. Keep exactly one (the one you actually wanted to publish today).
3. Cancel the rest (do not delete):
   - Set `status='cancelled'`
   - Set `error_message = 'Hotfix: cancelled to enforce one-post-per-day cap (date=YYYY-MM-DD)'`
4. Capture and commit an artefact: `docs/HOTFIX_CANCELLED_IDS_YYYYMMDD.csv` containing: id, role, content_type, scheduled_date, scheduled_time, status_before, status_after.

**Report back:** Counts found and counts cancelled; IDs of kept row + cancelled rows; screenshot or text excerpt from DB query confirming only one ready row remains for today.

### A2. Temporary executor guard (fast, minimal change)

**Goal:** Even with legacy/dirty queue, executor must never publish >1 per day.

Implement a hard cap in the executor: for a given scheduled_date (today), publish at most one row (except Saturday products).

- After building the list of due posts, group by scheduled_date.
- For each date: if Saturday, allow multiple posts only where content_type='product'; otherwise select one row to publish and mark the others as blocked or cancelled.
- No behaviour changes to creators as part of the stopgap.

**Report back:** PR-style summary (files changed, function, logic); example log output showing the cap triggered and extra posts skipped/cancelled.

---

## B) Long-term fix (properly correct and auditable)

### B1. Invariant (publish-time truth)

**Core invariant (Facebook):** For each (platform='facebook', scheduled_date): publish max 1 row; exception: Saturday may publish N product posts, but no non-product posts should publish on Saturday.

**Secondary invariant:** Publishing must be idempotent: a row is claimed atomically before posting; re-runs do not publish the same row twice.

### B2. Daily cap + deterministic selection in the executor

- **Deterministic selection:** When multiple eligible rows exist for a non-Saturday date, choose exactly one. Priority order (highest first): AUTHORITY_SHORT → DEPTH_LONG → HERITAGE → CULTURE → message (REASSURANCE) → Tuesday language (weekly_*). Tie-break: lowest id.
- **Weekday validation:** Filter out anything that isn’t allowed for that weekday; then apply the daily cap.
- **Surplus:** Set status='cancelled', error_message='Executor cap: cancelled surplus eligible post for date YYYY-MM-DD; kept queue_id=<X>'.
- **Logging:** Log when >1 eligible exists for a date; which one is selected and why; how many cancelled as surplus. Counters: eligible_after_validation, published, cancelled_surplus, blocked_wrong_day.

### B3. Atomic claim-before-publish

1. In DB: `UPDATE posting_queue SET status='publishing', updated_at=NOW() WHERE id=<id> AND status IN ('ready','pending')`.
2. Check rowcount==1 before proceeding; if 0, skip (already claimed/published).
3. Only then call Facebook API.
4. On success: set status='published', platform_post_id, timestamps.
5. On failure: set status='failed', store error message.

### B4. Queue hygiene

- **One-time cleanup script:** `scripts/cleanup_surplus_daily_posts.py` — scans forward N weeks (default 12), detects days with >1 publishable Facebook row, keeps one per date (deterministic), cancels the rest, outputs `docs/CLEANUP_SURPLUS_POSTS_YYYYMMDD.csv`.
- **DB constraints:** Existing P1 slot unique indexes align with one row per slot; for non-product Facebook posts the partial unique indexes already enforce one per (platform, scheduled_date) per slot. Saturday products use (platform, scheduled_date, scheduled_time). No additional constraint required unless extending to other platforms.

---

## C) Acceptance tests

- **C1.** Reproduce prior failure state: show a day with >1 eligible ready rows (historical is fine).
- **C2.** Executor behaviour: run executor (dry-run); confirm it selects exactly one for non-Saturday, cancels surplus, logs selection rationale.
- **C3.** Saturday: confirm multiple product posts still publish (or are eligible); non-product does not publish on Saturday.
- **C4.** Idempotency: run twice quickly; ensure a single row is published once; second run sees it claimed/published and does not duplicate.
- **C5.** Schedule API: for 2–3 future weeks, schedule shows one per day (except Saturday multiple products); no placeholder titles for roles.

---

## D) Report-back (deliverables)

1. Summary of changes (files, main functions, selection priority rules).
2. Before/after evidence (DB query outputs, executor log excerpts).
3. Artefacts: CSV of cancelled IDs (today hotfix + cleanup script run); any new scripts.
4. Risk notes: edge cases; whether any other publish paths bypass executor (should remain disabled per Phase C1).

---

## E) Non-scope

- Do not change creators (unless required for compatibility).
- Do not change publish formatting, parity, or channel preview logic.
- Do not add new scheduling concepts (defer/reschedule) unless explicitly approved.
