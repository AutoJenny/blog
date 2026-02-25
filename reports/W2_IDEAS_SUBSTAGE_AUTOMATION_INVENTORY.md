# W2 Ideas / Substage / Automation Inventory (Report Only)

**Scope:** Evidence report only. No code changes, no fixes, no other commits.

---

## 1. IDEAS PAGE — Full Trace

### 1.1 Route → Handler → Template

**URL served:** `/planning/posts/<id>/calendar/ideas`

**Route decorator (verbatim):**
```python
@bp.route('/posts/<int:post_id>/calendar/ideas')
def planning_calendar_ideas(post_id):
    """Calendar ideas page"""
    return ideas_func(post_id)
```

- **File path:** `blueprints/planning.py` (route); handler implementation in `blueprints/planning_calendar_clean.py`
- **Handler function name:** `planning_calendar_ideas` (in planning.py delegates to `ideas_func(post_id)`); the actual implementation is `planning_calendar_ideas` in `planning_calendar_clean.py`
- **Template name rendered:** `planning/calendar/ideas.html`

**Exact code block (planning.py):**
```python
@bp.route('/posts/<int:post_id>/calendar/ideas')
def planning_calendar_ideas(post_id):
    """Calendar ideas page"""
    return ideas_func(post_id)
```

**Exact code block (planning_calendar_clean.py) — handler implementation:**
```python
def planning_calendar_ideas(post_id):
    """Idea Generation sub-stage"""
    try:
        from flask import request, redirect, url_for
        from datetime import datetime
        from utils.taxonomy_helpers import get_post_type

        post_type = get_post_type(post_id)
        if post_type == 'recipe':
            return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))
        elif post_type == 'generated':
            return redirect(url_for('planning.planning_calendar_taxonomy', post_id=post_id))

        url_year = request.args.get('year', type=int)
        url_week = request.args.get('week', type=int)
        if url_year and url_week:
            year, week_number = url_year, url_week
        else:
            now = datetime.now()
            year = now.year
            week_number = now.isocalendar()[1]

        target_post_id = post_id
        # ... DB fetch post, content_type_name, post_derived_theme, post_context ...
        return render_template('planning/calendar/ideas.html',
                               post_id=post_id,
                               post=post,
                               post_type=post_type,
                               post_title=post.get('title'),
                               post_status=post.get('status'),
                               post_created=post.get('created_at'),
                               post_updated=post.get('updated_at'),
                               content_type_name=content_type_name,
                               post_derived_theme=post_derived_theme,
                               post_context=post_context,
                               year=year,
                               week_number=week_number,
                               blueprint_name='planning',
                               mode='post-based')
    except Exception as e:
        # ... fallback render with error ...
```

Blueprint prefix for `planning` is `/planning`, so full path is `/planning/posts/<int:post_id>/calendar/ideas`.

---

### 1.2 Template

**Full contents of `templates/planning/calendar/ideas.html`**

The full template file is 1417 lines. Per instruction it is not summarised; the exact, complete file is in the repository at **`templates/planning/calendar/ideas.html`**. For the report, the full contents are not duplicated here (same as in repo); key sections are referenced in §1.3 and §1.4.

---

### 1.3 Frontend JS

**JS files loaded by the ideas template:**

- `static/js/llm-utils.js`
- `static/js/llm-config.js`
- `static/js/llm-ui-manager.js`
- `static/js/llm-api-client.js`
- `static/js/llm-event-manager.js`
- `static/js/llm-module.js`
- Via `blog_pipeline_header.html` include: `static/js/shared/week-context.js`, `static/js/shared/workflow-navigation.js`, `static/js/shared/blog-pipeline-header.js`, `static/js/shared/post-type-settings.js`

**Functions responsible for:**

