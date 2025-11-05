# Category Variance Types

This document explains the two types of category variance supported by the blog pipeline system.

## Overview

The system supports two distinct types of category-based variance:

1. **Process-Level Variance**: Different workflows entirely (different panels, different routes, different backend logic)
2. **Prompt-Level Variance**: Same process, different prompts only (same panels, same routes, different LLM prompts)

## Type 1: Process-Level Variance

### Description
Process-level variance means the entire workflow is different for a category. This includes:
- Different UI panels
- Different output panels
- Different routes (e.g., `photo-selection` vs `image-generation`)
- Different backend logic (e.g., photo search APIs vs LLM image generation)

### Example
**Photo-harvesting** route:
- Uses `photo_settings_panel.html` instead of `llm_settings_panel.html`
- Uses `photo_prompts_panel.html` instead of `llm_prompts_panel.html`
- Uses `output_panel_photo_harvesting.html` instead of `output_panel_image_concepts.html`
- Redirects to `/photo-selection` route instead of `/image-generation`
- Uses photo search APIs (Pexels, Unsplash) instead of LLM image generation

### Configuration
Process-level variance routes are configured in `config/authoring_panel_configs.py`:

```python
'Photo-harvesting': {
    'active': False,  # Can be marked inactive but kept in reserve
    'variance_type': 'process',  # Different workflow entirely
    'panels': [...],  # Different panel set
    'output_panel': 'authoring/includes/output_panel_photo_harvesting.html',
    'output_script': 'js/authoring/photo-harvesting-output-panel.js'
}
```

### Status: Active/Inactive
Process-level routes can be marked as `active: False` to keep them in the codebase but disable them. When inactive:
- Route handlers check the `active` flag and fall back to LLM-creation
- The route configuration is preserved for future re-enabling
- Photo-harvesting is currently marked as inactive but kept in reserve

## Type 2: Prompt-Level Variance

### Description
Prompt-level variance means the process is identical, but different prompts are used based on category. This includes:
- Same UI panels
- Same output panels
- Same routes
- Same backend logic
- Only the LLM prompt text changes

### Example
**Landscapes & Seasons** category (proposed):
- Uses same panels as LLM-creation
- Uses same routes as LLM-creation
- Uses same backend logic
- Uses prompt: `'Image Concepts Generation (Landscapes & Seasons)'` instead of `'Image Concepts Generation'`

### Configuration
Prompt-level variance uses the same panel configuration as the base route (e.g., LLM-creation) but selects different prompts via `get_category_prompt_name()`:

```python
from utils.taxonomy_helpers import get_category_prompt_name

# Get content_type_name from taxonomy
content_type_name = get_content_type_name(post_id)

# Get category-specific prompt name
prompt_name = get_category_prompt_name(
    'Image Concepts Generation',
    illustration_method,
    content_type_name
)
# Returns: 'Image Concepts Generation (Landscapes & Seasons)'
```

### Prompt Naming Convention
- Base prompt: `'{Stage} Generation'` (e.g., `'Image Concepts Generation'`)
- Category-specific: `'{Stage} Generation ({Content Type})'` (e.g., `'Image Concepts Generation (Landscapes & Seasons)'`)
- Process-level: `'{Stage} Generation ({Illustration Method})'` (e.g., `'Image Concepts Generation (Photo-harvesting)'`)

## Implementation Details

### Retrieving Category Information

**Utility Functions** (`utils/taxonomy_helpers.py`):

1. **`get_illustration_method(post_id, default='LLM-creation')`**
   - Retrieves `illustration_method` from taxonomy
   - Standardizes retrieval across all blueprints
   - Uses LEFT JOIN to handle NULL content_type_id

2. **`get_illustration_method_with_post(post_id, year=None, week=None, default='LLM-creation')`**
   - Same as above but with week context resolution
   - Returns tuple: `(target_post_id, illustration_method)`

3. **`get_content_type_name(post_id)`**
   - Retrieves `content_type.name` from taxonomy
   - Used for prompt-level variance (category-specific prompts)

4. **`get_category_prompt_name(base_name, illustration_method, content_type_name=None)`**
   - Handles both variance types
   - Process-level: Uses `illustration_method` (Photo-harvesting)
   - Prompt-level: Uses `content_type_name` (Landscapes & Seasons)
   - Returns: Category-specific prompt name or base name

### Panel Configuration System

**Location**: `config/authoring_panel_configs.py`

