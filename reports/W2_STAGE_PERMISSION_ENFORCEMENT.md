# W2 Stage Permission Enforcement — Phase 2 Report

**Instruction Set 12 — Phase 2 complete.**  
Stage-as-permission: deterministic ordering, explicit min_stage gating at automation entry points, no stage mutation by automation, no new stage names.

---

## A) Stage order proof

Single canonical definition:

```text
$ rg -n "STAGE_ORDER" .
./utils/posts/stage_order.py
  6:STAGE_ORDER = [
  18:    """Return 0-based index of stage in STAGE_ORDER. Unknown stage returns 0."""
  20:        return STAGE_ORDER.index(stage)

./utils/posts/early_stage.py
  12:from utils.posts.stage_order import STAGE_ORDER, stage_index
  34:    if col and str(col).strip() in STAGE_ORDER:
  147:    if idx >= len(STAGE_ORDER) - 1:
  150:    next_stage = STAGE_ORDER[idx + 1]

./utils/posts/workflow_stage.py
  352:    from utils.posts.stage_order import STAGE_ORDER, stage_index
  355:    if idx >= len(STAGE_ORDER) - 1:
  357:    return STAGE_ORDER[idx + 1]

./utils/automation/calendar_driver.py
  13:from utils.posts.stage_order import STAGE_ORDER, stage_index
```

**Only one definition** of the canonical authoring stage order: `utils/posts/stage_order.py` (lines 6–14). All other files import `STAGE_ORDER` and `stage_index` from that module.  
Note: `blueprints/workflow_navigation.py` has `_STAGE_ORDER` for pipeline UI (planning, research, authoring, imaging, header); that is navbar/pipeline stage names, not the canonical `post.workflow_stage` order.

---

## B) Automation inventory table

| Automation | File | Function | Writes | min_stage | Previously gated? |
|------------|------|----------|--------|-----------|--------------------|
| execute-substage (planning: topic_brainstorming) | automation_core.py | execute_substage | ideas, post_development | ideas | No (gate added in Phase 2) |
| execute-substage (planning: section_structure) | automation_core.py | execute_substage | section_structure, post_section | ideas | No |
| execute-substage (planning: topic_allocation) | automation_core.py | execute_substage | topic_allocation, post_development | structure | No |
| execute-substage (planning: section_titling) | automation_core.py | execute_substage | section headings | structure | No |
| execute-substage (authoring: author_first_drafts) | automation_core.py | execute_substage → automation_execute | post_section.draft | titling | Yes (require_workflow_stage authoring) |
| execute-substage (authoring: image_concepts) | automation_core.py | execute_substage → automation_execute | post_section.image_concepts | authoring | Yes (require_workflow_stage imaging) |
| execute-substage (authoring: image_prompts) | automation_core.py | execute_substage → automation_execute | post_section.image_prompts | authoring | Yes |
| execute-substage (authoring: image_captions) | automation_core.py | execute_substage → automation_execute | post_section.image_captions | authoring | Yes |
| execute-substage (content: format_for_facebook, add_*, generate_caption) | automation_core.py | execute_substage → automation_execute | queue/caption content | authoring | Varies |
| execute-substage (imaging: optimize_for_facebook) | automation_core.py | execute_substage → automation_execute | images | imaging | Yes |
| execute-substage (publish: publish_to_facebook) | automation_core.py | execute_substage | (disabled) | review | Yes |
| start-automation | automation_settings.py | start_automation | post.status → in_process | imaging | Yes (stage_blocked) |

All automation entry points are either:

- **execute_substage** (single route): gated at top of handler with `AUTOMATION_MIN_STAGE` / `AUTOMATION_MIN_STAGE_BY_STAGE`; uses `stage_index(current_stage) < stage_index(min_stage)` → 403.
- **start_automation**: gated with `stage_index(current) < stage_index("imaging")` → 403.

---

## C) Gating diff summary

