# W2 N-ALIGN-2A — Canonical Registry Diff Report (Report-only)

Spec vs live registry for post_type=themed (metadata, ideas, structure). No code changes. No deletions.

**Inputs:** reports/artifacts/planned_pipeline_spec_v1.json, canonical_substages_729.json, pipeline_state_729.json

---

## A) Planned pipeline (spec truth)

Planned keys in order for post_type=themed, stages metadata / ideas / structure only (from planned_pipeline_spec_v1.json):

| # | stage     | substage key           | key (stage.substage)           |
|---|-----------|------------------------|---------------------------------|
| 1 | metadata  | edit_metadata          | metadata.edit_metadata         |
| 2 | ideas     | generate_idea_set      | ideas.generate_idea_set        |
| 3 | ideas     | curate_ideas           | ideas.curate_ideas             |
| 4 | structure | cluster_into_sections  | structure.cluster_into_sections|
| 5 | structure | edit_section_plan      | structure.edit_section_plan    |

---

## B) Live canonical registry (system truth)

Live canonical keys in order for post 729 from canonical_substages_729.json, stages metadata / ideas / structure:

| # | stage     | substage id (id / substage_key) | registry_key                    |
|---|-----------|----------------------------------|---------------------------------|
| 1 | metadata  | edit_metadata                   | metadata.edit_metadata         |
| 2 | ideas     | generate_idea_set               | ideas.generate_idea_set        |
| 3 | ideas     | curate_ideas                    | ideas.curate_ideas             |
| 4 | structure | cluster_into_sections           | structure.cluster_into_sections|
| 5 | structure | topic_brainstorming             | structure.topic_brainstorming  |
| 6 | structure | section_structure               | structure.section_structure    |
| 7 | structure | topic_allocation                | structure.topic_allocation     |
| 8 | structure | section_titling                 | structure.section_titling      |

*(structure.edit_section_plan is in the spec but not present in the live registry.)*

---

## C) Diff table

| registry_key                    | in_planned_spec | action_for_themed           | notes |
|---------------------------------|-----------------|-----------------------------|--------|
| metadata.edit_metadata         | YES             | KEEP                        | Matches spec. |
| ideas.generate_idea_set        | YES             | KEEP                        | Matches spec. |
| ideas.curate_ideas             | YES             | KEEP                        | Matches spec. |
| structure.cluster_into_sections | YES             | KEEP                        | Matches spec. |
| structure.edit_section_plan     | YES             | KEEP (add in 2B)            | In spec; not in registry yet; add for themed. |
| structure.topic_brainstorming  | NO              | EXCLUDE_FROM_THEMED_NAV     | Legacy; exclude from themed canonical nav only. |
| structure.section_structure    | NO              | EXCLUDE_FROM_THEMED_NAV     | Legacy; exclude from themed canonical nav only. |
| structure.topic_allocation     | NO              | EXCLUDE_FROM_THEMED_NAV     | Legacy; exclude from themed canonical nav only. |
| structure.section_titling       | NO              | EXCLUDE_FROM_THEMED_NAV     | Legacy; exclude from themed canonical nav only. |

---

## D) Acceptance checklist

- [ ] **After Phase 2B,** themed “structure” stage shows only:
  - structure.cluster_into_sections
  - structure.edit_section_plan (may be nav_exists=false if page not built yet)
- [ ] No routes/templates removed; legacy pages remain accessible directly by URL.

*(Checklist to be verified post 2B.)*
