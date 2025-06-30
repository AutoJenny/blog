# LLM Panel Module Documentation

## Overview

The LLM Panel module provides a universal, modular interface for AI-assisted content generation throughout the workflow system. It's designed as a reusable component that can be integrated into any workflow stage, providing consistent LLM functionality with dynamic field selection and format integration.

## Architecture

### Core Components

The LLM Panel consists of several modular components:

```
modules/llm_panel/
├── templates/
│   ├── panel.html                    # Main container template
│   └── components/
│       ├── inputs.html              # Input field selection and display
│       ├── prompt.html              # Prompt configuration and display
│       ├── settings.html            # LLM settings and parameters
│       └── outputs.html             # Output field selection and display
├── static/
│   ├── js/
│   │   ├── field_selector.js        # Dynamic field selection logic
│   │   └── accordion.js             # Accordion UI behavior
│   └── css/
│       └── panels.css               # Panel styling and themes
└── config/
    └── planning_steps.json          # Step configuration examples
```

### Integration Points

The LLM Panel integrates with the workflow system through:

1. **Template Inclusion**: Included via `_modular_llm_panels.html` in workflow templates
2. **API Integration**: Uses workflow API endpoints for data operations
3. **Format System**: Integrates with the format system for validation and structure
4. **Field Mapping**: Dynamic field selection based on workflow context

## Template Structure

### Main Container (`panel.html`)

The main panel template provides the container and orchestrates all components:

```html
<div class="space-y-4 p-4 rounded-lg shadow-md" 
     style="background-color: #2D0A50;"
     data-current-stage="{{ current_stage }}" 
     data-current-substage="{{ current_substage }}"
     data-current-step="{{ current_step }}" 
     data-step-id="{{ step_id }}" 
     data-post-id="{{ current_post_id }}">
    
    <!-- Run LLM Button -->
    <div class="mb-4 flex justify-center">
        <button id="run-llm-btn" data-action="run-llm"
                class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-8 rounded shadow-lg transition-colors duration-200 min-w-[200px]">
            Run LLM
        </button>
    </div>

    <!-- Component Includes -->
    {% include 'modules/llm_panel/templates/components/inputs.html' %}
    {% include 'modules/llm_panel/templates/components/prompt.html' %}
    {% include 'modules/llm_panel/templates/components/settings.html' %}
    {% include 'modules/llm_panel/templates/components/outputs.html' %}
</div>
```

### Component Templates

#### Inputs Component (`inputs.html`)
- **Purpose**: Display and select input fields for LLM processing
- **Features**: 
  - Dynamic field dropdown based on workflow context
  - Field value display with syntax highlighting
  - Format validation indicators
  - Field mapping to database tables

#### Prompt Component (`prompt.html`)
- **Purpose**: Configure and display LLM prompts
- **Features**:
  - Prompt template selection
  - Dynamic prompt preview
  - Format reference resolution (`[data:field_name]`)
  - Prompt validation and testing

#### Settings Component (`settings.html`)
- **Purpose**: Configure LLM parameters and model settings
- **Features**:
  - Model selection (Ollama models)
  - Temperature, max tokens, top_p configuration
  - Format template selection
  - Parameter validation

#### Outputs Component (`outputs.html`)
- **Purpose**: Configure output field mapping and display results
- **Features**:
  - Output field selection
  - Format validation for output
  - Result display with syntax highlighting
  - Save to database functionality

## JavaScript Components

### Field Selector (`field_selector.js`)

The FieldSelector class manages dynamic field selection and mapping:

```javascript
export class FieldSelector {
    constructor(postId, stage, substage) {
        this.postId = postId;
        this.stage = stage;
        this.substage = substage;
        this.initialize();
    }

    async initialize() {
        // Fetch available fields from API
        // Group fields by stage/substage
        // Initialize dropdowns
        // Set up event handlers
    }

    async updateFieldMappings() {
        // Update database field mappings
        // Validate format compliance
        // Handle errors gracefully
    }
}
```

**Key Features:**
- Fetches available fields from `/api/workflow/fields/available`
- Groups fields by stage and substage
- Updates field mappings via `/api/workflow/fields/mappings`
- Integrates with format validation system
- Handles error states and recovery

### Accordion Component (`accordion.js`)

Manages the collapsible accordion behavior for panel sections:

```javascript
export function initializeAccordions() {
    const accordions = document.querySelectorAll('.accordion');
    
    accordions.forEach(accordion => {
        const trigger = accordion.querySelector('.accordion-trigger');
        const content = accordion.querySelector('.accordion-content');
        
        trigger.addEventListener('click', () => {
            // Toggle accordion state
            // Update icons
            // Handle animations
        });
    });
}
```

## Integration with Workflow System

### Template Integration

The LLM Panel is integrated into workflow templates via the `_modular_llm_panels.html` include:

```html
<!-- In workflow templates -->
<div id="llm-workflow-root" data-substage="{{ current_substage }}" data-post-id="{{ post.id }}"
     class="max-w-5xl mx-auto py-10 flex flex-col gap-8">
    {% with step_config=step_config, field_values=field_values, step_id=step_id, 
            current_stage=current_stage, current_step=current_step %}
    {% include 'modules/llm_panel/templates/panel.html' %}
    {% endwith %}
</div>
```

### Required Context Variables

The following variables must be provided to the panel templates:

