# Deliverable D — Backfill script and command

**Step 5:** Script that, for a given ISO week, reassigns Facebook items to Matrix v1 weekdays and updates config.

---

## Script path

`scripts/backfill_matrix_v1_week.py`

---

## Exact command for week 2026-W5

```bash
python3 scripts/backfill_matrix_v1_week.py --week 2026-W5
```

Dry-run (no DB changes):

```bash
python3 scripts/backfill_matrix_v1_week.py --week 2026-W5 --dry-run
```

---

## What the script does

1. **Messages on Saturday** in that week → `scheduled_date` set to Wednesday of that week, `scheduled_timestamp` updated, `role = 'REASSURANCE'`.
2. **Products on Tue/Thu (or any non-Saturday)** in that week → `scheduled_date` set to Saturday of that week, `scheduled_timestamp` and `scheduled_time` preserved where possible, `role = 'COMMERCE'`.
3. **post_type_channel_config** → `publication_day = 3` for `channel = 'facebook'` and `post_type = 'message'`.

It does **not** create missing Wed message or Fri authority posts (creation of new rows is left to the normal creators / future authority_short creator).

---

## Before/after SQL (same as Step 1)

Use the same query as in Step 1 to compare before and after:

```sql
SELECT id, platform, role, content_type, status,
       scheduled_date, scheduled_time, rota_year, rota_week,
       topic_id, angle_id
FROM posting_queue
WHERE platform = 'facebook'
  AND scheduled_date BETWEEN '2026-01-26' AND '2026-02-01'
ORDER BY scheduled_date, scheduled_time, id;
```

Or run the Step 1 script before and after:

```bash
python3 scripts/step1_matrix_ground_truth.py --week 2026-W5
```
