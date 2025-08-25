# Social Media Syndication Database Schema

## Overview
This document provides a complete reference for the 17-table database structure implementing the social media syndication system with proper disambiguation between platform-wide and channel-specific settings.

## Database Architecture Principles

### 1. **Disambiguation Principle**
- **Platform-Wide Settings**: Stored in `platform_capabilities` table
- **Channel-Specific Settings**: Stored in `process_configurations` table
- **Clear Separation**: No overlap between platform capabilities and channel requirements

### 2. **Table Naming Convention**
- Clean naming without `social_media_` prefix
- Descriptive names that work for any platform
- Consistent structure across all tables

### 3. **Relationship Structure**
- Proper foreign key constraints with CASCADE deletion
- Indexed queries for performance optimization
- Timestamp tracking on all tables

## Core Tables

### 1. **platforms** - Platform Registry
**Purpose**: Central registry of all social media platforms

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| name | VARCHAR(50) | NOT NULL | - | Platform identifier (facebook, instagram, etc.) |
| display_name | VARCHAR(100) | NOT NULL | - | Human-readable name |
| description | TEXT | NULL | - | Platform description |
| status | VARCHAR(20) | NULL | 'active' | Platform status |
| priority | INTEGER | NULL | 0 | Development priority |
| website_url | VARCHAR(255) | NULL | - | Platform website |
| api_documentation_url | VARCHAR(255) | NULL | - | API docs URL |
| logo_url | VARCHAR(255) | NULL | - | Platform logo |
| development_status | VARCHAR(20) | NULL | 'not_started' | Development progress |
| is_featured | BOOLEAN | NULL | false | Featured in UI |
| menu_priority | INTEGER | NULL | 0 | Menu display order |
| is_visible_in_ui | BOOLEAN | NULL | true | UI visibility |
| last_activity_at | TIMESTAMP | NULL | - | Last activity timestamp |
| last_post_at | TIMESTAMP | NULL | - | Last post timestamp |
| last_api_call_at | TIMESTAMP | NULL | - | Last API call |
| total_posts_count | INTEGER | NULL | 0 | Total posts count |
| success_rate_percentage | NUMERIC(5,2) | NULL | - | Success rate |
| average_response_time_ms | INTEGER | NULL | - | Average response time |
| estimated_completion_date | DATE | NULL | - | Estimated completion |
| actual_completion_date | DATE | NULL | - | Actual completion |
| development_notes | TEXT | NULL | - | Development notes |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, name (unique), status, priority, development_status

### 2. **platform_capabilities** - Platform-Wide Settings
**Purpose**: General capabilities and specifications for each platform

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| platform_id | INTEGER | NOT NULL | - | Foreign key to platforms |
| capability_type | VARCHAR(50) | NOT NULL | - | Category (content, media, api, limits) |
| capability_name | VARCHAR(100) | NOT NULL | - | Capability identifier |
| capability_value | TEXT | NOT NULL | - | Actual capability value |
| description | TEXT | NULL | - | Human-readable description |
| unit | VARCHAR(50) | NULL | - | Unit of measurement |
| min_value | TEXT | NULL | - | Minimum value |
| max_value | TEXT | NULL | - | Maximum value |
| validation_rules | JSONB | NULL | - | JSON validation rules |
| is_active | BOOLEAN | NULL | true | Active status |
| display_order | INTEGER | NULL | 0 | Display order |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, platform_id, capability_type  
**Unique Constraint**: (platform_id, capability_type, capability_name)

### 3. **channel_types** - Generic Channel Definitions
**Purpose**: Generic content channel types across all platforms

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| name | VARCHAR(50) | NOT NULL | - | Channel identifier (feed_post, story_post, etc.) |
| display_name | VARCHAR(100) | NOT NULL | - | Human-readable name |
| description | TEXT | NULL | - | Channel description |
| content_type | VARCHAR(50) | NOT NULL | - | Content type (text, image, video, mixed) |
| media_support | TEXT[] | NULL | - | Array of supported media types |
| default_priority | INTEGER | NULL | 0 | Default priority |
| is_active | BOOLEAN | NULL | true | Active status |
| display_order | INTEGER | NULL | 0 | Display order |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, name (unique)

