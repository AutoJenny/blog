# Workflow Stage Model

**Date:** 2026-02-23  
**Status:** Implemented (W2-FIX-5, W2-FIX-6)  
**Source:** `utils/posts/workflow_stage.py`

---

## Overview

The workflow stage model enforces strict internal progression inside `status=draft`. Each post has a `workflow_stage` persisted in `post.extra_settings`, which gates which routes (planning, authoring, imaging, launchpad, publish) the user can access.

---

## Stage Flow

```
idea → structured → drafted → imaged → essentials_complete → ready → published
```

| Stage | Criteria to hold | Route gates that allow |
|-------|------------------|------------------------|
| **idea** | Base stage (new post) | planning |
| **structured** | section_structure, topic_allocation, sections | planning |
| **drafted** | All sections have non-empty draft | planning, authoring |
| **imaged** | All sections have image | authoring, imaging |
| **essentials_complete** | title/idea_seed, subtitle, header image | imaging, launchpad_essentials, publish |
| **ready** | status=in_process, preflight OK | publish |
| **published** | status=published | publish |

---

## Persistence

- **Location:** `post.extra_settings.workflow_stage`
- **Timestamp:** `post.extra_settings.workflow_stage_updated_at`
- **Merge:** Other keys in `extra_settings` (e.g. `paused`, `imaging`) are preserved

---

## Integrity (W2-FIX-6)

- **validate_workflow_stage(post_id):** Re-evaluates criteria; downgrades to highest valid stage if current criteria no longer met.
- **Downgrade chain:** published → ready → essentials_complete → imaged → drafted → structured → idea
- **Triggers:** Before gated routes (via get_workflow_stage), before publish, after section save, after essentials save
- **Logging:** Downgrades logged with post_id, old_stage, new_stage, reason

---

## Route Gates

| Route group | Allowed stages | Override |
|-------------|----------------|----------|
| planning | idea, structured | `?override=1` |
| authoring | structured, drafted | `?override=1` |
| imaging | drafted, imaged | `?override=1` |
| launchpad_essentials | imaged, essentials_complete | `?override=1` |
| publish | essentials_complete, ready, published | `?override=1` |

When blocked: HTTP 403 with `{ stage_blocked: true, current_stage, required_stage, message }`.

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/posts/<id>/workflow-stage` | Get current stage + next_advanceable |
| POST | `/posts/<id>/advance-stage` | Advance to target_stage (JSON: `{ target_stage }`) |

---

## Key Functions

| Function | Purpose |
|----------|---------|
| `get_workflow_stage(post_id, validate=True)` | Get stage; validate corrects drift |
| `validate_workflow_stage(post_id)` | Re-evaluate and downgrade if needed |
| `set_workflow_stage(post_id, stage)` | Persist stage |
| `advance_stage(post_id, target_stage)` | Transition if allowed |
| `require_workflow_stage(post_id, route_group)` | Gate check for routes |

---

## Automation Convergence (W2-FIX-7)

One-Click Publication execute substages (author_first_drafts, image_concepts, image_prompts, image_captions) are gated by authoring/imaging route groups. Per-stage toggles in `post.extra_settings.automation.stage_enabled` can disable automation for specific stages. `start_automation` requires workflow_stage >= essentials_complete and preflight OK. See `reports/W2-FIX-7_AUTOMATION_CONVERGENCE_IMPLEMENTATION_REPORT.md`.

---

## Related

- `docs/ARCHITECTURE_V2_OVERVIEW.md` — Layered architecture and validation order
- `reports/W2-DESIGN-2_PERSISTED_WORKFLOW_STAGE_MODEL_SPECIFICATION.md` — Design
- `docs/POST_STATUS_MANAGEMENT.md` — Status (draft, in_process, published)
- `docs/workflow/status_transitions.md` — Status transition rules
- `utils/publishing/validators.py` — Preflight (essentials check)
