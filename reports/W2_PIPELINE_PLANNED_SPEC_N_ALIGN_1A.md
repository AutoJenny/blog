# W2 N-ALIGN-1A — Planned Pipeline Spec (Report-only)

Subphase A: Freeze the planned process definition for post_type=themed. No code changes.

---

## Artifact

- **Path:** `reports/artifacts/planned_pipeline_spec_v1.json`
- **Content:** Single “Planned Pipeline Spec” for themed posts: canonical stage order, substages with key, stage, label, nav_url (with `<id>` placeholder), operation_type, writes, completion_rule.

### Full JSON (inline)

```json
{
  "post_type": "themed",
  "canonical_stage_order": ["metadata", "ideas", "structure", "titling", "authoring", "imaging", "review"],
  "substages": [
    {
      "key": "metadata.edit_metadata",
      "stage": "metadata",
      "label": "Edit metadata",
      "nav_url": "/planning/posts/<id>/calendar/metadata",
      "operation_type": "manual_only",
      "writes": ["post.title", "post.subtitle", "post.summary"],
      "completion_rule": "title+subtitle present"
    },
    {
      "key": "ideas.generate_idea_set",
      "stage": "ideas",
      "label": "Generate idea set",
      "nav_url": "/planning/posts/<id>/calendar/ideas/generate",
      "operation_type": "exec_substage",
      "writes": ["post_required_idea (replace-all)"],
      "completion_rule": "post_required_idea.total >= 30 AND categories >= 4"
    },
    {
      "key": "ideas.curate_ideas",
      "stage": "ideas",
      "label": "Curate ideas",
      "nav_url": "/planning/posts/<id>/calendar/ideas/curate",
      "operation_type": "manual_edit",
      "writes": ["post_required_idea.is_selected/category/rank/text/rationale/source_urls"],
      "completion_rule": "selected >= 10 AND selected_categories >= 3"
    },
    {
      "key": "structure.cluster_into_sections",
      "stage": "structure",
      "label": "Cluster into sections",
      "nav_url": "/planning/posts/<id>/calendar/structure/cluster",
      "operation_type": "exec_substage",
      "writes": ["post_section (replace-all)"],
      "completion_rule": "sections >= 6"
    },
    {
      "key": "structure.edit_section_plan",
      "stage": "structure",
      "label": "Edit section plan",
      "nav_url": "/planning/posts/<id>/calendar/structure/edit",
      "operation_type": "manual_edit",
      "writes": ["post_section.section_heading/description/metadata.idea_ids"],
      "completion_rule": "sections >= 6 AND all headings non-empty"
    }
  ],
  "notes": [
    "One operation per page, but Jump is allowed.",
    "Current/Next must refer to first incomplete substage at/after workflow_stage."
  ]
}
```

Pointer: `cat reports/artifacts/planned_pipeline_spec_v1.json | jq` reproduces the above.

---

## Redundancies explicitly forbidden

- No duplicate theme header: theme/title context must appear only once on post pages (in the header).
- No duplicate “Next” or “Current” UI: only the canonical pipeline strip (Current / Next / Jump) in the header may show current/next; no page-local Current/Next panel on post pages.
- No mixed legacy/canonical row on post pages: the legacy substage row (Ideas, Taxonomy, Topic Brainstorming, Section Structure Design, etc.) must remain hidden when post_id is present; only the canonical strip is used for substage navigation.
- One operation per page: each spec nav_url (after page-split) should host a single operation (either exec_substage run or manual_edit), not both generate and curate on the same URL.
