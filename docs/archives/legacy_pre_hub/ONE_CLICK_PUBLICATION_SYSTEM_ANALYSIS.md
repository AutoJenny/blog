# One-Click Publication System - Complete Analysis

**Date:** 2025-01-XX  
**Purpose:** Analyze current system for handling different post types and output channels, identify gaps

---

## Key Concepts

### Post Type vs Output Type/Channel

**Post Type** = Content category (themed, recipe, profile, weekly_word, weekly_phrase, weekly_insult)
- Determines WHAT content is being created
- Defined in `config/post_type_substages.py`
- Each has different stages/substages

**Output Type/Channel** = Publication destination (blog, facebook, instagram, twitter, newsletter)
- Determines WHERE content is being published
- May require different stages/substages for the same post type
- Example: `weekly_word` → Facebook needs different pipeline than `weekly_word` → Blog

---

## Current System Analysis

### 1. Post Type Configuration ✅

**File:** `config/post_type_substages.py`

**Current Post Types:**
- ✅ `themed` - Full pipeline (calendar → planning → research → authoring → imaging → header)
- ✅ `profile` - Pipeline (planning → authoring → imaging → header)
- ✅ `generated` - Pipeline (calendar → planning → authoring → imaging → header)
- ✅ `recipe` - Pipeline (planning → authoring → imaging → header)
- ❌ `weekly_word` - NOT defined
- ❌ `weekly_phrase` - NOT defined
- ❌ `weekly_insult` - NOT defined

**Structure:**
```python
POST_TYPE_SUBSTAGES = {
    'themed': {
        'calendar': ['view', 'week-view', 'ideas-week'],
        'planning': ['ideas', 'taxonomy', 'topic_brainstorming', ...],
        'research': ['research', 'sources', 'visuals', ...],
        'authoring': ['drafting', 'image_concepts', ...],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'header_image', 'seo_meta', ...]
    },
    # ... other types
}
```

**Gap:** No concept of output channel-specific stages

---

### 2. Pipeline Configuration ✅

**File:** `config/post_type_pipeline_configs.py`

**Current Structure:**
- Defines step-by-step pipeline for each post type
- Maps to JavaScript functions
- Example: `themed` has 19 steps, `recipe` has 13 steps

**Gap:** All pipelines assume blog output - no channel-specific pipelines

---

### 3. Channel Assignment ⚠️

**Proposed:** `post_type_channel_config` table (from architecture doc)
- Defines which channels each post type should publish to
- Does NOT define different stages per channel

**Gap:** No mechanism to say "weekly_word → Facebook needs different stages than weekly_word → Blog"

---

## The Problem: Output Channel-Specific Stages

### Example Scenarios

**Scenario 1: Weekly Word**
- **To Blog:** Needs full pipeline (calendar → planning → authoring → imaging → header)
- **To Facebook:** Needs minimal pipeline (content formatting → image optimization → publish)
- **To Instagram:** Needs different pipeline (image focus → caption optimization → publish)

**Scenario 2: Themed Post**
- **To Blog:** Full pipeline (all stages)
- **To Facebook:** May skip some stages (syndicated from blog)
- **To Newsletter:** Different format (summary + link)

**Current System:** Only defines stages per POST TYPE, not per OUTPUT CHANNEL

---

## What's Missing

### 1. Output Channel Stage Configuration ❌

**Need:** A system that defines stages/substages per (post_type, output_channel) combination

**Example:**
```python
OUTPUT_CHANNEL_STAGES = {
    ('weekly_word', 'blog'): {
        'calendar': ['view'],
        'planning': ['content_formatting'],
        'authoring': ['drafting'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'seo_meta']
    },
    ('weekly_word', 'facebook'): {
        'content': ['format_for_facebook'],  # Different stage name
        'imaging': ['image_optimize_facebook'],  # Platform-specific
        'publish': ['publish_to_facebook']  # Direct publish, no header
    },
    ('weekly_word', 'instagram'): {
        'content': ['format_for_instagram'],
        'imaging': ['image_optimize_instagram', 'create_carousel'],
        'publish': ['publish_to_instagram']
    },
    ('themed', 'blog'): {
        # Full pipeline as currently defined
    },
    ('themed', 'facebook'): {
        'syndication': ['extract_summary', 'format_for_facebook', 'publish']
    }
}
```

### 2. Unified Stage/Substage System ❌

**Need:** A system that can handle:
- Blog-specific stages (header, seo_meta)
- Social media-specific stages (format_for_platform, optimize_image_for_platform)
- Channel-agnostic stages (drafting, image_generation)

### 3. Weekly Content Types in Config ❌

**Need:** Add to `config/post_type_substages.py`:
- `weekly_word`
- `weekly_phrase`
- `weekly_insult`

With appropriate minimal pipelines

---

## Proposed Solution: Output-Aware Stage System

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Post Type Selection                                    │
│  (themed, recipe, weekly_word, etc.)                    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Output Channel Selection                               │
│  (blog, facebook, instagram, twitter, newsletter)       │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Stage/Substage Resolution                              │
│  Lookup: (post_type, output_channel) → stages           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Dynamic Pipeline Display                               │
│  Shows only relevant stages for this combination        │
└─────────────────────────────────────────────────────────┘
```

### Configuration Structure

**File:** `config/output_channel_stages.py` (NEW)

```python
"""
Output Channel Stage Configuration
Defines stages/substages per (post_type, output_channel) combination
"""

