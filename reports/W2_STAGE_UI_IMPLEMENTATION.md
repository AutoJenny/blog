# W2 Stage UI implementation (8.5)

## Behaviour

- In the blog header area: display **Stage: IDEAS (2/3 min)** or **Stage: STRUCTURE (4 sections)** or **Stage: METADATA** etc.
- Stage indicator **reflects DB value** (`post.workflow_stage` and counts from `post_required_idea` / `post_section`).
- **Not computed heuristically in JS** — values come from **GET /api/posts/<id>/early-stage**.
- **Updates only after successful backend stage change** — after user clicks "Advance Stage" and API returns success, the UI should refresh the indicator (e.g. call GET early-stage again or refetch).

## Implementation

- **Template:** `templates/shared/blog_pipeline_header.html` — added `<div id="early-stage-line">Stage: <span id="early-stage-value">—</span></div>` when `post_id` is defined.
- **JS:** `static/js/shared/blog-pipeline-header.js` — `updateEarlyStageIndicator()` fetches `/api/posts/<id>/early-stage` and sets:
  - IDEAS → `IDEAS (N/3 min)`
  - STRUCTURE → `STRUCTURE (N sections)`
  - Others → stage name in uppercase.
- Called from `updateHeaderFields()` after post data load.

## Screenshot

**Path:** `reports/screenshots/W2_STAGE_UI_INDICATOR.png` (optional: capture ideas page with Stage: METADATA or IDEAS).

## Curl (post.workflow_stage)

```bash
# Get early stage (includes workflow_stage from DB)
curl -s http://localhost:5000/api/posts/729/early-stage | jq .
```

Example: `{"success":true,"workflow_stage":"metadata","required_ideas_count":0,"sections_count":0}`.
