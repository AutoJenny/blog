# W2 N-ALIGN-2B — Themed Canonical Registry Matches Planned Pipeline

Code: themed-only filter in canonical substage construction. No deletions; legacy substages excluded from themed nav only.

---

## Verbatim API outputs (post 729, themed)

### canonical-substages

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq
```

Excerpt (structure stage only; full response in artifact):

```json
{
  "current_stage": "structure",
  "post_id": 729,
  "post_type": "themed",
  "stages": [
    { "stage": "metadata", "substages": [{ "id": "edit_metadata", "label": "Edit metadata", ... }] },
    { "stage": "ideas", "substages": [
      { "id": "generate_idea_set", "label": "Generate Idea Set", ... },
      { "id": "curate_ideas", "label": "Curate ideas", ... }
    ]},
    { "stage": "structure", "substages": [
      { "id": "cluster_into_sections", "label": "Cluster into Sections", "min_stage": "ideas", ... },
      { "id": "edit_section_plan", "label": "Edit section plan", "min_stage": "structure", ... }
    ]},
    ...
  ]
}
```

### pipeline-state

```bash
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq
```

Excerpt:

```json
{
  "current": { "stage": "structure", "substage": "cluster_into_sections" },
  "next": { "stage": "structure", "substage": "edit_section_plan" },
  "post_id": 729,
  "post_type": "themed",
  "reasons_blocked": { "structure.cluster_into_sections": "Need at least 10 selected ideas (have 29); ..." },
  "substages": [
    ...,
    { "stage": "structure", "substage": "cluster_into_sections", "label": "Cluster into Sections", "nav_url": "/planning/posts/729/calendar/structure", "nav_exists": false, ... },
    { "stage": "structure", "substage": "edit_section_plan", "label": "Edit section plan", "nav_url": "/planning/posts/729/calendar/structure", "nav_exists": false, ... },
    ...
  ]
}
```

---

## Assertion block

- **Structure substages returned for 729 are exactly:** `cluster_into_sections`, `edit_section_plan`. (No topic_brainstorming, section_structure, topic_allocation, section_titling in canonical-substages or pipeline-state substages for themed post 729.)
- **pipeline-state.next after cluster:** When current is `structure.cluster_into_sections`, next is **structure.edit_section_plan**. edit_section_plan has nav_exists=false (structure page not built yet); it still appears as next in the linear pipeline.

---

## Grep proof (planned spec v1 comment)

```bash
grep -R "planned spec v1" -n utils/posts/canonical_substages.py
```

Output:

```
26:# N-ALIGN-2B: Themed pipeline uses planned spec v1; legacy structure substages are excluded from
252:        # N-ALIGN-2B: Themed pipeline uses planned spec v1; legacy structure substages are excluded
```

---

## Acceptance (2A checklist)

- [x] After Phase 2B, themed “structure” stage shows only: structure.cluster_into_sections, structure.edit_section_plan.
- [x] edit_section_plan has nav_exists=false (page not built yet); nav_url is /planning/posts/<id>/calendar/structure.
- [x] No routes/templates removed; legacy pages remain accessible directly by URL.
