# W2 N-ALIGN-3 — Pipeline Necessity & Adequacy Audit (Report-Only)

No code changes. No schema or UI changes. Truth capture and recommendations only.

---

## A — Canonical Substage Inventory (Truth Capture)

**Source:** `curl -s http://localhost:5000/api/posts/729/canonical-substages | jq` (excerpt: structure stage shows only cluster_into_sections, edit_section_plan for themed).

**Registry in code:**

```bash
grep -R "CANONICAL_SUBSTAGES" -n utils/posts/
```

Output (excl. .pyc):

```
utils/posts/canonical_substages.py:36:CANONICAL_SUBSTAGES: Dict[str, List[Dict[str, Any]]] = {
utils/posts/canonical_substages.py:251:        substages_raw = CANONICAL_SUBSTAGES.get(stage, [])
utils/posts/canonical_substages.py:320:    for s in CANONICAL_SUBSTAGES.get(stage, []):
utils/posts/canonical_substages.py:327:        for s in CANONICAL_SUBSTAGES.get("ideas", []):
utils/posts/canonical_substages.py:331:    for canon_stage, substages in CANONICAL_SUBSTAGES.items():
```

### Flat table (full registry from utils/posts/canonical_substages.py)

| Stage     | Substage ID           | Title                  | min_stage  | post_types                          | Writes artefact? | Artefact table / target        |
|-----------|------------------------|------------------------|------------|-------------------------------------|------------------|---------------------------------|
| metadata  | edit_metadata          | Edit metadata          | metadata   | themed, recipe, profile, clan, gen  | YES              | post (title, subtitle, summary) |
| ideas     | generate_idea_set      | Generate Idea Set      | ideas      | themed, recipe, profile, clan, gen   | YES              | post_required_idea              |
| ideas     | curate_ideas           | Curate ideas           | ideas      | themed, recipe, profile, clan, gen   | YES*             | post_required_idea (updates)     |
| structure | cluster_into_sections   | Cluster into Sections  | ideas      | themed, recipe, profile, generated  | YES              | post_section                    |
| structure | edit_section_plan      | Edit section plan      | structure  | themed, recipe, profile, generated  | YES              | post_section                    |
| structure | topic_brainstorming    | Topic brainstorming   | ideas      | themed, recipe, profile, generated  | YES              | post_development                |
| structure | section_structure      | Section structure      | structure  | themed, recipe, profile, generated  | YES              | post_section                    |
| structure | topic_allocation       | Section ideas         | structure  | themed, recipe, profile, generated  | YES              | post_development, post_section  |
| structure | section_titling        | Section titling        | structure  | themed, recipe, profile, generated  | YES              | post_section                    |
| titling   | section_titling_final  | Section titling (final)| titling    | themed, recipe, profile, generated  | YES              | post_section                    |
| authoring | author_first_drafts    | First drafts           | titling    | themed, recipe, profile, generated  | YES              | post_section.draft              |
| authoring | image_concepts         | Image concepts         | authoring  | themed, recipe, profile, generated  | YES              | post_section (image_concepts)   |
| authoring | image_prompts          | Image prompts          | authoring  | themed, recipe, profile, generated  | YES              | post_section (image_prompts)   |
| authoring | image_captions         | Image captions         | authoring  | themed, recipe, profile, generated  | YES              | post_section (image_captions)   |
| imaging   | image_generation       | Image generation       | authoring  | themed, recipe, profile, generated  | YES              | post_section images, image_archive |
| imaging   | optimise               | Optimise               | imaging    | themed, recipe, profile, generated  | NO**             | — (in-place file ops)            |
| review    | final_review           | Final review           | review     | themed, recipe, profile, clan, gen   | NO               | UI_ONLY / publish state          |

\* curate_ideas: registry lists `artefacts_written: []` but UI persists edits to post_required_idea (is_selected, category, etc.) via PATCH — counted as writes to post_required_idea.  
\** optimise: registry `artefacts_written: []`; typically file-system or image table updates; no distinct artefact table listed.

- **Total canonical substage count (full registry):** 17  
- **Total themed-visible substage count (post 729):** 13 (metadata 1, ideas 2, structure 2, titling 1, authoring 4, imaging 2, review 1)

---

## B — Artefact Mapping (Adequacy Test)

