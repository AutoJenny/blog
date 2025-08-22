# New Database Framework Proposal for Social Media Syndication

## Overview
This document proposes a complete redesign of the social media syndication database architecture to address the fundamental flaws in the current system. The new framework will be generic, extensible, and properly normalized to support multiple platforms and channel types.

## Current Problems Identified
1. **Mixed concerns** - Platform capabilities mixed with channel requirements
2. **Poor normalization** - Key-value pairs instead of proper relational structure
3. **Hardcoded UI** - Labels and structure not database-driven
4. **Inflexible design** - Difficult to add new platforms or channels
5. **Architectural confusion** - Platform-wide vs channel-specific data mixed together

## New Architecture Principles

### 1. **Separation of Concerns**
- **Platform Registry** - What platforms exist
- **Platform Credentials** - How to authenticate with platforms
- **Platform Capabilities** - What each platform can do
- **Channel Types** - Generic content channels across platforms
- **Channel Requirements** - Specific needs for each channel type
- **Content Processes** - Implementation status and metadata

### 2. **Generic Field Names**
- All field names work for any platform (Facebook, Instagram, Twitter, LinkedIn, etc.)
- No platform-specific terminology in database schema
- Easy to extend for new platforms

### 3. **Proper Normalization**
- No more key-value pair tables
- Proper foreign key relationships
- Eliminate data duplication

## Proposed Database Schema

### Core Tables

#### 1. `platforms`
**Purpose**: Registry of all social media platforms
```sql
CREATE TABLE platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,           -- 'facebook', 'instagram', 'twitter'
    display_name VARCHAR(100) NOT NULL,         -- 'Facebook', 'Instagram', 'Twitter'
    description TEXT,                           -- Platform description
    status VARCHAR(20) DEFAULT 'active',        -- 'active', 'inactive', 'deprecated'
    priority INTEGER DEFAULT 0,                 -- Display order priority
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `platform_credentials`
**Purpose**: API keys, tokens, and authentication details
```sql
CREATE TABLE platform_credentials (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id),
    credential_type VARCHAR(50) NOT NULL,       -- 'api_key', 'access_token', 'app_secret'
    credential_key VARCHAR(100) NOT NULL,       -- 'facebook_app_id', 'instagram_token'
    credential_value TEXT NOT NULL,             -- Actual credential value
    is_encrypted BOOLEAN DEFAULT false,         -- Whether value is encrypted
    is_active BOOLEAN DEFAULT true,             -- Whether credential is active
    expires_at TIMESTAMP,                       -- When credential expires
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, credential_type, credential_key)
);
```

#### 3. `platform_capabilities`
**Purpose**: What each platform can do (generic features)
```sql
CREATE TABLE platform_capabilities (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id),
    capability_type VARCHAR(50) NOT NULL,       -- 'content', 'media', 'api', 'limits'
    capability_name VARCHAR(100) NOT NULL,      -- 'max_character_limit', 'image_formats'
    capability_value TEXT NOT NULL,             -- Actual capability value
    description TEXT,                           -- Human-readable description
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, capability_type, capability_name)
);
```

#### 4. `channel_types`
**Purpose**: Generic definitions of content channels across all platforms
```sql
CREATE TABLE channel_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,           -- 'feed_post', 'story_post', 'video_post'
    display_name VARCHAR(100) NOT NULL,         -- 'Feed Post', 'Story Post', 'Video Post'
    description TEXT,                           -- Channel description
    content_type VARCHAR(50) NOT NULL,          -- 'text', 'image', 'video', 'mixed'
    media_support TEXT[],                       -- Array of supported media types
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. `platform_channel_support`
**Purpose**: Which platforms support which channels
```sql
CREATE TABLE platform_channel_support (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id),
    channel_type_id INTEGER REFERENCES channel_types(id),
    is_supported BOOLEAN DEFAULT true,          -- Whether platform supports this channel
    status VARCHAR(20) DEFAULT 'active',        -- 'active', 'beta', 'deprecated'
    notes TEXT,                                 -- Additional notes about support
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, channel_type_id)
);
```