OUTPUT_CHANNEL_STAGES = {
    # Blog outputs (full pipelines)
    ('themed', 'blog'): {
        'stages': ['calendar', 'planning', 'research', 'authoring', 'imaging', 'header'],
        'substages': {
            'calendar': ['view', 'week-view', 'ideas-week'],
            'planning': ['ideas', 'taxonomy', 'topic_brainstorming', ...],
            # ... full pipeline
        }
    },
    ('recipe', 'blog'): {
        'stages': ['planning', 'authoring', 'imaging', 'header'],
        'substages': {
            # ... recipe pipeline
        }
    },
    ('weekly_word', 'blog'): {
        'stages': ['calendar', 'content', 'imaging', 'header'],
        'substages': {
            'calendar': ['view'],
            'content': ['format_content'],
            'imaging': ['image_generation', 'optimise'],
            'header': ['title_summary', 'seo_meta']
        }
    },
    
    # Social media outputs (minimal pipelines)
    ('weekly_word', 'facebook'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_facebook', 'add_hashtags'],
            'imaging': ['optimize_for_facebook'],
            'publish': ['publish_to_facebook']
        }
    },
    ('weekly_word', 'instagram'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_instagram', 'create_caption'],
            'imaging': ['optimize_for_instagram', 'create_carousel'],
            'publish': ['publish_to_instagram']
        }
    },
    ('weekly_phrase', 'facebook'): {
        'stages': ['content', 'imaging', 'publish'],
        'substages': {
            'content': ['format_for_facebook', 'add_translation'],
            'imaging': ['optimize_for_facebook'],
            'publish': ['publish_to_facebook']
        }
    },
    
    # Syndicated outputs (reuse blog content)
    ('themed', 'facebook'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_facebook', 'publish_to_facebook']
        }
    },
    ('themed', 'newsletter'): {
        'stages': ['syndication'],
        'substages': {
            'syndication': ['extract_summary', 'format_for_newsletter', 'add_to_newsletter']
        }
    }
}
```

### Helper Functions

```python
def get_stages_for_output(post_type: str, output_channel: str) -> dict:
    """
    Get stages/substages for a (post_type, output_channel) combination.
    
    Falls back to post_type only if no channel-specific config exists.
    """
    key = (post_type, output_channel)
    if key in OUTPUT_CHANNEL_STAGES:
        return OUTPUT_CHANNEL_STAGES[key]
    
    # Fallback: use post_type only (for blog outputs)
    if output_channel == 'blog':
        return get_stages_for_post_type(post_type)  # From post_type_substages.py
    
    # For social media, return minimal default
    return get_minimal_social_media_pipeline(post_type, output_channel)

def get_substages_for_output(post_type: str, output_channel: str, stage: str) -> list:
    """Get substages for a specific stage in an output pipeline."""
    config = get_stages_for_output(post_type, output_channel)
    return config.get('substages', {}).get(stage, [])
```

---

## Updated System Requirements

### 1. Add Weekly Content Types to `post_type_substages.py`

```python
POST_TYPE_SUBSTAGES = {
    # ... existing types ...
    'weekly_word': {
        'calendar': ['view'],
        'content': ['format_content'],  # New stage for simple content
        'header': ['title_summary']  # Minimal header
    },
    'weekly_phrase': {
        'calendar': ['view'],
        'content': ['format_content'],
        'header': ['title_summary']
    },
    'weekly_insult': {
        'calendar': ['view'],
        'content': ['format_content'],
        'header': ['title_summary']
    }
}
```

### 2. Create `config/output_channel_stages.py` (NEW)

Defines stages per (post_type, output_channel) combination

### 3. Update One-Click Publication UI

**New Flow:**
1. User selects item (e.g., weekly_word)
2. System determines output channels (from `post_type_channel_config`)
3. User selects output channel OR system shows all channels
4. UI displays stages/substages for that (post_type, output_channel) combination
5. User executes stages to create output

---

## Implementation Priority

### Phase 1: Add Weekly Content Types
- Add `weekly_word`, `weekly_phrase`, `weekly_insult` to `post_type_substages.py`
- Define minimal pipelines for blog output

### Phase 2: Create Output Channel Stage System
- Create `config/output_channel_stages.py`
- Define social media pipelines for weekly content
- Define syndication pipelines for themed posts

### Phase 3: Update UI
- Add output channel selector to One-Click Publication
- Dynamically load stages based on (post_type, output_channel)
- Update pipeline display to show channel-specific stages

---

## Summary

**Current State:**
- ✅ Post type stages defined (themed, recipe, profile, generated)
- ❌ Weekly content types missing
- ❌ No output channel-specific stages
- ❌ All pipelines assume blog output

**What's Needed:**
- ✅ Add weekly content types to config
- ✅ Create output channel stage system
- ✅ Update UI to handle output channel selection
- ✅ Rename "One-Click Blog" to "One-Click Publication"

**Status:** Architecture supports this, but needs implementation of output channel stage system.

