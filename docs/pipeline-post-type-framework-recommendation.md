# Blog Post Pipeline Framework - Post Type Support Recommendation

## Executive Summary

The current blog post pipeline is designed primarily for **themed posts** with hardcoded steps. To support **Recipe** and **Profile** post types reliably, we need to extend the existing category variance architecture to support:

1. **Post Type-Based Pipeline Configuration** - Different pipeline steps per post type
2. **Post Type-Based Prompt Selection** - Different prompts per post type (extending current prompt-level variance)
3. **Post Type-Based Substage Management** - Add/drop substages per post type (e.g., research substage for recipes)
4. **Unified Architecture** - Build on existing category variance system for consistency

## Current State Analysis

### Existing Architecture

The system already has a sophisticated category variance framework:

1. **Process-Level Variance** (`config/authoring_panel_configs.py`):
   - Different workflows entirely (different panels, routes, backend logic)
   - Example: Photo-harvesting (inactive, kept in reserve)
   - Configuration-based with `active` flags

2. **Prompt-Level Variance** (`utils/taxonomy_helpers.py`):
   - Same workflow, different LLM prompts
   - Based on `content_type_name` from taxonomy
   - Uses naming convention: `'{Stage} Generation ({Content Type})'`

3. **One-Click Blog Pipeline** (`templates/launchpad/one_click_blog_minimal.html`):
   - Hardcoded pipeline array (17 steps)
   - Steps: week-ideas, taxonomy, idea-generation, topic-brainstorming, section-structure, etc.
   - Currently designed for themed posts only

### Current Pipeline Steps

```javascript
const pipeline = [
    { id:'week-ideas', label:'Calendar — Week Ideas', run: runWeekIdeas },
    { id:'taxonomy', label:'Planning — Taxonomy', run: runTaxonomy },
    { id:'idea-generation', label:'Planning — Idea Generation', run: runIdeaGeneration },
    { id:'topic-brainstorming', label:'Planning — Topic Brainstorming', run: runTopicBrainstorming },
    { id:'section-structure-design', label:'Planning — Section Structure', run: runSectionStructure },
    { id:'section-ideas', label:'Planning — Section Ideas', run: runSectionIdeas },
    { id:'section-titling', label:'Planning — Section Titling', run: runSectionTitling },
    { id:'drafting', label:'Authoring — Drafting', run: runDrafting },
    { id:'image-concepts', label:'Authoring — Image Concepts', run: runImageConcepts },
    { id:'image-prompts', label:'Authoring — Image Prompts', run: runImagePrompts },
    { id:'image-captions', label:'Authoring — Image Captions', run: runImageCaptions },
    { id:'image-generation', label:'Imaging — Image Generation', run: runImageGeneration },
    { id:'optimise', label:'Imaging — Optimise', run: runImageOptimise },
    { id:'header-title-summary', label:'Header — Title & Summary', run: runHeaderTitleSummary },
    { id:'header-image-prompt', label:'Header Image — Prompt', run: runHeaderImagePrompt },
    { id:'header-image-details', label:'Header Image — Captions/Alt', run: runHeaderImageDetails },
    { id:'header-image-generate', label:'Header Image — Image', run: runHeaderImageGenerate },
    { id:'header-image-optimise', label:'Header Image — Optimise', run: runHeaderImageOptimize },
    { id:'header-seo-meta', label:'Header — SEO & Meta', run: runHeaderSeoMeta },
    { id:'final-review', label:'Final Review — Preview', run: runFinalReview }
];
```

### Post Type Requirements

**Recipe Posts**:
- ✅ Need: Recipe-specific sections (background, ingredients, method, variants, serving, gallery)
- ✅ Need: Recipe-specific prompts (already created in `llm_prompt` table)
- ✅ Need: Recipe-specific image prompts (hero + making process)
- ❌ Can skip: Topic brainstorming (topic is the recipe)
- ❌ Can skip: Section structure (fixed recipe structure)
- ❌ Can skip: Topic allocation (recipe sections are predefined)
- ➕ Might need: Research substage for web spidering (historical context, regional variations)

**Profile Posts**:
- ✅ Need: Profile-specific sections (product/category info, features, usage)
- ✅ Need: Profile-specific prompts
- ✅ Need: Profile-specific images (product photos)
- ❌ Can skip: Topic brainstorming (topic is the product/category)
- ❌ Can skip: Section structure (might be simpler/fixed)
- ➕ Might need: Product data integration (clan_products API)

