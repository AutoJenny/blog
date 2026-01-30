# P1 Duplicate Resolve: DELETE Behaviour and Rollback

## What `--resolve` does

**Confirmed: `--resolve` performs DELETE, not UPDATE to cancelled.**

In `scripts/p1_duplicate_scan_and_migrate.py`, the `resolve_duplicates()` function:

1. For each duplicate slot group, chooses one row to **keep** (prefer status ∈ ready/approved/scheduled/published, else highest `id`).
2. **Deletes** all other rows in that group with:
   ```python
   cursor.execute("DELETE FROM posting_queue WHERE id = %s", (id,))
   ```
3. Commits.

So duplicate slot rows are **permanently removed** from `posting_queue`. There is no `status = 'cancelled'` path; the rollback story relies on backups or archives, not on flipping status.

## Rollback

- **At run time (2026-01-29):** No CSV ID archive of the 490 deleted row IDs was written by the script. Restore is only possible from:
  - A **database backup** (e.g. `pg_dump`) taken before `--resolve`, or
  - Any **application-level backup** (e.g. exports of `posting_queue`) that includes those rows.
- **Future runs:** Before running `--resolve` again (e.g. after a future duplicate scan), operators should:
  1. Take a DB backup or at least export the duplicate group IDs (e.g. `--scan-only` output plus a query for those ids).
  2. Optionally extend the script to write a CSV of deleted ids (e.g. `--resolve --archive-deleted ids_deleted_YYYYMMDD.csv`) for audit/rollback.

## Policy note

Earlier policy was “cancel, don’t delete.” This script deliberately uses DELETE to satisfy the unique index (duplicate rows must be gone before the migration). If you want “cancel only” in future, the script would need to be changed to `UPDATE posting_queue SET status = 'cancelled', ... WHERE id IN (...)` and the migration would need to exclude cancelled rows in its partial unique index predicates (e.g. `AND status != 'cancelled'`), which is a larger design change.
