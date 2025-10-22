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

The page uses specialized APIs for LLM-assisted prompt generation and persistence.

### Core Endpoints
- **Fetch sections**: `GET /authoring/api/posts/<post_id>/sections`
- **Generate image prompt**: `POST /authoring/api/generate-image-prompt-from-builder-v2`
  - Uses carefully developed LLM-specific prompts from database
  - Applies model-aware character limit substitutions
  - Stores exact raw HTTP requests sent to LLM
  - Parameters: `post_id`, `section_id`, `compiled_prompt`, `enable_compression`, `enable_expansion`, `llm_provider`, `llm_model`
- **Get intercepted LLM messages**: `GET /authoring/api/posts/<post_id>/sections/<section_id>/intercepted-message`
  - Returns exact raw HTTP requests, complete API requests, and raw messages
  - Used by Complete LLM Input field to show verbatim data sent to LLM
- **Save prompt JSON**: `POST /authoring/api/posts/<post_id>/sections/<section_id>/save-image-prompt`
- **Get LLM prompt details**: `GET /authoring/api/posts/<post_id>/sections/<section_id>/llm-prompt-details`

### LLM Service Integration
- **LLM Service**: `modules/llm_service.py` - Centralized service for all LLM interactions
- **Intercept Context**: All LLM calls require valid `post_id` and `section_id` for proper data storage
- **Raw HTTP Storage**: Complete HTTP requests stored in `llm_message_intercepts.raw_http_request`
- **Model-Specific Limits**: GPT-Image-1 (2000 chars), SDXL (400 chars)

## UI Behavior

### Section Selection and Data Loading
- When a section is highlighted:
  - Load `selected_image_concept` and existing `image_prompts` JSON
  - **Complete LLM Input field** automatically refreshes to show latest stored data
  - Section selection emits `sectionSelected` event for panel communication
  - Dynamic section ID detection from `window.sectionsPanel.sections` objects

### Prompt Generation
- **Individual Generate Button**: 
  - Uses fresh prompt generation from database templates
  - Reads compiled prompt from Prompt Builder Panel
  - Generates detailed prompts (900+ characters for GPT-Image-1)
  - No compression for GPT-Image-1 models (uses full 2000 character budget)
- **Generate All Button**:
  - Iterates individual Generate button logic over all selected sections
  - Uses same API endpoint and parameters as individual generation
  - Extracts actual concept descriptions from `section.image_concepts` data
  - Shows proper success/error status for each section

### Complete LLM Input Field
- **Purpose**: Shows exact raw HTTP request sent to LLM (verbatim, no reconstruction)
- **Data Source**: `llm_message_intercepts.raw_http_request` field
- **Content**: Complete HTTP request including method, URL, headers, and JSON payload
- **Auto-refresh**: Updates when sections are selected or prompts are generated
- **No Fallbacks**: Only shows actual stored data, no specimen text or hardcoded content

### Live Validation and Feedback
- Live counters for character limits (authoring-level budgets, not model budgets)
- Style Guidelines panel displays rules and examples
- Save operations debounce to persist JSON updates
- Real-time status updates for batch generation progress

## Data Flow

### Complete LLM Prompt Generation Flow
1. **Page Load**: Sections list and LLM prompt templates fetched from database
2. **Section Selection**: 
   - User selects section from left panel
   - `sectionSelected` event emitted
   - Complete LLM Input field loads latest stored data for that section
3. **Prompt Generation**:
   - User clicks Generate button or Generate All
   - System retrieves `system_prompt_template` and `prompt_text` from `llm_prompt` table
   - Applies model-aware character limit substitutions
   - **Automatic Concept Extraction**: System extracts actual concept data from `post_section.image_concepts` JSON field using `selected_image_concept` ID
   - Replaces placeholders with actual concept data (description, mood, key_visual_elements)
   - Creates proper `intercept_context` with `post_id` and `section_id`
   - Calls `llm_service.execute_llm_request()` with intercept context
4. **Data Storage**:
   - LLM service stores exact raw HTTP request in `llm_message_intercepts.raw_http_request`
   - Stores complete API request, raw messages, and formatted intercepted message
   - Updates `post_section.image_prompts` with generated prompt
5. **UI Update**:
   - Complete LLM Input field refreshes to show newly stored raw HTTP request
   - Generated prompt displayed in Output panel
   - Section status updated to "Complete"

### Automatic Concept Data Extraction Flow
1. **Database Query**: System retrieves `image_concepts` JSON field from `post_section` table
2. **JSON Parsing**: Parses the JSON structure containing `concepts` array and `selected_image_concept` ID
3. **ID Matching**: Iterates through concepts array to find matching `concept_id`
4. **Data Assembly**: Builds concept text from:
   - `concept_description` (primary content)
   - `concept_mood` (formatted as "Mood: ...")
   - `key_visual_elements` (formatted as "Key Elements: ...")
5. **Fallback Handling**: If database extraction fails, falls back to frontend-provided data
6. **Placeholder Replacement**: Uses extracted concept text in LLM prompt template

### Database Schema Updates
- **`llm_message_intercepts`**: Stores intercepted LLM communications
  - `raw_http_request`: Complete HTTP request string (method, URL, headers, body)
  - `complete_api_request`: Full JSON API request payload
  - `raw_messages`: JSON array of messages sent to LLM
  - `intercepted_message`: Formatted display version
- **`llm_prompt`**: Stores LLM prompt templates
  - `system_prompt_template`: Clean template without JSON instructions
  - `system_prompt`: Complete prompt with JSON formatting instructions
  - `prompt_text`: User prompt template with placeholders

