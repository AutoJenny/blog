# Workflow Stage API

**Date:** 2026-02-23  
**Implementation:** W2-FIX-5

---

## Endpoints

### GET `/api/posts/<id>/workflow-stage`

Returns current workflow stage and next advanceable stage (for UI).

**Response:**
```json
{
  "success": true,
  "workflow_stage": "drafted",
  "next_advanceable": "imaged"
}
```

- `next_advanceable`: Next stage user can advance to if criteria met; `null` if none.

---

### POST `/posts/<id>/advance-stage`

Advance post to target stage.

**Request body:**
```json
{
  "target_stage": "imaged"
}
```

**Response (success):**
```json
{
  "success": true,
  "workflow_stage": "imaged"
}
```

**Response (error):**
```json
{
  "success": false,
  "error": "Criteria for 'imaged' not met. Complete required work first."
}
```

**Override:** `?override=1` or `{ "override": true }` bypasses criteria check.

---

## Blocked Response (403)

When a gated route is accessed with invalid stage:

```json
{
  "stage_blocked": true,
  "current_stage": "idea",
  "required_stage": "structured, drafted",
  "message": "Post is at stage 'idea'. This action requires stage: structured, drafted. Use ?override=1 for admin."
}
```

## Automation Blocked (403)

When automation is disabled via `post.extra_settings.automation` (W2-FIX-7):

```json
{
  "automation_blocked": true,
  "stage": "imaged",
  "message": "Automation for stage 'imaged' is disabled. Enable in post extra_settings.automation.stage_enabled.",
  "success": false
}
```

**Override:** `?override=1` or `{ "override": true }` bypasses workflow stage gate; automation.enabled and stage_enabled are not bypassed by override.

---

## Related

- `docs/ARCHITECTURE_V2_OVERVIEW.md` — Block types and validation order

---

## Field Contract

| Field | Location | Type | Notes |
|-------|----------|------|-------|
| workflow_stage | post.extra_settings | string | idea, structured, drafted, imaged, essentials_complete, ready, published |
| workflow_stage_updated_at | post.extra_settings | ISO8601 | Last stage change |
