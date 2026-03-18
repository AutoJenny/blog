# Category-Contingent Prompts - Implementation Recommendation

## Overview

This document provides a recommendation for making the Ideas page (and other templates) category-contingent, similar to how the Imaging process varies by illustration method.

**CRITICAL PRINCIPLES: NO FALLBACKS, DATABASE PERSISTENCE ONLY**
- Explicit prompt selection only
- Fail clearly if prompt not found (no silent fallbacks)
- Display selected prompt name in UI header
- User must explicitly choose "Default" or category-specific prompt
- **ALL settings persisted in database** (`post.extra_settings` JSONB field)
- **NO localStorage, sessionStorage, or temporary storage**
- Selection persists across sessions, devices, and page reloads

## Current State Analysis

### Ideas Page (`/planning/posts/<id>/calendar/ideas`)

**Current Implementation:**
- Uses generic prompt lookup: `WHERE name ILIKE '%idea%expansion%' OR name ILIKE '%scottish%idea%'`
- Single prompt used for all categories
- Location: `blueprints/planning_api_post_specific.py:311-326`

**Frontend:**
- Uses `LLMPromptsPanel` component from `templates/authoring/includes/llm_prompts_panel.html`
- Initialized in `templates/planning/calendar/ideas.html:612-617`
- No category detection currently

### Imaging Process (Reference Pattern)

**How it works:**
1. **Taxonomy Detection**: Reads `illustration_method` from `taxonomy_item` table via `post.content_type_id`
2. **Prompt Selection**: Uses different prompt names based on category:
   - `'Image Prompts Generation (Photo-harvesting)'` for Photo-harvesting
   - `'Image Prompts Generation'` for LLM-creation (default)
3. **Frontend**: Appends `illustration_method` query parameter to API endpoint
4. **Backend**: API endpoint checks `illustration_method` parameter to select prompt name
5. **Location**: `blueprints/authoring_api_prompts.py:389-402`

**Key Code Pattern:**
```python
# Backend (blueprints/authoring_api_prompts.py)
illustration_method = request.args.get('illustration_method', 'LLM-creation')
prompt_name = 'Image Prompts Generation (Photo-harvesting)' if illustration_method == 'Photo-harvesting' else 'Image Prompts Generation'
```

```javascript
// Frontend (static/js/authoring/llm-prompts-panel.js:148-153)
if ((url.includes('/image-concepts') || url.includes('/image-prompts')) && window.illustrationMethod) {
    const separator = url.includes('?') ? '&' : '?';
    url = `${url}${separator}illustration_method=${encodeURIComponent(window.illustrationMethod)}`;
}
```

## Taxonomy Structure

**Database Schema:**
- `post.theme_id` → References `taxonomy_item` (theme tier)
- `post.content_type_id` → References `taxonomy_item` (content_type tier)
- `post.format_id` → References `taxonomy_item` (format tier)
- `taxonomy_item.illustration_method` → Used for Imaging (Photo-harvesting vs LLM-creation)

**Retrieval:**
- API: `GET /planning/api/posts/<id>/taxonomy` (from `blueprints/planning_api_taxonomy.py:19-62`)
- Returns: `theme_name`, `content_type_name`, `format_name`, etc.

## Recommended Implementation

### Content Type-Based Prompt Selection

**Rationale:** Content types (e.g., "History", "Culture", "Nature") are more specific than themes and align better with different writing approaches.

**Approach:**
1. Create prompt naming convention: `"Expanded Idea Generation (<content_type_name>)"`
2. **Default prompt**: `"Expanded Idea Generation"` (explicit selection)
3. Use `content_type_name` from taxonomy to suggest category-specific prompt
4. **Explicit selection**: User or system must explicitly choose which prompt to use
5. **No fallbacks**: If selected prompt doesn't exist, fail clearly with error message
6. **Display selection**: Show selected prompt name in prompt panel header

**Implementation Steps:**

#### Backend Changes (`blueprints/planning_api_post_specific.py`)