**Themed Posts** (current):
- ✅ Keep all current steps
- ✅ All existing functionality works

## Recommended Architecture

### Three-Layer Variance System

Extend the existing two-layer system (process-level, prompt-level) to a three-layer system:

1. **Post Type Level** (new): Determines which pipeline steps to include/exclude
2. **Process Level** (existing): Different workflows (panels, routes, backend)
3. **Prompt Level** (existing): Different prompts within same workflow

### Implementation Strategy

#### Layer 1: Post Type Pipeline Configuration

**New File**: `config/post_type_pipeline_configs.py`

```python
"""
Post Type Pipeline Configuration
Defines which pipeline steps are used for each post type.
"""

POST_TYPE_PIPELINE_CONFIGS = {
    'themed': {
        'active': True,
        'steps': [
            'week-ideas',           # Calendar selection
            'taxonomy',             # Assign taxonomy
            'idea-generation',      # Expand idea
            'topic-brainstorming',  # Generate topics
            'section-structure-design', # Design structure
            'section-ideas',        # Section ideas
            'section-titling',      # Section titles
            'drafting',             # Author drafts
            'image-concepts',       # Image concepts
            'image-prompts',        # Image prompts
            'image-captions',       # Image captions
            'image-generation',     # Generate images
            'optimise',             # Optimize images
            'header-title-summary', # Header title/summary
            'header-image-prompt',  # Header image prompt
            'header-image-details', # Header image details
            'header-image-generate', # Header image generation
            'header-image-optimise', # Header image optimization
            'header-seo-meta',      # SEO metadata
            'final-review'          # Final review
        ]
    },
    'recipe': {
        'active': True,
        'steps': [
            'recipe-selection',     # Select recipe (replaces week-ideas)
            'recipe-research',      # NEW: Web research for historical context
            'recipe-background',    # Recipe background generation
            'recipe-ingredients',   # Ingredients list generation
            'recipe-method',        # Method generation
            'recipe-variants',      # Variations generation
            'recipe-serving',       # Serving suggestions
            'recipe-image-concepts', # Recipe-specific image concepts
            'recipe-image-prompts', # Recipe-specific image prompts
            'recipe-image-generation', # Recipe images (hero + making process)
            'recipe-image-optimise', # Optimize recipe images
            'header-title-summary', # Header title/summary
            'header-image-prompt',  # Header image prompt
            'header-image-details', # Header image details
            'header-image-generate', # Header image generation
            'header-image-optimise', # Header image optimization
            'header-seo-meta',      # SEO metadata
            'final-review'          # Final review
        ]
    },
    'profile': {
        'active': True,
        'steps': [
            'profile-selection',    # Select product/category (replaces week-ideas)
            'profile-data-sync',    # NEW: Sync product data from clan_products
            'profile-sections',     # Profile sections generation
            'profile-image-concepts', # Profile image concepts
            'profile-image-prompts', # Profile image prompts
            'profile-image-generation', # Profile images
            'profile-image-optimise', # Optimize profile images
            'header-title-summary', # Header title/summary
            'header-image-prompt',  # Header image prompt
            'header-image-details', # Header image details
            'header-image-generate', # Header image generation
            'header-image-optimise', # Header image optimization
            'header-seo-meta',      # SEO metadata
            'final-review'          # Final review
        ]
    }
}

def get_pipeline_steps(post_type):
    """
    Get pipeline steps for a post type.
    
    Args:
        post_type (str): Post type ('themed', 'recipe', 'profile')
    
    Returns:
        list: List of step IDs for the pipeline
    """
    config = POST_TYPE_PIPELINE_CONFIGS.get(
        post_type,
        POST_TYPE_PIPELINE_CONFIGS['themed']  # Default to themed
    )
    
    if not config.get('active', True):
        # Fallback to themed if post type is inactive
        return POST_TYPE_PIPELINE_CONFIGS['themed']['steps']
    
    return config['steps']


def get_step_config(step_id, post_type):
    """
    Get configuration for a specific step within a post type.
    
    Allows step-level customization (e.g., different run functions,
    different prompts, different completion events).
    
    Args:
        step_id (str): Step ID (e.g., 'recipe-research')
        post_type (str): Post type
    
    Returns:
        dict: Step configuration with run function, label, completion event, etc.
    """
    # Default step configurations
    step_configs = {
        'recipe-research': {
            'label': 'Research — Recipe Context',
            'run': 'runRecipeResearch',
            'completeEvent': None,  # Manual step
            'prompt_category': 'recipe'  # Use recipe prompts
        },
        'profile-data-sync': {
            'label': 'Data Sync — Product Information',
            'run': 'runProfileDataSync',
            'completeEvent': None,
            'prompt_category': 'profile'
        }
    }
    
    return step_configs.get(step_id, {})
```

