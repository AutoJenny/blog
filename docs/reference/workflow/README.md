# Workflow System Documentation

## Overview

The workflow system provides a structured approach to content creation and management through defined stages, substages, and associated field mappings. This document provides a comprehensive guide to understanding and working with the workflow system.

## Documentation Structure

This workflow documentation is organized into the following sections:

- **[README.md](./README.md)** - This overview and system architecture guide
- **[formats.md](./formats.md)** - Format system documentation and usage
- **[prompts.md](./prompts.md)** - Prompt system and template management
- **[testing.md](./testing.md)** - Testing procedures and step naming conventions
- **[llm_panel.md](./llm_panel.md)** - LLM Panel module architecture and integration
- **[endpoints.md](./endpoints.md)** - Complete API endpoint reference

## Core Concepts

### 1. Workflow Structure
- **Stages**: High-level workflow phases (e.g., Planning, Authoring, Publishing)
- **Substages**: Specific steps within each stage (e.g., Idea, Research, Draft)
- **Field Mappings**: Associations between post development fields and workflow stages/substages

### 2. Key Components
- **Navigation Module**: Handles workflow navigation and stage transitions
- **LLM Panel**: Universal modular panel for AI-assisted content generation
- **Field Selector**: Dynamic field selection based on workflow context
- **API Layer**: RESTful endpoints for workflow operations

## Architecture

### Frontend Components
```
app/templates/workflow/
├── base.html                    # Base template for workflow pages
├── _modular_llm_panels.html     # Universal LLM panel component
└── steps/                       # Stage-specific templates
    ├── planning.html
    ├── authoring.html
    └── publishing.html
```

### Backend Structure
```
app/
├── api/
│   └── workflow/               # API endpoints
│       ├── fields.py          # Field mapping operations
│       ├── posts.py           # Post development endpoints
│       └── llm.py            # LLM integration endpoints
└── workflow/
    ├── context.py            # Workflow context management
    ├── routes.py            # UI routes
    └── scripts/             # Background processing
```

## Database Schema

### Core Tables
- `workflow_stage_entity`: Defines workflow stages
- `workflow_sub_stage_entity`: Defines substages within stages
- `workflow_field_mapping`: Maps post fields to stages/substages
- `post_development`: Stores field values for posts

## Integration Points

### 1. LLM Integration
- Universal modular LLM panel for all workflow stages
- Dynamic field selection based on stage/substage
- Configurable LLM actions per stage

### 2. Navigation System
- Hierarchical navigation through stages and substages
- Context-aware field display and editing
- Progress tracking and stage transitions

### 3. Field Management
- Dynamic field mapping through settings interface
- Automatic field population based on context
- Field validation and persistence

## Usage Guidelines

### 1. Adding New Stages
1. Add stage definition to `workflow_stage_entity`
2. Create corresponding templates in `workflow/steps/`
3. Update field mappings as needed
4. Add any required LLM actions

### 2. Field Mapping
1. Use the settings interface at `/workflow/fields/mappings`
2. Map fields to appropriate stages/substages
3. Set order and visibility preferences

### 3. LLM Integration
1. Configure LLM actions in the database
2. Map actions to specific stages/substages
3. Use the universal modular panel for consistency

## Best Practices

1. **Route Naming**
   - Use consistent `/api/workflow/` prefix for API routes
   - Follow RESTful conventions for endpoint naming
   - Use plural nouns for resource collections

2. **Template Structure**
   - Maintain separation between panel wrapper and content
   - Use consistent variable naming across templates
   - Follow proper template inheritance

3. **JavaScript Integration**
   - Use the API configuration module for endpoints
   - Follow the navigation utility functions
   - Maintain consistent error handling

4. **Database Operations**
   - Use direct SQL via psycopg2 (no ORM)
   - Follow the schema documentation
   - Maintain proper foreign key relationships

## Deprecated Components

The following components are deprecated and should not be used:

1. **Old Route Patterns**
   ```
   /api/v1/workflow/  (Use /api/workflow/ instead)
   /workflow/api/     (Use /api/workflow/ instead)
   /blog/api/v1/     (Use /api/workflow/ instead)
   ```

2. **Deprecated Files**
   - `app/workflow/navigation.py`
   - `app/templates/workflow/_workflow_nav.html`

3. **Old API Patterns**
   - Multiple base paths for API endpoints
   - Inconsistent parameter styles
   - Duplicate functionality across routes

## Migration Guide

When working with the workflow system:

1. **Use New API Routes**
   - All API endpoints should use `/api/workflow/` prefix
   - Follow standardized parameter naming
   - Use proper HTTP methods for operations

2. **Template Updates**
   - Use `nav/workflow_nav.html` for navigation
   - Follow proper template inheritance
   - Use consistent variable naming

3. **JavaScript Updates**
   - Use API configuration for endpoints
   - Follow navigation utility functions
   - Use proper error handling

## Testing

1. **API Testing**
   - Test all endpoint variations
   - Verify proper error handling
   - Check parameter validation

2. **UI Testing**
   - Verify navigation flow
   - Test field mapping interface
   - Check LLM panel functionality

3. **Integration Testing**
   - Test complete workflow cycles
   - Verify data persistence
   - Check stage transitions

## Support

For technical issues:
1. Check the documentation in `/docs/reference/workflow/`
2. Review the API reference in `endpoints.md`
3. Consult the LLM panel documentation in `llm_panel.md`
4. Contact the project maintainers

Remember: This project does not use logins or registration. Never add authentication-related code.