| Substage                | Writes persistent artefact? | Table / classification   |
|-------------------------|-----------------------------|---------------------------|
| edit_metadata           | YES                         | post                      |
| generate_idea_set       | YES                         | post_required_idea        |
| curate_ideas            | YES                         | post_required_idea (PATCH)|
| cluster_into_sections   | YES                         | post_section              |
| edit_section_plan       | YES                         | post_section              |
| topic_brainstorming     | YES                         | post_development          |
| section_structure       | YES                         | post_section              |
| topic_allocation        | YES                         | post_development, post_section |
| section_titling         | YES                         | post_section              |
| section_titling_final   | YES                         | post_section              |
| author_first_drafts     | YES                         | post_section (draft)      |
| image_concepts          | YES                         | post_section              |
| image_prompts           | YES                         | post_section              |
| image_captions          | YES                         | post_section              |
| image_generation        | YES                         | post_section / image_archive / files |
| optimise                | NO (in-place)               | UI_ONLY / file ops        |
| final_review            | NO                          | UI_ONLY                   |

**Flagged:** optimise, final_review — no persistent DB artefact in registry; optimise may touch files; final_review is gate/UI only.

---

## C — Redundancy Classification

| Substage                | Classification        | Notes |
|-------------------------|-----------------------|--------|
| edit_metadata           | UNIQUE_OPERATION      | Single metadata entry. |
| generate_idea_set       | UNIQUE_OPERATION      | Only bulk-idea generator. |
| curate_ideas            | UI_EDIT_MODE          | Human selection/edits on existing ideas; no exec handler that “runs” to create artefact. |
| cluster_into_sections   | UNIQUE_OPERATION      | Single LLM/exec step for themed section-first. |
| edit_section_plan       | UI_EDIT_MODE          | Manual edit of section headings/briefs/idea_ids. |
| topic_brainstorming     | LEGACY_VARIANT        | Superseded by generate_idea_set + cluster for themed. |
| section_structure       | LEGACY_VARIANT        | Superseded by cluster_into_sections for themed. |
| topic_allocation        | LEGACY_VARIANT        | Superseded by cluster_into_sections (idea_ids in sections). |
| section_titling         | LEGACY_VARIANT        | Overlaps section_titling_final / edit_section_plan. |
| section_titling_final   | UNIQUE_OPERATION       | Final titles/order. |
| author_first_drafts     | UNIQUE_OPERATION       | Section body content. |
| image_concepts          | UNIQUE_OPERATION       | Concepts per section. |
| image_prompts           | UNIQUE_OPERATION       | Prompts per section. |
| image_captions          | UNIQUE_OPERATION       | Captions/alt. |
| image_generation        | UNIQUE_OPERATION       | Image assets. |
| optimise                | UNIQUE_OPERATION       | Resize/compress; pipeline guard/helper. |
| final_review            | PIPELINE_GUARD_ONLY    | Gate before publish; no artefact. |

### 1) Is curate_ideas a formal pipeline step?

**Conclusion: KEEP as pipeline step.**

Curate_ideas is the gate between “many ideas” and “committed set”: generate_idea_set produces 30–60 ideas; curate_ideas is where the human selects ≥10 across ≥3 categories. That selection is required for cluster_into_sections and for stage advancement. Without it as a named step, completion rules (“selected >= 10, categories >= 3”) have no clear owner and the pipeline would either auto-advance or leave the gate implicit. Keeping it as a formal step makes the gate visible, auditable, and consistent with “run then curate then cluster.”

### 2) Legacy structure substages: atomic operations or superseded fragments?

**Superseded fragments for themed.** topic_brainstorming, section_structure, topic_allocation, section_titling were atomic steps in the old flow (post_development + section outline). For themed, cluster_into_sections replaces them with one exec step that writes post_section from selected ideas. They remain in the registry for non-themed/legacy flows and are correctly EXCLUDE_FROM_THEMED_NAV; they are not atomic operations in the themed pipeline.

---

## D — Minimal Sufficient Pipeline

**Minimal ordered list of operations to move a themed post from metadata → publishable:**

