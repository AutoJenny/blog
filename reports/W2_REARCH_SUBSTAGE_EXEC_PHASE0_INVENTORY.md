# W2 Re-architecture: Substage Execution — Phase 0 Inventory (Report Only)

**Scope:** Inventory freeze. No code changes. Report-only deliverable.

---

## 0.1 DB Truth

### `\d post` (workflow_stage, extra_settings)

```
                                                      Table "public.post"
                Column                |            Type             | Collation | Nullable |              Default               
--------------------------------------+-----------------------------+-----------+----------+------------------------------------
 ...
 extra_settings                       | jsonb                       |           |          | 
 ...
 workflow_stage                       | text                        |           | not null | 'metadata'::text
...
Check constraints:
    ...
    "post_workflow_stage_valid" CHECK (workflow_stage = ANY (ARRAY['metadata'::text, 'ideas'::text, 'structure'::text, 'titling'::text, 'authoring'::text, 'imaging'::text, 'review'::text]))
```

- **workflow_stage:** column type `text`, NOT NULL, default `'metadata'`. Valid values (check constraint): `metadata`, `ideas`, `structure`, `titling`, `authoring`, `imaging`, `review`.
- **extra_settings:** column type `jsonb`, nullable, no default.

### For post 729

```sql
SELECT id, workflow_stage, extra_settings FROM post WHERE id=729;
```

**Verbatim output:**

```
 id  | workflow_stage |                                                                                                                                                                                                                                                                                                                           extra_settings                                                                                                                                                                                                                                                                                                                            
-----+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 729 | structure      | {"substage_state": {"ideas": {"angle_diversity": {"status": "done"}}}, "workflow_stage": "idea", "substage_playbook": {"ideas": [{"id": "angle_diversity", "label": "Angle diversity check"}, {"id": "specificity_targets", "label": "Specificity targets"}], "review": [{"id": "claims_sourced", "label": "Claims sourced"}, {"id": "repetition_check", "label": "Repetition/waffle check"}], "authoring": [{"id": "example_density", "label": "Examples per section"}, {"id": "generic_phrase_scan", "label": "Generic phrase scan"}]}, "expanded_idea_prompt_name": "Expanded Idea Generation", "workflow_stage_updated_at": "2026-02-25T14:45:45.036267+00:00"}
(1 row)
```

### Existing substage config tables used by `/settings/substage-management`

Substage-management uses **three DB tables** (not code-only):

1. **substage_metadata**
2. **post_type_substages**
3. **output_channel_substages**

**`\d substage_metadata`**

```
                                          Table "public.substage_metadata"
     Column     |            Type             | Collation | Nullable |                    Default                    
----------------+-----------------------------+-----------+----------+-----------------------------------------------
 id             | integer                     |           | not null | nextval('substage_metadata_id_seq'::regclass)
 substage_key   | character varying(100)      |           | not null | 
 label          | character varying(200)      |           | not null | 
 route_function | character varying(255)      |           |          | 
 display_order  | integer                     |           | not null | 999
 stage          | character varying(50)       |           | not null | 
 description    | text                        |           |          | 
 is_active      | boolean                     |           |          | true
 created_at     | timestamp without time zone |           |          | now()
 updated_at     | timestamp without time zone |           |          | now()
Indexes:
    "substage_metadata_pkey" PRIMARY KEY, btree (id)
    "idx_substage_metadata_active" btree (is_active)
    "idx_substage_metadata_stage" btree (stage)
    "idx_substage_metadata_stage_order" btree (stage, display_order)
    "unique_substage_key" UNIQUE CONSTRAINT, btree (substage_key)
Referenced by:
    TABLE "output_channel_substages" ... REFERENCES substage_metadata(substage_key) ...
    TABLE "post_type_substages" ... REFERENCES substage_metadata(substage_key) ...
```

**`\d post_type_substages`**

```
                                          Table "public.post_type_substages"
    Column     |            Type             | Collation | Nullable |                     Default                     
---------------+-----------------------------+-----------+----------+-------------------------------------------------
 id            | integer                     |           | not null | nextval('post_type_substages_id_seq'::regclass)
 post_type     | character varying(50)       |           | not null | 
 stage         | character varying(50)       |           | not null | 
 substage_key  | character varying(100)      |           | not null | 
 display_order | integer                     |           | not null | 
 is_active     | boolean                     |           |          | true
 created_at    | timestamp without time zone |           |          | now()
 updated_at    | timestamp without time zone |           |          | now()
Indexes:
    "post_type_substages_pkey" PRIMARY KEY, btree (id)
    "idx_post_type_substages_active" btree (is_active)
    "idx_post_type_substages_lookup" btree (post_type, stage, is_active, display_order)
    "idx_post_type_substages_post_type" btree (post_type)
    "idx_post_type_substages_stage" btree (stage)
    "unique_post_type_stage_substage" UNIQUE CONSTRAINT, btree (post_type, stage, substage_key)
Foreign-key constraints:
    "fk_substage_key" FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT
```