### 4. **content_processes** - Process Implementation Status
**Purpose**: Content conversion processes with development status tracking

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| platform_id | INTEGER | NOT NULL | - | Foreign key to platforms |
| channel_type_id | INTEGER | NOT NULL | - | Foreign key to channel_types |
| process_name | VARCHAR(100) | NOT NULL | - | Process identifier |
| display_name | VARCHAR(100) | NOT NULL | - | Human-readable name |
| description | TEXT | NULL | - | Process description |
| development_status | VARCHAR(20) | NULL | 'not_started' | Development progress |
| priority | INTEGER | NULL | 0 | Process priority |
| is_active | BOOLEAN | NULL | true | Active status |
| estimated_completion_date | DATE | NULL | - | Estimated completion |
| actual_completion_date | DATE | NULL | - | Actual completion |
| development_notes | TEXT | NULL | - | Development notes |
| last_activity_at | TIMESTAMP | NULL | - | Last activity |
| total_executions | INTEGER | NULL | 0 | Total executions |
| success_rate_percentage | NUMERIC(5,2) | NULL | - | Success rate |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, platform_id, channel_type_id, development_status  
**Unique Constraint**: (platform_id, channel_type_id, process_name)

### 5. **process_configurations** - Channel-Specific Settings
**Purpose**: Detailed configuration for each content process (implements disambiguation principle)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| process_id | INTEGER | NOT NULL | - | Foreign key to content_processes |
| config_category | VARCHAR(50) | NOT NULL | - | Configuration category |
| config_key | VARCHAR(100) | NOT NULL | - | Configuration key |
| config_value | TEXT | NOT NULL | - | Configuration value |
| description | TEXT | NULL | - | Human-readable description |
| display_order | INTEGER | NULL | 0 | Display order |
| is_active | BOOLEAN | NULL | true | Active status |
| validation_rules | JSONB | NULL | - | JSON validation rules |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, process_id, config_category  
**Unique Constraint**: (process_id, config_category, config_key)

### 6. **channel_requirements** - Channel-Specific Requirements
**Purpose**: Detailed requirements for each channel type on each platform

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| platform_id | INTEGER | NOT NULL | - | Foreign key to platforms |
| channel_type_id | INTEGER | NOT NULL | - | Foreign key to channel_types |
| requirement_category | VARCHAR(50) | NOT NULL | - | Requirement category |
| requirement_key | VARCHAR(100) | NOT NULL | - | Requirement key |
| requirement_value | TEXT | NOT NULL | - | Requirement value |
| description | TEXT | NULL | - | Human-readable description |
| is_required | BOOLEAN | NULL | true | Required status |
| validation_rules | JSONB | NULL | - | JSON validation rules |
| unit | VARCHAR(50) | NULL | - | Unit of measurement |
| min_value | TEXT | NULL | - | Minimum value |
| max_value | TEXT | NULL | - | Maximum value |
| display_order | INTEGER | NULL | 0 | Display order |
| is_active | BOOLEAN | NULL | true | Active status |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, platform_id, channel_type_id, requirement_category  
**Unique Constraint**: (platform_id, channel_type_id, requirement_category, requirement_key)

### 7. **platform_channel_support** - Platform-Channel Support Matrix
**Purpose**: Tracks which platforms support which channel types

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| platform_id | INTEGER | NOT NULL | - | Foreign key to platforms |
| channel_type_id | INTEGER | NOT NULL | - | Foreign key to channel_types |
| is_supported | BOOLEAN | NULL | true | Support status |
| status | VARCHAR(20) | NULL | 'active' | Channel status |
| development_status | VARCHAR(20) | NULL | 'not_started' | Development progress |
| priority | INTEGER | NULL | 0 | Development priority |
| notes | TEXT | NULL | - | Development notes |
| estimated_completion_date | DATE | NULL | - | Estimated completion |
| actual_completion_date | DATE | NULL | - | Actual completion |
| development_notes | TEXT | NULL | - | Development notes |
| last_activity_at | TIMESTAMP | NULL | - | Last activity |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, platform_id, channel_type_id, development_status  
**Unique Constraint**: (platform_id, channel_type_id)

### 8. **platform_credentials** - Platform Authentication
**Purpose**: API keys, tokens, and authentication details for each platform

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| platform_id | INTEGER | NOT NULL | - | Foreign key to platforms |
| credential_type | VARCHAR(50) | NOT NULL | - | Credential type (api_key, access_token, etc.) |
| credential_key | VARCHAR(100) | NOT NULL | - | Credential identifier |
| credential_value | TEXT | NOT NULL | - | Actual credential value |
| is_encrypted | BOOLEAN | NULL | false | Encryption status |
| is_active | BOOLEAN | NULL | true | Active status |
| expires_at | TIMESTAMP | NULL | - | Expiration timestamp |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, platform_id, credential_type  
**Unique Constraint**: (platform_id, credential_type, credential_key)

## Priority Management Tables

### 9. **content_priorities** - Priority Scoring
**Purpose**: Calculated priority scores for content and processes

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| content_type | VARCHAR(50) | NOT NULL | - | Content type (platform, process, etc.) |
| content_id | INTEGER | NOT NULL | - | ID of the content item |
| priority_score | NUMERIC(8,4) | NOT NULL | 0 | Calculated priority score |
| priority_factors | JSONB | NULL | - | JSON of contributing factors |
| last_calculated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Last calculation |
| next_calculation_at | TIMESTAMP | NULL | - | Next calculation due |
| calculation_version | VARCHAR(20) | NULL | - | Calculation algorithm version |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, content_type, content_id (unique), priority_score, last_calculated_at

