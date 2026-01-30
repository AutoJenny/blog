# Phase C2 Report — Duplication Risk Elimination & Queue Hygiene

**Date:** 2026-01-29  
**Scope:** Analysis and proposal only. No cleanup executed, no constraints added.

---

## 1. Read-only SQL evidence

### 1.1 Duplicate queue rows (language)

**Definition:** Rows with the same `(platform, content_type, idea_id, scheduled_date)`.

**SQL:**
```sql
SELECT platform, content_type, idea_id, scheduled_date,
       COUNT(*) AS cnt,
       array_agg(id ORDER BY id) AS queue_ids
FROM posting_queue
WHERE platform = 'facebook'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  AND idea_id IS NOT NULL
  AND scheduled_date IS NOT NULL
GROUP BY platform, content_type, idea_id, scheduled_date
HAVING COUNT(*) > 1
ORDER BY cnt DESC;
```

**Result (run 2026-01-29):**  
- **Groups with duplicates:** 0  
- No duplicate language groups were found in the current database. Historical duplicate creation (see `docs/CRITICAL_DUPLICATE_POST_BUG.md`) may have been cleaned up or the current snapshot does not contain those rows.

---

### 1.2 Non-Tuesday language rows

**Definition:** Language rows (`weekly_word`, `weekly_phrase`, `weekly_insult`) with `scheduled_date` on any day other than Tuesday (ISO weekday 2).

**SQL:**
```sql
SELECT content_type, status, scheduled_date, COUNT(*) AS cnt
FROM posting_queue
WHERE platform = 'facebook'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  AND scheduled_date IS NOT NULL
  AND EXTRACT(ISODOW FROM scheduled_date) != 2
GROUP BY content_type, status, scheduled_date
ORDER BY scheduled_date, content_type, status;
```

**Result (run 2026-01-29):**

| Status    | Count |
|----------|-------|
| ready    | 337   |
| published| 21    |
| pending  | 1     |
| **Total**| **359** |

- **337 ready** and **1 pending** non-Tuesday language rows could theoretically be published if another path were to call `publish_to_facebook()` (Phase C1 disabled those paths; executor blocks non-Tuesday language). Neutralising them removes residual risk and queue clutter.
- **21 published** rows are historical; leaving them as-is (no delete, no status change) preserves audit trail.

---

### 1.3 Language rows “due” (scheduled time in the past)

**Definition:** Language rows with status `ready` or `pending` and `(scheduled_date + scheduled_time) < NOW()` — i.e. they would be selected as “due” by the executor’s SQL before weekday validation.

**SQL:**
```sql
SELECT COUNT(*) AS cnt
FROM posting_queue
WHERE platform = 'facebook'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  AND status IN ('ready', 'pending')
  AND scheduled_date IS NOT NULL
  AND scheduled_time IS NOT NULL
  AND (scheduled_date::date + scheduled_time::time)::timestamp < NOW();
```

**Result:** **345** rows.  
Almost all “due” language rows are non-Tuesday; the executor’s Matrix v1.1 validation blocks them. This confirms that cleanup (cancelling non-Tuesday language) aligns queue state with policy and avoids unnecessary processing.

---

### 1.4 Duplicate product rows

**Definition:** Rows with the same `(platform, content_type, product_id, scheduled_date)` for `content_type = 'product'`.

**SQL:**
```sql
SELECT platform, content_type, product_id, scheduled_date,
       COUNT(*) AS cnt, array_agg(id ORDER BY id) AS queue_ids
FROM posting_queue
WHERE platform = 'facebook'
  AND content_type = 'product'
  AND product_id IS NOT NULL
  AND scheduled_date IS NOT NULL
GROUP BY platform, content_type, product_id, scheduled_date
HAVING COUNT(*) > 1
ORDER BY cnt DESC;
```

**Result:**  
- **Groups with duplicates:** 2  
- **Total duplicate product rows (to neutralise):** 2  

Small but present; same duplication class as language (multiple rows, same logical content).

---

### 1.5 Risky patterns summary

| Pattern | Count | Risk |
|--------|-------|------|
| Duplicate language groups | 0 | None in current DB; prevention still needed. |
| Non-Tuesday language (ready/pending) | 338 | Executor blocks; other paths disabled in C1. Neutralising removes residual risk. |
| Non-Tuesday language (published) | 21 | Left as-is for audit. |
| “Due” language (past scheduled time) | 345 | Almost all non-Tuesday; blocked by executor. |
| Duplicate product rows | 2 | Could cause duplicate product posts if both published. |