**`\d output_channel_substages`**

```
                                             Table "public.output_channel_substages"
        Column        |            Type             | Collation | Nullable |                       Default                        
----------------------+-----------------------------+-----------+----------+------------------------------------------------------
 id                   | integer                     |           | not null | nextval('output_channel_substages_id_seq'::regclass)
 post_type            | character varying(50)       |           | not null | 
 output_channel       | character varying(50)       |           | not null | 
 stage                | character varying(50)       |           | not null | 
 substage_key         | character varying(100)      |           | not null | 
 display_order        | integer                     |           | not null | 
 use_post_type_config | boolean                     |           |          | false
 is_active            | boolean                     |           |          | true
 created_at           | timestamp without time zone |           |          | now()
 updated_at           | timestamp without time zone |           |          | now()
Indexes:
    "output_channel_substages_pkey" PRIMARY KEY, btree (id)
    "idx_output_channel_substages_lookup" btree (post_type, output_channel, stage, is_active, display_order)
    "idx_output_channel_substages_post_type_channel" btree (post_type, output_channel)
    "unique_channel_substage" UNIQUE CONSTRAINT, btree (post_type, output_channel, stage, substage_key)
Foreign-key constraints:
    "fk_channel_substage_key" FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT
```

---

## 0.2 Code Truth (grep hits)

Commands: `grep -Rn "PATTERN" .` (or equivalent). Exclusions: binary/build dirs where applicable. Output verbatim below.

### execute-substage

**Command:** `grep -Rn "execute-substage" .` (excluding docs/reports for brevity; code hits below)

**Output (code paths):**

```
./blueprints/automation_core.py
  139:            "message": f"Worklist: {len(posts)} posts. Call execute-substage per post with target_year/target_week.",
  174:@bp.route('/execute-substage/<stage>/<substage>', methods=['POST'])

./static/js/launchpad/automation-engine.js
  100:            const response = await fetch(`/launchpad/one-click-publication/api/execute-substage/${stage}/${substage}`, {
```

(Other hits in reports/docs reference the same route.)

### substage-management

**Command:** `grep -Rn "substage-management" .`

**Output (key code paths):**

```
./blueprints/substage_management.py
  23:@bp.route('/substage-management', methods=['GET'])
  45:@bp.route('/api/substage-management/overview', methods=['GET'])
  133:@bp.route('/api/substage-management/post-types/<post_type>', methods=['GET'])
  148:@bp.route('/api/substage-management/output-channels/<post_type>/<output_channel>', methods=['GET'])
  ... (toggle, reorder, substage-metadata PUT/POST, bulk-copy, etc.)

./templates/shared/blog_pipeline_header.html
  98:            <a href="/settings/substage-management?post_id={{ post_id }}&post_type={{ post_type }}...

./templates/settings/substage_management.html
  9:    <link rel="stylesheet" href="/static/css/settings/substage-management.css">
  197:    <script src="/static/js/settings/substage-management.js"></script>

./templates/launchpad/one_click_publication.html
  83:                    <a href="/settings/substage-management" ...
  2329:        const link = document.getElementById('substage-management-link');
  2337:        let url = '/settings/substage-management';

./static/js/settings/substage-management.js
  5:const API_BASE = '/settings/api/substage-management';
```

### SUBSTAGE_CONFIG_MAP

**Command:** `grep -Rn "SUBSTAGE_CONFIG_MAP" .`

**Output:**

```
./static/js/shared/post-type-settings.js
  10:    const SUBSTAGE_CONFIG_MAP = {
  578:                const config = SUBSTAGE_CONFIG_MAP[substage];
  737:                                const prevSubstage = Object.keys(SUBSTAGE_CONFIG_MAP).find(
  738:                                    k => SUBSTAGE_CONFIG_MAP[k].pipelineStep === step.previous.stepId
  765:                                const nextSubstage = Object.keys(SUBSTAGE_CONFIG_MAP).find(
  766:                                    k => SUBSTAGE_CONFIG_MAP[k].pipelineStep === step.next.stepId
```

(Also referenced in reports/docs.)

### AUTOMATION_MIN_STAGE

**Command:** `grep -Rn "AUTOMATION_MIN_STAGE" .` (code only)

**Output:**

