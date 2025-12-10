# Channel Assignment Analysis & Proposal

**Date:** 2025-01-XX  
**Purpose:** Analyze current channel assignment structure and propose solution for determining which content goes to which channels

---

## Current State Analysis

### What We Have

1. **Syndication System** (For Blog Posts)
   - `syndication_progress` table tracks which blog post **sections** have been syndicated to which platforms/channels
   - Works on published blog posts, not calendar items directly
   - Platform/channel combinations: Facebook Feed Post, Instagram, Twitter, etc.
   - **Scope**: Only handles syndication of existing blog post content

2. **Posting Queue System** (For Products & Blog Posts)
   - `posting_queue` table handles scheduled posts for different platforms
   - Supports `content_type`: 'blog_post' or 'product'
   - **Scope**: Handles scheduled publishing, not channel assignment rules

3. **Post Type Configuration**
   - `post_type_config` table defines publication day/time per post type
   - **Does NOT** define which channels each type should use
   - **Gap**: No channel assignment configuration

### What's Missing

1. **No Channel Assignment Rules**
   - No table/configuration that says "weekly_word goes to Facebook only" or "theme goes to blog + Facebook + newsletter"
   - No way to determine which channels a calendar item should publish to

2. **No Content Type → Channel Mapping**
   - Can't automatically determine: "This is a weekly_word, so it should go to Facebook and Instagram, not blog"
   - Can't determine: "This is a theme, so it should go to blog + Facebook + newsletter"

3. **Ambiguity in Mockup**
   - Mockup shows words/phrases/insults in both "Blog Posts" and "Facebook Posts"
   - **Question**: Do they actually go to both, or is this a data modeling problem?

---

## The Problem

### Current Behavior (Unclear)

When a `weekly_word` is scheduled:
- **Does it create a blog post?** (Then syndicated to Facebook)
- **Does it go directly to Facebook?** (No blog post)
- **Does it go to both?** (Blog post AND direct Facebook post)

### What We Need

A clear structure that defines:
- **For each post type**: Which channels should it publish to
- **For each calendar item**: Which channels it's assigned to
- **For each publication**: Track which channels it's been published to

---

## Proposed Solution: Channel Assignment Configuration

### Option 1: Post Type → Channel Mapping (Recommended)

**Table**: `post_type_channel_config`

```sql
CREATE TABLE post_type_channel_config (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL,  -- 'themed', 'recipe', 'weekly_word', etc.
    channel VARCHAR(50) NOT NULL,     -- 'blog', 'facebook', 'instagram', 'newsletter', 'twitter'
    is_primary BOOLEAN DEFAULT FALSE, -- Is this the primary channel?
    is_required BOOLEAN DEFAULT TRUE,  -- Must this channel be used?
    publication_delay_hours INTEGER DEFAULT 0, -- Delay after primary channel
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(post_type, channel)
);

-- Example data
INSERT INTO post_type_channel_config (post_type, channel, is_primary, is_required) VALUES
    ('themed', 'blog', TRUE, TRUE),           -- Themes: Blog is primary, required
    ('themed', 'facebook', FALSE, TRUE),      -- Themes: Facebook is required
    ('themed', 'newsletter', FALSE, FALSE),   -- Themes: Newsletter is optional
    
    ('recipe', 'blog', TRUE, TRUE),           -- Recipes: Blog is primary, required
    ('recipe', 'facebook', FALSE, TRUE),      -- Recipes: Facebook is required
    
    ('weekly_word', 'facebook', TRUE, TRUE),  -- Words: Facebook is primary, NOT blog
    ('weekly_word', 'instagram', FALSE, TRUE), -- Words: Instagram is required
    
    ('weekly_phrase', 'facebook', TRUE, TRUE), -- Phrases: Facebook is primary, NOT blog
    ('weekly_phrase', 'twitter', FALSE, TRUE), -- Phrases: Twitter is required
    
    ('weekly_insult', 'facebook', TRUE, TRUE), -- Insults: Facebook is primary, NOT blog
    ('weekly_insult', 'twitter', FALSE, TRUE),  -- Insults: Twitter is required
    
    ('profile_product', 'blog', TRUE, TRUE),   -- Product profiles: Blog is primary
    ('profile_product', 'facebook', FALSE, TRUE), -- Product profiles: Facebook required
    ('profile_product', 'instagram', FALSE, TRUE), -- Product profiles: Instagram required
    
    ('profile_surname', 'blog', TRUE, TRUE);  -- Surname profiles: Blog only
```

**Usage**:
- When scheduling a `weekly_word`, system checks `post_type_channel_config` where `post_type='weekly_word'`
- Finds channels: `facebook` (primary), `instagram` (required)
- **Does NOT** find `blog`, so word does NOT appear in "Blog Posts" section
- Appears only in "Facebook Posts" and "Instagram Posts" sections

### Option 2: Per-Item Channel Assignment

**Table**: `calendar_item_channels`

```sql
CREATE TABLE calendar_item_channels (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,  -- 'theme', 'recipe', 'weekly_word', etc.
    item_id INTEGER NOT NULL,        -- ID of the calendar item
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    channel VARCHAR(50) NOT NULL,    -- 'blog', 'facebook', 'instagram', etc.
    is_scheduled BOOLEAN DEFAULT TRUE,
    scheduled_date DATE,
    scheduled_time TIME,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'published', 'failed'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(category, item_id, year, week_number, channel)
);
```

**Usage**:
- Each calendar item can have multiple channel assignments
- More flexible but more complex
- Allows per-item overrides

### Option 3: Hybrid Approach (Recommended for Flexibility)

**Combine both**:
1. **Default rules** via `post_type_channel_config` (Option 1)
2. **Per-item overrides** via `calendar_item_channels` (Option 2)

**Workflow**:
1. When item is scheduled, apply default channels from `post_type_channel_config`
2. User can override per-item if needed
3. Dashboard shows channels based on actual assignments

---

## Implementation for Dashboard

### Data Structure

```python
# When loading dashboard data
def get_item_channels(category, item_id, year, week):
    """
    Get channels for a calendar item.
    
    Returns: ['blog', 'facebook', 'instagram'] or ['facebook'] etc.
    """
    # 1. Check for per-item overrides (calendar_item_channels)
    # 2. If none, use default from post_type_channel_config
    # 3. Return list of channels
```

### Dashboard Display Logic

```python
# Group items by channel
items_by_channel = {
    'blog': [],
    'facebook': [],
    'instagram': [],
    'newsletter': []
}

for item in scheduled_items:
    channels = get_item_channels(item.category, item.id, item.year, item.week)
    for channel in channels:
        items_by_channel[channel].append(item)
```

---

## Questions to Resolve

1. **Weekly Words/Phrases/Insults**:
   - Do they create blog posts? (Then syndicated)
   - Or do they go directly to social media only?
   - Or both?

2. **Themes**:
   - Always go to blog + Facebook + newsletter?
   - Or configurable per theme?

3. **Recipes**:
   - Always blog + Facebook?
   - Or sometimes Instagram too?

4. **Profiles**:
   - Product profiles: Blog + Facebook + Instagram?
   - Surname profiles: Blog only?

5. **Default Behavior**:
   - Should we assume "blog + Facebook" for most types?
   - Or be explicit about each type?

---

## Recommended Next Steps

1. **Clarify intended behavior** for each post type
2. **Create `post_type_channel_config` table** with default rules
3. **Update dashboard API** to use channel assignments
4. **Update mockup** to reflect correct channel assignments
5. **Add UI** for managing channel assignments (optional per-item overrides)

---

*Document Status: Analysis & Proposal*  
*Next: User clarification on intended behavior*

