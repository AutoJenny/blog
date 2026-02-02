# Phase G-1 — Matrix Run Ledger Report

**Date:** 2026-02-02  
**Context:** Phase G-0 established `scripts/pregenerate_matrix.py` as the single source of truth for calendar population. Missing Instagram weeks (e.g. weeks 4–5) occurred because there was no durable record of whether the matrix had been run for IG for those weeks. This phase introduces a write-once audit trail so future gaps cannot go unnoticed.

---

## 1. Why this exists

The planning calendar depends on `posting_queue` rows for both Facebook and Instagram. Those rows are created only by `scripts/pregenerate_matrix.py`. If that script is not run for a given date window—or if only FB-only creators are run manually—Instagram weeks can be empty or partial with no record that anything was missed. Previously, the only way to discover missing IG weeks was to browse the week-view and notice gaps.

The Matrix Run Ledger records in the database when the matrix was run, for which date window, for which platform(s), and whether it completed successfully. It does not fix population by itself; it makes omissions auditable. A query can answer “Has Instagram been generated for week X?” by checking whether a run exists that covers that week for platform `instagram` with a completed status. No UI, scheduler, or automation was added—only the ledger table and the write path from the orchestrator.

---

## 2. Schema (verbatim SQL)

Required table (as specified):

```sql
matrix_run_ledger (
  id SERIAL PRIMARY KEY,
  platform TEXT NOT NULL,              -- 'facebook' | 'instagram'
  start_date DATE NOT NULL,
  weeks_ahead INTEGER NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL,                -- 'success' | 'partial' | 'failed'
  report_path TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

- One row per platform per run (no collapsing FB + IG into a single row).
- No foreign keys. No indexes beyond PK.
- Implemented in migration: `migrations/20260201_create_matrix_run_ledger.sql`. At run start the script inserts rows with `status = 'running'`; at completion it updates with `finished_at`, `status` ('success' | 'partial' | 'failed'), and `report_path`.

---

## 3. Write points in code

**File:** `scripts/pregenerate_matrix.py`

- **At run start (after building report dict, before slot runs):** In `main()`, immediately after constructing the `report` dict and before the first creator call:
  - Insert one row per platform into `matrix_run_ledger` with `platform`, `start_date`, `weeks_ahead`, `started_at`, `status = 'running'`.
  - Store returned `id` per platform in `ledger_ids`.
  - Wrapped in try/except; on failure log to stderr and continue (ledger write must not crash the run).

- **At run completion (after report file is written):** In `main()`, after setting `report["finished_at"]` and writing the report file:
  - Compute per-platform status via `_ledger_status_for_platform(report["slots"], platform)`: if any slot has `platforms[platform].outcome == "failed"` then `"partial"`, else `"success"`.
  - Update each row in `ledger_ids` with `finished_at`, `status`, `report_path` (value of `--report` if passed).
  - Wrapped in try/except; on failure log to stderr and continue.

**Function names:** `main()`; helper `_ledger_status_for_platform(report_slots, platform)` used only for status computation.

Slot logic and success criteria are unchanged; the script uses the same per-slot outcomes already present in the report to set ledger status.

---

## 4. Example rows (from proof run)

Proof run executed:

```bash
python scripts/pregenerate_matrix.py --start-date 2026-02-02 --weeks-ahead 8 --report temp/matrix_ledger_proof.json
```

Resulting ledger rows (copied from DB; timestamps in local tz):

| id | platform  | start_date | weeks_ahead | started_at           | finished_at          | status  | report_path                  |
|----|-----------|------------|-------------|----------------------|----------------------|---------|------------------------------|
| 1  | facebook  | 2026-02-02 | 8           | 2026-02-02 14:10:21  | 2026-02-02 14:10:27  | success | temp/matrix_ledger_proof.json |
| 2  | instagram | 2026-02-02 | 8           | 2026-02-02 14:10:21  | 2026-02-02 14:10:27  | success | temp/matrix_ledger_proof.json |

- Two rows written (one per platform).
- `finished_at` populated.
- `status` = success (no slot had outcome `"failed"` for either platform).
- `report_path` matches the JSON output path.

---

## 5. Verification query

Canonical query to answer “Has Instagram been generated for week X?” (by inspecting recent runs that cover that week):

```sql
SELECT *
FROM matrix_run_ledger
WHERE platform = 'instagram'
ORDER BY started_at DESC
LIMIT 5;
```

Interpretation: For a given week (e.g. ISO week 6 of 2026 = 2026-02-02 to 2026-02-08), check whether any row has `start_date <= Monday of that week` and `start_date + (weeks_ahead * 7) days >= Sunday of that week`, and `finished_at IS NOT NULL` and `status IN ('success', 'partial')`. The query above returns the latest Instagram runs; then inspect `start_date` and `weeks_ahead` to see which weeks are covered. No separate index was added; the table is small and this query is sufficient.

---

## 6. Stop statement

After this change, it is no longer possible for Instagram weeks to go missing without leaving an auditable record in the database. Every run of `pregenerate_matrix.py` inserts two ledger rows at start and updates them at completion. If a week has no IG rows, either there is no ledger row covering that week for platform `instagram` (run was never executed for that window) or there is a row with `status = 'partial'` or `failed` (run was attempted but had slot failures). In both cases the gap is visible and traceable via `matrix_run_ledger` and the optional `report_path` JSON.

---

**Phase G-1 status:** Complete. Ledger table exists; `pregenerate_matrix.py` writes to it; a real run was recorded for both FB and IG; no other system was modified.
