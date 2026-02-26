# W2 Pipeline Operation Itemisation and Mapping (N-OPS-2)

Evidence-based report for **themed post 729**: canonical substages, pages, execution wiring, artefact model, and gaps/duplication. Report-only; no code changes.

---

## A) Canonical registry truth (what substages exist today)

### 1. GET /api/posts/729/canonical-substages

Full response saved to: **reports/artifacts/canonical_substages_729.json** (8052 bytes).

Verbatim curl and excerpt:

```bash
curl -s http://localhost:5000/api/posts/729/canonical-substages | jq
```

Excerpt (structure only; full JSON in artifact):

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
      { "id": "cluster_into_sections", "label": "Cluster into Sections", ... },
      { "id": "topic_brainstorming", "label": "Topic brainstorming", ... },
      { "id": "section_structure", "label": "Section structure", ... },
      { "id": "topic_allocation", "label": "Section ideas", ... },
      { "id": "section_titling", "label": "Section titling", ... }
    ]},
    { "stage": "titling", "substages": [{ "id": "section_titling_final", ... }] },
    { "stage": "authoring", "substages": [ "author_first_drafts", "image_concepts", "image_prompts", "image_captions" ] },
    { "stage": "imaging", "substages": [ "image_generation", "optimise" ] },
    { "stage": "review", "substages": [{ "id": "final_review", ... }] }
  ]
}
```

### 2. GET /api/posts/729/pipeline-state

Full response saved to: **reports/artifacts/pipeline_state_729.json** (5892 bytes).

Verbatim curl:

```bash
curl -s http://localhost:5000/api/posts/729/pipeline-state | jq
```

Excerpt (key fields):

```json
{
  "success": true,
  "post_id": 729,
  "post_type": "themed",
  "workflow_stage": "structure",
  "current": { "stage": "structure", "substage": "cluster_into_sections" },
  "next": { "stage": "structure", "substage": "topic_brainstorming" },
  "reasons_blocked": {
    "structure.cluster_into_sections": "Need at least 10 selected ideas (have 29); at least 3 categories (have 5); and at least 6 sections (have 5)."
  },
  "substages": [ /* one object per canonical substage with stage, substage, label, nav_url, nav_exists, is_complete, is_blocked, can_execute, ... */ ]
}
```

---

## B) Page inventory (does the nav_url exist, and what does it host)

One row per canonical substage from pipeline-state. Evidence for each nav_url: HTTP status and route definition.

### HTTP status (all nav_urls for post 729)

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/planning/posts/729/calendar/metadata  # 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/planning/posts/729/calendar/ideas    # 200
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/planning/posts/729/calendar/structure  # 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/planning/posts/729/calendar/titling   # 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/planning/posts/729/calendar/authoring # 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/planning/posts/729/calendar/imaging   # 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/planning/posts/729/calendar/review   # 404
```

Result: **Only /planning/posts/729/calendar/ideas returns 200.** All other calendar segment URLs return 404.

### Route definition (grep)

```bash
grep -R "calendar/ideas\|calendar/structure\|posts/.*calendar" -n blueprints | head -n 50
```

Relevant matches:

- **blueprints/planning.py:174** — `@bp.route('/posts/<int:post_id>/calendar/ideas')` → planning.planning_calendar_ideas (or delegated to planning_calendar_clean). Template: planning/calendar/ideas.html.
- **blueprints/posts.py:1084–1100** — `_get_pipeline_nav()` returns nav_url and nav_exists; only `calendar/ideas` has nav_exists=True; metadata, structure, titling, authoring, imaging, review have nav_exists=False and no matching Flask route for `/planning/posts/<id>/calendar/<segment>` except ideas.

No route found for: calendar/metadata, calendar/structure, calendar/titling, calendar/authoring, calendar/imaging, calendar/review (hence 404).

### Page inventory table