**Key Fields**:
- `active`: Boolean flag to enable/disable route (keeps code but disables usage)
- `variance_type`: `'process'` or `'prompt'` (for documentation/clarity)
- `panels`: List of panel configurations
- `output_panel`: Template path for output panel
- `output_script`: JavaScript file for output panel

**Usage**:
```python
from config.authoring_panel_configs import get_panel_config

panel_config = get_panel_config(illustration_method)
# Automatically checks active flag and falls back to LLM-creation if inactive
```

### Route Handler Pattern

**Standard Pattern**:
```python
# Get illustration_method with week context
from utils.taxonomy_helpers import get_illustration_method_with_post
target_post_id, illustration_method = get_illustration_method_with_post(
    post_id, url_year, url_week
)

# Get panel configuration (checks active flag)
from config.authoring_panel_configs import get_panel_config
panel_config = get_panel_config(illustration_method)

# Use panel_config in template
return render_template('template.html', 
    illustration_method=illustration_method,
    panel_config=panel_config
)
```

### Prompt Selection Pattern

**For Process-Level Variance**:
```python
# Photo-harvesting uses different prompts
if illustration_method == 'Photo-harvesting':
    prompt_name = 'Image Concepts Generation (Photo-harvesting)'
else:
    prompt_name = 'Image Concepts Generation'
```

**For Prompt-Level Variance**:
```python
# Use utility function
from utils.taxonomy_helpers import get_category_prompt_name, get_content_type_name

content_type_name = get_content_type_name(post_id)
prompt_name = get_category_prompt_name(
    'Image Concepts Generation',
    illustration_method,
    content_type_name
)
```

**Combined (Recommended)**:
```python
# Utility function handles both types automatically
from utils.taxonomy_helpers import get_category_prompt_name, get_content_type_name

content_type_name = get_content_type_name(post_id)
prompt_name = get_category_prompt_name(
    'Image Concepts Generation',
    illustration_method,
    content_type_name
)
```

## Frontend Integration

**JavaScript** (`static/js/authoring/llm-prompts-panel.js`):

The frontend automatically appends `illustration_method` query parameter to API calls for image-related stages:

```javascript
// Append illustration_method to endpoint if available
if ((url.includes('/image-concepts') || 
     url.includes('/image-prompts') || 
     url.includes('/image-captions')) && 
    window.illustrationMethod) {
    const separator = url.includes('?') ? '&' : '?';
    url = `${url}${separator}illustration_method=${encodeURIComponent(window.illustrationMethod)}`;
}
```

**Template** (`templates/authoring/sections/*.html`):

All templates set `window.illustrationMethod`:

```html
<script>
    window.illustrationMethod = '{{ illustration_method|default("LLM-creation") }}';
</script>
```

## Adding New Categories

### Process-Level Variance

1. Add configuration to `config/authoring_panel_configs.py`:
   ```python
   'New-Process-Route': {
       'active': True,
       'variance_type': 'process',
       'panels': [...],  # Different panels
       'output_panel': 'path/to/output_panel.html',
       'output_script': 'js/path/to/output-script.js'
   }
   ```

2. Create route handler that checks `active` flag
3. Create templates and panels
4. Update redirect logic if needed

### Prompt-Level Variance

1. Ensure category has `content_type_id` set in `post` table
2. Create category-specific prompts in `llm_prompt` table:
   - `'Image Concepts Generation (Category Name)'`
   - `'Image Prompts Generation (Category Name)'`
   - `'Image Captions Generation (Category Name)'`
   - etc.

3. No code changes needed - utility functions handle prompt selection automatically

## Current Status

### Process-Level Routes
- **Photo-harvesting**: `active: False` (inactive but kept in reserve)

### Prompt-Level Routes
- **Landscapes & Seasons**: Ready for implementation (prompts can be created)

### Default Route
- **LLM-creation**: Always active, default fallback

## Testing Checklist

When adding or modifying category variance:

- [ ] Process-level routes: Verify `active` flag works correctly
- [ ] Process-level routes: Test fallback to LLM-creation when inactive
- [ ] Prompt-level routes: Verify prompts are selected correctly
- [ ] Prompt-level routes: Verify prompts exist in database
- [ ] Both types: Verify route banners display correctly
- [ ] Both types: Verify frontend passes `illustration_method` query param
- [ ] Both types: Verify week context resolution works
- [ ] Both types: Verify no silent fallbacks (prompts fail clearly if missing)

