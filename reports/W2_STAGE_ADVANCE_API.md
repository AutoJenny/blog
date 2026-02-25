# W2 Stage advance API (8.6)

## Endpoint

**POST** `/api/posts/<id>/advance-stage`

Advances the post to the next early-development stage if the condition for the current stage is met. No body required (advance is one step only). Stage only advances on explicit call (e.g. "Advance Stage" button).

## Success response

```json
{
  "success": true,
  "new_stage": "structure"
}
```

## Error response (invalid / condition not met)

```json
{
  "success": false,
  "error": "Minimum 3 required ideas not met"
}
```

Other errors: "Post not found" (404), or condition messages for other transitions.

## Implementation

- **Blueprint:** `blueprints/posts.py`, `api_advance_early_stage`
- **Backend:** `utils/posts/early_stage.advance_post_stage(post_id)` — checks current stage, next stage condition, updates `post.workflow_stage`, returns `(success, error, new_stage)`.

## GET early-stage (for UI)

**GET** `/api/posts/<id>/early-stage` — returns `{ success, workflow_stage, required_ideas_count, sections_count }` for the stage indicator and badges.