#### Layer 2: Post Type Detection & Prompt Selection

**Extend**: `utils/taxonomy_helpers.py`

```python
def get_post_type(post_id):
    """
    Determine post type: recipe, profile, or themed.
    
    Args:
        post_id (int): Post ID
    
    Returns:
        str: Post type ('recipe', 'profile', 'themed')
    """
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN p.recipe_week_number IS NOT NULL THEN 'recipe'
                        WHEN p.profile_category_id IS NOT NULL THEN 'profile'
                        ELSE 'themed'
                    END as post_type
                FROM post p
                WHERE p.id = %s
            """, (post_id,))
            
            result = cursor.fetchone()
            if result:
                return result.get('post_type', 'themed')
            
            return 'themed'
    except Exception as e:
        logger.error(f"Error determining post type for post {post_id}: {e}")
        return 'themed'


def get_post_type_prompt_name(base_name, post_type, content_type_name=None):
    """
    Get prompt name based on post type and category.
    
    Extends get_category_prompt_name() to support post type-specific prompts.
    
    Args:
        base_name (str): Base prompt name (e.g., 'Expanded Idea Generation')
        post_type (str): Post type ('recipe', 'profile', 'themed')
        content_type_name (str, optional): Content type for additional specificity
    
    Returns:
        str: Post type-specific prompt name
    
    Examples:
        # Recipe post
        get_post_type_prompt_name('Expanded Idea Generation', 'recipe')
        # Returns: 'Expanded Idea Generation (Recipe)'
        
        # Profile post with content type
        get_post_type_prompt_name('Section Ideas', 'profile', 'Product')
        # Returns: 'Section Ideas (Profile: Product)'
        
        # Themed post (unchanged)
        get_post_type_prompt_name('Expanded Idea Generation', 'themed')
        # Returns: 'Expanded Idea Generation'
    """
    # Post type-specific prompts
    if post_type == 'recipe':
        prompt_name = f"{base_name} (Recipe)"
    elif post_type == 'profile':
        prompt_name = f"{base_name} (Profile)"
        if content_type_name:
            prompt_name = f"{base_name} (Profile: {content_type_name})"
    else:
        # Themed posts use existing category-based prompts
        if content_type_name:
            prompt_name = f"{base_name} ({content_type_name})"
        else:
            prompt_name = base_name
    
    return prompt_name
```

#### Layer 3: Dynamic Pipeline Loading

**Update**: `templates/launchpad/one_click_blog_minimal.html`

```javascript
// Load pipeline steps dynamically based on post type
async function loadPipelineForPostType(postId) {
    try {
        // Get post type from API
        const response = await fetch(`/api/posts/${postId}/type`);
        const data = await response.json();
        const postType = data.post_type || 'themed';
        
        // Get pipeline steps for this post type
        const stepsResponse = await fetch(`/api/post-type-pipeline/${postType}`);
        const stepsData = await stepsResponse.json();
        const stepIds = stepsData.steps || [];
        
        // Build pipeline array from step IDs
        const pipeline = stepIds.map(stepId => {
            // Get step configuration
            const stepConfig = getStepConfig(stepId, postType);
            
            // Map to run function
            const runFunction = getRunFunction(stepId, postType);
            
            return {
                id: stepId,
                label: stepConfig.label || stepId,
                run: runFunction,
                completeEvent: stepConfig.completeEvent
            };
        });
        
        return pipeline;
    } catch (error) {
        console.error('Error loading pipeline:', error);
        // Fallback to default themed pipeline
        return getDefaultThemedPipeline();
    }
}

// Step function mapping
function getRunFunction(stepId, postType) {
    // Recipe-specific steps
    if (postType === 'recipe') {
        if (stepId === 'recipe-selection') return runRecipeSelection;
        if (stepId === 'recipe-research') return runRecipeResearch;
        if (stepId === 'recipe-background') return runRecipeBackground;
        // ... etc
    }
    
    // Profile-specific steps
    if (postType === 'profile') {
        if (stepId === 'profile-selection') return runProfileSelection;
        if (stepId === 'profile-data-sync') return runProfileDataSync;
        // ... etc
    }
    
    // Themed steps (existing)
    if (stepId === 'week-ideas') return runWeekIdeas;
    if (stepId === 'taxonomy') return runTaxonomy;
    // ... etc
    
    // Default: no-op
    return () => {};
}
```