1. **Create API endpoint to get available prompts and current selection:**
   ```python
   @bp.route('/api/posts/<int:post_id>/expanded-idea-prompt-selection', methods=['GET'])
   def api_get_expanded_idea_prompt_selection(post_id):
       """Get available prompt options and current selection for expanded idea generation"""
       try:
           with db_manager.get_cursor() as cursor:
               # Get taxonomy for the post
               cursor.execute("""
                   SELECT ti.display_name as content_type_name
                   FROM post p
                   LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
                   WHERE p.id = %s
               """, (post_id,))
               taxonomy_result = cursor.fetchone()
               content_type_name = taxonomy_result.get('content_type_name') if taxonomy_result else None
               
               # Get available prompts
               available_prompts = []
               
               # Default prompt
               cursor.execute("""
                   SELECT name, id FROM llm_prompt 
                   WHERE name = 'Expanded Idea Generation'
                   ORDER BY updated_at DESC 
                   LIMIT 1
               """)
               default_prompt = cursor.fetchone()
               if default_prompt:
                   available_prompts.append({
                       'name': default_prompt['name'],
                       'id': default_prompt['id'],
                       'is_default': True
                   })
               
               # Category-specific prompt (if category exists)
               if content_type_name:
                   category_prompt_name = f'Expanded Idea Generation ({content_type_name})'
                   cursor.execute("""
                       SELECT name, id FROM llm_prompt 
                       WHERE name = %s
                       ORDER BY updated_at DESC 
                       LIMIT 1
                   """, (category_prompt_name,))
                   category_prompt = cursor.fetchone()
                   if category_prompt:
                       available_prompts.append({
                           'name': category_prompt['name'],
                           'id': category_prompt['id'],
                           'is_default': False,
                           'category': content_type_name
                       })
               
               # Get current selection (from post settings)
               cursor.execute("""
                   SELECT extra_settings FROM post WHERE id = %s
               """, (post_id,))
               post_result = cursor.fetchone()
               current_selection = None
               
               if post_result and post_result.get('extra_settings'):
                   settings = post_result['extra_settings']
                   current_selection = settings.get('expanded_idea_prompt_name')
               
               # LEGACY POSTS: If no selection exists, explicitly set to default prompt
               # This is an explicit initial selection, not a fallback
               # We save it to the post so it's persistent
               if not current_selection and available_prompts:
                   # Find the default prompt (marked with is_default: true)
                   default_prompt = next((p for p in available_prompts if p.get('is_default')), None)
                   if default_prompt:
                       current_selection = default_prompt['name']
                       # Save this explicit selection to the post for legacy posts
                       import json
                       if post_result and post_result.get('extra_settings'):
                           settings = post_result['extra_settings']
                       else:
                           settings = {}
               settings['expanded_idea_prompt_name'] = current_selection
               # PERSIST TO DATABASE - NO TEMPORARY STORAGE
               cursor.execute("""
                   UPDATE post 
                   SET extra_settings = %s::jsonb
                   WHERE id = %s
               """, (json.dumps(settings), post_id))
               cursor.connection.commit()
                   else:
                       # No default prompt available - this is a system error
                       return jsonify({
                           'error': 'Default prompt "Expanded Idea Generation" not found. Please create it in the database.'
                       }), 500
               
               return jsonify({
                   'success': True,
                   'available_prompts': available_prompts,
                   'current_selection': current_selection,
                   'content_type_name': content_type_name
               })
       except Exception as e:
           logger.error(f"Error getting prompt selection: {e}")
           return jsonify({'error': str(e)}), 500
   ```