## Error Handling

### System-Level Error Handling
- **Missing post/section**: Return 404; guard UI with proper error messages
- **Invalid intercept context**: LLM service requires valid `post_id` and `section_id` - no default fallbacks
- **Corrupted data**: Clean up malformed section IDs and records with missing context
- **JSON parsing errors**: Graceful handling of `image_concepts` data (string vs object)

### Frontend Error Handling
- **Section ID detection**: Dynamic detection from `window.sectionsPanel.sections` objects
- **API response validation**: Proper HTTP status checking before JSON parsing
- **Batch generation errors**: Individual section error handling with detailed logging
- **Data refresh failures**: Fallback mechanisms for Complete LLM Input field loading

### Database Integrity
- **No specimen text**: System only uses actual concept data from database
- **No hardcoded content**: All prompts generated from database templates
- **Consistent data storage**: All LLM calls properly store data with correct section IDs
- **Automatic operation**: System works for all sections and future posts without manual intervention

## Interplay with Imaging

- Imaging page consumes `image_prompts` and applies model-specific rendering and parameters.
- Compatible with all supported models: SDXL LoRA, DALL-E 3, GPT-Image-1, and DALL-E 2.
- No direct calls to generation APIs here; the UI should not expose imaging controls.

### Recent Imaging Simplifications (October 2025)
- **Removed Rendered Prompt Preview Panel**: Eliminated confusing preview that showed truncated/nonsense prompts
- **Removed All Truncation**: Full prompts now sent to all models without character limits
- **Direct Database Access**: Imaging now directly extracts `image_prompt` from `post_section.image_prompts` JSON
- **Model Selection Fix**: Default model changed from DALL-E to gpt-image-1
- **Quality Parameter Fix**: Corrected quality='high' for GPT-Image-1 compatibility
- **Eliminated Prompt Service**: Removed unnecessary prompt rendering layer for simpler data flow

## Related Pages

- Authoring: Image Concepts (`/authoring/posts/<post_id>/sections/image_concepts`)
- Authoring: Image Captions
- Imaging: Sections Image Generation (`/imaging/posts/<post_id>/sections/image-generation`)
- Header: Header Image (`/header/posts/<post_id>/header-image`)

## Recent System Improvements (October 2025)

### Major Fixes Implemented (October 22, 2025)
1. **Complete LLM Input Field**: Now shows exact raw HTTP requests sent to LLM (verbatim, no reconstruction)
2. **Compression Logic**: Disabled for GPT-Image-1 models - uses full 2000 character budget
3. **Generate All Button**: Rewritten to use same logic as individual Generate button
4. **Section Selection**: Fixed dynamic section ID detection and automatic data refresh
5. **Data Integrity**: Eliminated specimen text and hardcoded content - uses only actual concept data
6. **Automatic Concept Extraction**: Backend now automatically extracts selected concept data from database
7. **Simplified Image Generation**: Removed truncation and Rendered Prompt Preview panel
8. **Model Selection Fix**: Default changed from DALL-E to gpt-image-1
9. **Quality Parameter Fix**: Corrected quality='high' for GPT-Image-1 compatibility

### Technical Improvements
- **LLM Service Consolidation**: All LLM calls go through centralized `modules/llm_service.py`
- **Intercept Context Enforcement**: Mandatory `post_id` and `section_id` for all LLM calls
- **Raw HTTP Storage**: Complete HTTP requests stored in `llm_message_intercepts.raw_http_request`
- **Model-Aware Substitutions**: Character limits automatically adjusted based on target model
- **Event-Driven Architecture**: Proper `sectionSelected` event emission for panel communication
- **Database-Driven Concept Extraction**: Automatic parsing of `image_concepts` JSON field
- **ID-Based Concept Matching**: Uses `selected_image_concept` to find correct concept data
- **Eliminated Fallback Text**: System only uses actual concept data, no specimen text

### Automatic Concept Data Extraction
The system now automatically extracts concept data from the database without requiring frontend changes:

```python
# Automatic extraction from post_section.image_concepts JSON
if section['image_concepts']:
    image_concepts_data = json.loads(section['image_concepts'])
    selected_concept_id = section.get('selected_image_concept')
    
    # Find matching concept by ID
    for concept in image_concepts_data.get('concepts', []):
        if concept.get('concept_id') == selected_concept_id:
            # Build concept text from database fields
            concept_parts = []
            if concept.get('concept_description'):
                concept_parts.append(concept['concept_description'])
            if concept.get('concept_mood'):
                concept_parts.append(f"Mood: {concept['concept_mood']}")
            if concept.get('key_visual_elements'):
                concept_parts.append(f"Key Elements: {concept['key_visual_elements']}")
            concept_text = '\n'.join(concept_parts)
            break
```

### Performance Results
- **Prompt Quality**: GPT-Image-1 prompts now 900+ characters (vs previous ~400)
- **Data Accuracy**: Complete LLM Input field shows exact data sent to LLM
- **System Reliability**: Automatic operation for all sections and future posts
- **Error Reduction**: Proper error handling and status reporting for batch operations
- **Concept Accuracy**: All sections now use actual selected concept data instead of fallback text
- **Imaging Simplification**: Removed unnecessary truncation and preview panels
- **Model Compatibility**: Fixed quality parameters for GPT-Image-1 model

## Guardrails and Conventions

- Keep prompt JSON model-agnostic; avoid embedding model parameter keys.
- Separate `core` idea from `styling` consistently across sections.
- Preserve legacy data; do non-destructive normalization.
- Style guidelines are advisory at authoring time; hard constraints applied during imaging.