| stage     | substage_id          | label                 | exec_endpoint                                                    | nav_url                              | nav_exists | page_http_status | route_definition              | ui_run_button_present | ui_editor_present | operations_on_page                    | artefacts_written              | notes |
|-----------|----------------------|------------------------|------------------------------------------------------------------|--------------------------------------|------------|------------------|------------------------------|------------------------|-------------------|----------------------------------------|---------------------------------|-------|
| metadata  | edit_metadata        | Edit metadata          | —                                                                | /planning/posts/729/calendar/metadata | false      | 404              | —                            | no                     | no                | —                                      | —                               | No page. |
| ideas     | generate_idea_set    | Generate Idea Set      | POST .../execute-substage/ideas/generate_idea_set                 | /planning/posts/729/calendar/ideas   | true       | 200              | planning.py:174              | yes                    | no (run only)     | generate_idea_set                      | post_required_idea               | Run + list on same page. |
| ideas     | curate_ideas         | Curate ideas           | — (no handler in CANONICAL_HANDLERS)                             | /planning/posts/729/calendar/ideas   | true       | 200              | planning.py:174              | no                     | yes               | curate_required_ideas (PATCH items)    | post_required_idea (updates)     | Same URL as generate; editor only. |
| structure | cluster_into_sections| Cluster into Sections  | — (handler in registry but not in CANONICAL_HANDLERS)            | /planning/posts/729/calendar/structure | false    | 404              | —                            | no                     | no                | —                                      | post_section (intended)          | No page; no Run. |
| structure | topic_brainstorming   | Topic brainstorming    | POST .../execute-substage/structure/topic_brainstorming (legacy)  | /planning/posts/729/calendar/structure | false    | 404              | —                            | no                     | no                | —                                      | post_development                 | No page. |
| structure | section_structure    | Section structure      | section_structure in CANONICAL_HANDLERS                          | /planning/posts/729/calendar/structure | false    | 404              | —                            | no                     | no                | —                                      | post_development, post_section   | No page. |
| structure | topic_allocation     | Section ideas          | topic_allocation in CANONICAL_HANDLERS                           | /planning/posts/729/calendar/structure | false    | 404              | —                            | no                     | no                | —                                      | post_development                 | No page. |
| structure | section_titling      | Section titling        | section_titling in CANONICAL_HANDLERS                             | /planning/posts/729/calendar/structure | false    | 404              | —                            | no                     | no                | —                                      | post_development, post_section   | No page. |
| titling   | section_titling_final| Section titling (final)| —                                                                | /planning/posts/729/calendar/titling  | false      | 404              | —                            | no                     | no                | —                                      | post_section                     | No page. |
| authoring | author_first_drafts  | First drafts           | author_first_drafts in CANONICAL_HANDLERS                         | /planning/posts/729/calendar/authoring | false    | 404              | —                            | no                     | no                | —                                      | post_section.draft               | No page. |
| authoring | image_concepts       | Image concepts         | image_concepts in CANONICAL_HANDLERS                             | /planning/posts/729/calendar/authoring | false    | 404              | —                            | no                     | no                | —                                      | post_section                     | No page. |
| authoring | image_prompts        | Image prompts          | image_prompts in CANONICAL_HANDLERS                              | /planning/posts/729/calendar/authoring | false    | 404              | —                            | no                     | no                | —                                      | post_section                     | No page. |
| authoring | image_captions       | Image captions         | image_captions in CANONICAL_HANDLERS                              | /planning/posts/729/calendar/authoring | false    | 404              | —                            | no                     | no                | —                                      | post_section                     | No page. |
| imaging   | image_generation     | Image generation       | image_generation (not in CANONICAL_HANDLERS; legacy path)         | /planning/posts/729/calendar/imaging  | false      | 404              | —                            | no                     | no                | —                                      | post_section, image_archive      | No page. |
| imaging   | optimise             | Optimise               | optimise (legacy)                                                 | /planning/posts/729/calendar/imaging  | false      | 404              | —                            | no                     | no                | —                                      | —                               | No page. |
| review    | final_review         | Final review           | —                                                                | /planning/posts/729/calendar/review   | false      | 404              | —                            | no                     | no                | —                                      | —                               | No page. |

---

## C) Artefact model crosswalk (what data exists for each stage)

### post

```bash
psql -d blog -c "\d post"
```

Verbatim (excerpt): table `post` — columns include id, title, slug, summary, subtitle, status, workflow_stage, extra_settings, content_type_id, theme_id, recipe_id, header_image_id, meta_*, author_id, publish_at, first_published_at, clan_*, profile_*, recipe_*, etc. Full output omitted; see schema in repo/docs.

### post_required_idea

```bash
psql -d blog -c "\d post_required_idea"
```