```
./blueprints/automation_core.py
  147:AUTOMATION_MIN_STAGE = {
  164:AUTOMATION_MIN_STAGE_BY_STAGE = {
  186:        min_stage = AUTOMATION_MIN_STAGE.get((stage, substage)) or AUTOMATION_MIN_STAGE_BY_STAGE.get(stage)
```

### get_default_playbook

**Command:** `grep -Rn "get_default_playbook" .`

**Output:**

```
./utils/posts/playbooks.py
  81:def get_default_playbook(post_type: str) -> Dict[str, List[Dict[str, str]]]]:
  121:    Idempotent: if extra_settings.substage_playbook missing, set from get_default_playbook(post_type)
  132:        playbook = get_default_playbook(post_type)
```

(Also in reports.)

### advance_post_stage

**Command:** `grep -Rn "advance_post_stage" .` (code only)

**Output:**

```
./blueprints/posts.py
  861:        from utils.posts.early_stage import advance_post_stage
  862:        ok, err, new_stage = advance_post_stage(post_id)

./utils/posts/early_stage.py
  4:Stage only advances when user explicitly calls advance_post_stage (e.g. "Advance Stage" button).
  139:def advance_post_stage(post_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
```

(Also in utils/posts/workflow_stage.py and reports.)

### required-ideas rendering on the ideas page

**Command:** `grep -Rn "requiredIdeas\|renderRequiredIdeasList\|required_ideas" templates/planning/calendar/ideas.html static/js`

**Output (ideas page + static):**

```
templates/planning/calendar/ideas.html
  125:                        <div id="required-ideas-list" ...
  127:                                No required ideas added yet. Click "Add Idea" to add one.
  689:// Store required ideas in memory
  690:let requiredIdeas = [];
  692:// Load and save post metadata (subtitle, required ideas)
  738:            // Load required ideas from embedding_overrides
  739:            requiredIdeas = [];
  745:                    if (overrides && overrides.required_ideas && Array.isArray(overrides.required_ideas)) {
  746:                        requiredIdeas = overrides.required_ideas;
  752:            renderRequiredIdeasList();
  822:function renderRequiredIdeasList() {
  823:    const ideasList = document.getElementById('required-ideas-list');
  ...
  837:        ideasList.innerHTML = requiredIdeas.map((idea, index) => `
  ...
  855:        requiredIdeas.splice(index, 1);
  856:        renderRequiredIdeasList();
  ...
  866:        requiredIdeas.push(ideaText.trim());
  867:        renderRequiredIdeasList();
  875:        console.log('[saveRequiredIdeas] Saving:', requiredIdeas);
  876:        const response = await fetch(`/planning/api/posts/${window.postId}/required-ideas`, {
  879:            body: JSON.stringify({ required_ideas: requiredIdeas })
  ...
```

Static JS only reference: `static/js/shared/blog-pipeline-header.js` line 234: `data.required_ideas_count`.

---

## 0.3 Runtime Proof

### Exact URLs

| Purpose | Exact URL |
|--------|-----------|
| **Execute endpoint** | `POST /launchpad/one-click-publication/api/execute-substage/<stage>/<substage>` (e.g. `http://localhost:5000/launchpad/one-click-publication/api/execute-substage/planning/topic_brainstorming`) |
| **Substage management endpoint** | Page: `GET /settings/substage-management`. API base: `GET /settings/api/substage-management/overview`, `GET /settings/api/substage-management/post-types/<post_type>`, etc. |
| **Ideas page endpoint** | `GET /planning/posts/<post_id>/calendar/ideas` (e.g. `http://localhost:5000/planning/posts/729/calendar/ideas`) |

### Which registry currently controls each?

- **Execute endpoint:** Controlled by a **hardcoded router** in `blueprints/automation_core.py` (`execute_substage` + `AUTOMATION_MIN_STAGE` / `AUTOMATION_MIN_STAGE_BY_STAGE`); it does **not** use the DB substage tables. Only the (stage, substage) pairs implemented in that router can be executed; e.g. "ideas" is not in the router.
- **Substage management:** Controlled by **DB tables** `substage_metadata`, `post_type_substages`, and `output_channel_substages`. The UI reads/writes these via `/settings/api/substage-management/*`. Config is **not** code-only.
- **Ideas page:** The **page** is served by the planning blueprint; **substage list/nav** for the header is from the same DB (via `get_substages_for_navbar` → `utils.substage_config`). The **Post Type Settings modal** (cog) uses the **JS-only** `SUBSTAGE_CONFIG_MAP` in `post-type-settings.js`, which has **no** entry for "ideas", so opening settings on the ideas substage yields "No configuration found for substage: ideas". So: ideas **page** and **navbar** use DB; **settings modal** uses JS map (and ideas is missing there).

---

*End of Phase 0 inventory. No code changes. Stop and wait for approval before Phase 1.*