2. **Create API endpoint to set prompt selection:**
   ```python
   @bp.route('/api/posts/<int:post_id>/expanded-idea-prompt-selection', methods=['POST'])
   def api_set_expanded_idea_prompt_selection(post_id):
       """Set the selected prompt for expanded idea generation"""
       try:
           data = request.get_json()
           prompt_name = data.get('prompt_name')
           
           if not prompt_name:
               return jsonify({'error': 'prompt_name is required'}), 400
           
           # Verify prompt exists
           with db_manager.get_cursor() as cursor:
               cursor.execute("""
                   SELECT id FROM llm_prompt WHERE name = %s
               """, (prompt_name,))
               if not cursor.fetchone():
                   return jsonify({'error': f'Prompt "{prompt_name}" not found'}), 404
               
               # Save selection to post.extra_settings
               cursor.execute("""
                   SELECT extra_settings FROM post WHERE id = %s
               """, (post_id,))
               post_result = cursor.fetchone()
               
               import json
               if post_result and post_result.get('extra_settings'):
                   settings = post_result['extra_settings']
               else:
                   settings = {}
               
               settings['expanded_idea_prompt_name'] = prompt_name
               
               # PERSIST TO DATABASE - NO TEMPORARY STORAGE
               cursor.execute("""
                   UPDATE post 
                   SET extra_settings = %s::jsonb
                   WHERE id = %s
               """, (json.dumps(settings), post_id))
               cursor.connection.commit()
               
               return jsonify({'success': True, 'prompt_name': prompt_name})
       except Exception as e:
           logger.error(f"Error setting prompt selection: {e}")
           return jsonify({'error': str(e)}), 500
   ```

3. **Modify `api_posts_expanded_idea()` to use explicit selection:**
   ```python
   # Get selected prompt name from post settings
   cursor.execute("""
       SELECT extra_settings FROM post WHERE id = %s
   """, (post_id,))
   post_result = cursor.fetchone()
   prompt_name = None
   
   if post_result and post_result.get('extra_settings'):
       settings = post_result['extra_settings']
       prompt_name = settings.get('expanded_idea_prompt_name')
   
   # LEGACY POSTS: If no selection exists, use default prompt
   # This should only happen if the selection endpoint hasn't been called yet
   # (which would have set the selection). This is an explicit default, not a fallback.
   if not prompt_name:
       prompt_name = 'Expanded Idea Generation'
   
   # Get the selected prompt - NO FALLBACKS
   cursor.execute("""
       SELECT system_prompt, prompt_text
       FROM llm_prompt 
       WHERE name = %s
       ORDER BY updated_at DESC 
       LIMIT 1
   """, (prompt_name,))
   prompt_data = cursor.fetchone()
   
   # FAIL CLEARLY if prompt not found
   if not prompt_data:
       return jsonify({
           'error': f'Selected prompt "{prompt_name}" not found. Please select a valid prompt in the prompt panel.'
       }), 404
   ```

#### Frontend Changes

