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
4. Row-based alignment system
5. Platform settings accordion interface
6. Channel selection dropdown
7. API endpoints for platform data

### 🚧 In Progress
1. Content process registry design
2. LLM integration framework planning

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

**Document Version**: 1.0  
**Last Updated**: 2025-01-27  
**Status**: Active Development  
**Next Review**: After process registry implementation
