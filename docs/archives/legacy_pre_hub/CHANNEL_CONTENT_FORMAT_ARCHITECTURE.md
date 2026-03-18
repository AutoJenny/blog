# Channel Content Format Architecture - Recommendation

**Date:** 2025-12-10  
**Purpose:** Define robust architecture for handling content formats/types within channels  
**Status:** Proposal for Implementation

---

## Problem Statement

The current system distinguishes:
1. **Post Type** (themed, recipe, weekly_word, etc.) - WHAT the content is
2. **Channel** (blog, facebook, instagram, etc.) - WHERE it goes

But it **lacks**:
3. **Content Format/Type within Channel** - HOW it's formatted/presented

### Examples of the Problem

- **Recipe → Blog**: Needs "Recipe" format (recipe-specific blog structure with ingredients, method, etc.)
- **Recipe → Facebook**: Needs "Recipe" format (recipe-specific Facebook post format, different from generic blog post syndication)
- **Weekly Word → Facebook**: Needs "Word of the Day" format (word-specific Facebook format, not generic post)
- **Weekly Word → Instagram**: Needs "Word of the Day" format (word-specific Instagram format)
- **Themed → Blog**: Needs "Article" format (standard blog article)
- **Themed → Facebook**: Needs "Article Syndication" format (syndicated blog post)

Currently, the system can't distinguish between:
- A recipe Facebook post (recipe-specific format)
- A word-of-day Facebook post (word-specific format)
- A syndicated blog post on Facebook (generic format)

---

## Proposed Solution: Three-Level Hierarchy

### Architecture

```
Post Type (WHAT)
    ↓
Channel (WHERE)
    ↓
Content Format (HOW)
```

### Data Model

#### Option 1: Extended `post_type_channel_config` Table (Recommended)

Add a `content_format` field to the existing `post_type_channel_config` table:

```sql
CREATE TABLE post_type_channel_config (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL,           -- 'themed', 'recipe', 'weekly_word', etc.
    channel VARCHAR(50) NOT NULL,              -- 'blog', 'facebook', 'instagram', etc.
    content_format VARCHAR(50) NOT NULL,       -- 'recipe', 'word_of_day', 'article', 'syndication', etc.
    is_primary BOOLEAN DEFAULT FALSE,
    is_required BOOLEAN DEFAULT TRUE,
    publication_delay_hours INTEGER DEFAULT 0,
    publication_time TIME,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(post_type, channel, content_format),
    CHECK (channel IN ('blog', 'facebook', 'instagram', 'twitter', 'newsletter')),
    CHECK (content_format IN (
        -- Blog formats
        'article', 'recipe', 'profile', 'word_of_day', 'phrase_of_day', 'insult_of_day',
        -- Facebook formats
        'recipe', 'word_of_day', 'phrase_of_day', 'insult_of_day', 'syndication', 'product',
        -- Instagram formats
        'recipe', 'word_of_day', 'phrase_of_day', 'insult_of_day', 'carousel', 'syndication',
        -- Twitter formats
        'word_of_day', 'phrase_of_day', 'insult_of_day', 'syndication',
        -- Newsletter formats
        'syndication', 'roundup'
    ))
);
```

**Default Data:**
```sql
INSERT INTO post_type_channel_config (post_type, channel, content_format, is_primary, is_required) VALUES
    -- Themed posts
    ('themed', 'blog', 'article', TRUE, TRUE),
    ('themed', 'facebook', 'syndication', FALSE, TRUE),
    ('themed', 'newsletter', 'syndication', FALSE, FALSE),
    
    -- Recipe posts
    ('recipe', 'blog', 'recipe', TRUE, TRUE),           -- Recipe format on blog
    ('recipe', 'facebook', 'recipe', FALSE, TRUE),      -- Recipe format on Facebook (not syndication)
    
    -- Weekly word
    ('weekly_word', 'facebook', 'word_of_day', TRUE, TRUE),   -- Word of Day format on Facebook
    ('weekly_word', 'instagram', 'word_of_day', FALSE, TRUE), -- Word of Day format on Instagram
    -- NO blog entry - weekly_word doesn't go to blog
    
    -- Weekly phrase
    ('weekly_phrase', 'facebook', 'phrase_of_day', TRUE, TRUE),
    ('weekly_phrase', 'twitter', 'phrase_of_day', FALSE, TRUE),
    
    -- Weekly insult
    ('weekly_insult', 'facebook', 'insult_of_day', TRUE, TRUE),
    ('weekly_insult', 'twitter', 'insult_of_day', FALSE, TRUE),
    
    -- Product profiles
    ('profile_product', 'blog', 'profile', TRUE, TRUE),
    ('profile_product', 'facebook', 'syndication', FALSE, TRUE),
    ('profile_product', 'instagram', 'carousel', FALSE, TRUE),
    
    -- Surname profiles
    ('profile_surname', 'blog', 'profile', TRUE, TRUE);
```

#### Option 2: Separate `channel_content_formats` Table

Create a dedicated table for content formats:

```sql
CREATE TABLE channel_content_formats (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(50) NOT NULL,
    format_name VARCHAR(50) NOT NULL,
    format_description TEXT,
    format_config JSONB,  -- Format-specific configuration
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(channel, format_name),
    CHECK (channel IN ('blog', 'facebook', 'instagram', 'twitter', 'newsletter'))
);

-- Then reference in post_type_channel_config
ALTER TABLE post_type_channel_config 
ADD COLUMN content_format_id INTEGER REFERENCES channel_content_formats(id);
```

**Recommendation:** Option 1 is simpler and more direct. Option 2 provides more flexibility but adds complexity.

---

## Implementation Strategy

### Phase 1: Database Schema (1 day)

1. **Extend `post_type_channel_config` table**
   - Add `content_format` column
   - Update unique constraint to include `content_format`
   - Add check constraint for valid formats
   - Create migration script

2. **Populate default data**
   - Insert all (post_type, channel, content_format) combinations
   - Define which formats are valid for which channels

### Phase 2: Configuration Layer (1 day)

1. **Create `config/channel_content_formats.py`**
   ```python
   # Defines format-specific configurations
   CHANNEL_CONTENT_FORMATS = {
       ('blog', 'recipe'): {
           'template': 'blog/recipe.html',
           'sections': ['ingredients', 'method', 'notes'],
           'required_fields': ['ingredients', 'method']
       },
       ('facebook', 'recipe'): {
           'template': 'facebook/recipe.html',
           'max_length': 2000,
           'requires_image': True,
           'format_function': 'format_recipe_for_facebook'
       },
       ('facebook', 'word_of_day'): {
           'template': 'facebook/word_of_day.html',
           'max_length': 500,
           'requires_image': True,
           'format_function': 'format_word_for_facebook'
       },
       # ... etc
   }
   ```

2. **Update `config/output_channel_stages.py`**
   - Extend to include format in key: `(post_type, channel, content_format)`
   - Or keep as `(post_type, channel)` and resolve format from `post_type_channel_config`

### Phase 3: API & Logic Updates (2 days)

1. **Update `utils/channel_assignment.py`** (new file)
   ```python
   def get_channels_for_post_type(post_type: str) -> list:
       """Get all (channel, content_format) pairs for a post type"""
       # Query post_type_channel_config
       # Return: [{'channel': 'facebook', 'format': 'word_of_day'}, ...]
   
   def get_content_format(post_type: str, channel: str) -> str:
       """Get the content format for (post_type, channel)"""
       # Query post_type_channel_config
       # Return: 'word_of_day', 'recipe', 'syndication', etc.
   ```

2. **Update `create-post-from-item` endpoint**
   - Check if channel requires blog post creation
   - If not, create social media post directly with correct format
   - If yes, create blog post with correct format

3. **Update pipeline resolution**
   - Resolve stages based on (post_type, channel, content_format)
   - Use format-specific templates and functions

### Phase 4: Format-Specific Handlers (2-3 days)

1. **Create format handlers**
   - `utils/formatters/facebook_recipe_formatter.py`
   - `utils/formatters/facebook_word_formatter.py`
   - `utils/formatters/instagram_word_formatter.py`
   - etc.

2. **Update social media posting**
   - Route to format-specific formatter
   - Apply format-specific rules (length, image requirements, etc.)

---

## Benefits of This Architecture

1. **Clear Separation**: Post Type → Channel → Format hierarchy is explicit
2. **Flexibility**: Same post type can have different formats on different channels
3. **Extensibility**: Easy to add new formats without changing core logic
4. **Type Safety**: Database constraints ensure valid combinations
5. **Maintainability**: Format logic is isolated and testable

---

## Migration Path

1. **Immediate**: Add `content_format` column with default values
2. **Short-term**: Update all queries to include format
3. **Long-term**: Add format-specific handlers and templates

---

## Example Usage

```python
# Get format for a post type + channel
format = get_content_format('weekly_word', 'facebook')
# Returns: 'word_of_day'

# Get all channels and formats for a post type
channels = get_channels_for_post_type('recipe')
# Returns: [
#     {'channel': 'blog', 'format': 'recipe', 'is_primary': True},
#     {'channel': 'facebook', 'format': 'recipe', 'is_primary': False}
# ]

# Format content for specific channel + format
formatted = format_content_for_channel(
    post_type='weekly_word',
    channel='facebook',
    content_format='word_of_day',
    item_data=word_data
)
# Returns: Facebook-formatted word of the day post
```

---

## Questions to Resolve

1. **Format Naming**: Should formats be channel-specific (e.g., 'facebook_recipe') or generic (e.g., 'recipe')?
   - **Recommendation**: Generic names, resolved per channel context

2. **Format Inheritance**: Can formats inherit from base formats?
   - **Recommendation**: Start simple, add inheritance later if needed

3. **Format Validation**: Should formats have required fields?
   - **Recommendation**: Yes, define in `channel_content_formats` config

4. **Backward Compatibility**: How to handle existing posts without format?
   - **Recommendation**: Default to 'article' for blog, 'syndication' for social media

---

## Next Steps

1. **Review and approve** this architecture
2. **Define format list** for each channel
3. **Create database migration** script
4. **Implement Phase 1** (database schema)
5. **Implement Phase 2** (configuration layer)
6. **Update existing code** to use new format system

---

*Document Status: Proposal*  
*Next: User review and approval*