1. **Update `LLMPromptsPanel` to support prompt selection (`static/js/authoring/llm-prompts-panel.js`):**
   ```javascript
   class LLMPromptsPanel {
       constructor(options = {}) {
           // ... existing initialization ...
           this.promptSelectionEndpoint = options.promptSelectionEndpoint;
           this.availablePrompts = [];
           this.currentPromptName = null;
       }
       
       async loadPromptSelection() {
           if (!this.promptSelectionEndpoint) return;
           
           try {
               const response = await fetch(this.promptSelectionEndpoint);
               const data = await response.json();
               
               if (data.success) {
                   this.availablePrompts = data.available_prompts || [];
                   this.currentPromptName = data.current_selection;
                   
                   // Update header to show selected prompt name
                   this.updatePromptTitle(this.currentPromptName || 'No prompt selected');
                   
                   // Show prompt selector if multiple options available
                   if (this.availablePrompts.length > 1) {
                       this.showPromptSelector();
                   }
               }
           } catch (error) {
               console.error('[LLM Prompts Panel] Error loading prompt selection:', error);
           }
       }
       
       showPromptSelector() {
           // Create dropdown selector in panel header
           const header = document.querySelector('.llm-prompts-panel .panel-header');
           if (!header) return;
           
           // Remove existing selector if present
           const existing = header.querySelector('.prompt-selector');
           if (existing) existing.remove();
           
           const selector = document.createElement('select');
           selector.className = 'prompt-selector';
           selector.style.cssText = 'margin-left: 1rem; padding: 0.25rem 0.5rem; background: #1e293b; border: 1px solid #334155; border-radius: 4px; color: #f1f5f9;';
           
           this.availablePrompts.forEach(prompt => {
               const option = document.createElement('option');
               option.value = prompt.name;
               option.textContent = prompt.is_default ? 'Default' : prompt.name.replace('Expanded Idea Generation (', '').replace(')', '');
               if (prompt.name === this.currentPromptName) {
                   option.selected = true;
               }
               selector.appendChild(option);
           });
           
           selector.addEventListener('change', async (e) => {
               await this.selectPrompt(e.target.value);
           });
           
           header.appendChild(selector);
       }
       
       async selectPrompt(promptName) {
           if (!this.promptSelectionEndpoint) return;
           
           try {
               const response = await fetch(this.promptSelectionEndpoint.replace('/selection', '/selection'), {
                   method: 'POST',
                   headers: { 'Content-Type': 'application/json' },
                   body: JSON.stringify({ prompt_name: promptName })
               });
               
               const data = await response.json();
               if (data.success) {
                   this.currentPromptName = promptName;
                   this.updatePromptTitle(promptName);
                   // Reload the prompt content
                   await this.loadPromptFromAPI();
               } else {
                   alert(`Error selecting prompt: ${data.error}`);
               }
           } catch (error) {
               console.error('[LLM Prompts Panel] Error selecting prompt:', error);
               alert(`Error selecting prompt: ${error.message}`);
           }
       }
       
       async loadPromptFromAPI() {
           // Use selected prompt name instead of generic endpoint
           if (!this.currentPromptName) {
               await this.loadPromptSelection();
           }
           
           // Build endpoint with selected prompt name
           let url = this.config.promptEndpoint;
           if (this.currentPromptName) {
               const separator = url.includes('?') ? '&' : '?';
               url = `${url}${separator}prompt_name=${encodeURIComponent(this.currentPromptName)}`;
           }
           
           // ... rest of existing loadPromptFromAPI code ...
       }
   }
   ```

2. **Update `LLMPromptsPanel` initialization (`templates/planning/calendar/ideas.html`):**
   ```javascript
   document.addEventListener('DOMContentLoaded', function() {
       if (typeof LLMPromptsPanel !== 'undefined') {
           window.llmPromptsPanel = new LLMPromptsPanel({
               postId: window.postId,
               pageType: 'expanded-idea',
               promptEndpoint: `/planning/api/posts/${window.postId}/expanded-idea-prompt`,
               promptSelectionEndpoint: `/planning/api/posts/${window.postId}/expanded-idea-prompt-selection`
           });
           
           // Load prompt selection from database first (not localStorage/sessionStorage)
           window.llmPromptsPanel.loadPromptSelection().then(() => {
               // Then load the actual prompt content from database
               window.llmPromptsPanel.loadPromptFromAPI();
           });
       }
   });
   ```

3. **Update prompt panel header to display selected prompt name:**
   - Modify `templates/authoring/includes/llm_prompts_panel.html`
   - Update header to show: `"LLM Prompts: <selected_prompt_name>"`
   - Add prompt selector dropdown if multiple options available

### Prompt Naming Examples

**Category-specific prompts:**
- `"Expanded Idea Generation (History)"`
- `"Expanded Idea Generation (Culture)"`
- `"Expanded Idea Generation (Landscapes & Seasons)"`
- `"Expanded Idea Generation (Nature)"`

**Default prompt:**
- `"Expanded Idea Generation"` (always available as "Default" option)

## Prompt Naming Convention

**Recommended naming pattern:**
- Category-specific: `"<Function> (<Category>)"`
- Default: `"<Function>"`

**Examples:**
- `"Expanded Idea Generation (History)"`
- `"Expanded Idea Generation (Culture)"`
- `"Expanded Idea Generation (Landscapes & Seasons)"`
- `"Expanded Idea Generation"` (default, always available)

