# Research System - Post Type Integration Analysis

**Date:** 2026-01-19  
**Purpose:** Confirm that the current post-type structure automatically implements research categories per post type

---

## Executive Summary

**YES** ✅ - The current blog post-type structure **perfectly handles** this requirement:

1. **Automatic Implementation**: All recipes automatically get the same research categories
2. **Post-Type Specific**: Different post types can have completely different research types
3. **Configuration-Driven**: Uses the same pattern as existing post-type configurations

---

## Current Post-Type Configuration Pattern

### Existing Pattern: `config/post_type_substages.py`

The system already uses a **post-type-specific configuration dictionary**:

```python
POST_TYPE_SUBSTAGES = {
    'recipe': {
        'planning': ['taxonomy', 'section_structure', ...],
        'authoring': ['drafting', 'recipe_image_style_prompt', ...],
        # No 'research' stage currently
    },
    'themed': {
        'planning': ['ideas', 'taxonomy', ...],
        'research': ['research', 'sources', 'visuals', ...],  # Different research!
        'authoring': ['drafting', ...],
    },
    'profile': {
        'planning': ['taxonomy', ...],
        # No 'research' stage
        'authoring': ['drafting', ...],
    }
}
```

**Key Observation:**
- Each post type has its **own dictionary entry**
- Each post type can have **different stages/substages**
- Themed posts have a `research` stage, recipes don't (yet)
- This pattern is **already extensible** to research topics

---

## Research Topics Configuration Pattern

### Proposed: `config/research_topics.py`

Following the **exact same pattern** as `post_type_substages.py`:

```python
RESEARCH_TOPICS_CONFIG = {
    'recipe': {
        'topics': [
            {
                'key': 'origins',
                'label': 'Origins & Early History',
                'search_template': 'earliest mentions and recorded origins of {item_name} in Scotland',
                'focus_areas': [...],
                'source_priorities': ['academic', 'museum', 'heritage'],
                'word_target': 150
            },
            {
                'key': 'geographic_spread',
                'label': 'Geographic Spread & Regional Variations',
                'search_template': 'geographic distribution and regional variations of {item_name} across Scotland',
                ...
            },
            {
                'key': 'evolution',
                'label': 'Evolution Over Time',
                ...
            },
            {
                'key': 'cultural_significance',
                'label': 'Cultural Significance & Traditions',
                ...
            },
            {
                'key': 'modern_incarnations',
                'label': 'Modern Incarnations & Contemporary Use',
                ...
            }
        ]
    },
    'themed': {
        'topics': [
            {
                'key': 'historical_context',
                'label': 'Historical Context',
                'search_template': 'historical context and background of {theme_title} in Scotland',
                'focus_areas': [...],
                'source_priorities': ['academic', 'museum', 'heritage'],
                'word_target': 200
            },
            {
                'key': 'cultural_significance',
                'label': 'Cultural Significance',
                'search_template': 'cultural significance of {theme_title} in Scottish culture',
                ...
            },
            {
                'key': 'key_figures',
                'label': 'Key Figures & Events',
                ...
            }
        ]
    },
    'profile': {
        'topics': [
            {
                'key': 'family_history',
                'label': 'Family History & Origins',
                'search_template': 'history and origins of {family_name} family in Scotland',
                ...
            },
            {
                'key': 'geographic_origins',
                'label': 'Geographic Origins',
                ...
            },
            {
                'key': 'notable_members',
                'label': 'Notable Family Members',
                ...
            }
        ]
    }
}
```

---

## How It Works Automatically

### 1. Post Type Detection

The system already detects post types:

```python
# From utils/taxonomy_helpers.py (or similar)
def get_post_type(post_id):
    # Checks post.recipe_id, post.profile_category_id, etc.
    # Returns: 'recipe', 'themed', 'profile', etc.
    ...
```

### 2. Research Topics Lookup

```python
# From config/research_topics.py
def get_research_topics_for_post_type(post_type):
    """
    Get research topics for a specific post type.
    
    Args:
        post_type (str): Post type ('recipe', 'themed', 'profile', etc.)
    
    Returns:
        list: List of research topic configurations
    """
    if post_type not in RESEARCH_TOPICS_CONFIG:
        return []  # No research topics for this post type
    
    return RESEARCH_TOPICS_CONFIG[post_type]['topics']
```

### 3. Automatic Initialization

When a recipe post is created or research stage is accessed:

```python
# In research API endpoint
post_type = get_post_type(post_id)

# Get research topics for this post type
research_topics = get_research_topics_for_post_type(post_type)

# Initialize research structure in post_development.recipe_research
research_data = {
    'background_research': {
        'topics': [
            {
                'key': topic['key'],
                'label': topic['label'],
                'status': 'pending',
                'research_query': topic['search_template'].format(item_name=recipe_name),
                'sources': [],
                'extracted_facts': {},
                'synthesized_content': None
            }
            for topic in research_topics
        ]
    }
}
```

**Result:** All recipes automatically get the same 5 research topics, configured once in `config/research_topics.py`.

---

## Example: Recipe vs Themed Post

### Recipe Post (post_id=709, type='recipe')

```python
# System detects: post_type = 'recipe'
research_topics = get_research_topics_for_post_type('recipe')

# Returns:
[
    {'key': 'origins', 'label': 'Origins & Early History', ...},
    {'key': 'geographic_spread', 'label': 'Geographic Spread & Regional Variations', ...},
    {'key': 'evolution', 'label': 'Evolution Over Time', ...},
    {'key': 'cultural_significance', 'label': 'Cultural Significance & Traditions', ...},
    {'key': 'modern_incarnations', 'label': 'Modern Incarnations & Contemporary Use', ...}
]

# All recipes get these same 5 topics automatically
```

