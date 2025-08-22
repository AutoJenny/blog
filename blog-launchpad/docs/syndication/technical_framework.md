# Syndication System Technical Framework

## Overview
This document records the technical frameworks and data structures that have been designed and implemented for the Social Media Syndication System. It serves as a comprehensive reference for the current architecture and planned extensions.

## Implemented Data Frameworks

### 1. Social Media Platform Management
**Status**: ✅ **IMPLEMENTED**

#### Core Tables
- **`social_media_platforms`**: Platform registry with status tracking
- **`social_media_platform_specs`**: Platform-specific specifications and requirements

#### Table Structure
```sql
-- Platforms table
CREATE TABLE social_media_platforms (
    id SERIAL PRIMARY KEY,
    platform_name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'undeveloped' CHECK (status IN ('undeveloped', 'developed', 'active')),
    priority INTEGER DEFAULT 0,
    icon_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Specifications table
CREATE TABLE social_media_platform_specs (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES social_media_platforms(id) ON DELETE CASCADE,
    spec_category VARCHAR(50) NOT NULL,
    spec_key VARCHAR(100) NOT NULL,
    spec_value TEXT NOT NULL,
    spec_type VARCHAR(20) DEFAULT 'text' CHECK (spec_type IN ('text', 'integer', 'json', 'boolean', 'url')),
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, spec_category, spec_key)
);
```

#### Specification Categories
- **`content`**: Content requirements and guidelines
- **`image`**: Image specifications and requirements  
- **`adaptation`**: Content adaptation strategies
- **`api`**: API integration details

#### Current Data
- **Facebook**: Fully configured with all specifications (status: 'developed')
- **Other platforms**: Basic platform info only (status: 'undeveloped')

#### Database Models
- **`SocialMediaPlatform`**: Python class for platform management
- **Methods**: `get_all_platforms()`, `get_platforms_by_status()`, `get_platform_by_name()`

#### API Endpoints
- **`/api/syndication/social-media-platforms`**: Returns platforms filtered by status
- **`/api/syndication/content-processes`**: Returns all active content processes
- **`/api/syndication/content-processes/{id}/configs`**: Returns configurations for a specific process

### 2. Content Syndication Interface
**Status**: ✅ **IMPLEMENTED**

#### Frontend Components
- **Post Selection**: Dropdown for blog post selection
- **Section Display**: Left column showing post sections with original styling
- **Piece Generation**: Right column for social media content pieces
- **Channel Selection**: Full-width panel with social media platform dropdown

#### Layout Architecture
- **Flexbox-based Grid**: Custom CSS for true row-based alignment
- **Row Synchronization**: Each "Piece" panel aligns 100% vertically with corresponding "Section" panel
- **Height Matching**: Panels stretch to match tallest content in each row

#### CSS Framework
```css
.sections-content-grid {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.grid-row {
    display: flex;
    gap: 1rem;
    align-items: stretch;
}

.grid-row .sections-panel,
.grid-row .pieces-panel {
    flex: 1;
}
```

#### JavaScript Functions
- **`displayPostDetails()`**: Handles post selection and channel display
- **`displaySections()`**: Creates synchronized section/piece rows
- **`fetchSocialMediaPlatforms()`**: Populates platform dropdown

### 3. Content Process Registry
**Status**: ✅ **IMPLEMENTED**

#### Core Tables
- **`social_media_content_processes`**: Process definitions with development status
- **`social_media_process_configs`**: Process-specific configurations and prompts
- **`social_media_process_executions`**: Execution history and results tracking

