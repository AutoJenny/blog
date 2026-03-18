# Phase P1 — Matrix Pre-Generation Execution Report

**Date:** 2026-01-29  
**Status:** Implemented per execution brief.

---

## 1. Delivered

| Item | Delivered |
|------|-----------|
| Normalised creators (Mon–Sat) | Yes — culture, weekly_content, message_post, heritage, authority_short (unchanged), product_post |
| New Sunday depth_long creator | Yes — `scripts/automated_depth_long_creator.py` |
| pregenerate_matrix.py | Yes — `scripts/pregenerate_matrix.py` |
| DB partial unique index migrations | Yes — `migrations/20260129_p1_one_row_per_slot_unique_indexes.sql` |
| CHANGELOG + docs | Yes — CHANGELOG entry; this report |

---

## 2. Creator behaviour (P1.1)

- **One slot = one row:** Each creator SELECTs the single row for (platform, slot, scheduled_date); if none, INSERT skeleton then fill; if valid, SKIP; if failed/empty/placeholder, UPDATE same row. No duplicate inserts.
- **Valid:** generated_content non-empty, not placeholder text, status ∈ (ready, approved, scheduled, published) [and for depth_long also 'generated'].
- **Regeneration:** Monday/Thursday — new library pick, UPDATE; Tuesday — UPDATE idea_id/content; Wednesday — next message in CSV, UPDATE; Friday — existing generator, UPDATE; Saturday — re-pick product, UPDATE product_id and status draft; Sunday — rota + DepthLongGenerator, UPDATE.

---

## 3. Orchestrator (P1.2)

- **Script:** `scripts/pregenerate_matrix.py`
- **Parameters:** --weeks-ahead (default 8, min 8), --platform (default facebook), --dry-run, --force, --report &lt;file&gt;
- **Order:** Mon → Tue → Wed → Thu → Fri → Sat → Sun
- **Output:** Per-script exit code and stdout; optional JSON report file.
- **Exit:** Non-zero if any creator script exited non-zero.

---

## 4. DB indexes

- Applied via `migrations/20260129_p1_one_row_per_slot_unique_indexes.sql`.
- Run migration before first full pre-generation pass. If duplicate rows exist for a slot, migration may fail; resolve duplicates first.

---

## 5. Verification (acceptance criteria)

- Run: `python3 scripts/pregenerate_matrix.py --weeks-ahead 12` (with migration applied and no duplicate rows).
- Re-run: same command; no duplicate rows; failed rows regenerated in place.
- Schedule API: one slot per day; no placeholders for future weeks (after creators have run).
- Executor: unchanged; publishes only valid rows.

---

## 6. References

- **Brief:** Phase P1 execution brief (locked).
- **Plan:** docs/PHASE_P1_LOCKED_PLAN.md
- **Migration:** migrations/20260129_p1_one_row_per_slot_unique_indexes.sql