#### 6. `channel_requirements`
**Purpose**: Specific requirements for each channel on each platform
```sql
CREATE TABLE channel_requirements (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id),
    channel_type_id INTEGER REFERENCES channel_types(id),
    requirement_category VARCHAR(50) NOT NULL,  -- 'dimensions', 'content', 'engagement'
    requirement_key VARCHAR(100) NOT NULL,      -- 'image_width', 'max_hashtags'
    requirement_value TEXT NOT NULL,            -- Actual requirement value
    description TEXT,                           -- Human-readable description
    is_required BOOLEAN DEFAULT true,           -- Whether this is mandatory
    validation_rules JSONB,                     -- JSON validation rules
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, channel_type_id, requirement_category, requirement_key)
);
```

#### 7. `content_processes`
**Purpose**: Implementation status and metadata for content processes
```sql
CREATE TABLE content_processes (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id),
    channel_type_id INTEGER REFERENCES channel_types(id),
    process_name VARCHAR(100) NOT NULL,         -- 'facebook_feed_post', 'instagram_story'
    display_name VARCHAR(100) NOT NULL,         -- 'Facebook Feed Post', 'Instagram Story'
    description TEXT,                           -- Process description
    development_status VARCHAR(20) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'developed', 'active'
    priority INTEGER DEFAULT 0,                 -- Development priority
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, channel_type_id, process_name)
);
```

#### 8. `process_configurations`
**Purpose**: Actual configuration values for content processes
```sql
CREATE TABLE process_configurations (
    id SERIAL PRIMARY KEY,
    process_id INTEGER REFERENCES content_processes(id),
    config_category VARCHAR(50) NOT NULL,       -- 'content_strategy', 'image_requirements', 'engagement_tactics'
    config_key VARCHAR(100) NOT NULL,           -- 'tone_guidelines', 'hashtag_strategy'
    config_value TEXT NOT NULL,                 -- Actual configuration value
    description TEXT,                           -- Human-readable description
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,            -- Order in UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(process_id, config_category, config_key)
);
```

### Supporting Tables

#### 9. `requirement_categories`
**Purpose**: Standardized categories for channel requirements
```sql
CREATE TABLE requirement_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,           -- 'dimensions', 'content', 'engagement'
    display_name VARCHAR(100) NOT NULL,         -- 'Dimensions', 'Content Guidelines', 'Engagement'
    description TEXT,                           -- Category description
    display_order INTEGER DEFAULT 0,            -- Order in UI
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 10. `config_categories`
**Purpose**: Standardized categories for process configurations
```sql
CREATE TABLE config_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,           -- 'content_strategy', 'image_requirements'
    display_name VARCHAR(100) NOT NULL,         -- 'Content Strategy', 'Image Requirements'
    description TEXT,                           -- Category description
    display_order INTEGER DEFAULT 0,            -- Order in UI
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### UI & Operational Tables

