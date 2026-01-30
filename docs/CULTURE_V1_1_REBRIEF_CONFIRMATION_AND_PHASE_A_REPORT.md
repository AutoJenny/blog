# Re-brief confirmation and CULTURE v1.1 Phase A report

**Date:** 2026-01-29  
**Context:** Re-anchor after chat interruption; execution refactor signed off; Phase A = schema + migrations only.

---

## 1. Execution refactor — confirmation (frozen)

### 1.1 No changes were made to

- **Matrix logic** — Not touched. Execution refactor only changed: `scheduled_posting_executor.py` (bug fix + existing logic), `posting_executor.py` (thin wrapper), `platform_publishers.py` (already existed), `automation_execute.execute_publish_to_facebook` (already deprecated), workflow scripts (already set status to `ready` only), `monitoring.py` (log entry), `background_posting_monitor.sh` (already called `scheduled_posting_executor.py`).
- **Schedule API selection** — Not touched.
- **Existing content generators** — Language (weekly_word/phrase/insult), AUTHORITY_SHORT, DEPTH_LONG / deep dive: no changes.
- **Schema** — No new tables or columns added by the execution refactor.

### 1.2 Execution refactor is backward-compatible with

- **`status='ready'`** — Workflows set status to `ready`; scheduler picks up `pending` and `ready`. Unchanged.
- **`scheduled_date` + `scheduled_time`** — Scheduler uses these (and `scheduled_timestamp`) for due-post selection and failsafe validation. Unchanged.
- **Facebook publishing** — All Facebook publishing goes through `utils.platform_publishers.publish_to_facebook(queue_id)`. Unchanged.

**Conclusion:** Execution is out of scope going forward unless there is a concrete failure.

---

## 2. CULTURE v1.1 Phase A — scope and status

**Phase A scope (per re-brief):** Schema + library implementation only. Migration(s) only — no generators yet. Report back for approval before Phase B.

### 2.1 What “schema done” means (acceptance checklist)

| Item | Status |
|------|--------|
| Table `culture_library` exists with: `id`, `category`, `title`, `body_text`, `source_note`, `active`, `created_at` | ✅ Migration present |
| Indexes on `culture_library` for selection (e.g. `active`, `category`) | ✅ In migration |
| Column `posting_queue.culture_library_id` (nullable FK → `culture_library.id`, ON DELETE SET NULL) | ✅ Migration present |
| Index on `posting_queue.culture_library_id` for 90-day queries | ✅ In migration |
| No generators, no creator scripts, no schedule API changes in Phase A | ✅ See 2.2 |

### 2.2 Migrations in repo (Phase A deliverables)

1. **`migrations/20260204_create_culture_library.sql`**
   - Creates `culture_library` with: `id` (SERIAL PK), `category` (VARCHAR 100), `title` (VARCHAR 500 NOT NULL), `body_text` (TEXT NOT NULL), `source_note` (TEXT), `active` (BOOLEAN NOT NULL DEFAULT TRUE), `created_at` (TIMESTAMP DEFAULT NOW()).
   - Indexes: `idx_culture_library_active`, `idx_culture_library_category`.
   - Table/column comments describe CULTURE v1.1 and 90-day use.

2. **`migrations/20260204_add_culture_library_id_to_posting_queue.sql`**
   - Adds `posting_queue.culture_library_id` INTEGER REFERENCES `culture_library(id)` ON DELETE SET NULL.
   - Index: `idx_posting_queue_culture_library_id` (partial WHERE `culture_library_id IS NOT NULL`).
   - Column comment describes use for Mon/Thu CULTURE and 90-day repeat avoidance.

**Run order:** Run `20260204_create_culture_library.sql` first, then `20260204_add_culture_library_id_to_posting_queue.sql`.

### 2.3 Phase B–related code already in repo

The following exist in the codebase; they are **out of Phase A scope** (generators/creators). Treat as Phase B until you explicitly approve:

- **`utils/content_roles/culture_generator.py`** — Culture selection/generator logic.
- **`scripts/automated_culture_creator.py`** — Creator script (e.g. Mon/Thu, weeks-ahead, dry-run).

Phase A report is **migrations only**. No changes to these files were made as part of this Phase A sign-off. Any further work on CULTURE v1.1 (selection logic, creators, schedule API surfacing Mon/Thu CULTURE) should be Phase B after your approval of Phase A.

### 2.4 Phase A summary

- **Done:** Schema + library table + migrations only (two migration files).
- **Not in Phase A:** Generators, creator scripts, schedule API changes, Tuesday language rotation changes.
- **Approval requested:** Confirm Phase A (schema + migrations) as complete so we can proceed to Phase B when you say so.

---

## 3. If anything is unclear

No ambiguity or implementation risk identified for:

- Execution refactor (frozen as above).
- Phase A scope (schema + migrations only; two migrations; no generators).

If you want a Phase A acceptance checklist in a different form (e.g. exact migration spec to run in production), or a short “Phase B scope” draft before any Phase B work, say how you’d like it and we’ll produce it.

---

---

## 4. Status (updated after approval)

- **Phase A:** Approved and treated as complete (schema + migrations only). No further Phase A work.
- **Phase B:** Do not proceed until explicitly approved. Next step will be Phase B scope sign-off.