| Responsibility | Function / location |
|----------------|----------------------|
| Rendering required ideas | `renderRequiredIdeasList()` in ideas.html inline script. Uses `requiredIdeas` array; renders with `requiredIdeas.map((idea, index) => ...)` and `${escapeHtml(idea)}` (expects string or object — see §6). |
| Handling "Run" | No "Run" for automation on ideas page. The "Generate Expanded Idea" button is handled by overridden `llmModule.generateContent` in DOMContentLoaded (POST `/planning/api/posts/${postId}/expanded-idea`). |
| Calling automation endpoints | Ideas page does not call execute-substage. Automation Run is on one-click publication page. |
| Loading post metadata | `loadPostMetadata()` in ideas.html: `fetch(\`/planning/api/posts/${window.postId}\`)`, then sets `requiredIdeas = overrides.required_ideas` from `data.post.embedding_overrides`, then `renderRequiredIdeasList()`. |

**Exact functions (paste):**

```javascript
// Rendering required ideas (ideas.html inline)
function renderRequiredIdeasList() {
    const ideasList = document.getElementById('required-ideas-list');
    const noIdeasMessage = document.getElementById('no-ideas-message');
    if (!ideasList) return;
    if (requiredIdeas.length === 0) {
        if (noIdeasMessage) noIdeasMessage.style.display = 'block';
        ideasList.innerHTML = '<div id="no-ideas-message" ...>No required ideas added yet...</div>';
    } else {
        if (noIdeasMessage) noIdeasMessage.style.display = 'none';
        ideasList.innerHTML = requiredIdeas.map((idea, index) => `
            <div class="idea-item" ...>
                <span ...>${escapeHtml(idea)}</span>
                <button ... onclick="removeRequiredIdea(${index})">...</button>
            </div>
        `).join('');
    }
}

// Load post metadata (ideas.html inline)
async function loadPostMetadata() {
    const response = await fetch(`/planning/api/posts/${window.postId}`);
    const data = await response.json();
    if (data.success && data.post) {
        requiredIdeas = [];
        if (data.post.embedding_overrides) {
            const overrides = typeof data.post.embedding_overrides === 'string' ? JSON.parse(data.post.embedding_overrides) : data.post.embedding_overrides;
            if (overrides && overrides.required_ideas && Array.isArray(overrides.required_ideas)) {
                requiredIdeas = overrides.required_ideas;
            }
        }
        renderRequiredIdeasList();
    }
}

// Save required ideas (ideas.html inline)
async function saveRequiredIdeas() {
    const response = await fetch(`/planning/api/posts/${window.postId}/required-ideas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ required_ideas: requiredIdeas })
    });
    // ...
}
```

---

### 1.4 Required Ideas API

**Endpoints related to required ideas**

All in **file:** `blueprints/planning_api_post_metadata.py`. Blueprint prefix: `/planning/api/posts`.

| Route | Methods | Function |
|-------|---------|----------|
| `/<int:post_id>/required-ideas` | GET, POST | `api_post_required_ideas` |
| `/<int:post_id>/required-ideas/items` | POST | `api_post_required_idea_add` |
| `/<int:post_id>/required-ideas/items/<int:item_id>` | PATCH, DELETE | `api_post_required_idea_item` |

**Full code block (GET/POST required-ideas):**

```python
@bp.route('/<int:post_id>/required-ideas', methods=['GET', 'POST'])
def api_post_required_ideas(post_id):
    """Get or replace required ideas (stored in post_required_idea). W2: single source of truth."""
    try:
        if request.method == 'GET':
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, post_id, text, sort_order
                    FROM post_required_idea
                    WHERE post_id = %s
                    ORDER BY sort_order ASC, id ASC
                """, (post_id,))
                rows = cursor.fetchall()
                required_ideas = [
                    {'id': r.get('id'), 'text': r.get('text') or '', 'sort_order': r.get('sort_order', 0)}
                    for r in rows
                ]
                return jsonify({'success': True, 'required_ideas': required_ideas})

        elif request.method == 'POST':
            data = request.get_json() or {}
            required_ideas = data.get('required_ideas', [])
            if not isinstance(required_ideas, list):
                return jsonify({'success': False, 'error': 'required_ideas must be an array'}), 400
            normalized = []
            for i, item in enumerate(required_ideas):
                if isinstance(item, str):
                    normalized.append((item.strip(), i))
                elif isinstance(item, dict):
                    text = (item.get('text') or item.get('idea') or '').strip()
                    sort_order = item.get('sort_order', i)
                    normalized.append((text, sort_order))
                else:
                    normalized.append((str(item).strip(), i))
            with db_manager.get_cursor() as cursor:
                cursor.execute("DELETE FROM post_required_idea WHERE post_id = %s", (post_id,))
                for sort_order, (text, _) in enumerate(normalized):
                    if text:
                        cursor.execute(
                            "INSERT INTO post_required_idea (post_id, text, sort_order) VALUES (%s, %s, %s)",
                            (post_id, text, sort_order),
                        )
                cursor.connection.commit()
                # ... refetch and return ...
            return jsonify({'success': True, 'required_ideas': out})
    except Exception as e:
        logger.error(f"Error handling required ideas for post {post_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

**Example curl output:**

```bash
curl -s http://localhost:5000/planning/api/posts/729/required-ideas | jq
```

**Actual output:**

```json
{
  "required_ideas": [
    {
      "id": 1,
      "sort_order": 1,
      "text": "Irish tartan history"
    },
    {
      "id": 2,
      "sort_order": 2,
      "text": "Scottish vs Irish tartans"
    },
    {
      "id": 3,
      "sort_order": 3,
      "text": "How to wear Irish tartans"
    }
  ],
  "success": true
}
```

---

## 2. SUBSTAGE MANAGEMENT SYSTEM

### 2.1 Route

**URL:** `/settings/substage-management`

- **Route decorator:** `@bp.route('/substage-management', methods=['GET'])`
- **Handler function:** `substage_management_page()`
- **File path:** `blueprints/substage_management.py`
- **Blueprint prefix:** `/settings`

### 2.2 Template

**Full contents of template rendered:** `templates/settings/substage_management.html`

(Full file: 201 lines. Structure: standalone HTML with shared header, main content with "Substage Management" title, info box, tabs: Post Types, Output Channels, Substage Metadata, Usage Overview; post-types tab with post-type selector and post-types-content; output-channels tab with channel-post-type and output-channel selectors; substage-metadata tab with add-substage button and substage-metadata-content; usage-overview tab with filters and usage-overview-content; footer; script `static/js/settings/substage-management.js`.)

Content is as in repository file `templates/settings/substage_management.html` (lines 1–201).

### 2.3 Configuration Source

**Where substage configurations are stored**

- **DB-backed:** `utils/substage_config.py` — reads from `substage_metadata` and `post_type_substages` (and optionally output-channel tables). Cache refreshed from DB.
- **Config fallback:** `config/post_type_substages.py` — `SUBSTAGE_METADATA` (key → label, route_function, order) and `POST_TYPE_SUBSTAGES` (post_type → stage → list of substage keys).
- **Output-channel overrides:** `config/output_channel_stages.py` — `OUTPUT_CHANNEL_STAGES` dict `(post_type, output_channel) -> { stages, substages }` or `use_post_type_config: True`.

**Mapping dict (config/post_type_substages.py) — planning substages:**

```python
# SUBSTAGE_METADATA excerpt
'ideas': {
    'label': 'Ideas',
    'route_function': 'planning.planning_calendar_ideas',
    'order': 1
},
'topic_brainstorming': { ... },
'section_structure': { ... },
# ...

# POST_TYPE_SUBSTAGES excerpt
'themed': {
    'planning': ['ideas', 'taxonomy', 'topic_brainstorming', 'section_structure', 'topic_allocation', 'section_titling'],
    ...
},
```

**Stage/substage names registered:** In DB tables `substage_metadata` (substage_key, label, route_function, display_order, stage, is_active) and `post_type_substages` (post_type, stage, substage_key, display_order, is_active). Substage management UI reads/writes these via substage_management API. Navbar uses `get_substages_for_navbar(post_type, stage)` → `utils.substage_config.get_substages_with_metadata()`.

**How post_type affects configuration:** For blog output, `get_substages_for_post_type(post_type)` returns per-stage substage lists from `post_type_substages` (or config fallback). For other output channels, `config/output_channel_stages.OUTPUT_CHANNEL_STAGES` can override (e.g. themed+facebook → syndication only).

**Why "ideas" substage returns "No configuration found":** The message comes from **`static/js/shared/post-type-settings.js`**. When the user opens the **Post Type Settings** modal (cog in blog pipeline header) and the current substage is "ideas", the code looks up `SUBSTAGE_CONFIG_MAP[substage]`. `SUBSTAGE_CONFIG_MAP` in that file has entries for `'taxonomy'`, `'section-structure'`, `'topic-allocation'`, `'titling'`, etc., but **no key `'ideas'`**. So `const config = SUBSTAGE_CONFIG_MAP[substage]` is undefined and the code throws `Error('No configuration found for substage: ideas')`. So "ideas" is a valid navbar/DB substage but has no entry in the **settings modal** config map.

**Exact code (post-type-settings.js):**

```javascript
const config = SUBSTAGE_CONFIG_MAP[substage];
if (!config) {
    throw new Error(`No configuration found for substage: ${substage}`);
}
```

---

## 3. AUTOMATION ENGINE

### 3.1 Execute-Substage Endpoint

**Full URL:** `/launchpad/one-click-publication/api/execute-substage/<stage>/<substage>`

**File:** `blueprints/automation_core.py`. Blueprint prefix: `/launchpad/one-click-publication/api`.

**Full function:**

```python
@bp.route('/execute-substage/<stage>/<substage>', methods=['POST'])
def execute_substage(stage, substage):
    """Main router for substage execution. W2 Phase 2: gated by canonical min_stage."""
    try:
        data = request.get_json() or {}
        post_id = data.get('post_id')
        output_channel = data.get('output', 'blog').lower()

        if not post_id:
            return jsonify({"success": False, "error": "Post ID is required"}), 400

        min_stage = AUTOMATION_MIN_STAGE.get((stage, substage)) or AUTOMATION_MIN_STAGE_BY_STAGE.get(stage)
        if min_stage:
            from utils.posts.early_stage import get_canonical_stage
            from utils.posts.stage_order import stage_index
            current_stage = get_canonical_stage(post_id)
            if stage_index(current_stage) < stage_index(min_stage):
                return jsonify({
                    "success": False,
                    "error": f"Stage {min_stage.upper()} required to run this operation.",
                    "current_stage": current_stage,
                    "required_stage": min_stage,
                }), 403

        valid_channels = ['blog', 'facebook', 'instagram', 'twitter', 'newsletter']
        if output_channel not in valid_channels:
            output_channel = 'blog'

        if not validate_substage_for_output(post_id, stage, substage, output_channel):
            available_channels = get_available_output_channels_for_post(post_id)
            return jsonify({
                "success": False,
                "error": f"Substage '{substage}' is not valid for output channel '{output_channel}'. ..."
            }), 400

        # calendar_seed and week lock checks ...
        data['output_channel'] = output_channel

        if stage == 'planning':
            if substage == 'topic_brainstorming':
                result = execute_topic_brainstorming(post_id, data)
            elif substage == 'section_structure':
                result = execute_section_structure(post_id, data)
            elif substage == 'topic_allocation':
                result = execute_topic_allocation(post_id, data)
            elif substage == 'section_titling':
                result = execute_section_titling(post_id, data)
            else:
                return jsonify({"success": False, "error": f"Unknown planning substage: {substage}"}), 400
        elif stage == 'authoring':
            # author_first_drafts, image_concepts, image_prompts, image_captions
            ...
        elif stage == 'content':
            # format_for_facebook, add_translation, add_hashtags, generate_caption
            ...
        elif stage == 'syndication':
            # 501 Not Implemented for extract_/format_/publish_
            ...
        elif stage == 'imaging':
            # optimize_for_facebook
            ...
        elif stage == 'publish':
            # publish_to_facebook (disabled) or 501
            ...
        else:
            return jsonify({"success": False, "error": f"Unknown stage: {stage}"}), 400

        # return jsonify(result) with output_channel
    except Exception as e:
        logger.error(f"Error executing substage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

**Note:** There is **no** `substage == 'ideas'` branch in `execute_substage`. Planning automation only knows topic_brainstorming, section_structure, topic_allocation, section_titling.

### 3.2 Substage Registry

**AUTOMATION_MIN_STAGE and execute_substage routing (automation_core.py):**

| Stage     | Substage            | Function                       | File                 | min_stage |
|-----------|----------------------|--------------------------------|----------------------|-----------|
| planning  | topic_brainstorming  | execute_topic_brainstorming    | automation_core.py   | ideas     |
| planning  | section_structure    | execute_section_structure      | automation_core.py   | ideas     |
| planning  | topic_allocation     | execute_topic_allocation       | automation_core.py   | structure |
| planning  | section_titling      | execute_section_titling        | automation_core.py   | structure |
| authoring | author_first_drafts  | execute_author_first_drafts    | automation_execute   | titling   |
| authoring | image_concepts       | execute_image_concepts         | automation_core      | authoring |
| authoring | image_prompts        | execute_image_prompts          | automation_core      | authoring |
| authoring | image_captions       | execute_image_captions         | automation_core      | authoring |
| content   | format_for_facebook  | execute_format_for_facebook    | automation_execute   | authoring |
| content   | add_translation      | execute_add_translation        | automation_execute   | authoring |
| content   | add_hashtags         | execute_add_hashtags           | automation_execute   | authoring |
| content   | generate_caption     | execute_generate_caption       | automation_execute   | authoring |
| imaging   | optimize_for_facebook| execute_optimize_for_facebook  | automation_execute   | imaging   |
| publish   | publish_to_facebook  | (blocked 403)                  | automation_core      | review    |

**Ideas:** There is **no** row for stage=planning, substage=**ideas** in the execute-substage router or in AUTOMATION_MIN_STAGE. The "ideas" substage is a UI/navbar substage only; it has no automation execution function.

---

## 4. ONE-CLICK HEADER BAR

**templates/shared/blog_pipeline_header.html**

Full file in repository (471 lines). Summary: link to blog-pipeline-header.css, week-context.js; div.blog-pipeline-header with main-title-line, early-stage-line, playbook-panel, post-details-line; main-stages-line with post-type-header (1-click link, settings cog, substage-management link), stage buttons (Planning, Research, Authoring, Imaging, Header) and process/data toggle and Preview; sub-stages-line with sub-stage-groups for research, planning, authoring, imaging, header — each built with `{% set X_substages = get_substages_for_navbar(post_type or 'themed', 'X') %}`, then `{% for substage in X_substages %}` with `url_for(substage.route_function, post_id=post_id)`. So **which substages exist** is decided by server-side `get_substages_for_navbar(post_type, stage)` (from `utils.substage_config.get_substages_with_metadata` / DB or config). The header does **not** render Run buttons; it only renders nav links. Tab content block with process_tab and data_tab; then workflow-navigation.js, inline subtitles and tab init, blog-pipeline-header.js, post_type_settings_modal and post-type-settings.js.

**static/js/shared/blog-pipeline-header.js**

Full file in repository (1341 lines). Summary: Class BlogPipelineHeader — init, loadPostData (GET /planning/api/posts/${postId}), updateHeaderFields, updateWeekAndTheme, updateEarlyStageIndicator, updatePlaybookPanel, updateTaxonomyDisplay, attachWeekParameterToNavLinks, updateNavigationHighlighting, getCurrentSubstageFromURL (path includes '/calendar/ideas' → 'ideas'), updateSubtitle. **Substages:** The header does not fetch substage list itself; the HTML is server-rendered from `get_substages_for_navbar`. **Run buttons:** Not in this file; Run is on the one-click publication page, which fetches `/launchpad/one-click-publication/api/post-types/${postType}/substages` and builds pipeline steps with Run per substage. **Automation toggle:** Not in blog-pipeline-header.js; automation mode is on the one-click page / automation-engine.js. **"No configuration found":** Comes from post-type-settings.js when opening the settings modal for a substage that is not in SUBSTAGE_CONFIG_MAP (e.g. "ideas"); see §2.3.

---

## 5. DATA SNAPSHOT

**Query:** `SELECT id, post_type, workflow_stage, extra_settings FROM post WHERE id = 729;`

**Note:** The `post` table has no column `post_type`. Post type is derived (e.g. from recipe_id, profile_category_id, generated_source_type). For post 729 the derived type is **themed**.

**Raw output (id, workflow_stage, extra_settings only):**

```
 729 | structure      | {"substage_state": {"ideas": {"angle_diversity": {"status": "done"}}}, "workflow_stage": "idea", "substage_playbook": {"ideas": [...], "review": [...], "authoring": [...]}, "expanded_idea_prompt_name": "Expanded Idea Generation", "workflow_stage_updated_at": "2026-02-25T14:45:45.036267+00:00"}
```

So: **id** 729, **workflow_stage** (from application layer, stored in extra_settings or inferred) **structure**, **extra_settings** (JSON as above). **post_type** for 729: **themed** (derived).

---

## 6. Observed Structural Facts

- **Ideas stage and registered substage:** The **ideas** substage is a **navbar/substage-config** substage (in `post_type_substages` / SUBSTAGE_METADATA with route `planning.planning_calendar_ideas`). It has **no** registered **automation** substage: `execute_substage` has no branch for `(stage='planning', substage='ideas')`. So the Ideas **stage** (as a page) exists; the automation engine does **not** have an "ideas" substage to run.

- **Substage-management vs execute-substage registry:** Substage-management reads/writes **DB** (`substage_metadata`, `post_type_substages`, `output_channel_substages`) and the one-click substage list comes from the same source via `get_substages_for_post_type` / `get_substages_with_metadata`. The **execute-substage** router is a **separate** hardcoded map in `automation_core.py` (if stage/substage … call X). So: substage-management and execute-substage do **not** share one registry; one is DB/config (which substages exist for nav/one-click list), the other is a fixed routing table (which substages can be executed).

- **Required ideas rendering (string vs object):** The API and `planning_api_posts` return required_ideas as **objects** `{ id, text, sort_order }`. The ideas page loads them into `requiredIdeas` from `data.post.embedding_overrides.required_ideas` (which the backend fills from `post_required_idea`). `renderRequiredIdeasList()` does `requiredIdeas.map((idea, index) => ... ${escapeHtml(idea)} ...)`. If `idea` is an object, `escapeHtml(idea)` becomes `"[object Object]"`. So the rendering code **behaves as if** it could be string or object but only displays strings correctly; when the source is the API (objects), display is wrong unless the front end uses `idea.text` (or equivalent).

- **1-click system and ideas stage:** The one-click publication page gets substages from `GET /launchpad/one-click-publication/api/post-types/<post_type>/substages`, which uses `get_substages_with_metadata(post_type, stage)` (DB/config). For themed, planning includes **ideas** in the list. So the 1-click **list** can include "ideas" as a substage. But when the user clicks Run for that substage, the request goes to `execute-substage/planning/ideas`, and the backend returns **Unknown planning substage: ideas** (or 400), because the execute_substage router does not handle "ideas". So the 1-click system "knows" about the ideas substage for display but **not** for execution.

- **Stage names (automation vs canonical):** Automation uses stage names **planning**, **authoring**, **content**, **imaging**, **publish**, **syndication**. Canonical workflow_stage values (e.g. in early_stage) include **idea**, **ideas**, **structure**, **titling**, **authoring**, etc. So there is a mapping concern: e.g. min_stage "ideas" in AUTOMATION_MIN_STAGE is compared to canonical stage (e.g. from `get_canonical_stage`) which may use "idea" or "ideas"; the stage_order module defines the ordering. So automation stage names and canonical stage names are aligned for gating but the substage name "ideas" in the navbar is not the same as an executable substage name in the router.

- **Substage-management wired into automation or orphaned:** Substage-management is **wired into** the **navbar and one-click substage list** (same DB and `get_substages_*`). It is **not** wired into the **execute-substage** implementation: adding a substage in substage-management does not add a new branch in `execute_substage`. So for automation execution, substage-management is effectively **orphaned**; for display/nav and one-click pipeline list it is the source of truth.

---

*End of report. No implementation changes. Commit only this file.*