#### Table Structure
```sql
-- Content processes table
CREATE TABLE social_media_content_processes (
    id SERIAL PRIMARY KEY,
    process_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    platform_id INTEGER REFERENCES social_media_platforms(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    development_status VARCHAR(20) DEFAULT 'draft' CHECK (development_status IN ('draft', 'developed', 'testing', 'production')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Process configurations table
CREATE TABLE social_media_process_configs (
    id SERIAL PRIMARY KEY,
    process_id INTEGER REFERENCES social_media_content_processes(id) ON DELETE CASCADE,
    config_category VARCHAR(50) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) DEFAULT 'text',
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(process_id, config_category, config_key)
);

-- Process executions table
CREATE TABLE social_media_process_executions (
    id SERIAL PRIMARY KEY,
    process_id INTEGER REFERENCES social_media_content_processes(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    result_data TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Development Status Levels
- **`draft`**: Basic process defined, not yet configured
- **`developed`**: Process fully configured and ready for use
- **`testing`**: Process being tested with real content
- **`production`**: Process live and working in production

#### Current Processes (Facebook Platform)
1. **Feed Post** (`facebook_feed_post`) - Status: `developed`
2. **Story Post** (`facebook_story_post`) - Status: `developed`
3. **Reels Caption** (`facebook_reels_caption`) - Status: `developed`
4. **Group Post** (`facebook_group_post`) - Status: `developed`

#### Configuration Categories
- **`llm_prompt`**: System and user prompts for LLM processing
- **`constraints`**: Character limits, hashtag counts, etc.
- **`style_guide`**: Tone, hashtag strategy, CTA examples

#### Database Models
- **`ContentProcess`**: Python class for process management
- **Methods**: `get_all_processes()`, `get_processes_by_platform()`, `get_processes_by_development_status()`, `get_process_configs()`, `create_process_execution()`, `update_execution_status()`

### 4. Two-Stage Conversion Selection System
**Status**: ✅ **IMPLEMENTED**

#### UI Components
- **Conversion Settings Panel**: Full-width panel above the sections/pieces table
- **Platform Selection**: First dropdown showing only 'developed' social media platforms
- **Process Selection**: Second dropdown showing processes for the selected platform
- **Process Details**: Information panel showing selected process details

#### Selection Flow
1. **Platform Selection**: User selects from developed platforms (currently Facebook)
2. **Process Filtering**: Second dropdown populates with processes for selected platform
3. **Process Selection**: User selects specific content process (Feed Post, Story Post, etc.)
4. **Details Display**: Process information panel shows configuration and status

#### JavaScript Implementation
- **`fetchSocialMediaPlatforms()`**: Loads developed platforms
- **`fetchContentProcesses(platformId)`**: Filters processes by platform
- **`displayProcessDetails(process)`**: Shows selected process information
- **Cascading Dropdowns**: Second dropdown enabled only after platform selection

#### Integration Points
- **Post Selection**: Conversion panel appears when post is selected
- **Process Execution**: Selected process can be used for content conversion
- **Status Tracking**: Development status visible for each process

### 3. Platform Settings Management
**Status**: ✅ **IMPLEMENTED**

#### Facebook Platform Settings
- **Content Specifications**: Character limits, style guidelines, posting frequency
- **Image Requirements**: Dimensions, aspect ratios, format specifications
- **Content Adaptation**: Platform-specific content strategies
- **API Integration**: Technical integration details

#### UI Implementation
- **Bootstrap Accordions**: Four main panels converted to collapsible sections
- **Visual Indicators**: Expand/collapse arrows with SVG icons
- **Default State**: All accordions closed by default
- **Responsive Design**: Maintains existing styling and functionality

#### CSS Enhancements
```css
.accordion-button::after {
    background-image: url("data:image/svg+xml,%3csvg...");
    transition: transform 0.2s ease-in-out;
}