### 10. **priority_factors** - Priority Calculation Factors
**Purpose**: Configurable factors for priority calculations

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| factor_name | VARCHAR(100) | NOT NULL | - | Factor identifier |
| display_name | VARCHAR(200) | NOT NULL | - | Human-readable name |
| description | TEXT | NULL | - | Factor description |
| factor_type | VARCHAR(50) | NOT NULL | - | Factor type |
| weight | NUMERIC(5,4) | NOT NULL | 1.0 | Factor weight |
| calculation_formula | TEXT | NULL | - | Calculation formula |
| is_active | BOOLEAN | NULL | true | Active status |
| is_configurable | BOOLEAN | NULL | true | Configurable status |
| min_value | NUMERIC(10,4) | NULL | - | Minimum value |
| max_value | NUMERIC(10,4) | NULL | - | Maximum value |
| default_value | NUMERIC(10,4) | NULL | - | Default value |
| unit | VARCHAR(50) | NULL | - | Unit of measurement |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, factor_name (unique), factor_type, is_active, weight

## UI Management Tables

### 11. **ui_sections** - UI Section Definitions
**Purpose**: Dynamic UI section management

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| name | VARCHAR(100) | NOT NULL | - | Section identifier |
| display_name | VARCHAR(200) | NOT NULL | - | Human-readable name |
| description | TEXT | NULL | - | Section description |
| section_type | VARCHAR(50) | NOT NULL | - | Section type |
| parent_section_id | INTEGER | NULL | - | Parent section (self-referencing) |
| display_order | INTEGER | NULL | 0 | Display order |
| is_visible | BOOLEAN | NULL | true | Visibility status |
| is_collapsible | BOOLEAN | NULL | true | Collapsible status |
| default_collapsed | BOOLEAN | NULL | false | Default collapsed state |
| color_theme | VARCHAR(50) | NULL | - | Color theme |
| icon_class | VARCHAR(100) | NULL | - | Icon CSS class |
| css_classes | TEXT | NULL | - | Additional CSS classes |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, name (unique), display_order, is_visible, parent_section_id, section_type

### 12. **ui_menu_items** - Menu Item Management
**Purpose**: Dynamic menu system with hierarchical structure

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| name | VARCHAR(100) | NOT NULL | - | Menu item identifier |
| display_name | VARCHAR(200) | NOT NULL | - | Human-readable name |
| description | TEXT | NULL | - | Menu item description |
| menu_type | VARCHAR(50) | NOT NULL | - | Menu type |
| parent_menu_id | INTEGER | NULL | - | Parent menu item (self-referencing) |
| section_id | INTEGER | NULL | - | Associated UI section |
| url_pattern | VARCHAR(255) | NULL | - | URL pattern |
| icon_class | VARCHAR(100) | NULL | - | Icon CSS class |
| display_order | INTEGER | NULL | 0 | Display order |
| is_visible | BOOLEAN | NULL | true | Visibility status |
| is_active | BOOLEAN | NULL | true | Active status |
| requires_permission | VARCHAR(100) | NULL | - | Required permission |
| badge_text | VARCHAR(50) | NULL | - | Badge text |
| badge_color | VARCHAR(50) | NULL | - | Badge color |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, name (unique), display_order, is_visible, menu_type, parent_menu_id, section_id

### 13. **ui_display_rules** - Conditional Display Logic
**Purpose**: Rules for conditional UI element display

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| rule_name | VARCHAR(100) | NOT NULL | - | Rule identifier |
| description | TEXT | NULL | - | Rule description |
| rule_type | VARCHAR(50) | NOT NULL | - | Rule type |
| target_type | VARCHAR(50) | NOT NULL | - | Target element type |
| target_id | INTEGER | NULL | - | Target element ID |
| condition_expression | TEXT | NULL | - | Condition logic |
| is_active | BOOLEAN | NULL | true | Active status |
| priority | INTEGER | NULL | 0 | Rule priority |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, rule_name (unique), rule_type, target_type, target_id, is_active, priority

### 14. **ui_user_preferences** - User-Specific Settings
**Purpose**: User preferences and settings storage

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| user_id | INTEGER | NOT NULL | - | User identifier |
| preference_key | VARCHAR(100) | NOT NULL | - | Preference key |
| preference_value | TEXT | NULL | - | Preference value |
| preference_type | VARCHAR(50) | NOT NULL | - | Preference type |
| category | VARCHAR(100) | NULL | - | Preference category |
| is_global | BOOLEAN | NULL | false | Global preference flag |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, user_id, preference_key (unique), category, is_global