```
                                       Table "public.post_required_idea"
   Column    |           Type           | Collation | Nullable |                    Default
-------------+--------------------------+-----------+----------+------------------------------------------------
 id          | integer                  |           | not null | nextval('post_required_idea_id_seq'::regclass)
 post_id     | integer                  |           | not null |
 text        | text                     |           | not null |
 sort_order  | integer                  |           | not null | 0
 created_at  | timestamp with time zone |           |          | now()
 category    | text                     |           |          |
 rationale   | text                     |           |          |
 source_urls | jsonb                    |           |          |
 rank        | integer                  |           |          |
 is_selected | boolean                  |           | not null | true
 created_by  | text                     |           |          |
 updated_at  | timestamp with time zone |           | not null | now()
```

### post_section

```bash
psql -d blog -c "\d post_section"
```

```
         Column         |            Type             | Collation | Nullable |                 Default
------------------------+-----------------------------+-----------+----------+------------------------------------------
 id                     | integer                     |           | not null | nextval('post_section_id_seq'::regclass)
 post_id                | integer                     |           | not null |
 section_order          | integer                     |           |          |
 section_heading        | text                        |           |          |
 ideas_to_include       | text                        |           |          |
 facts_to_include       | text                        |           |          |
 highlighting           | text                        |           |          |
 image_concepts         | text                        |           |          |
 image_prompts          | text                        |           |          |
 image_alt_text         | text                        |           |          |
 image_captions         | text                        |           |          |
 section_description    | text                        |           |          |
 status                 | text                        |           |          | 'draft'::text
 polished               | text                        |           |          |
 draft                  | text                        |           |          |
 ...
```

### post_images

```bash
psql -d blog -c "\d post_images"
```

```
   Column   |            Type             | Collation | Nullable |                 Default
------------+-----------------------------+-----------+----------+-----------------------------------------
 id         | integer                     |           | not null | nextval('post_images_id_seq'::regclass)
 post_id    | integer                     |           |          |
 image_id   | integer                     |           |          |
 image_type | character varying(50)       |           | not null |
 section_id | integer                     |           |          |
 sort_order | integer                     |           |          | 0
```

(image_id → image_archive.id)

### Section body storage (critical)

- **Table:** `post_section`
- **Columns for section body/draft content:**
  - **draft** (text) — main draft/body content for the section.
  - **polished** (text) — polished/final copy if used.
- **Section title/brief:** `section_heading` (title), `section_description` (brief/notes).

Proof: `\d post_section` lists `draft` and `polished`; automation_execute and authoring flows read/update `post_section.draft` for section content.

---

## D) Execution wiring truth (what actually runs on “Run”)

### Registry map (canonical substages with execution)

| substage (stage.substage_id)     | handler function name           | file path                         | tables written              | stage/mode gates |
|----------------------------------|----------------------------------|-----------------------------------|-----------------------------|------------------|
| ideas.generate_idea_set          | execute_generate_idea_set        | blueprints/automation_execute.py  | post_required_idea          | min_stage ideas; manual/assisted/auto |
| ideas.curate_ideas               | — (not in CANONICAL_HANDLERS)    | —                                 | —                           | N/A (editor-only) |
| structure.cluster_into_sections  | — (not in CANONICAL_HANDLERS)    | —                                 | post_section (intended)     | N/A (no handler) |
| structure.topic_brainstorming   | execute_topic_brainstorming      | blueprints/automation_execute.py  | post_development           | min_stage ideas |
| structure.section_structure      | execute_section_structure        | blueprints/automation_execute.py  | post_development, post_section | min_stage structure |
| structure.topic_allocation      | execute_topic_allocation         | blueprints/automation_execute.py  | post_development           | — |
| structure.section_titling       | execute_section_titling          | blueprints/automation_execute.py  | post_development, post_section | — |
| authoring.author_first_drafts   | execute_author_first_drafts      | blueprints/automation_execute.py  | post_section.draft         | authoring stage |
| authoring.image_concepts        | execute_image_concepts           | blueprints/automation_execute.py  | post_section               | imaging stage |
| authoring.image_prompts         | execute_image_prompts            | blueprints/automation_execute.py  | post_section               | — |
| authoring.image_captions        | execute_image_captions           | blueprints/automation_execute.py  | post_section               | — |
| imaging.image_generation        | (legacy path in automation_core) | —                                 | post_section, image_archive| — |
| imaging.optimise                | (legacy)                         | —                                 | —                           | — |

### Grep evidence

```bash
grep -R "CANONICAL_EXEC_REGISTRY" -n utils blueprints | head -n 30
```

