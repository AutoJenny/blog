# Architecture V2 Overview — Governed Calendar-Driven Automation

**Date:** 2026-02-23  
**Status:** Phase complete (W2-FIX-5 → W2-FIX-9.2)  
**Scope:** Workflow stage, output readiness, calendar seed, week automation controls

---

## Layered Architecture (Text Diagram)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER / AUTOMATION ACTOR                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  WEEK LAYER (W2-FIX-9.2)                                                 │
│  calendar_week_controls: automation_enabled, locked                       │
│  • Locked week → automation refuses to modify (409 week_locked)          │
│  • Disabled week → automation skips (empty worklist)                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  POST LAYER                                                              │
│  • post.extra_settings.automation.enabled (W2-FIX-7)                     │
│  • post.extra_settings.automation.stage_enabled.{drafted,imaged}         │
│  • post.extra_settings.calendar_seed (W2-FIX-9.1)                         │
│  • post.extra_settings.workflow_stage (W2-FIX-5)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE GATE (W2-FIX-5, W2-FIX-6)                                         │
│  require_workflow_stage(post_id, route_group)                             │
│  • planning: idea, structured                                             │
│  • authoring: structured, drafted                                         │
│  • imaging: drafted, imaged                                                │
│  • launchpad_essentials: imaged, essentials_complete                      │
│  • publish: essentials_complete, ready, published                          │
│  Blocked → 403 stage_blocked                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OUTPUT READINESS (W2-FIX-8)                                              │
│  get_output_readiness(post_id, output_channel)                             │
│  • Checks substage completion for channel                                 │
│  • Purely diagnostic; does not modify stage                               │
│  Blocked → 409 output_blocked                                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PREFLIGHT (W2-FIX-4, validators)                                         │
│  validate_post_for_clan_publish(post_id)                                   │
│  • Title, summary, header image, meta, status                             │
│  Blocked → 400 with errors                                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STATUS TRANSITION (W2-FIX-4)                                             │
│  transition_post_status(post_id, target_status, actor)                     │
│  • draft → in_process → published                                          │
│  Blocked → 400/404                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Validation Order (Publish / Start Automation)

The exact sequence for output-producing actions:

| Step | Check | On failure |
|------|-------|------------|
| 1 | **workflow_stage gate** | 403 `stage_blocked` |
| 2 | **output_readiness check** | 409 `output_blocked` |
| 3 | **preflight validation** | 400 with errors |
| 4 | **status transition** | 400/404 |

---

## Automation Control Layers

| Layer | Control | Effect |
|-------|---------|--------|
| **Week** | `calendar_week_controls.automation_enabled` | False → skip week (empty worklist) |
| **Week** | `calendar_week_controls.locked` | True → 409 `week_locked` |
| **Post** | `post.extra_settings.automation.enabled` | False → 403 `automation_blocked` |
| **Post** | `post.extra_settings.automation.stage_enabled.{stage}` | False → 403 for that stage |
| **Post** | `post.extra_settings.calendar_seed` | Missing/mismatch → 409 `calendar_mismatch` (when target week provided) |

---

## Calendar-Driven Model Summary

- **Calendar seed** (`post.extra_settings.calendar_seed`): All posts have a seed (theme, recipe, weekly_*, or manual). Traceability for automation.
- **Week controls** (`calendar_week_controls`): Per-week automation on/off and lock.
- **Work selection** (`get_posts_for_week`): Automation selects posts from `calendar_week_items` and `calendar_seed`; ordered by workflow stage.
- **Orphan prevention**: `create_post_from_item` requires year+week for theme/weekly types.
- **Governance panel** (homepage): Modal showing current week’s scheduled content and **Blog Candidates** (ideas). One candidate can be selected (`is_selected`); **Start Blog Post** converts an idea to a draft and links it via the same week-item (no separate theme row). See `docs/page-reference/planning/governance-panel.md`.

---

## Actor Model

| Actor | Meaning |
|-------|---------|
| **user** | Human interacting via UI; can use override (?override=1) |
| **automation** | System-driven; sets actor='automation' in status/stage transitions |
| **system** | Internal (validate, migrate, backfill) |

---

## Block Types (User-Facing)

| Block | HTTP | Meaning |
|-------|------|---------|
| **Automation disabled** | 403 `automation_blocked` | Post or week has automation turned off |
| **Stage blocked** | 403 `stage_blocked` | Post has not reached the required workflow stage |
| **Output blocked** | 409 `output_blocked` | Output channel substage not complete (e.g. final_review) |
| **Week locked** | 409 `week_locked` | Week is locked; automation cannot modify posts |
| **Calendar mismatch** | 409 `calendar_mismatch` | Post’s calendar_seed does not match target week |

---

## Detailed Documentation

| Document | Scope |
|----------|-------|
| `docs/workflow/workflow_stage_model.md` | Stage flow, route gates, integrity |
| `docs/workflow/output_readiness_model.md` | Output channel validation |
| `docs/workflow/calendar_seed_model.md` | Calendar seed traceability |
| `docs/workflow/week_automation_controls.md` | Week controls, work selection |
| `docs/workflow/status_transitions.md` | Status transition rules |
| `docs/page-reference/planning/governance-panel.md` | Homepage Governance panel, blog candidates, convert flow |
| `docs/api/workflow_stage_api.md` | Workflow stage API |
| `docs/POST_STATUS_MANAGEMENT.md` | Status and reuse rules |

---

## Knowledge Base (User Guides)

| Document | Audience |
|----------|----------|
| `docs/kb/blog_post_workflow.md` | Stages and progression |
| `docs/kb/status_and_stage_guide.md` | Status/stage meanings, block types |
| `docs/kb/how_to_publish.md` | Publishing checklist |
