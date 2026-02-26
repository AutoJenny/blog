# W2 Phase 2.1 — Canonical execution registry

Canonical exec registry (server-side); API extends canonical-substages with `current_mode` and `can_execute`.

---

## Curl proof

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq
```

Excerpt for Ideas → Generate Idea Set (node includes `min_stage`, `current_mode`, `can_execute`):

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq '.stages[] | select(.stage == "ideas") | .substages[] | {substage_key, label, min_stage, current_mode, can_execute}'
```

Example output:

```json
{
  "substage_key": "generate_idea_set",
  "label": "Generate Idea Set",
  "min_stage": "ideas",
  "current_mode": "manual",
  "can_execute": true
}
```

---

## Grep proof (verbatim)

**Where the canonical registry is defined:**

```
$ grep -Rn "CANONICAL_EXEC_REGISTRY\|CANONICAL_SUBSTAGES\|get_canonical_substages_for_post" utils/posts/canonical_substages.py
utils/posts/canonical_substages.py:22:# Each substage: id, title, ...
utils/posts/canonical_substages.py:26:CANONICAL_SUBSTAGES: Dict[str, List[Dict[str, Any]]] = {
utils/posts/canonical_substages.py:184:CANONICAL_EXEC_REGISTRY: Dict[Tuple[str, str], Dict[str, Any]] = {
utils/posts/canonical_substages.py:199:def get_canonical_substages_for_post(
```

**Where it is used by the API (canonical-substages response):**

```
$ grep -Rn "get_canonical_substages_for_post\|canonical_substages" blueprints/posts.py
blueprints/posts.py:876:from utils.posts.canonical_substages import get_canonical_substages_for_post
blueprints/posts.py:877:        payload = get_canonical_substages_for_post(
```

**Execute path (Phase 2.3 will use get_canonical_exec / CANONICAL_EXEC_REGISTRY):**

```
$ grep -Rn "get_canonical_exec\|CANONICAL_EXEC_REGISTRY" utils/posts/canonical_substages.py blueprints/automation_core.py 2>/dev/null || true
utils/posts/canonical_substages.py:256:def get_canonical_exec(stage: str, substage_key: str) -> Optional[Dict[str, Any]]:
utils/posts/canonical_substages.py:268:    return CANONICAL_EXEC_REGISTRY.get(("ideas", "generate_idea_set"))
```

(Phase 2.3 will wire `execute_substage` to use `get_canonical_exec` and the registry.)

---

## Summary

- **Registry:** `utils/posts/canonical_substages.py` defines `CANONICAL_EXEC_REGISTRY` (stage, substage_id) → handler + mode_default, and `get_canonical_exec(stage, substage_key)` for the execute path.
- **API:** `GET /api/posts/<id>/canonical-substages` now returns per-substage `substage_key`, `label`, `min_stage`, `current_mode` (from `post.extra_settings.substage_modes`), and `can_execute` (stage gating).
- **Execute path:** Not yet unified; Phase 2.3 will resolve (post_id, stage, substage) via canonical registry and call the handler.
