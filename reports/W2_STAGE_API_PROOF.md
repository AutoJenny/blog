# W2 Stage API proof (2.3 + 2.4)

## Backend

- **Module:** `utils/posts/early_stage.py` — `get_early_stage(post_id)`, `advance_post_stage(post_id)`.
- **Endpoints:** GET `/api/posts/<id>/early-stage`, POST `/api/posts/<id>/advance-stage` (in `blueprints/posts.py`).

## Proof commands (post 729)

```bash
curl -s http://localhost:5000/api/posts/729/early-stage | jq
```

```json
{
  "required_ideas_count": 3,
  "sections_count": 5,
  "success": true,
  "workflow_stage": "ideas"
}
```

```bash
curl -s -X POST http://localhost:5000/api/posts/729/advance-stage | jq
```

```json
{
  "new_stage": "structure",
  "success": true
}
```

```bash
curl -s http://localhost:5000/api/posts/729/early-stage | jq
```

```json
{
  "required_ideas_count": 3,
  "sections_count": 5,
  "success": true,
  "workflow_stage": "structure"
}
```

## Gating checks observed for post 729

- **Stage:** ideas → structure when `required_ideas_count >= 3` (3 required ideas).
- **Counts:** `required_ideas_count: 3`, `sections_count: 5` from DB.
- **Advance:** POST returns `success: true`, `new_stage: structure`; next GET returns `workflow_stage: structure`.

---

## Proof block

```
git rev-parse HEAD
git status
git log -1 --oneline
```
