# W2 Stage Canonical Freeze — Phase 1 Report

**Instruction Set 11 — Phase 1 complete.**  
Canonical read/write freeze: `post.workflow_stage` is the only source of truth for authoring stage. No playbooks or automation logic changed yet.

---

## 1. Grep proof

### Before Phase 1 (summary)

- **Reads of legacy:** `core.py` selected `p.extra_settings->>'workflow_stage' AS workflow_stage_raw`; `calendar_driver.py` selected `COALESCE(p.extra_settings->>'workflow_stage', 'idea')`; `get_early_stage` fell back to `extra_settings.workflow_stage` when column missing; `get_workflow_stage` read and optionally inferred/persisted from `extra_settings`.
- **Writes:** `set_workflow_stage` wrote to `extra_settings.workflow_stage`; `ensure_workflow_stage_idea` and `advance_stage` called it; `launchpad/publishing.py` called `set_workflow_stage(post_id, 'published')` on publish.

### After Phase 1 (current)

Run: `rg -n "workflow_stage" .` (excluding reports and blog-core/ARCHIVED for brevity; main app only).

**Python (main app) — stage read/write and gates:**

| File | Line | Role |
|------|------|------|
| `utils/posts/early_stage.py` | 40, 48, 174 | **Only writer:** `advance_post_stage` updates `post.workflow_stage`. `get_canonical_stage` / `get_early_stage` read column only. |
| `utils/posts/workflow_stage.py` | 29, 263–265, 272–282, 286–288, 376–385 | **Gates + compat:** `require_workflow_stage` uses `get_canonical_stage` and `CANONICAL_ROUTE_GATES`. `get_workflow_stage` returns `get_canonical_stage(post_id)`. `set_workflow_stage`, `ensure_workflow_stage_idea`, `advance_stage` are no-ops (no DB write). |
| `blueprints/core.py` | 454, 740, 756–759 | **Read only:** SELECT `p.workflow_stage AS workflow_stage_raw`; slot uses it; governance uses `get_canonical_stage(post_id)`. |
| `blueprints/launchpad/publishing.py` | 53–54, 82–83, 109–110, 120–123, 413 | **Gates only:** `require_workflow_stage`, `validate_workflow_stage` (read-only). No stage write on publish. |
| `utils/automation/calendar_driver.py` | 95, 105, 109 | **Read only:** SELECT `p.workflow_stage`; `STAGE_ORDER` = canonical stages. |
| `blueprints/automation_settings.py` | 43–49 | **Read only:** `get_canonical_stage(post_id)` for start-automation gate. |
| `blueprints/posts.py` | 787–789, 803–825, 874–885 | **Single mutate path:** `api_advance_early_stage` → `advance_post_stage`. Legacy `api_advance_workflow_stage` and `ensure_workflow_stage_idea` are no-op. |
| Other blueprints | various | `require_workflow_stage` (gates) or `ensure_workflow_stage_idea` (no-op). |

**Before Phase 1 (summary of what was removed or changed):**

- **Reads removed/changed:** `extra_settings->>'workflow_stage'` in `core.py` (replaced by `p.workflow_stage`); same in `calendar_driver.py`; `get_early_stage` fallback to `extra_settings` (removed); `get_workflow_stage` no longer reads or writes `extra_settings`.
- **Writes removed:** `set_workflow_stage(post_id, 'published')` in `launchpad/publishing.py`; `set_workflow_stage` and `ensure_workflow_stage_idea` in `workflow_stage.py` (now no-op); `advance_stage` no longer calls `set_workflow_stage` (no-op).

---

## 2. List of removed read/write locations

### Read-path (legacy removed; now canonical only)

