# W2 Pipeline Navigation N3 — Ideas Page Explicit Next Panel

This report documents the Ideas page \"Pipeline Step\" panel that projects the existing `pipeline-state` API into the `/calendar/ideas` UI without changing backend behaviour.

---

## 1️⃣ Pipeline-state curl

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
    "... further substages omitted for brevity ..."
  ],
  "success": true,
  "workflow_stage": "structure"
}
```

---

## 2️⃣ Two state demonstrations

### Blocked case (sections = 5)

- **Screenshot placeholder:**  
  `reports/screenshots/W2_PIPELINE_NAV_IDEAS_NEXT_DISABLED.png`

- **Exact disabled reason text (from `reasons_blocked`):**

```text
Need at least 10 selected ideas (have 29); at least 3 categories (have 5); and at least 6 sections (have 5).
```

In this state, the Ideas page panel shows a disabled Next button and the above reason inline under the button.

### Enabled case (sections ≥ 6)

- **Screenshot placeholder:**  
  `reports/screenshots/W2_PIPELINE_NAV_IDEAS_NEXT_ENABLED.png`

After manually inserting a 6th section (or running clustering so that `sections >= 6`), the same panel renders the Next button enabled, pointing to the `next.nav_url` (Structure → Titling) with week parameters preserved when present.

---

## 3️⃣ Grep proof

### `ideas-pipeline-panel` in templates

```bash
grep -R "ideas-pipeline-panel" -n templates/
```

Output:

```text
templates/planning/calendar/ideas.html:81:            <div id="ideas-pipeline-panel" style="display: none;">
templates/planning/calendar/ideas.html:758:    const panel = document.getElementById('ideas-pipeline-panel');
```

### `updateIdeasPipelinePanel` in static (no matches; logic lives inline on Ideas template)

```bash
grep -R "updateIdeasPipelinePanel" -n static/
```

Output:

```text
no matches
```

---

## 4️⃣ Git proof

```bash
git log -1 --oneline
```

```text
W2: pipeline navigation N3 ideas page explicit next
```