1. metadata.edit_metadata  
2. ideas.generate_idea_set  
3. ideas.curate_ideas  
4. structure.cluster_into_sections  
5. structure.edit_section_plan  
6. titling.section_titling_final  
7. authoring.author_first_drafts  
8. authoring.image_concepts  
9. authoring.image_prompts  
10. authoring.image_captions  
11. imaging.image_generation  
12. imaging.optimise  
13. review.final_review  

**Proposed Themed Pipeline v2 (ordered list)**

1. metadata.edit_metadata  
2. ideas.generate_idea_set  
3. ideas.curate_ideas  
4. structure.cluster_into_sections  
5. structure.edit_section_plan  
6. titling.section_titling_final  
7. authoring.author_first_drafts  
8. authoring.image_concepts  
9. authoring.image_prompts  
10. authoring.image_captions  
11. imaging.image_generation  
12. imaging.optimise  
13. review.final_review  

---

## E — Adequacy Matrix

| Required published artefact | Responsible substage (exactly one) | 0 → INADEQUATE / 1 → OK |
|-----------------------------|--------------------------------------|--------------------------|
| metadata (title, subtitle, summary) | metadata.edit_metadata | 1 |
| selected ideas (min 10, 3 cats)    | ideas.curate_ideas                  | 1 |
| structured sections (6–7)          | structure.cluster_into_sections     | 1 |
| section headings / briefs           | structure.edit_section_plan (+ titling.section_titling_final) | 1* |
| section bodies                     | authoring.author_first_drafts      | 1 |
| images (per section)                | imaging.image_generation            | 1 |
| header/meta image                  | (not in canonical substages; header flow) | 0 → INADEQUATE in this list |
| SEO fields                         | (often post or header)              | 0 → INADEQUATE in this list |
| publish state                      | review.final_review (gate)          | 1 (as gate) |

\* Section headings: edit_section_plan and section_titling_final both touch headings; one could be deemed “final” owner for published headings.

Rule: 0 responsible → INADEQUATE; 1 responsible → adequate; >1 → redundant.

**Explicit verdict:** Current pipeline is **OVER-SPECIFIED** (17 substages in registry; 4 legacy structure steps redundant for themed). It is **UNDER-SPECIFIED** for full publishability: header image and SEO are not mapped to a canonical substage in this registry (they live in header/preview flows).

---

## F — Overcount Explanation

**Why ~21 substages is overstated:** The registry defines **17** canonical substages; “~21” may include legacy planning substages (e.g. taxonomy, ideas as nav keys) or duplicate counts. Overcount comes from legacy structure (4) plus optional/overlapping steps.

**Categories and counts:**

| Category                 | Substages | Count |
|--------------------------|-----------|-------|
| Core                     | edit_metadata, generate_idea_set, curate_ideas, cluster_into_sections, edit_section_plan, section_titling_final, author_first_drafts, image_concepts, image_prompts, image_captions, image_generation, optimise, final_review | 13 |
| Legacy retained          | topic_brainstorming, section_structure, topic_allocation, section_titling | 4 |
| Optional extension       | (none explicitly; optimise could be optional) | 0 |
| Internal execution helper| (handlers exist for exec; no extra “helper-only” substage) | 0 |
| UI-only                  | curate_ideas (partial), edit_section_plan (partial), final_review | 0 (they are steps with persistence or gate) |

**Counts per category:** Core 13, Legacy retained 4, Total in registry 17. Themed-visible 13 (legacy excluded).

---

## G — Final Recommendations (Binary Decisions Required)

1. **Keep curate_ideas as formal step?** **YES.**  
2. **Keep structure as two steps (cluster + edit)?** **YES.**  
3. **Keep titling separate from structure?** **YES.**  
4. **Deprecate any canonical substages from themed?** **YES.** List: topic_brainstorming, section_structure, topic_allocation, section_titling. (Already excluded from themed nav in N-ALIGN-2B.)  
5. **Final themed substage count (number):** **13.**

**Final Proposed Themed Pipeline v2**

1. metadata.edit_metadata  
2. ideas.generate_idea_set  
3. ideas.curate_ideas  
4. structure.cluster_into_sections  
5. structure.edit_section_plan  
6. titling.section_titling_final  
7. authoring.author_first_drafts  
8. authoring.image_concepts  
9. authoring.image_prompts  
10. authoring.image_captions  
11. imaging.image_generation  
12. imaging.optimise  
13. review.final_review  
