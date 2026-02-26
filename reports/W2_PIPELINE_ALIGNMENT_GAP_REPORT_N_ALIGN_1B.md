# W2 N-ALIGN-1B — Pipeline Alignment Gap Report (Report-only)

Subphase B: Measure reality (UI + API + registry) against the planned spec. No fixes applied.

---

## 1. Spec excerpt (keys + completion rules only)

From `reports/artifacts/planned_pipeline_spec_v1.json`:

| spec_key | completion_rule |
|----------|-----------------|
| metadata.edit_metadata | title+subtitle present |
| ideas.generate_idea_set | post_required_idea.total >= 30 AND categories >= 4 |
| ideas.curate_ideas | selected >= 10 AND selected_categories >= 3 |
| structure.cluster_into_sections | sections >= 6 |
| structure.edit_section_plan | sections >= 6 AND all headings non-empty |

---

## 2. Reality excerpt

### From canonical_substages_729.json (substages with key, label, min_stage, nav_url, current_mode, can_execute)

Canonical API does not return nav_url/nav_exists; pipeline-state does. Flattened from pipeline_state_729.json substages:

| key | label | min_stage | nav_url | nav_exists | current_mode | can_execute |
|-----|-------|-----------|---------|------------|--------------|-------------|
| metadata.edit_metadata | Edit metadata | metadata | /planning/posts/729/calendar/metadata | false | manual | true |
| ideas.generate_idea_set | Generate Idea Set | ideas | /planning/posts/729/calendar/ideas | true | manual | true |
| ideas.curate_ideas | Curate ideas | ideas | /planning/posts/729/calendar/ideas | true | manual | true |
| structure.cluster_into_sections | Cluster into Sections | ideas | /planning/posts/729/calendar/structure | false | manual | false |
| structure.topic_brainstorming | Topic brainstorming | ideas | /planning/posts/729/calendar/structure | false | manual | true |
| structure.section_structure | Section structure | structure | /planning/posts/729/calendar/structure | false | manual | true |
| structure.topic_allocation | Section ideas | structure | /planning/posts/729/calendar/structure | false | manual | true |
| structure.section_titling | Section titling | structure | /planning/posts/729/calendar/structure | false | manual | true |
| titling.section_titling_final | Section titling (final) | titling | /planning/posts/729/calendar/titling | false | manual | false |
| … (authoring, imaging, review) | … | … | … | false | manual | … |

### From pipeline_state_729.json (workflow_stage, current, next, reasons_blocked)

```json
{
  "workflow_stage": "structure",
  "current": { "stage": "structure", "substage": "cluster_into_sections" },
  "next": { "stage": "structure", "substage": "topic_brainstorming" },
  "reasons_blocked": {
    "structure.cluster_into_sections": "Need at least 10 selected ideas (have 29); at least 3 categories (have 5); and at least 6 sections (have 5)."
  }
}
```

---

## 3. Gap table

| spec_key | exists_in_registry? | nav_url matches spec intent? | UI has one-operation-per-page? | redundant UI elements present? | action required (report-only) |
|----------|---------------------|-----------------------------|--------------------------------|--------------------------------|-------------------------------|
| metadata.edit_metadata | yes | no (spec: /metadata; current: /metadata, page 404) | N/A (no page) | — | Add route + page or leave as-is. |
| ideas.generate_idea_set | yes | no (spec: /ideas/generate; current: /ideas) | no (generate + curate on same page) | no | Split ideas into /ideas/generate and /ideas/curate. |
| ideas.curate_ideas | yes | no (spec: /ideas/curate; current: /ideas) | no (same page as generate) | no | Same split. |
| structure.cluster_into_sections | yes | no (spec: /structure/cluster; current: /structure) | N/A (no structure page) | — | Add /calendar/structure then split to /cluster. |
| structure.edit_section_plan | no | N/A | N/A | — | Add substage to registry + nav_url /structure/edit. |

---

## 4. Redundancy list

- **Duplicated theme display:** None. UI inventory (ui_surface_inventory_729.json): theme shown only in header on post ideas page; no in-content theme block.
- **Duplicated “Next/Current” components:** None on post pages. workflow-navigation-container is hidden when post_id is set; only header strip shows Current/Next/Jump.
- **Remaining legacy pipeline elements visible on post pages:** None. Legacy substage row (#sub-stages-line) is hidden when post_id is defined (blog_pipeline_header.html); only canonical pipeline strip is visible.

---

## 5. Commands recorded (verbatim)

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq . > reports/artifacts/canonical_substages_729.json
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq . > reports/artifacts/pipeline_state_729.json
```

---

## Acceptance statement for Subphase B

**We have a complete gap list; no fixes applied.**