---

### 1.6 Rows explicitly out of scope (do not touch)

**SQL:**
```sql
SELECT content_type, role, status, COUNT(*) AS cnt
FROM posting_queue
WHERE platform = 'facebook'
  AND (content_type = 'culture_fact' OR role IN ('AUTHORITY_SHORT', 'DEPTH_LONG'))
GROUP BY content_type, role, status
ORDER BY content_type, role, status;
```

**Result (run 2026-01-29):**  
- culture_fact: 0  
- authority_short (AUTHORITY_SHORT): draft 3, ready 1  
- depth_long (DEPTH_LONG): approved 1, generated 3, scheduled 2  

No CULTURE v1.1, AUTHORITY_SHORT, or DEPTH_LONG rows will be modified by the proposed cleanup.

---

## 2. Cleanup proposal (no execution)

### 2.1 What to neutralise

| Target | Action | Rationale |
|--------|--------|-----------|
| **Non-Tuesday language rows** (platform = 'facebook', content_type IN ('weekly_word','weekly_phrase','weekly_insult'), EXTRACT(ISODOW FROM scheduled_date) != 2) with status IN ('ready','pending') | **Cancel** (set `status = 'cancelled'`, optionally set `error_message` to a fixed string e.g. `'Phase C2: non-Tuesday language row neutralised'`) | They will never be valid under Matrix v1.1. Cancelling removes them from “due” queries and prevents any future path from publishing them. |
| **Duplicate product rows** | For each group with COUNT(*) > 1, keep one row (e.g. minimum `id`) and **cancel** the others (same as above). | Ensures one logical product post per (product_id, scheduled_date); prevents duplicate product posts. |

**Default: cancel, not delete.**  
- Preserves row for audit and rollback.  
- `status = 'cancelled'` is an existing value (see `utils/publication_status_resolver.py`, `blueprints/launchpad_old.py`).  
- No schema change required.

### 2.2 What not to touch

- **CULTURE v1.1:** Rows with `content_type = 'culture_fact'` or role/content used for CULTURE Mon/Thu.  
- **AUTHORITY_SHORT:** Rows with `role = 'AUTHORITY_SHORT'` (or content_type `authority_short`).  
- **DEPTH_LONG:** Rows with `role = 'DEPTH_LONG'` or content_type `depth_long`.  
- **Published rows:** Do not change status of rows with `status = 'published'` (including the 21 published non-Tuesday language rows).  
- **Tuesday language rows:** Any language row with `scheduled_date` on Tuesday; leave as-is.  
- **Message, product (non-duplicate), and any content type not in the duplication or wrong-day scope above.**

### 2.3 Ordering and safety

- **Ordering:**  
  1. Cancel non-Tuesday language (ready/pending) in a single transaction (e.g. `UPDATE ... WHERE ... SET status = 'cancelled', error_message = '...'`).  
  2. For duplicate product groups, select the set of `id`s to cancel (all but min(id) per group), then `UPDATE ... WHERE id = ANY(...) SET status = 'cancelled', ...`.  
- **Currently scheduled valid posts:** Cleanup only affects (a) non-Tuesday language and (b) duplicate product rows. Tuesday language and single-copy product rows are untouched. Executor continues to pick only due, Matrix-valid rows.  
- **Reversibility:** If `status` is set to `'cancelled'` and `error_message` stored, rollback is “set status back to 'ready'/'pending' and clear error_message” for the same set of ids. A pre-cleanup snapshot of affected ids (or a backup) allows full audit and restore.

### 2.4 Rollback strategy

- Before running cleanup: persist the list of `id`s that will be updated (e.g. output of the SELECT that identifies them).  
- Rollback: `UPDATE posting_queue SET status = 'ready', error_message = NULL WHERE id = ANY(<saved_ids>)` (adjust status to original where known, or document “restore from backup” if needed).  
- All changes are status (+ optional error_message) only; no deletes.

---

## 3. Recurrence prevention recommendation

### 3.1 Recommended option: **Option A — Database constraint**

**Proposal:** Add a **partial unique index** on `posting_queue` so that for language rows, the same `(platform, content_type, idea_id, scheduled_date)` cannot appear more than once.

**Definition:**
- Index: `UNIQUE` on `(platform, content_type, idea_id, scheduled_date)`  
- **Partial:** `WHERE platform = 'facebook' AND content_type IN ('weekly_word','weekly_phrase','weekly_insult') AND idea_id IS NOT NULL AND scheduled_date IS NOT NULL`.