### Database Schema Extensions

#### New Table: `post_type_pipeline_steps`

```sql
CREATE TABLE post_type_pipeline_steps (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    step_order INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    step_label VARCHAR(255),
    run_function VARCHAR(255),
    complete_event VARCHAR(100),
    prompt_category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_type, step_id)
);

-- Insert default configurations
INSERT INTO post_type_pipeline_steps (post_type, step_id, step_order, step_label, run_function) VALUES
    ('themed', 'week-ideas', 1, 'Calendar — Week Ideas', 'runWeekIdeas'),
    ('themed', 'taxonomy', 2, 'Planning — Taxonomy', 'runTaxonomy'),
    -- ... etc
    
    ('recipe', 'recipe-selection', 1, 'Recipe — Selection', 'runRecipeSelection'),
    ('recipe', 'recipe-research', 2, 'Research — Recipe Context', 'runRecipeResearch'),
    -- ... etc
    
    ('profile', 'profile-selection', 1, 'Profile — Selection', 'runProfileSelection'),
    ('profile', 'profile-data-sync', 2, 'Data Sync — Product Information', 'runProfileDataSync');
    -- ... etc
```

### API Endpoints

**New File**: `blueprints/post_type_pipeline.py`

```python
@bp.route('/api/post-type-pipeline/<post_type>', methods=['GET'])
def get_pipeline_steps(post_type):
    """Get pipeline steps for a post type."""
    from config.post_type_pipeline_configs import get_pipeline_steps
    steps = get_pipeline_steps(post_type)
    return jsonify({'success': True, 'steps': steps})

@bp.route('/api/posts/<int:post_id>/type', methods=['GET'])
def get_post_type(post_id):
    """Get post type for a post."""
    from utils.taxonomy_helpers import get_post_type
    post_type = get_post_type(post_id)
    return jsonify({'success': True, 'post_type': post_type})
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. Create `config/post_type_pipeline_configs.py`
2. Create `post_type_pipeline_steps` table
3. Extend `utils/taxonomy_helpers.py` with `get_post_type()`
4. Create API endpoints for pipeline configuration

### Phase 2: Recipe Pipeline (Week 2)
1. Define recipe pipeline steps
2. Create recipe-specific step functions (JavaScript)
3. Create recipe-specific prompts in database
4. Test recipe pipeline end-to-end

### Phase 3: Profile Pipeline (Week 3)
1. Define profile pipeline steps
2. Create profile-specific step functions
3. Integrate `clan_products` API for data sync
4. Create profile-specific prompts
5. Test profile pipeline end-to-end

### Phase 4: Research Substage (Week 4)
1. Create research substage UI
2. Implement web spidering backend
3. Integrate research results into recipe generation
4. Test research substage

### Phase 5: Refinement (Week 5)
1. Add step-level customization (skip, conditional, etc.)
2. Add step dependencies (step X must complete before step Y)
3. Add progress tracking per post type
4. Documentation and testing

## Benefits

1. **Scalability**: Easy to add new post types
2. **Maintainability**: Configuration-driven, not hardcoded
3. **Flexibility**: Different workflows per post type
4. **Consistency**: Builds on existing category variance architecture
5. **Backward Compatibility**: Themed posts continue to work as-is

## Migration Path

1. **Phase 1**: Deploy foundation (no breaking changes)
2. **Phase 2**: Add recipe pipeline (existing recipes unaffected)
3. **Phase 3**: Add profile pipeline (existing profiles unaffected)
4. **Phase 4**: Add research substage (optional enhancement)
5. **Phase 5**: Refine and optimize

## Risk Mitigation

1. **Default Fallback**: Always fall back to themed pipeline if post type unknown
2. **Active Flags**: Can disable post type pipelines without code changes
3. **Step-Level Flags**: Can disable individual steps per post type
4. **Testing**: Comprehensive testing for each post type before production

## Next Steps

1. Review and approve this architecture
2. Create detailed implementation plan
3. Begin Phase 1 implementation
4. Test with sample recipe and profile posts
5. Iterate based on feedback