**Database:**
- Store in `llm_prompt` table with `name` field
- Use exact match (not ILIKE) for reliability
- **No fallbacks**: If selected prompt doesn't exist, return clear error

## Applying to Other Templates

### Templates Needing Category-Contingent Prompts

1. **Topic Brainstorming** (`/planning/posts/<id>/concept/brainstorm`)
   - Prompt: `"Topic Brainstorming (<category>)"`
   - Use same pattern as Ideas

2. **Section Structure Design** (`/planning/posts/<id>/concept/section-structure`)
   - Prompt: `"Section Structure Design (<category>)"`

3. **Topic Allocation** (`/planning/posts/<id>/concept/topic-allocation`)
   - Prompt: `"Topic Allocation (<category>)"`

4. **Section Titling** (`/planning/posts/<id>/concept/titling`)
   - Prompt: `"Section Titling (<category>)"`

5. **Drafting** (`/authoring/posts/<id>/sections/author-first-drafts`)
   - Prompt: `"Section Drafting (<category>)"`

### Implementation Pattern for All Templates

**Standardized approach:**
1. Create selection endpoint (`/api/posts/<id>/<function>-prompt-selection`) for each template
2. Create set selection endpoint (POST to same URL)
3. Modify generation endpoint to use explicit selection from `post.extra_settings`
4. Update frontend to load selection and show selector
5. Auto-select default for legacy posts (explicit initial selection, saved to DB)

**Key Requirements:**
- Default prompt must always exist (`"<Function>"`)
- Selection stored in `post.extra_settings['<function>_prompt_name']` (database JSONB field)
- **Database persistence only** - NO localStorage, sessionStorage, or temporary storage
- Legacy posts auto-select default on first access (selection saved to database)
- Clear error if selected prompt missing
- No fallback logic anywhere
- Selection persists across sessions, devices, and page reloads

## Migration Strategy

### Phase 1: Ideas Page (Proof of Concept)
1. Implement explicit prompt selection for Ideas page
2. Create test prompts:
   - `"Expanded Idea Generation (History)"`
   - `"Expanded Idea Generation (Culture)"`
   - `"Expanded Idea Generation (Landscapes & Seasons)"`
   - `"Expanded Idea Generation"` (default)
3. Implement prompt selection UI in header
4. Test with existing categories
5. Verify clear error messages when prompt not found
6. Document results

### Phase 2: Rollout to Other Templates
1. Apply same explicit selection pattern to Topic Brainstorming
2. Apply to Section Structure Design
3. Continue with remaining templates
4. Each template must have explicit prompt selection UI

### Phase 3: Optimization
1. Create reusable helper functions for prompt selection
2. Standardize prompt naming across all stages
3. Add UI for managing category-specific prompts
4. Document prompt selection workflow (no fallbacks)

## Database Considerations

### Prompt Management
- **Naming convention**: Must be consistent and predictable
- **Versioning**: Consider prompt versioning for category-specific prompts
- **Admin UI**: May need UI to manage category-specific prompts

### Persistence (CRITICAL)
- **ALL settings stored in database**: `post.extra_settings` JSONB field
- **NO client-side storage**: 
  - ❌ NO localStorage
  - ❌ NO sessionStorage
  - ❌ NO cookies
  - ❌ NO in-memory only storage
- **Storage location**: `post.extra_settings['expanded_idea_prompt_name']` (or `<function>_prompt_name`)
- **Immediate persistence**: Selection saved to database immediately on change via API call
- **Persistence guarantees**:
  - Settings persist across browser sessions
  - Settings persist across devices (same database)
  - Settings persist across page reloads
  - Settings persist if browser cache cleared
  - Settings persist if user switches browsers

### Performance
- Cache taxonomy lookups (already done in some places)
- Index `llm_prompt.name` for fast lookups
- Consider caching prompt lookups by category
- Database reads are fast (JSONB indexed queries)

## Testing Checklist