.accordion-button:not(.collapsed)::after {
    transform: rotate(180deg);
}
```

## Planned Data Frameworks

### 4. Content Process Registry
**Status**: 🚧 **DESIGNED** (Not yet implemented)

#### Proposed Table Structure
```sql
-- Main process table
CREATE TABLE social_media_content_processes (
    id SERIAL PRIMARY KEY,
    process_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    platform_id INTEGER REFERENCES social_media_platforms(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Process configuration table
CREATE TABLE social_media_process_configs (
    id SERIAL PRIMARY KEY,
    process_id INTEGER REFERENCES social_media_content_processes(id) ON DELETE CASCADE,
    config_category VARCHAR(50) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) DEFAULT 'text' CHECK (config_type IN ('text', 'integer', 'json', 'boolean')),
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(process_id, config_category, config_key)
);

-- Process execution history table
CREATE TABLE social_media_process_executions (
    id SERIAL PRIMARY KEY,
    process_id INTEGER REFERENCES social_media_content_processes(id),
    post_id INTEGER,
    section_id INTEGER,
    input_content TEXT,
    output_content TEXT,
    execution_status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Design Principles
- **Platform Agnostic**: Same process structure across different platforms
- **Modular Configuration**: Flexible settings via key-value pairs
- **Execution Tracking**: History and performance monitoring
- **Multiple Processes**: Support for different content styles per platform

#### Configuration Categories
- **`llm_prompt`**: AI model instructions and system prompts
- **`constraints`**: Platform-specific limitations and requirements
- **`style_guide`**: Content tone, format, and branding guidelines

## Technical Architecture Patterns

### Database Design Principles
- **Consistent Naming**: All tables follow `social_media_*` prefix convention
- **Timestamp Tracking**: `created_at` and `updated_at` on all tables
- **Foreign Key Relationships**: Proper referential integrity
- **Indexing Strategy**: Performance optimization for common queries
- **Trigger Functions**: Automatic `updated_at` maintenance

### API Design Patterns
- **RESTful Endpoints**: Consistent URL structure
- **JSON Response Format**: Standardized data structure
- **Error Handling**: Proper HTTP status codes and error messages
- **Database Integration**: Direct model usage in endpoints

### Frontend Architecture
- **Bootstrap 5.1.3**: Primary UI framework
- **Custom CSS**: Specialized styling for syndication features
- **Vanilla JavaScript**: DOM manipulation and API integration
- **Responsive Design**: Mobile-friendly layouts

### Data Flow Patterns
- **Post Selection** → **Section Extraction** → **Channel Selection** → **Content Generation**
- **Platform Configuration** → **Process Definition** → **Content Adaptation** → **Output Generation**

## Integration Points

### Existing Systems
- **Blog Post Database**: Source content for syndication
- **Post Sections**: Individual content units for adaptation
- **Image Assets**: Visual content for platform-specific formatting

### External Dependencies
- **PostgreSQL**: Primary database system
- **Psycopg2**: Python database adapter
- **Flask**: Web framework for API endpoints
- **Bootstrap**: Frontend component library

## Current Implementation Status

### ✅ Completed Components
1. Social media platform database schema
2. Platform specifications management
3. Content syndication interface
4. Bulletproof table-based row alignment system
5. Platform settings accordion interface
6. Channel selection dropdown
7. API endpoints for platform data
8. Content process registry tables and models
9. Database viewer integration (Social Media group)
10. Two-stage conversion selection system
11. Development status tracking for processes
12. Complete API endpoint implementation
13. Tasks column with row numbering
14. Conversion Settings panel with process details

### 🚧 In Progress
1. LLM integration framework planning

### 📋 Planned Components
1. Content generation processes
2. Automated posting workflows
3. Performance analytics
4. Multi-platform content scheduling

## Technical Constraints

### Database Limitations
- **PostgreSQL**: No SQLite usage (as per user rules)
- **Schema Changes**: Require user approval before implementation
- **Migration Strategy**: Proper backup and rollback procedures

### Development Rules
- **No Login/Registration**: Authentication systems not required
- **No Port Conflicts**: Use existing ports (3000, 5000) or stop conflicting processes
- **Bug Fixes**: Automatic resolution without user permission
- **Documentation**: Maintain changes log and update docs after each completion

## Performance Considerations

### Database Optimization
- **Indexed Queries**: Performance optimization for platform lookups
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Minimal database round trips

### Frontend Performance
- **Lazy Loading**: Content loaded on demand
- **Efficient DOM Updates**: Minimal re-rendering
- **CSS Optimization**: Efficient styling rules

## Security Considerations

### Data Protection
- **Input Validation**: Sanitize all user inputs
- **SQL Injection Prevention**: Parameterized queries
- **API Security**: Rate limiting and access control

### Platform Integration
- **API Key Management**: Secure storage of platform credentials
- **OAuth Implementation**: Secure authentication flows
- **Data Encryption**: Sensitive information protection

## Maintenance and Monitoring

### Database Maintenance
- **Regular Backups**: Automated backup procedures
- **Performance Monitoring**: Query performance tracking
- **Schema Evolution**: Controlled schema changes

### Application Monitoring
- **Error Logging**: Comprehensive error tracking
- **Performance Metrics**: Response time monitoring
- **User Activity**: Usage pattern analysis

## Future Considerations

### Scalability
- **Horizontal Scaling**: Database sharding strategies
- **Caching Layer**: Redis or similar for performance
- **Load Balancing**: Multiple application instances

### Extensibility
- **Plugin Architecture**: Modular process definitions
- **API Versioning**: Backward compatibility management
- **Third-party Integrations**: External service connections

---

**Document Version**: 1.1  
**Last Updated**: 2025-01-27  
**Status**: Active Development - Process Registry Implemented  
**Next Review**: After LLM integration implementation