### Themed Post (post_id=123, type='themed')

```python
# System detects: post_type = 'themed'
research_topics = get_research_topics_for_post_type('themed')

# Returns:
[
    {'key': 'historical_context', 'label': 'Historical Context', ...},
    {'key': 'cultural_significance', 'label': 'Cultural Significance', ...},
    {'key': 'key_figures', 'label': 'Key Figures & Events', ...}
]

# Themed posts get different research topics automatically
```

---

## Integration with Existing Workflow

### Update `config/post_type_substages.py`

Add research stage to recipes:

```python
'recipe': {
    'planning': ['taxonomy', 'section_structure', 'topic_allocation', 'section_titling'],
    'research': ['background_research'],  # NEW - automatically uses recipe research topics
    'authoring': ['drafting', 'recipe_image_style_prompt', 'image_captions'],
    'imaging': ['image_generation', 'optimise'],
    'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
}
```

**Themed posts already have:**
```python
'themed': {
    'research': ['research', 'sources', 'visuals', 'prompts', 'verification'],
    # Different research substages!
}
```

**Profile posts:**
```python
'profile': {
    # No research stage (or add one later with profile-specific topics)
}
```

---

## Research Topic Metadata

Add to `SUBSTAGE_METADATA` in `config/post_type_substages.py`:

```python
SUBSTAGE_METADATA = {
    ...
    'background_research': {
        'label': 'Background Research',
        'route_function': 'research.recipe_background_research',
        'order': 1
    },
    ...
}
```

---

## API Endpoint Implementation

### Research Topics API

```python
@bp.route('/api/posts/<int:post_id>/research/topics', methods=['GET'])
def get_research_topics(post_id):
    """Get available research topics for this post type."""
    from utils.taxonomy_helpers import get_post_type
    from config.research_topics import get_research_topics_for_post_type
    
    post_type = get_post_type(post_id)
    topics = get_research_topics_for_post_type(post_type)
    
    return jsonify({
        'post_type': post_type,
        'topics': topics
    })
```

**Result:** API automatically returns the correct research topics based on post type.

---

## Benefits of This Approach

### ✅ Automatic Implementation
- All recipes get the same research categories automatically
- No per-post configuration needed
- Single source of truth in `config/research_topics.py`

### ✅ Post-Type Specific
- Each post type can have completely different research topics
- Easy to add new post types with their own research topics
- No conflicts between post types

### ✅ Consistent Pattern
- Follows the same pattern as `post_type_substages.py`
- Developers already familiar with this pattern
- Easy to maintain and extend

### ✅ Extensible
- Add new research topics to a post type: Update `config/research_topics.py`
- Add research to new post type: Add new entry to `RESEARCH_TOPICS_CONFIG`
- Change research topics: Update config file, all posts of that type get updated

---

## Example: Adding Research to Profile Posts

### Step 1: Add Research Topics to Config

```python
# config/research_topics.py
RESEARCH_TOPICS_CONFIG = {
    ...
    'profile': {
        'topics': [
            {
                'key': 'family_history',
                'label': 'Family History & Origins',
                'search_template': 'history and origins of {family_name} family in Scotland',
                'focus_areas': ['earliest records', 'name origin', 'historical significance'],
                'source_priorities': ['academic', 'genealogy', 'heritage'],
                'word_target': 200
            },
            {
                'key': 'geographic_origins',
                'label': 'Geographic Origins & Distribution',
                'search_template': 'geographic origins and distribution of {family_name} surname in Scotland',
                ...
            }
        ]
    }
}
```

### Step 2: Add Research Stage to Profile Workflow

```python
# config/post_type_substages.py
'profile': {
    'planning': ['taxonomy', 'section_structure', ...],
    'research': ['background_research'],  # NEW
    'authoring': ['drafting', ...],
    ...
}
```

### Step 3: Done!

- All profile posts now automatically get family history research topics
- Recipe posts still get recipe research topics
- Themed posts still get themed research topics
- No code changes needed in research execution logic

---

## Code Structure

```
config/
├── post_type_substages.py      # Existing: Workflow stages per post type
├── research_topics.py          # NEW: Research topics per post type
└── post_type_config.py         # Existing: Publication config per post type

utils/
└── research_agents/
    ├── __init__.py
    ├── config.py               # Helper: get_research_topics_for_post_type()
    └── ...

blueprints/
└── research_api.py             # Uses get_research_topics_for_post_type()
```

---

## Conclusion

**YES** - The current post-type structure **perfectly supports** this requirement:

1. ✅ **Automatic**: All recipes get the same research categories (configured once)
2. ✅ **Post-Type Specific**: Different post types get different research topics
3. ✅ **Consistent**: Uses the same pattern as existing post-type configurations
4. ✅ **Extensible**: Easy to add research to new post types or modify existing ones

**No changes needed to the post-type system** - it already supports this pattern! We just need to:
1. Create `config/research_topics.py` with post-type-specific research topic definitions
2. Add helper function `get_research_topics_for_post_type(post_type)`
3. Use it in research API endpoints

The system will automatically:
- Detect post type
- Look up appropriate research topics
- Initialize research structure with those topics
- Execute research for each topic sequentially

**Perfect fit!** ✅