**Why it is sufficient:**  
- Prevents duplicate language rows at insert time regardless of which process or script inserts (creator, workflow, future code).  
- Single source of truth; no reliance on application logic or locking.  
- Fits the established duplication class from the audit and CRITICAL_DUPLICATE_POST_BUG.md.

**Edge cases and exclusions:**  
- **idea_id NULL:** Language rows should always have `idea_id` set by the creator; NULL would be a bug. The partial index excludes NULLs, so legacy or buggy rows without idea_id are not constrained (they remain a separate fix).  
- **Product duplicates:** Same pattern could be applied later with a separate partial unique index on `(platform, content_type, product_id, scheduled_date)` WHERE `content_type = 'product' AND product_id IS NOT NULL`. Not required for Phase C2 approval; can be added when product duplication is in scope.  
- **message / culture_fact / authority_short / depth_long:** No unique key of the form (platform, content_type, idea_id, scheduled_date) is mandated for these types; they are out of scope for this index.

**What it does not protect against:**  
- Duplicate posts caused by the same row being published twice (idempotency/race). Phase C1 and executor re-check (status, platform_post_id) address that.  
- Wrong-day language: the executor’s weekday validation (Phase C1) blocks that; the index does not enforce weekday.  
- Duplicates introduced by bulk load or direct SQL that bypasses the application (operational discipline).

### 3.2 Why Option B (creator-side transactional guard) was rejected

- **Option B** would be “check-then-insert” under a transaction/lock in the weekly content creator (and any other inserter).  
- **Rejected because:**  
  - Multiple code paths can create posting_queue rows (e.g. `automated_weekly_content_creator.py`, workflow in `automation_core.py`). Guarding only one path leaves others open.  
  - Requires every current and future inserter to use the same guard and locking; easy to miss in new code.  
  - Database constraint is simpler, global, and impossible to bypass from the application.

### 3.3 Summary

- **Recommendation:** Option A — partial unique index on `(platform, content_type, idea_id, scheduled_date)` for Facebook language rows.  
- **Implement only after approval;** no migration or index creation has been run as part of Phase C2 analysis.

---

## 4. Required status statement

**No data has been modified and no cleanup has been executed as part of Phase C2 analysis.**

---

## 5. Supporting artefacts

- **Read-only analysis script:** `scripts/phase_c2_queue_hygiene_analysis.py`  
  Run locally: `PYTHONPATH=. python3 scripts/phase_c2_queue_hygiene_analysis.py`  
  It runs only SELECTs and prints the summaries above; no UPDATE/INSERT/DELETE.

### 5.1 Proposed cleanup SQL (do not run until approved)

The following SQL is for reference only. **Do not execute until Phase C2 cleanup is explicitly approved.**

```sql
-- Phase C2 cleanup (READ FIRST)
-- 1. Non-Tuesday language: cancel ready/pending rows (do not touch published).
-- 2. Duplicate product: cancel all but one row per (platform, content_type, product_id, scheduled_date).
-- Reversibility: save the list of affected ids before running; rollback = set status back to 'ready' and clear error_message.

-- Step 0 (optional): Persist ids that will be updated, for rollback.
-- CREATE TEMP TABLE phase_c2_affected_ids AS
-- SELECT id FROM posting_queue WHERE ... (same predicates as below);

-- Step 1: Cancel non-Tuesday language (ready/pending only)
UPDATE posting_queue
SET status = 'cancelled',
    error_message = 'Phase C2: non-Tuesday language row neutralised'
WHERE platform = 'facebook'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  AND scheduled_date IS NOT NULL
  AND EXTRACT(ISODOW FROM scheduled_date) != 2
  AND status IN ('ready', 'pending');

-- Step 2: Cancel duplicate product rows (keep min(id) per group)
-- First, identify ids to cancel (all but min(id) per platform, content_type, product_id, scheduled_date)
UPDATE posting_queue
SET status = 'cancelled',
    error_message = 'Phase C2: duplicate product row neutralised'
WHERE id IN (
  SELECT id FROM (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY platform, content_type, product_id, scheduled_date ORDER BY id) AS rn
    FROM posting_queue
    WHERE platform = 'facebook'
      AND content_type = 'product'
      AND product_id IS NOT NULL
      AND scheduled_date IS NOT NULL
  ) sub
  WHERE rn > 1
);
```