- [ ] Test with existing category (History, Culture, etc.)
- [ ] Test with new category (creates generic prompt)
- [ ] Test with no category assigned (uses generic)
- [ ] Test fallback chain (category → generic)
- [ ] Test prompt editing (category-specific vs generic)
- [ ] Test prompt creation (auto-detect category)
- [ ] Verify prompt persistence across page reloads
- [ ] Test with multiple posts in different categories

## Benefits

1. **Category-Specific Guidance**: Prompts can be tailored to different content types
2. **Explicit Selection**: User/system knows exactly which prompt is being used
3. **Clear Failures**: If prompt missing, error is clear and actionable
4. **No Silent Fallbacks**: Prevents confusion from unexpected prompt changes
5. **Scalability**: Easy to add new category-specific prompts
6. **Maintainability**: Clear naming convention and explicit selection
7. **Transparency**: Selected prompt name always visible in UI

## Risks and Mitigations

**Risk**: Breaking existing prompts if prompt not found
**Mitigation**: Clear error messages, default prompt always available, UI shows selection

**Risk**: Prompt proliferation (many category-specific prompts)
**Mitigation**: Start with key categories, add as needed. UI shows all available options.

**Risk**: Inconsistent category names
**Mitigation**: Use standardized taxonomy items, validate names, exact match in database

**Risk**: User confusion about which prompt to select
**Mitigation**: Clear UI labels, show "Default" option prominently, category-specific options clearly labeled

## UI Display Requirements

### Prompt Panel Header
The prompt panel header must display:
- **Format**: `"LLM Prompts: <selected_prompt_name>"`
- **Examples**:
  - `"LLM Prompts: Expanded Idea Generation"` (default)
  - `"LLM Prompts: Expanded Idea Generation (Landscapes & Seasons)"` (category-specific)

### Prompt Selector (when multiple options available)
- Dropdown in panel header (right side)
- Options formatted as:
  - `"Default"` for `"Expanded Idea Generation"`
  - `"Landscapes & Seasons"` for `"Expanded Idea Generation (Landscapes & Seasons)"`
- Shows current selection
- Saves selection on change
- Reloads prompt content after selection

## Legacy Post Handling

### Initial Selection for Legacy Posts
When a legacy post (no prompt selection set) is accessed:
1. **Selection endpoint** (`/api/posts/<id>/expanded-idea-prompt-selection`) is called
2. **Default prompt** (`"Expanded Idea Generation"`) is checked for existence
3. **If default exists**: Automatically selected and saved to `post.extra_settings`
4. **If default missing**: System error - default prompt must exist
5. **This is explicit**: The selection is saved, making it persistent (no fallback)

### Posts Without Categories
- **No category assigned**: Only default prompt is available
- **Category assigned**: Default + category-specific prompt (if exists) are available
- **Selection**: Default is explicitly selected for legacy posts without categories

### Migration Path
1. **Legacy post accessed** → Selection endpoint called
2. **Default prompt selected** → Saved to `post.extra_settings`
3. **User can change** → Select category-specific prompt if desired
4. **Selection persists** → No more "legacy" handling needed

## Error Handling

### When Prompt Not Found
- **Clear error message**: `"Selected prompt '<name>' not found. Please select a valid prompt."`
- **Actionable**: Error includes instructions to select different prompt
- **No silent fallback**: System fails explicitly
- **UI feedback**: Error shown in prompt panel, not just console

### When Default Prompt Missing
- **System error**: `"Default prompt 'Expanded Idea Generation' not found. Please create it in the database."`
- **Critical**: Default prompt must always exist for legacy post handling
- **Action**: Create default prompt in database before deploying

## Next Steps

1. **Review and approve this recommendation**
2. **Create implementation plan** with specific tasks
3. **Implement Ideas page** as proof of concept with explicit selection
4. **Test error handling** - verify clear failures when prompt missing
5. **Test UI display** - verify prompt name shown in header
6. **Test and iterate** before rolling out to other templates
7. **Document** final implementation pattern

