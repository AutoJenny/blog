# Status Transition Rules

**Date:** 2026-02-23  
**Source:** `utils/posts/status_transitions.py` (W2-FIX-4)

---

## Valid Statuses

| Status | Meaning |
|--------|---------|
| draft | Post in progress, not ready for publish |
| in_process | Marked ready; publishable |
| published | Successfully published to Clan.com |
| archived | Archived (final) |
| deleted | Soft-deleted (terminal) |

**Note:** `in_progress` and `ready` are deprecated/aliases. Use `in_process`.

---

## Allowed Transitions

```
draft       → in_process  (Mark Ready)
draft       → deleted
in_process  → published  (Publish succeeds)
in_process  → draft       (Revoke ready)
in_process  → deleted
published   → archived
archived    → draft
archived    → deleted
```

**Terminal:** `deleted` cannot transition out.

---

## Implementation

All post.status writes go through `transition_post_status()`:

```python
from utils.posts.status_transitions import transition_post_status
ok, err = transition_post_status(post_id, 'in_process', actor='mark_ready')
```

---

## Override

`?override=1` or JSON `override: true` bypasses transition validation (admin only).

---

## Related

- `docs/ARCHITECTURE_V2_OVERVIEW.md` — Validation order and actor model
- `docs/POST_STATUS_MANAGEMENT.md` — Reuse rules, workflow states
- `docs/workflow/workflow_stage_model.md` — Workflow stage (internal progression)
- `utils/posts/workflow_stage.py` — Stage engine