| File | Change |
|------|--------|
| **utils/posts/stage_order.py** | New module: `STAGE_ORDER` list and `stage_index(stage)` (return 0 on unknown). |
| **utils/posts/early_stage.py** | Removed local `EARLY_STAGES` and `_stage_index`. Import and use `STAGE_ORDER`, `stage_index` from `stage_order`. |
| **utils/automation/calendar_driver.py** | Removed local `STAGE_ORDER`. Import from `utils.posts.stage_order`; use `stage_index(stage)` for sort order. |
| **utils/posts/workflow_stage.py** | `get_next_advanceable_stage` now uses `stage_order.STAGE_ORDER` and `stage_index`. |
| **blueprints/automation_core.py** | Added `AUTOMATION_MIN_STAGE` and `AUTOMATION_MIN_STAGE_BY_STAGE`. At top of `execute_substage`, after `post_id` check: get `min_stage` for (stage, substage) or stage; if `stage_index(current_stage) < stage_index(min_stage)` return 403 with `"Stage {MIN_STAGE} required to run this operation."`. |
| **blueprints/automation_settings.py** | start_automation gate now uses `stage_index(current) < stage_index("imaging")` and returns 403 with same-style error. |
| **blueprints/core.py** | Governance block_reason "stage_blocked" now uses `stage_index(stage) < stage_index("imaging")` (canonical only). |

No automation code path mutates `post.workflow_stage`; Phase 1 no-ops remain.

---

## D) Proof of blocking

**Request:** Post 729 is at canonical stage **structure**. Authoring substage **author_first_drafts** requires **titling** (min_stage).

```bash
curl -X POST http://localhost:5000/launchpad/one-click-publication/api/execute-substage/authoring/author_first_drafts \
     -H "Content-Type: application/json" \
     -d '{"post_id":729}'
```

**Actual output:**

```json
{
  "current_stage": "structure",
  "error": "Stage TITLING required to run this operation.",
  "required_stage": "titling",
  "success": false
}
```

HTTP status: **403**. No stage mutation; error message matches the required format.

---

## E) Proof no stage mutation

```text
$ rg -n "set_workflow_stage|update.*workflow_stage|advance_post_stage" .
./utils/posts/workflow_stage.py
  4:Stage mutation is ONLY via POST /api/posts/<id>/advance-stage (early_stage.advance_post_stage).
  272:def set_workflow_stage(
  282:    logger.debug("W2: set_workflow_stage is deprecated (no-op); ...")
  300:    W2 Phase 1: Stage advances only via advance_post_stage; this is advisory.

./utils/posts/early_stage.py
  4:Stage only advances when user explicitly calls advance_post_stage ...
  139:def advance_post_stage(post_id: int) -> ...

./blueprints/posts.py
  861:        from utils.posts.early_stage import advance_post_stage
  862:        ok, err, new_stage = advance_post_stage(post_id)
```

- **advance_post_stage** is the only function that writes to `post.workflow_stage` (in `early_stage.py`, single `UPDATE post SET workflow_stage = %s ...`).
- It is invoked only from **blueprints/posts.py** in **api_advance_early_stage**, which serves **POST /api/posts/<id>/advance-stage**.
- **set_workflow_stage** is a documented no-op (no DB write). No other code path updates workflow_stage.

---

## F) Final statement

**“All automation entry points are explicitly gated by canonical stage. No automation mutates stage. No automation auto-runs on page load or stage change.”**

---

## Silent automation audit (4)

Searches for `DOMContentLoaded`, `onload`, `after_save`, `post_save`, `on_stage_change`:

- **DOMContentLoaded**: Used only for UI init (load panels, bind events). No call to execute-substage or start-automation on load.
- **execute-substage** and **start-automation** are invoked from `static/js/launchpad/automation-engine.js` and `static/js/home_governance.js` in response to user actions (e.g. Run, Start automation), not on page load or stage change.
- No automation triggered inside save handlers or during publishing (Phase 1 already removed stage write on publish).

No silent automation was found; none removed in this phase.

---

**Phase 2 complete. Stopping for approval before Phase 3.**