- utils/posts/canonical_substages.py:202 — CANONICAL_EXEC_REGISTRY defined (ideas.generate_idea_set, ideas.curate_ideas, structure.cluster_into_sections, structure.topic_brainstorming, …).
- blueprints/automation_core.py — uses get_canonical_exec(); CANONICAL_HANDLERS dict does not include curate_ideas or cluster_into_sections.

```bash
grep -R "def execute_" -n blueprints/automation_execute.py | head -n 25
```

- execute_generate_idea_set (186), execute_topic_allocation (283), execute_section_titling (343), execute_topic_brainstorming (415), execute_section_structure (481), execute_author_first_drafts (547), execute_image_concepts (739), execute_image_prompts (944), execute_image_captions (1125), …

```bash
grep -R "execute-substage" -n blueprints static | head -n 20
```

- blueprints/automation_core.py:209 — `@bp.route('/execute-substage/<stage>/<substage>', methods=['POST'])`
- static/js/launchpad/automation-engine.js:100 — fetch(`/launchpad/one-click-publication/api/execute-substage/${stage}/${substage}`, ...)
- templates/planning/calendar/ideas.html:742 — fetch('/launchpad/one-click-publication/api/execute-substage/ideas/generate_idea_set', ...)

---

## E) Duplication + gaps (mechanical findings)

- **Pages hosting >1 operation:**  
  **/planning/posts/729/calendar/ideas** (page_http_status 200) hosts **generate_idea_set** (Run button) and **curate_required_ideas** (editor: checkboxes, category, text, PATCH items). So one page, two operations (B rows: ideas.generate_idea_set, ideas.curate_ideas).

- **Substages with exec but no page:**  
  All of structure (cluster_into_sections, topic_brainstorming, section_structure, topic_allocation, section_titling), titling, authoring, imaging, review — exec_endpoint may exist but nav_url returns 404, so no dedicated page. (B rows: structure.*, titling.*, authoring.*, imaging.*, review.*.)

- **Substages with page but no Run:**  
  **curate_ideas** has the same nav_url as ideas (200) and has an editor (ui_editor_present yes) but no Run button for “curate” itself; curation is done via PATCH. (B row: ideas.curate_ideas.)

- **UI elements duplicating pipeline/navigation content:**  
  - Ideas page: header has pipeline strip (Current/Next/Jump). workflow-navigation-container on ideas page is hidden when post_id is set (N-UI-1), so only one Next/Current in header. No other duplication identified in this report.

- **nav_exists=false blocking “Next”:**  
  **structure.cluster_into_sections** is current for post 729; nav_url is /planning/posts/729/calendar/structure, nav_exists=false, page_http_status 404. So “Next” (or “current”) points to a URL that does not exist and blocks meaningful navigation. (B row: structure.cluster_into_sections.)

---

## F) Minimal recommendation (no implementation yet)

1. **Proposed split for /calendar/ideas into two pages:**
   - **Generate (run-only):** One page (e.g. keep /calendar/ideas or /calendar/ideas/generate) with only the “Generate Idea Set” Run button and minimal context; artefact: post_required_idea (bulk insert). No editor.
   - **Curate (editor-only):** Second page (e.g. /calendar/ideas/curate or a distinct route) with only the required-ideas editor (checkboxes, category, text, select all/none, PATCH items); no Generate Run button. Artefact: post_required_idea (updates).

2. **Next page to build after that split:**  
   **/calendar/structure** — so that “Next” from ideas (or from cluster_into_sections as current) leads to a real page. That page should host at least **cluster_into_sections** (Run) and a sections editor (list/edit title+brief, reorder, add/delete), writing to post_section, as per N-STRUCT-3.

---

## Output rules

- Command outputs above are verbatim where shown; full JSON is in reports/artifacts/ (canonical_substages_729.json, pipeline_state_729.json).
- No screenshots for this instruction set.
- No code changes besides adding this report and the artifacts.

---

## Acceptance check (report footer)

- [x] Canonical substages + pipeline-state captured for post 729 (curl + artifacts).
- [x] Every canonical substage has a row in the page inventory table (B).
- [x] Every nav_url has HTTP status + route proof (or explicit “unknown”/— where no route).
- [x] All core artefact tables (post_required_idea, post_section, post_images) have \d output; post referenced.
- [x] Section body storage location identified and proven: post_section.draft (and polished).
- [x] Duplication/gaps list is evidence-backed (citations to B rows and nav_exists/status).
