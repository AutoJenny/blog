# Workflow System Documentation

## Overview

The workflow system provides a structured approach to content creation and management through defined stages, substages, and associated field mappings. This document provides a comprehensive guide to understanding and working with the workflow system.

**Current Status (June 30, 2025):** The workflow system has been enhanced with a unified format template system. All format configuration is now step-level only, with complete schema and LLM instruction integration. Post-specific format overrides have been removed for consistency.

## Core Concepts

### 1. Workflow Structure
- **Stages**: High-level workflow phases (e.g., Planning, Authoring, Publishing)
- **Substages**: Specific steps within each stage (e.g., Idea, Research, Draft)
- **Field Mappings**: Associations between post development fields and workflow stages/substages

### 2. Key Components
- **Navigation Module**: Handles workflow navigation and stage transitions
- **LLM Panel**: Universal modular panel for AI-assisted content generation
- **Field Selector**: Dynamic field selection based on workflow context
- **Format Template System**: Step-level format configuration with complete schema and LLM instruction integration
- **API Layer**: RESTful endpoints for workflow operations

### 3. Format Template System
- **Step-level configuration**: All format configuration stored in `workflow_step_entity.default_input_format_id` and `default_output_format_id`
- **No post-specific overrides**: All posts use the same step-level format configuration
- **Complete integration**: Format template data includes schema, LLM instructions, and descriptions
- **Unified logs**: Format templates appear once in diagnostic logs with complete data

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
│       ├── llm.py            # LLM integration endpoints
│       └── step_formats.py   # Step-level format configuration
└── workflow/
    ├── context.py            # Workflow context management
    ├── routes.py            # UI routes
    └── scripts/             # Background processing
        ├── llm_processor.py # LLM processing with format integration
        └── prompt_constructor.py # External prompt construction (planned)
```

## Database Schema

### Core Tables
- `workflow_stage_entity`: Defines workflow stages
- `workflow_sub_stage_entity`: Defines substages within stages
- `workflow_step_entity`: Defines workflow steps with format configuration
- `workflow_field_mapping`: Maps post fields to stages/substages
- `workflow_format_template`: Format templates with schema and LLM instructions
- `post_development`: Stores field values for posts

### Format Configuration Schema
```sql
-- Step-level format configuration
workflow_step_entity:
  - default_input_format_id (references workflow_format_template.id)
  - default_output_format_id (references workflow_format_template.id)

-- Format template data
workflow_format_template:
  - id, name, description
  - fields (JSON schema)
  - llm_instructions
  - created_at, updated_at
```

## Integration Points

### 1. LLM Integration
- Universal modular LLM panel for all workflow stages
- Dynamic field selection based on stage/substage
- Configurable LLM actions per stage
- Format template integration with complete schema and LLM instructions

### 2. Navigation System
- Hierarchical navigation through stages and substages
- Context-aware field display and editing
- Progress tracking and stage transitions

### 3. Field Management
- Dynamic field mapping through settings interface
- Automatic field population based on context
- Field validation and persistence

### 4. Format Template System
- Step-level format configuration only
- Complete schema and LLM instruction integration
- Unified diagnostic logging
- Clean, non-duplicated data structures

## Usage Guidelines

### 1. Adding New Stages
1. Add stage definition to `workflow_stage_entity`
2. Create corresponding templates in `workflow/steps/`
3. Update field mappings as needed
4. Add any required LLM actions
5. Configure step-level format templates

### 2. Field Mapping
1. Use the settings interface at `/workflow/fields/mappings`
2. Map fields to appropriate stages/substages
3. Set order and visibility preferences

### 3. LLM Integration
1. Configure LLM actions in the database
2. Map actions to specific stages/substages
3. Use the universal modular panel for consistency
4. Configure step-level format templates for input/output

### 4. Format Template Configuration
1. Create format templates with complete schema and LLM instructions
2. Assign input/output formats to workflow steps via `/settings/workflow_step_formats`
3. Ensure format templates include proper LLM instructions for input/output handling
4. Test format integration with diagnostic logs

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

5. **Format Template Management**
   - Use step-level configuration only (no post-specific overrides)
   - Include complete schema and LLM instructions in format templates
   - Maintain clean, unified log structures
   - Test format integration thoroughly

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

4. **Post-Specific Format Configuration**
   - All post-specific `workflow_step_format` rows have been removed
   - Use step-level format configuration only
   - No post-specific overrides are supported

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

4. **Format Template Updates**
   - Use step-level configuration only
   - Include complete schema and LLM instructions
   - Test format integration with diagnostic logs
   - Ensure no duplication in log structures

## Testing

1. **API Testing**
   - Test all endpoint variations
   - Verify proper error handling
   - Check parameter validation

2. **UI Testing**
   - Verify navigation flow
   - Test field mapping interface
   - Check LLM panel functionality
   - Test format template configuration

3. **Integration Testing**
   - Test complete workflow cycles
   - Verify data persistence
   - Check stage transitions
   - Validate format template integration
   - Test diagnostic log generation

4. **Format Template Testing**
   - Test step-level format configuration
   - Verify format template data in logs
   - Check LLM instruction integration
   - Validate schema compliance

## Support

For technical issues:
1. Check the documentation in `/docs/workflow/`
2. Review the API reference
3. Consult the database schema
4. Check format template configuration
5. Review diagnostic logs for format integration
6. Contact the project maintainers

Remember: This project does not use logins or registration. Never add authentication-related code.

## Recent Changes (June 2025)

### Format Template System Cleanup
- **Step-level configuration only:** All format configuration now uses `workflow_step_entity.default_input_format_id` and `default_output_format_id`
- **Removed post-specific overrides:** All post-specific `workflow_step_format` rows deleted
- **Unified diagnostic logs:** Format templates appear once at top level with complete data
- **Clean integration:** No duplication in log structures

### Backend Updates
- Updated `llm_processor.py` to use step-level format configuration
- Modified format template fetching to use `workflow_step_entity` table
- Confirmed frontend only calls step-level endpoint

### Next Steps
- Externalize prompt construction to dedicated script
- Integrate format template instructions into LLM prompts
- Complete format template system integration
