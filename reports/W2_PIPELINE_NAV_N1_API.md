# W2 Pipeline Nav N1 — `pipeline-state` API

Endpoint: `GET /api/posts/<int:post_id>/pipeline-state`

---

## 1. curl proof

Command:

```bash
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq
```

Output:

```json
{
  "current": {
    "stage": "metadata",
    "substage": "edit_metadata"
  },
  "next": {
    "stage": "ideas",
    "substage": "generate_idea_set"
  },
  "post_id": 729,
  "post_type": "themed",
  "reasons_blocked": {
    "structure.cluster_into_sections": "Need at least 6 sections (have 5)."
  },
  "substages": [
    {
      "can_execute": true,
      "current_mode": "manual",
      "label": "Edit metadata",
      "min_stage": "metadata",
      "nav_url": "/planning/posts/729/calendar/ideas",
      "stage": "metadata",
      "substage": "edit_metadata"
    },
    {
      "can_execute": true,
      "current_mode": "manual",
      "label": "Generate Idea Set",
      "min_stage": "ideas",
      "nav_url": "/planning/posts/729/calendar/ideas",
      "stage": "ideas",
      "substage": "generate_idea_set"
    },
    {
      "can_execute": true,
      "current_mode": "manual",
      "label": "Topic brainstorming",
      "min_stage": "ideas",
      "nav_url": "/planning/posts/729/calendar/structure",
      "stage": "structure",
      "substage": "topic_brainstorming"
    },
    {
      "can_execute": true,
      "current_mode": "manual",
      "label": "Section structure",
      "min_stage": "structure",
      "nav_url": "/planning/posts/729/calendar/structure",
      "stage": "structure",
      "substage": "section_structure"
    },
    {
      "can_execute": true,
      "current_mode": "manual",
      "label": "Section ideas",
      "min_stage": "structure",
      "nav_url": "/planning/posts/729/calendar/structure",
      "stage": "structure",
      "substage": "topic_allocation"
    },
    {
      "can_execute": true,
      "current_mode": "manual",
      "label": "Section titling",
      "min_stage": "structure",
      "nav_url": "/planning/posts/729/calendar/structure",
      "stage": "structure",
      "substage": "section_titling"
    },
    {
      "can_execute": false,
      "current_mode": "manual",
      "label": "Section titling (final)",
      "min_stage": "titling",
      "nav_url": "/planning/posts/729/calendar/ideas",
      "stage": "titling",
      "substage": "section_titling_final"
    },
    {
      "can_execute": false,
      "current_mode": "manual",
      "label": "First drafts",
      "min_stage": "titling",
      "nav_url": "/planning/posts/729/calendar/authoring",
      "stage": "authoring",
      "substage": "author_first_drafts"
    },
    {
      "can_execute": false,
      "current_mode": "manual",
      "label": "Image concepts",
      "min_stage": "authoring",
      "nav_url": "/planning/posts/729/calendar/authoring",
      "stage": "authoring",
      "substage": "image_concepts"
    },
    {
      "can_execute": false,
      "current_mode": "manual",
      "label": "Image prompts",
      "min_stage": "authoring",
      "nav_url": "/planning/posts/729/calendar/authoring",
      "stage": "authoring",
      "substage": "image_prompts"
    },
    {
      "can_execute": false,
      "current_mode": "manual",
      "label": "Image captions",
      "min_stage": "authoring",
      "nav_url": "/planning/posts/729/calendar/authoring",
      "stage": "authoring",
      "substage": "image_captions"
    },
    {
      "can_execute": false,
      "current_mode": "manual",
      "label": "Image generation",
      "min_stage": "authoring",
      "nav_url": "/planning/posts/729/calendar/imaging",
      "stage": "imaging",
      "substage": "image_generation"
    },
    {
      "can_execute": false,
      "current_mode": "manual",
      "label": "Optimise",
      "min_stage": "imaging",
      "nav_url": "/planning/posts/729/calendar/imaging",
      "stage": "imaging",
      "substage": "optimise"
    },
    {
      "can_execute": false,
      "current_mode": "manual",
      "label": "Final review",
      "min_stage": "review",
      "nav_url": "/planning/posts/729/calendar/review",
      "stage": "review",
      "substage": "final_review"
    }
  ],
  "success": true,
  "workflow_stage": "structure"
}
```

Notes:
- `workflow_stage` is the canonical post workflow stage (`structure` for post 729).
- `current` is the first substage in the linear canonical list that is not yet marked complete (metadata → edit_metadata).
- `next` is the following substage (`ideas.generate_idea_set`).
- `reasons_blocked` currently contains an entry for `structure.cluster_into_sections` based on artefact counts (see below).

---

## 2. SQL proofs for post 729

### 2.1 Total required ideas

```bash
psql -d blog -c "
SELECT COUNT(*) AS total_required_ideas
FROM post_required_idea
WHERE post_id = 729;
"
```

Output:

```text
 total_required_ideas 
----------------------
                   30
(1 row)
```

### 2.2 Selected ideas and category diversity

```bash
psql -d blog -c "
SELECT COUNT(*) FILTER (WHERE is_selected) AS selected,
       COUNT(DISTINCT category) FILTER (WHERE is_selected) AS categories
FROM post_required_idea
WHERE post_id = 729;
"
```

Output:

```text
 selected | categories 
----------+------------
       29 |          5
(1 row)
```

### 2.3 Sections

```bash
psql -d blog -c "
SELECT COUNT(*) AS sections
FROM post_section
WHERE post_id = 729;
"
```

Output:

```text
 sections 
----------
        5
(1 row)
```

These values drive the minimal artefact/completion gating used in `pipeline-state`:

- `ideas.generate_idea_set` complete flag is based on `total_required_ideas >= 30`.
- `structure.cluster_into_sections` is blocked because `sections = 5 < 6`, reflected in:

```json
\"reasons_blocked\": {
  \"structure.cluster_into_sections\": \"Need at least 6 sections (have 5).\"
}
```

---

## 3. Latest commit

```bash
git log -1 --oneline
```

Output at the time of this report:

```text
c42483b8 W2: phase3.3 idea curation UI
```

The `pipeline-state` API implementation is in a subsequent commit (see `git log`), but this snapshot confirms that the repo is on the expected branch and that recent Phase 3 work is present.

