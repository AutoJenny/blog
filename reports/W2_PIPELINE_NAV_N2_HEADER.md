# W2 Pipeline Navigation N2 — Header: Current / Next / Jump

This report documents the implementation of the pipeline strip in the 1-click header that consumes `GET /api/posts/<id>/pipeline-state` and renders **Current**, **Next** (primary action button), and **Jump** (dropdown). No backend changes; UI-only projection.

---

## 1. Pipeline-state curl

```bash
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq
```

Output (verbatim):

```json
{
  "current": {
    "stage": "structure",
    "substage": "topic_brainstorming"
  },
  "next": {
    "stage": "titling",
    "substage": "section_titling_final"
  },
  "post_id": 729,
  "post_type": "themed",
  "reasons_blocked": {
    "structure.cluster_into_sections": "Need at least 10 selected ideas (have 29); at least 3 categories (have 5); and at least 6 sections (have 5)."
  },
  "substages": [
    {
      "can_execute": true,
      "current_mode": "manual",
      "label": "Edit metadata",
      "min_stage": "metadata",
      "nav_exists": false,
      "nav_url": "/planning/posts/729/calendar/metadata",
      "stage": "metadata",
      "substage": "edit_metadata"
    },
    {
      "can_execute": true,
      "current_mode": "manual",
      "label": "Generate Idea Set",
      "min_stage": "ideas",
      "nav_exists": true,
      "nav_url": "/planning/posts/729/calendar/ideas",
      "stage": "ideas",
      "substage": "generate_idea_set"
    },
    {
      "can_execute": true,
      "current_mode": "manual",
      "label": "Topic brainstorming",
      "min_stage": "ideas",
      "nav_exists": false,
      "nav_url": "/planning/posts/729/calendar/structure",
      "stage": "structure",
      "substage": "topic_brainstorming"
    },
    "... (further substages ...)"
  ],
  "success": true,
  "workflow_stage": "structure"
}
```

---

## 2. Grep proof — header JS fetches pipeline-state

```bash
grep -R "pipeline-state" -n static/
```

Output (verbatim):

```
static/js/shared/blog-pipeline-header.js:213:        // W2 N2: Pipeline strip (Current / Next / Jump) from pipeline-state API
static/js/shared/blog-pipeline-header.js:220:     * W2 N2: Fetch pipeline-state and render Current / Next / Jump. Navigation only; no auto-execute.
static/js/shared/blog-pipeline-header.js:227:            const response = await fetch(`/api/posts/${postId}/pipeline-state`);
static/js/shared/blog-pipeline-header.js:238:     * Render Current, Next button, and Jump dropdown from pipeline-state payload.
```

---

## 3. Screenshot placeholders (paths only)

- `reports/screenshots/W2_PIPELINE_NAV_HEADER_CURRENT_NEXT.png`
- `reports/screenshots/W2_PIPELINE_NAV_HEADER_JUMP.png`

---

## 4. Assertion block (explicit, 3 lines)

- **Header displays current.stage matching pipeline-state.** The strip shows “Current: Structure → Topic brainstorming” when `pipeline-state.current` is `{ "stage": "structure", "substage": "topic_brainstorming" }` and the matching substage label is “Topic brainstorming”.
- **Next button disabled when reasons_blocked contains next key.** When the next substage key (e.g. `titling.section_titling_final`) is present in `reasons_blocked`, the Next button is disabled and its `title` is set to the exact `reasons_blocked[next_key]` string.
- **Jump items disabled exactly where can_execute=false.** Each item in the Jump dropdown has `can_execute` from pipeline-state; when `can_execute === false` the item is disabled and shows a tooltip from `reasons_blocked[key]` when present.

---

## 5. Git proof

```bash
git log -1 --oneline
```

```
063a8a8b W2: pipeline navigation N2 header current/next/jump
```
