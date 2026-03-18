# Phase C2 Execution Report

**Date executed:** 2026-01-29  
**Executed by:** Automated execution (Phase C2 Execution Brief).  
**Scope:** Cleanup (data hygiene) + prevention (partial unique index).

---

## 1. What was executed

### 1.1 Cleanup (data hygiene)

1. **Export affected IDs (no updates)**  
   - Script: `scripts/phase_c2_queue_cleanup.py` (run with `--dry-run` then without).  
   - Exported IDs to CSV before any UPDATE.

2. **Cancellations**  
   - **Non-Tuesday Facebook language** (status IN ('ready','pending')): set `status = 'cancelled'`, `error_message = 'Phase C2: non-Tuesday language row neutralised'`.  
   - **Duplicate product rows** (all but min(id) per group): set `status = 'cancelled'`, `error_message = 'Phase C2: duplicate product row neutralised'`.  
   - No published rows were updated. CULTURE v1.1, AUTHORITY_SHORT, DEPTH_LONG were not touched.

### 1.2 Prevention (recurrence guard)

- **Migration:** `migrations/20260129_add_unique_facebook_language_queue.sql`  
- **Index created:** `idx_posting_queue_facebook_language_unique`  
- **Definition:** UNIQUE on `(platform, content_type, idea_id, scheduled_date)` WHERE `platform = 'facebook'` AND `content_type IN ('weekly_word','weekly_phrase','weekly_insult')` AND `idea_id IS NOT NULL` AND `scheduled_date IS NOT NULL`.

---

## 2. Counts before / after

### 2.1 Before (from `scripts/phase_c2_queue_hygiene_analysis.py`)

| Metric | Before |
|--------|--------|
| Non-Tuesday language rows (ready + pending) | 338 |
| Non-Tuesday language total (any status) | 359 |
| Duplicate language groups | 0 |
| Duplicate product groups (any status) | 2 |
| Duplicate product rows to cancel | 2 |
| Language rows ready/pending with scheduled time in past | 345 |

### 2.2 After cleanup and migration

| Metric | After |
|--------|--------|
| Non-Tuesday language (ready + pending) | **0** |
| Non-Tuesday language (cancelled) | 338 |
| Non-Tuesday language (published, untouched) | 21 |
| Duplicate product groups (ready/pending only) | **0** |
| Duplicate language groups (for index safety) | 0 |

### 2.3 Verification

- Re-ran `PYTHONPATH=. python3 scripts/phase_c2_queue_hygiene_analysis.py` after cleanup.  
- Confirmed: non-Tuesday language ready/pending = 0; duplicate product groups (publishable) = 0; Tuesday language and CULTURE/AUTHORITY/DEPTH unchanged.  
- After migration: duplicate-language query (GROUP BY ... HAVING COUNT(*) > 1) still returns 0 rows.

---

## 3. Exact SQL and script commands

### 3.1 Cleanup script

```bash
PYTHONPATH=. python3 scripts/phase_c2_queue_cleanup.py
```

The script:

1. Exports non-Tuesday language IDs (ready/pending) to `docs/PHASE_C2_AFFECTED_IDS_LANGUAGE_<date>.csv`.  
2. Exports duplicate product IDs (to cancel) to `docs/PHASE_C2_AFFECTED_IDS_PRODUCT_<date>.csv`.  
3. Runs:

```sql
UPDATE posting_queue
SET status = 'cancelled', error_message = 'Phase C2: non-Tuesday language row neutralised'
WHERE id = ANY(<language_ids>);

UPDATE posting_queue
SET status = 'cancelled', error_message = 'Phase C2: duplicate product row neutralised'
WHERE id = ANY(<product_ids>);
```

### 3.2 Migration (index)

**File:** `migrations/20260129_add_unique_facebook_language_queue.sql`

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_posting_queue_facebook_language_unique
ON posting_queue (platform, content_type, idea_id, scheduled_date)
WHERE platform = 'facebook'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  AND idea_id IS NOT NULL
  AND scheduled_date IS NOT NULL;
```

**Applied with:** Python `db_manager.get_connection()` and `cursor.execute(sql)` reading the migration file.

---

## 4. Affected IDs (artefacts)

| Artefact | Path | Row count |
|----------|------|-----------|
| Non-Tuesday language IDs cancelled | `docs/PHASE_C2_AFFECTED_IDS_LANGUAGE_20260129.csv` | 338 |
| Duplicate product IDs cancelled | `docs/PHASE_C2_AFFECTED_IDS_PRODUCT_20260129.csv` | 2 |

CSVs include header row. Language CSV columns: `id`, `content_type`, `idea_id`, `scheduled_date`, `status`. Product CSV columns: `id`, `product_id`, `scheduled_date`, `status`.

---

## 5. Rollback instructions

**Limitation:** Prior status was not stored per row. Rollback restores cancelled rows to `status = 'ready'` and clears `error_message`. If some rows were originally `pending` or (for product) `failed`, adjust manually after rollback.

### 5.1 Restore non-Tuesday language rows

Use the IDs from `docs/PHASE_C2_AFFECTED_IDS_LANGUAGE_20260129.csv` (column `id`). Example (replace with actual id list or use a temp table loaded from CSV):

```sql
UPDATE posting_queue
SET status = 'ready', error_message = NULL
WHERE id IN (
  -- paste ids from PHASE_C2_AFFECTED_IDS_LANGUAGE_20260129.csv column "id"
);
```

### 5.2 Restore duplicate product rows

The two product IDs cancelled were **598** and **624** (see CSV). They had `status = 'failed'` before cleanup. To restore exact prior state:

```sql
UPDATE posting_queue
SET status = 'failed', error_message = NULL
WHERE id IN (598, 624);
```

### 5.3 Remove the partial unique index (if rolling back prevention)

```sql
DROP INDEX IF EXISTS idx_posting_queue_facebook_language_unique;
```

Only drop the index if you are reverting the recurrence-prevention change. It does not affect the cancelled rows.

---

## 6. Confirmation

- **Nothing out of scope was touched:** No CULTURE v1.1, AUTHORITY_SHORT, or DEPTH_LONG rows were updated. No published rows were updated. Tuesday language and non-duplicate product rows were not modified.  
- **Cleanup:** 338 non-Tuesday language rows and 2 duplicate product rows were cancelled; IDs exported to CSVs before update.  
- **Prevention:** Partial unique index `idx_posting_queue_facebook_language_unique` created; duplicate-language query remains 0.
