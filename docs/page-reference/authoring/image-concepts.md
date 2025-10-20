# Image Concepts - Technical Reference

## Purpose and Separation of Concerns

- The Image Concepts page focuses on conceiving visual concepts from section content. It is strictly an authoring task, not image generation.
- Output: curated conceptual statements and a selected concept per section. No model parameters or rendering.
- Styling details (e.g., watercolor, collage rules) are not stored here; they belong to prompt styling fields applied later during Image Prompts authoring.

## Page Overview

- **URL**: `/authoring/posts/<int:post_id>/sections/image_concepts`
- **Blueprint**: `authoring`
- **Template**: `authoring/sections/image_concepts.html`
- **Stage**: Authoring (Stage 3 of 5)
- **Substage**: Image Concepts (Step 53)
- **Purpose**: Derive one or more visual concepts from each section’s content and choose one concept as the basis for later prompt creation.

### Workflow Position
- **Preceded by**: Drafting and polishing the section text
- **Current**: Conceive and select a visual concept per section
- **Followed by**: Image Prompts authoring (where style and prompt text are created), then Image Captions

## Technical Architecture

### Flask Route Handler
```startLine:endLine:blueprints/authoring.py
@bp.route('/posts/<int:post_id>/sections/image_concepts')
def authoring_sections_image_concepts(post_id):
    """Image concepts step - Step 53"""
    try:
        with db_manager.get_cursor() as cursor:
            # Get post details
            cursor.execute("""
                SELECT id, title, status, created_at, updated_at
                FROM post 
                WHERE id = %s
            """, (post_id,))
            post = cursor.fetchone()
            
            if not post:
                return "Post not found", 404
            
            return render_template('authoring/sections/image_concepts.html', 
                                 post_id=post_id,
                                 post=post,
                                 page_title="Image Concepts",
                                 blueprint_name='authoring')
            
    except Exception as e:
        logger.error(f"Error in authoring_sections_image_concepts: {e}")
        return f"Error: {e}", 500
```

### Template Structure
- **Base Template**: `base.html`
- **Main Template**: `authoring/sections/image_concepts.html`
- **Includes**: typically uses `shared/sections_panel.html` plus authoring panels for context and outputs
- **JavaScript**: authoring bundle; page sets `window.currentStage = 'authoring'` and `window.currentSubstage = 'image-concepts'`

```startLine:endLine:templates/authoring/sections/image_concepts.html
{% block js_assets %}
{% set currentSubstage = 'image-concepts' %}
{{ js_assets('authoring') }}
<script>
    window.currentStage = 'authoring';
        window.currentSubstage = 'image-concepts';
  window.postId = {{ post_id|default(0) }};
</script>
<script src="{{ url_for('static', filename='js/authoring/image-concepts-output-panel.js') }}"></script>
{% endblock %}
```

## Responsibilities and Data Model

### What belongs here
- Extract candidate visual concepts from section text (nouns, scenes, metaphors, key entities, actions).
- Store a list of concept strings and optionally structured metadata (source sentence, confidence, rationale).
- Allow selecting one concept per section as `selected_image_concept`.

### What does NOT belong here
- Model selection (SDXL, DALL·E) and parameters.
- Prompt wording, style modifiers, or rendering.
- Any image generation calls.

### Database Fields
- **`post_section.image_concepts`**: JSON array of concept candidates per section. Example structure:
```json
[
  {
    "concept": "A lone oak tree on a windswept hill at dusk",
    "source": "paragraph_2",
    "rationale": "Encapsulates solitude theme",
    "score": 0.82
  },
  { "concept": "Close-up of ink on parchment", "score": 0.61 }
]
```
- **`post_section.selected_image_concept`**: string or object referencing the chosen concept.

Note: Style choices (e.g., watercolor, ink wash) should be stored separately (see Image Prompts doc). Do not mix styling into concepts.

## API Endpoints

### Generate Concepts (Authoring)
- Purpose: propose concept candidates from section text.
- Suggested route (existing):
```startLine:endLine:blueprints/authoring.py
@bp.route('/api/posts/<int:post_id>/sections/<section_id>/generate-image-concepts', methods=['POST'])
def api_generate_image_concepts(post_id, section_id):
    """Generate image concepts for a specific section"""
    # Resolves section; returns candidate list stored in post_section.image_concepts
```

### Select Concept (Authoring)
- Purpose: set `selected_image_concept` for a section.
```startLine:endLine:blueprints/authoring.py
@bp.route('/api/posts/<int:post_id>/sections/<section_id>/select-concept', methods=['POST'])
def api_select_concept(post_id, section_id):
    # Persists selected concept to post_section.selected_image_concept
```

## UI Behavior

- Load sections via shared panel `shared/sections_panel.html`.
- For the highlighted section:
  - Display current `image_concepts` with scores/rationales.
  - Provide actions to regenerate/refine concepts.
  - Allow selecting exactly one concept as primary.
- Persist changes immediately on selection.

## Data Flow

1. Page loads; sections fetched; current section highlighted.
2. User requests concept generation → server computes candidates → stores in `post_section.image_concepts` → returns JSON.
3. User selects a concept → POST selection → updates `post_section.selected_image_concept`.
4. Later, Image Prompts page consumes `selected_image_concept` to author final prompts (with styling kept separate).

## Error Handling

- Missing section/post: return 404 with clear message.
- DB errors: log and return JSON error with non-200 status.
- Validation: ensure selected concept exists among candidates before persisting.

## Related Pages

- Authoring: Image Prompts (`/authoring/posts/<post_id>/sections/image_prompts`)
- Authoring: Image Captions (`/authoring/posts/<post_id>/sections/image_captions`)
- Imaging: Sections Image Generation (`/imaging/posts/<post_id>/sections/image-generation`) — consumes prompts, not concepts

## Guardrails and Conventions

- Keep concepts text-only and model-agnostic.
- Do not embed style descriptors here; defer to prompts stage.
- Ensure consistent section ID resolution across APIs.
- Validate JSON shape on write; tolerate legacy values on read (list of strings).