#### 11. `ui_sections` - UI Section Definitions
**Purpose**: Define UI sections for organized navigation
```sql
CREATE TABLE ui_sections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,                    -- 'main_navigation', 'platform_sidebar', 'channel_selector'
    display_name VARCHAR(100) NOT NULL,                  -- 'Main Navigation', 'Platform Sidebar', 'Channel Selector'
    description TEXT,                                     -- Section description
    display_order INTEGER DEFAULT 0,                     -- Order in UI
    is_active BOOLEAN DEFAULT true,                      -- Whether section is active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 12. `ui_menu_items` - Menu Item Management
**Purpose**: Manage menu items with conditional display rules
```sql
CREATE TABLE ui_menu_items (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES ui_sections(id) ON DELETE CASCADE,
    parent_item_id INTEGER REFERENCES ui_menu_items(id) ON DELETE CASCADE, -- For nested menus
    item_type VARCHAR(50) NOT NULL,                      -- 'platform', 'channel', 'category', 'action'
    reference_id INTEGER,                                 -- ID of referenced item (platform_id, channel_type_id, etc.)
    display_name VARCHAR(100) NOT NULL,                  -- Text to display in menu
    icon_class VARCHAR(100),                             -- FontAwesome icon class
    url_path VARCHAR(255),                               -- URL path for navigation
    is_visible BOOLEAN DEFAULT true,                     -- Whether item is visible
    is_active BOOLEAN DEFAULT true,                      -- Whether item is active
    display_order INTEGER DEFAULT 0,                     -- Order within section
    requires_development_status VARCHAR(20),              -- Minimum development status required
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 13. `ui_display_rules` - Conditional Display Logic
**Purpose**: Define rules for when menu items should be displayed
```sql
CREATE TABLE ui_display_rules (
    id SERIAL PRIMARY KEY,
    menu_item_id INTEGER NOT NULL REFERENCES ui_menu_items(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL,                      -- 'development_status', 'user_permission', 'platform_status'
    rule_condition VARCHAR(100) NOT NULL,                -- 'equals', 'greater_than', 'in_list', 'not_null'
    rule_value TEXT NOT NULL,                            -- Value to compare against
    rule_description TEXT,                                -- Human-readable rule description
    is_active BOOLEAN DEFAULT true,                      -- Whether rule is active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 14. `content_priorities` - Dynamic Priority Management
**Purpose**: Calculate and manage priorities based on recency and activity
```sql
CREATE TABLE content_priorities (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id) ON DELETE CASCADE,
    channel_type_id INTEGER REFERENCES channel_types(id) ON DELETE CASCADE,
    priority_type VARCHAR(50) NOT NULL,                  -- 'development', 'posting', 'engagement', 'maintenance'
    priority_score INTEGER NOT NULL,                     -- 1-100 priority score
    priority_factors JSONB,                              -- Factors contributing to priority
    last_calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_calculation_at TIMESTAMP,                       -- When to recalculate priority
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 15. `priority_factors` - Priority Calculation Factors
**Purpose**: Define factors and weights for priority calculations
```sql
CREATE TABLE priority_factors (
    id SERIAL PRIMARY KEY,
    factor_name VARCHAR(100) UNIQUE NOT NULL,            -- 'recent_activity', 'development_progress', 'user_demand'
    factor_description TEXT,                             -- Factor description
    weight DECIMAL(3,2) DEFAULT 1.00,                   -- Weight in priority calculation (0.00-1.00)
    calculation_formula TEXT,                            -- Formula for calculating factor score
    is_active BOOLEAN DEFAULT true,                      -- Whether factor is active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 16. `ui_user_preferences` - User-Specific UI Settings
**Purpose**: Store user preferences for UI customization
```sql
CREATE TABLE ui_user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,                            -- Reference to user system
    preference_type VARCHAR(50) NOT NULL,                -- 'default_platform', 'favorite_channels', 'ui_theme'
    preference_key VARCHAR(100) NOT NULL,                -- Specific preference key
    preference_value TEXT NOT NULL,                      -- Preference value
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_type, preference_key)
);
```

#### 17. `ui_session_state` - Session-Specific UI State
**Purpose**: Track UI state across user sessions
```sql
CREATE TABLE ui_session_state (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,                    -- Session identifier
    user_id INTEGER,                                     -- Reference to user system
    state_type VARCHAR(50) NOT NULL,                     -- 'last_viewed_platform', 'expanded_sections', 'selected_channels'
    state_key VARCHAR(100) NOT NULL,                     -- State key
    state_value TEXT NOT NULL,                           -- State value
    expires_at TIMESTAMP NOT NULL,                       -- When state expires
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, state_type, state_key)
);
```

## Example Data Structure

### Facebook Platform Example

#### Platforms
```sql
INSERT INTO platforms (name, display_name, description, priority) VALUES
('facebook', 'Facebook', 'Meta social media platform', 1),
('instagram', 'Instagram', 'Meta photo and video sharing platform', 2);
```

#### Platform Capabilities (Facebook)
```sql
INSERT INTO platform_capabilities (platform_id, capability_type, capability_name, capability_value, description) VALUES
(1, 'content', 'max_character_limit', '63206', 'Maximum characters for text posts'),
(1, 'media', 'supported_image_formats', 'JPG,PNG,GIF', 'Supported image formats'),
(1, 'media', 'max_file_size_mb', '30', 'Maximum file size in MB'),
(1, 'api', 'rate_limit_posts_per_hour', '200', 'Maximum posts per hour per user');
```

#### Channel Types
```sql
INSERT INTO channel_types (name, display_name, description, content_type, media_support) VALUES
('feed_post', 'Feed Post', 'Standard social media posts', 'mixed', '{text,image,video}'),
('story_post', 'Story Post', 'Temporary 24-hour content', 'mixed', '{image,video}'),
('reels_post', 'Reels Post', 'Short-form video content', 'video', '{video}'),
('group_post', 'Group Post', 'Community-focused content', 'mixed', '{text,image,video}');
```

#### Channel Requirements (Facebook Feed Post)
```sql
INSERT INTO channel_requirements (platform_id, channel_type_id, requirement_category, requirement_key, requirement_value, description) VALUES
(1, 1, 'dimensions', 'image_width', '1200', 'Recommended image width for feed posts'),
(1, 1, 'dimensions', 'image_height', '630', 'Recommended image height for feed posts'),
(1, 1, 'dimensions', 'aspect_ratio', '1.91:1', 'Recommended aspect ratio for feed posts'),
(1, 1, 'content', 'max_hashtags', '3', 'Recommended maximum hashtags for feed posts');
```

#### Content Processes
```sql
INSERT INTO content_processes (platform_id, channel_type_id, process_name, display_name, description, development_status, priority) VALUES
(1, 1, 'facebook_feed_post', 'Facebook Feed Post', 'Standard Facebook text + image posts', 'developed', 1),
(1, 2, 'facebook_story_post', 'Facebook Story Post', 'Facebook Stories with engaging visuals', 'not_started', 2);
```

#### Process Configurations
```sql
INSERT INTO process_configurations (process_id, config_category, config_key, config_value, description, display_order) VALUES
(1, 'content_strategy', 'tone_guidelines', 'Conversational, engaging, authentic', 'Recommended tone for feed posts', 1),
(1, 'content_strategy', 'hashtag_strategy', '2-3 relevant hashtags for feed posts', 'Hashtag usage guidelines', 2),
(1, 'image_requirements', 'style_guidelines', 'Authentic, engaging, shareable', 'Image style recommendations', 1);
```

## Benefits of New Framework

### 1. **Clear Separation**
- Platform capabilities vs channel requirements
- Authentication vs configuration
- Generic vs platform-specific data

### 2. **Extensibility**
- Easy to add new platforms
- Easy to add new channel types
- Easy to add new requirement categories

### 3. **Data Integrity**
- Proper foreign key relationships
- No duplicate data
- Consistent structure across platforms

### 4. **UI Flexibility**
- All labels can be database-driven
- Easy to add new fields
- Consistent presentation across platforms

### 5. **Maintenance**
- Single source of truth for each data type
- Easy to update platform capabilities
- Easy to modify channel requirements

## Migration Strategy

### Phase 1: Create New Schema
1. Create new tables with proper structure
2. Set up foreign key relationships
3. Create indexes for performance

### Phase 2: Migrate Existing Data
1. Map current data to new structure
2. Transform key-value pairs to proper fields
3. Validate data integrity

### Phase 3: Update Application
1. Modify API endpoints
2. Update UI templates
3. Test functionality

### Phase 4: Cleanup
1. Remove old tables
2. Update documentation
3. Performance optimization

## Next Steps

1. **Review and approve** this framework proposal
2. **Define detailed specifications** for each table
3. **Create migration scripts** for existing data
4. **Implement new schema** in development
5. **Test with sample data** from multiple platforms
6. **Deploy and migrate** production data

## Questions for Discussion

1. **Platform Coverage**: Which platforms should we support initially?
2. **Channel Types**: Are there channel types we haven't considered?
3. **Requirement Categories**: Do we need additional requirement categories?
4. **Validation Rules**: How complex should validation rules be?
5. **Performance**: Any concerns about table sizes or query performance?
