# Image Prompts - Technical Reference

## Purpose and Separation of Concerns

- The Image Prompts page transforms the selected visual concept into concrete, model-agnostic prompt text, plus separate styling fields.
- Output: per-section prompt records suitable for later imaging. No images are generated here.
- Clear separation from Image Concepts (ideation) and Imaging (rendering and file outputs).

## Page Overview

- **URL**: `/authoring/posts/<int:post_id>/sections/image_prompts`
- **Blueprint**: `authoring`
- **Template**: `authoring/sections/image_prompts.html`
- **Stage**: Authoring (Stage 3 of 5)
- **Substage**: Image Prompts (Step 54)
- **Purpose**: Author and manage the per-section image prompts and styling data that downstream imaging will consume.

### Workflow Position
- **Preceded by**: Image Concepts (selected concept exists)
- **Current**: Author prompt text and styling attributes
- **Followed by**: Image Captions → Imaging (Sections Image Generation)

## Technical Architecture

### Flask Route Handler
```startLine:endLine:blueprints/authoring.py
@bp.route('/posts/<int:post_id>/sections/image_prompts')
def authoring_sections_image_prompts(post_id):
    """Image prompts step - Step 54"""
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            if not post:
                return "Post not found", 404

            # llm_prompt + image_format style_guidelines fetched for UI context
            # Renders authoring/sections/image_prompts.html
            return render_template('authoring/sections/image_prompts.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Image Prompts",
                                 blueprint_name='authoring',
                                 prompt_name=prompt_name,
                                 system_prompt=system_prompt,
                                 user_prompt=user_prompt,
                                 style_guidelines=style_guidelines)
    except Exception as e:
        logger.error(f"Error in authoring_sections_image_prompts: {e}")
        return f"Error: {e}", 500
```

### Template Structure
- **Base Template**: `base.html`
- **Main Template**: `authoring/sections/image_prompts.html`
- **Includes**:
  - `shared/sections_panel.html` (select/highlight section)
  - `authoring/includes/llm_settings_panel.html`
  - `authoring/includes/llm_prompts_panel.html`
  - `authoring/includes/prompt_builder_panel_image_prompts.html`
  - `authoring/includes/context_panel.html`
  - `authoring/includes/batch_progress_panel.html`
  - `authoring/includes/output_panel_image_prompts.html`

```startLine:endLine:templates/authoring/sections/image_prompts.html
{% block js_assets %}
{{ js_assets('authoring') }}
<script>
    window.currentStage = 'authoring';
                window.currentSubstage = 'image-prompts';
  window.postId = {{ post_id|default(0) }};
</script>
{% endblock %}
```

## Responsibilities and Data Model

### What belongs here
- Author and store per-section prompt data derived from `selected_image_concept`.
- Maintain styling attributes in a distinct structure from the core prompt idea.
- Provide live validation against style guidelines and prompt length.

### What does NOT belong here
- Model-specific parameters (width, steps, LoRA scale, size/quality) or any generation.
- Header collage prompt compilation (belongs to Header stage).

### Database Fields
- Primary prompt field: **`post_section.image_prompts`** (JSON). Support both legacy text and structured JSON.
- Styling field: distinct JSON field (recommended) separate from concept text; if not present, use namespaced keys within `image_prompts` while planning migration.

Recommended schema (back-compatible):
```json
{
  "version": 1,
  "core": {
    "idea": "A lone oak tree on a windswept hill at dusk",  
    "description": "Emphasize solitude; maintain open sky and rolling fields"
  },
  "styling": {
    "medium": "watercolor and ink", 
    "palette": ["indigo", "sap green", "sepia"],
    "composition": "rule-of-thirds, negative space top third",
    "lighting": "golden hour",
    "constraints": ["no text", "no watermark in frame"]
  },
  "negatives": ["low-res", "blurry"],
  "keywords": ["windswept", "solitude"],
  "notes": "Avoid hyperrealism; keep brush texture"
}
```

Backward compatibility rules:
- If `image_prompts` is a string, treat as `core.description`.
- If JSON missing fields, auto-fill minimal structure on read.

## API Endpoints

The page typically uses shared authoring APIs for LLM assistance and persistence.

- Fetch sections: `GET /authoring/api/posts/<post_id>/sections`
- Save prompt JSON: `POST /authoring/api/posts/<post_id>/sections/<section_id>/save-image-prompt` (proposed if not present)
- Validate prompt: client-side checks; optional `POST /authoring/api/validate-prompt` for server-side enforcement
- Style guidelines reference: sourced from `image_format.extra_settings->>'style_guidelines'`

## UI Behavior

- When a section is highlighted:
  - Load `selected_image_concept` and existing `image_prompts` JSON.
  - Show Prompt Builder fields for core idea and styling separately.
  - Live counters for character limits (authoring-level budgets, not model budgets).
  - Style Guidelines panel displays rules and examples.
  - Save operations debounce to persist JSON updates.

- Batch tools:
  - Generate draft prompts for all sections from selected concepts.
  - Provide per-section review and override.

## Data Flow

1. Page loads; sections list and guidelines fetched.
2. User selects a section; page loads its concept and prompt JSON.
3. Edits to core idea and styling are stored to `post_section.image_prompts` (structured JSON).
4. Downstream imaging reads this data and performs model-aware rendering (outside authoring).

## Error Handling

- Missing post/section: return 404; guard UI.
- Invalid JSON shape: normalize on read; reject on write with detailed messages.
- Concurrent edits: last-write-wins with timestamp checks; consider etags later.

## Interplay with Imaging

- Imaging page consumes `image_prompts` and applies model-specific rendering and parameters.
- No direct calls to generation APIs here; the UI should not expose imaging controls.

## Related Pages

- Authoring: Image Concepts (`/authoring/posts/<post_id>/sections/image_concepts`)
- Authoring: Image Captions
- Imaging: Sections Image Generation (`/imaging/posts/<post_id>/sections/image-generation`)
- Header: Header Image (`/header/posts/<post_id>/header-image`)

## Guardrails and Conventions

- Keep prompt JSON model-agnostic; avoid embedding model parameter keys.
- Separate `core` idea from `styling` consistently across sections.
- Preserve legacy data; do non-destructive normalization.
- Style guidelines are advisory at authoring time; hard constraints applied during imaging.
