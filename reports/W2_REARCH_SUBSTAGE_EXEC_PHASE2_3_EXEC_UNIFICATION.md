# W2 Phase 2.3 — Unify execution endpoint to canonical registry

Execute-substage now resolves (post_id, stage, substage) via the canonical exec registry, enforces stage gating and mode gating, and dispatches to the handler.

---

## Verbatim proofs

**A) Successful execute for ideas (POST execute-substage):**

```bash
curl -s -X POST http://localhost:5000/launchpad/one-click-publication/api/execute-substage/ideas/generate_idea_set \
  -H "Content-Type: application/json" \
  -d '{"post_id":729}' | jq
```

Output:

```json
{
  "message": "Generated 1 required idea(s).",
  "output_channel": "blog",
  "required_ideas_count": 1,
  "success": true
}
```

**B) Blocked execute due to mode mismatch (403) — pipeline attempt when mode=manual:**

Set mode to manual:

```bash
curl -s -X PATCH http://localhost:5000/api/posts/729/substage-modes \
  -H "Content-Type: application/json" \
  -d '{"key":"ideas.generate_idea_set","mode":"manual"}' | jq .success
```

Then pipeline-style execute (with target_year/target_week):

```bash
curl -s -X POST http://localhost:5000/launchpad/one-click-publication/api/execute-substage/ideas/generate_idea_set \
  -H "Content-Type: application/json" \
  -d '{"post_id":729,"target_year":2026,"target_week":9}' | jq
```

Output:

```json
{
  "current_mode": "manual",
  "error": "Substage is in manual mode; pipeline execution not allowed.",
  "success": false
}
```

(HTTP 403.)

**C) Blocked execute due to stage too low (403):**

When `get_canonical_stage(post_id)` returns a stage earlier than the substage’s `min_stage`, the endpoint returns 403 with `required_stage` and `current_stage`. Example (for a post at `metadata` calling a substage that requires `ideas`): response body includes `"error": "Stage IDEAS required to run this operation."`, `"current_stage": "metadata"`, `"required_stage": "ideas"`.

---

## Summary

- **Resolution:** `find_substage_by_nav(stage, substage)` and `get_canonical_exec(canon_stage, substage_id)` resolve to a canonical handler.
- **Stage gating:** `min_stage` from the substage dict; if `stage_index(current_stage) < stage_index(min_stage)` → 403.
- **Mode gating:** `post.extra_settings.substage_modes[key]`; if request is pipeline (`source=pipeline` or `target_year`/`target_week` present) and mode is `manual` → 403.
- **Dispatch:** `CANONICAL_HANDLERS[handler_name](post_id, data)`; includes `generate_idea_set` → `execute_generate_idea_set` (writes to `post_required_idea`).