### 15. **ui_session_state** - Session State Management
**Purpose**: Session-specific state storage

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| session_id | VARCHAR(255) | NOT NULL | - | Session identifier |
| user_id | INTEGER | NULL | - | User identifier |
| state_key | VARCHAR(100) | NOT NULL | - | State key |
| state_value | TEXT | NULL | - | State value |
| state_type | VARCHAR(50) | NOT NULL | - | State type |
| expires_at | TIMESTAMP | NULL | - | Expiration timestamp |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Update timestamp |

**Indexes**: Primary key, session_id, state_key (unique), user_id, expires_at

## Metadata Tables

### 16. **requirement_categories** - Requirement Category Definitions
**Purpose**: Categories for organizing requirements

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| name | VARCHAR(50) | NOT NULL | - | Category identifier |
| display_name | VARCHAR(100) | NOT NULL | - | Human-readable name |
| description | TEXT | NULL | - | Category description |
| display_order | INTEGER | NULL | 0 | Display order |
| color_theme | VARCHAR(20) | NULL | 'primary' | Color theme |
| icon_class | VARCHAR(100) | NULL | - | Icon CSS class |
| is_active | BOOLEAN | NULL | true | Active status |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |

**Indexes**: Primary key, name (unique)

### 17. **config_categories** - Configuration Category Definitions
**Purpose**: Categories for organizing process configurations

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | SERIAL | NOT NULL | - | Primary key |
| name | VARCHAR(50) | NOT NULL | - | Category identifier |
| display_name | VARCHAR(100) | NOT NULL | - | Human-readable name |
| description | TEXT | NULL | - | Category description |
| display_order | INTEGER | NULL | 0 | Display order |
| color_theme | VARCHAR(20) | NULL | 'primary' | Color theme |
| icon_class | VARCHAR(100) | NULL | - | Icon CSS class |
| is_active | BOOLEAN | NULL | true | Active status |
| created_at | TIMESTAMP | NULL | CURRENT_TIMESTAMP | Creation timestamp |

**Indexes**: Primary key, name (unique)

## Key Relationships

### **Platform Hierarchy**
```
platforms (1) ←→ (N) platform_capabilities
platforms (1) ←→ (N) platform_credentials
platforms (1) ←→ (N) platform_channel_support
```

### **Channel Hierarchy**
```
channel_types (1) ←→ (N) channel_requirements
channel_types (1) ←→ (N) content_processes
channel_types (1) ←→ (N) platform_channel_support
```

### **Process Hierarchy**
```
content_processes (1) ←→ (N) process_configurations
platforms (1) ←→ (N) content_processes
channel_types (1) ←→ (N) content_processes
```

### **UI Hierarchy**
```
ui_sections (1) ←→ (N) ui_sections (self-referencing)
ui_sections (1) ←→ (N) ui_menu_items
ui_menu_items (1) ←→ (N) ui_menu_items (self-referencing)
```

## Disambiguation Principle Implementation

### **Platform-Wide Settings** → `platform_capabilities`
- General platform capabilities (API endpoints, rate limits, file formats)
- Universal settings that apply to all channels on a platform
- Example: Facebook's 63,206 character limit (platform-wide capability)

### **Channel-Specific Settings** → `process_configurations`
- Specific requirements for each channel type
- Process-specific configurations and strategies
- Example: Feed Post character limit, Story Post dimensions, Reels caption length

### **Clear Separation**
- No overlap between platform capabilities and channel requirements
- Platform capabilities stored once per platform
- Channel requirements stored per process (platform + channel combination)
- Easy to maintain and extend

## Current Data Status

### **Facebook Platform** (ID: 1)
- **Status**: Developed
- **Channels**: Feed Post, Story Post, Reels, Group Post
- **Processes**: 4 content processes with full configuration
- **Configurations**: 24 channel-specific configurations

### **Other Platforms**
- **Status**: Undeveloped
- **Channels**: Basic channel type definitions
- **Processes**: None implemented
- **Configurations**: None

## Performance Considerations

### **Indexes**
- Primary keys on all tables
- Foreign key indexes for relationship queries
- Category and status indexes for filtering
- Priority score indexes for sorting

### **Constraints**
- Unique constraints prevent duplicate data
- Foreign key constraints maintain referential integrity
- Check constraints validate data values
- CASCADE deletion maintains consistency

## Maintenance Notes

- **Timestamps**: All tables include created_at and updated_at
- **Soft Deletion**: Use is_active flag instead of hard deletion
- **Validation**: JSONB validation_rules for complex validation logic
- **Extensibility**: Generic design supports any platform or channel type

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-27  
**Status**: Complete database schema documentation  
**Database**: PostgreSQL with 17 tables implementing disambiguation principle