- `current_stage`: Current workflow stage (e.g., 'planning', 'authoring')
- `current_substage`: Current substage (e.g., 'idea', 'research')
- `current_step`: Current step name (e.g., 'Initial Concept')
- `step_id`: Database ID of the current step
- `step_config`: Step configuration object from database
- `field_values`: Current field values for the post
- `post.id`: Post ID for API calls

### API Integration

The panel uses several API endpoints:

1. **Field Operations**:
   - `GET /api/workflow/fields/available` - List available fields
   - `POST /api/workflow/fields/mappings` - Update field mappings

2. **Format Operations**:
   - `GET /api/workflow/formats/templates` - List format templates
   - `POST /api/workflow/formats/validate` - Validate data against formats

3. **LLM Operations**:
   - `POST /api/workflow/posts/{post_id}/{stage}/{substage}/llm` - Execute LLM processing

4. **Post Development**:
   - `GET /api/workflow/posts/{post_id}/development` - Get field values
   - `POST /api/workflow/posts/{post_id}/development` - Update field values

## Configuration

### Step Configuration Format

Each workflow step can have LLM panel configuration:

```json
{
    "inputs": {
        "basic_idea": {
            "type": "textarea",
            "db_field": "idea_seed",
            "db_table": "post_development",
            "format_id": 1
        }
    },
    "outputs": {
        "refined_idea": {
            "type": "textarea",
            "db_field": "basic_idea",
            "db_table": "post_development",
            "format_id": 2
        }
    },
    "settings": {
        "llm": {
            "model": "llama3.1:70b",
            "temperature": 0.7,
            "max_tokens": 1000,
            "format_id": 2
        }
    }
}
```

### Format Integration

The panel integrates with the format system for:

1. **Input Validation**: Validate input data against format specifications
2. **Output Structuring**: Ensure LLM output matches required format
3. **Field References**: Resolve `[data:field_name]` references in prompts
4. **Type Safety**: Enforce data types and constraints

## Usage Patterns

### Basic Integration

To add the LLM Panel to a workflow template:

```html
{% extends 'base.html' %}

{% block content %}
<div class="flex flex-col min-h-screen">
    <!-- Navigation -->
    <div id="workflow-nav" class="mb-0">
        {% include 'nav/workflow_nav.html' %}
    </div>

    <!-- Content with LLM Panel -->
    <div class="flex-grow">
        <div class="px-6 -mt-20">
            <div id="workflow-llm-actions" 
                 style="background-color: #2D0A50; width: 100%; min-height: 400px;"
                 class="rounded-lg p-6 shadow-lg">
                {% include 'workflow/_modular_llm_panels.html' %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Customization

The panel can be customized by:

1. **Styling**: Override CSS classes in `panels.css`
2. **Behavior**: Extend JavaScript components
3. **Configuration**: Modify step configuration in database
4. **Templates**: Customize component templates for specific needs

## Error Handling

### Common Error Scenarios

1. **Missing Context Variables**:
   - Panel won't initialize properly
   - JavaScript errors in console
   - Missing field data

2. **API Failures**:
   - Network errors during field fetching
   - Database connection issues
   - LLM service unavailable

3. **Format Validation Errors**:
   - Invalid data structure
   - Missing required fields
   - Type mismatches

### Error Recovery

The panel includes error recovery mechanisms:

- **Graceful Degradation**: Panel remains functional with reduced features
- **Retry Logic**: Automatic retry for transient failures
- **User Feedback**: Clear error messages and suggestions
- **Fallback Values**: Default values when data is unavailable

## Best Practices

### 1. Template Design
- Always provide required context variables
- Use consistent naming conventions
- Follow proper template inheritance
- Include error handling in templates

### 2. JavaScript Integration
- Use ES6 modules for component organization
- Implement proper error handling
- Follow async/await patterns
- Maintain consistent API usage

### 3. Configuration Management
- Store configuration in database, not hardcoded
- Use format system for validation
- Implement proper field mapping
- Document configuration requirements

### 4. Performance Optimization
- Lazy load components when possible
- Cache field data appropriately
- Minimize API calls
- Use efficient DOM manipulation

## Troubleshooting

### Common Issues

1. **Panel Not Loading**:
   - Check context variables are provided
   - Verify template includes are correct
   - Check JavaScript console for errors

2. **Fields Not Populating**:
   - Verify API endpoints are accessible
   - Check field mapping configuration
   - Ensure post ID is valid

3. **LLM Processing Fails**:
   - Check Ollama service is running
   - Verify step configuration
   - Check format validation

4. **Styling Issues**:
   - Verify CSS files are loaded
   - Check for CSS conflicts
   - Ensure proper class names

### Debug Tools

1. **Browser Console**: Check for JavaScript errors
2. **Network Tab**: Monitor API calls and responses
3. **Database Queries**: Verify data integrity
4. **Template Debugging**: Use template debugging tools

## Migration Guide

When updating the LLM Panel:

1. **Backup Configuration**: Export step configurations
2. **Test Integration**: Verify all workflow stages work
3. **Update Documentation**: Keep this guide current
4. **Validate Formats**: Ensure format compatibility
5. **Performance Testing**: Verify no regressions

## Support

For technical issues with the LLM Panel:

1. Check this documentation first
2. Review the API reference in `endpoints.md`
3. Check the workflow system documentation
4. Consult the format system guide
5. Contact the project maintainers

Remember: This project does not use logins or registration. Never add authentication-related code to the LLM Panel. 