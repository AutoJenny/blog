# Output Readiness Model

**Date:** 2026-02-23  
**Status:** Implemented (W2-FIX-8)  
**Source:** `utils/posts/output_readiness.py`

---

## Overview

Output Readiness formalises substage/output-channel validation as an explicit, DB-backed, observable layer. It answers: *"Is this post ready to produce output for channel X?"* without modifying `workflow_stage`. It is purely diagnostic and used before One-Click execute, start_automation, and publish.

---

## Validation Order

The exact validation sequence for output-producing actions (publish, start_automation) is:

| Step | Check | On failure |
|------|-------|------------|
| 1 | **workflow_stage gate** | 403 `stage_blocked` |
| 2 | **output_readiness check** | 409 `output_blocked` |
| 3 | **preflight validation** | 400 with errors |
| 4 | **status transition** | 400/404 |

### Detailed Flow

1. **workflow_stage gate** — `require_workflow_stage(post_id, 'publish')` (or equivalent). Blocks if post has not reached the required stage.

2. **output_readiness check** — `get_output_readiness(post_id, output_channel)`. Blocks if the required substage for the output channel has not been completed (e.g. `final_review` for blog).

3. **preflight validation** — `validate_post_for_clan_publish(post_id)`. Ensures required fields (title, summary, header image, meta, etc.) are present.

4. **status transition** — `transition_post_status` or publish execution. Enforces status rules (e.g. in_process for publish).

---

## API

### `get_output_readiness(post_id, output_channel='blog')`

Returns:

```json
{
  "ok": true,
  "required_substage": "final_review",
  "required_stage": "header",
  "current_substage": "final_review",
  "current_stage": "header",
  "errors": [],
  "warnings": [],
  "post_type": "themed",
  "output_channel": "blog"
}
```

When not ready:

```json
{
  "ok": false,
  "required_substage": "final_review",
  "required_stage": "header",
  "current_substage": "seo_meta",
  "current_stage": "header",
  "errors": ["Missing substage 'final_review' (stage: header). Current: 'seo_meta' (stage: header)."],
  "warnings": [],
  "post_type": "themed",
  "output_channel": "blog"
}
```

### HTTP Endpoint

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/launchpad/api/publish/<id>/output-readiness?output=blog` | Get output readiness for post |

---

## 409 Response Shape (Blocked Output)

When output readiness fails before execution:

```json
{
  "success": false,
  "error": "Output not ready for publish",
  "output_blocked": true,
  "current_substage": "seo_meta",
  "required_substage": "final_review",
  "errors": ["Missing substage 'final_review' (stage: header). ..."]
}
```

HTTP status: **409 Conflict**

---

## Integration Points

| Action | Integration |
|--------|-------------|
| **Publish** (`publish_post_to_clan`) | After workflow_stage gate, before preflight |
| **Start automation** (`start_automation`) | After workflow_stage gate, before preflight |
| **Launchpad UI** | "Output Readiness" section below Preflight in Publish Essentials panel |

---

## Rules

- **Purely diagnostic** — does not modify `workflow_stage` or post state
- **Pipeline-derived** — required substage = last substage in pipeline for (post_type, output_channel)
- **Completion logic** — mirrors `automation_pipeline` completion checks for blog substages (planning → header)
- **DB-backed pipeline** — uses `post_type_substages` and `substage_metadata` via `utils.substage_config` and `config.output_channel_stages`

---

## Related Documentation

- `docs/ARCHITECTURE_V2_OVERVIEW.md` — Layered architecture and validation order
- `docs/workflow/workflow_stage_model.md` — workflow stage gates
- `reports/W2-AUDIT-7_SUBSTAGE_OUTPUT_CHANNEL_VALIDATION_INVENTORY_AND_GOVERNANCE_PLAN.md` — substage/output-channel governance
