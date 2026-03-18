# W2 Stage UI proof (4.3 + 4.4)

## Implementation

- **Template:** `templates/shared/blog_pipeline_header.html` — `Stage: <span id="early-stage-value">—</span>` when `post_id` is present.
- **JS:** `static/js/shared/blog-pipeline-header.js` — `updateEarlyStageIndicator()` fetches GET `/api/posts/<id>/early-stage`, renders IDEAS (N/3 min), STRUCTURE (X sections), or stage name.

## Proof

**1. Open** `/planning/posts/729/calendar/ideas` — stage badge shows a value (not —), reflecting DB stage.

**2. Curl early-stage**

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

**3. Screenshot**

Path: `reports/screenshots/W2_STAGE_UI_INDICATOR.png`

---

## Proof block

```
c0a3a287
...
c0a3a287 W2: UI stage indicator proof report + screenshot
```