| File | Function / location | Change |
|------|----------------------|--------|
| `utils/posts/early_stage.py` | `get_early_stage` | Removed fallback to `extra_settings.workflow_stage`. Reads `post.workflow_stage` only. Added `get_canonical_stage` (column only). |
| `utils/posts/workflow_stage.py` | `get_workflow_stage` | Now returns `get_canonical_stage(post_id)`; no read of `extra_settings`. |
| `utils/posts/workflow_stage.py` | `require_workflow_stage` | Uses `get_canonical_stage(post_id)` and `CANONICAL_ROUTE_GATES` (canonical stage names). |
| `utils/posts/workflow_stage.py` | `validate_workflow_stage` | No longer reads or writes `extra_settings`; returns `get_canonical_stage(post_id)`, no persist. |
| `blueprints/core.py` | Governance SELECT | Replaced `p.extra_settings->>'workflow_stage'` with `p.workflow_stage AS workflow_stage_raw`. |
| `blueprints/core.py` | Slot block_reason | Replaced `get_workflow_stage` + legacy STAGES index with `get_canonical_stage(post_id)` and `allowed_for_automation = {'imaging', 'review'}`. |
| `blueprints/core.py` | Slot default | Default stage when missing changed from `'idea'` to `'metadata'`. |
| `blueprints/automation_settings.py` | Start-automation gate | Replaced `get_workflow_stage` + STAGES index with `get_canonical_stage(post_id)` and `allowed_for_start = {'imaging', 'review'}`. |
| `utils/automation/calendar_driver.py` | `get_posts_for_week` SELECT | Replaced `extra_settings->>'workflow_stage'` with `p.workflow_stage`; default `'idea'` → `'metadata'`; `STAGE_ORDER` = canonical list. |

### Write-path (removed or no-op)

| File | Function / location | Change |
|------|----------------------|--------|
| `utils/posts/workflow_stage.py` | `set_workflow_stage` | No-op; no write to `extra_settings` or `post.workflow_stage`. Logs debug. |
| `utils/posts/workflow_stage.py` | `ensure_workflow_stage_idea` | No-op. |
| `utils/posts/workflow_stage.py` | `advance_stage` | No-op; does not call `set_workflow_stage`. Returns `(True, None)`. |
| `utils/posts/workflow_stage.py` | `validate_workflow_stage` | No longer calls `set_workflow_stage`; no persist. |
| `blueprints/launchpad/publishing.py` | After successful publish | Removed `set_workflow_stage(post_id, 'published', actor='publish')`. |

Call sites of `ensure_workflow_stage_idea` (planning_api_posts, posts, automation_core, recipes, planning_api_profiles, planning_api_post_specific, content_generation_api) remain; the function is a no-op so no stage write occurs. New posts rely on DB default `workflow_stage = 'metadata'`.

---

## 3. Curl proof

```bash
curl -s http://localhost:5000/api/posts/729/early-stage | jq
```

**Result (post 729):**

```json
{
  "required_ideas_count": 3,
  "sections_count": 5,
  "success": true,
  "workflow_stage": "structure"
}
```

Stage is read from `post.workflow_stage` only (early_stage API uses `get_early_stage` → `get_canonical_stage`).

---

## 4. SQL proof

```sql
SELECT workflow_stage, COUNT(*) FROM post GROUP BY 1 ORDER BY 2 DESC;
```

**Result:**

```
 workflow_stage | count 
----------------+-------
 metadata       |    77
 structure      |     1
(2 rows)
```

Only canonical values (`metadata`, `ideas`, `structure`, `titling`, `authoring`, `imaging`, `review`) are allowed by the check constraint. No legacy values in the column.

---

## 5. Statement

**No code path outside advance-stage mutates `post.workflow_stage`.**

- The only code that writes to `post.workflow_stage` is `utils/posts/early_stage.py` → `advance_post_stage()`, which runs a single `UPDATE post SET workflow_stage = %s, ... WHERE id = %s`.
- That function is invoked only from `blueprints/posts.py` → `api_advance_early_stage()`, which is the handler for **POST /api/posts/<id>/advance-stage**.
- All other former writers (`set_workflow_stage`, `ensure_workflow_stage_idea`, `advance_stage`, publishing) are either removed or no-op and do not touch `post.workflow_stage` or `extra_settings.workflow_stage`.

---

## DB rule (1.3)

- **extra_settings.workflow_stage** is never written by any code path after this phase.
- It is not read for logic: all gates and UI use `post.workflow_stage` via `get_canonical_stage` / `get_early_stage`.
- It may remain in the table for migration/reference only.

---

**Phase 1 complete. Stopping for approval before Phase 2.**
