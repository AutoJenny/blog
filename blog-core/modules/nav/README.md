# Workflow Navigation Module

This module provides the navigation interface for the workflow system. It handles stage, substage, and step navigation, as well as post selection.

## Features

- Breadcrumb navigation
- Post selector dropdown
- Stage icons with visual grouping
- Substage tabs
- Active state indicators
- Error handling for missing context
- **Context-aware template rendering** (works in standalone and integrated modes)

## Database Access Pattern

The navigation module follows strict separation of concerns:
- Uses shared services (`app.services.shared`) for all database operations
- Focuses purely on navigation state and context management
- No direct database queries in the navigation module
- Clear dependency on core database services

Example:
```python
# Navigation module ONLY manages navigation state
from app.services.shared import get_workflow_stages_from_db

# Use shared service for data, build navigation-specific context
stages = get_workflow_stages_from_db()
nav_context = build_navigation_context(stages)
```

## Structure

```
modules/nav/
├── static/
│   ├── css/
│   │   └── nav.css        # Navigation styles
│   └── js/
│       └── nav.js         # Navigation behavior
├── templates/
│   └── nav.html          # Navigation template (context-aware)
├── routes.py             # Navigation routes
├── services.py           # Navigation services
└── __init__.py          # Module initialization
```

## Context-Aware Template Pattern

The nav template automatically adapts to its execution context:

### Standalone Mode (`/modules/nav/`)
- Uses blueprint static files: `url_for('workflow_nav.static', filename='css/nav.dist.css')`
- Detected by: `request.blueprint == 'workflow_nav'`

### Integrated Mode (`/workflow/`)
- Uses main app static files: `url_for('static', filename='modules/nav/nav.dist.css')`
- Detected by: `request.blueprint != 'workflow_nav'`

## Multi-Module Naming Convention

For scalability across multiple modules (nav, llm-actions, sections, etc.):

### Static Files
- **Standalone**: `modules/{module}/static/css/{module}.dist.css`
- **Integrated**: `static/modules/{module}/{module}.dist.css`

### Template Pattern
```jinja
{% if request.blueprint == 'workflow_{module}' %}
    {# Standalone mode #}
    <link rel="stylesheet" href="{{ url_for('workflow_{module}.static', filename='css/{module}.dist.css') }}">
{% else %}
    {# Integrated mode #}
    <link rel="stylesheet" href="{{ url_for('static', filename='modules/{module}/{module}.dist.css') }}">
{% endif %}
```

### Module Examples
- **nav**: `workflow_nav` → `modules/nav/nav.dist.css`
- **llm-actions**: `workflow_llm_actions` → `modules/llm-actions/llm-actions.dist.css`
- **sections**: `workflow_sections` → `modules/sections/sections.dist.css`

## Usage

1. Include the navigation template in your workflow pages:
```jinja
{% include 'nav.html' %}
```

2. Include the required static files (automatic in context-aware template):
```html
<!-- Automatically handled by context-aware template -->
```

3. Provide the required context variables:
- `post_id`: Current post ID
- `current_stage`: Current workflow stage
- `current_substage`: Current workflow substage
- `current_step`: Current workflow step
- `all_posts`: List of all posts for the selector

## API

### Routes

- `/api/workflow/stages` - Get all workflow stages and their substages
- `/` - Standalone preview (redirects to `/dev`)
- `/dev` - Standalone preview with mock context

### Context Processor

The module provides a `workflow_context` function that can be used in templates:

```jinja
{% with nav_context = workflow_context(stage, substage, step) %}
  {# Use nav_context #}
{% endwith %}
```

## Dependencies

- Flask
- Font Awesome (for icons)
- Tailwind CSS (for styling)

## Integration Notes

When merging this module into MAIN_HUB:

1. **Template**: The context-aware template will automatically work
2. **Static Files**: Copy `modules/nav/static/css/nav.dist.css` to `static/modules/nav/nav.dist.css`
3. **Blueprint**: Register as `workflow_nav` with `/modules/nav` prefix
4. **No Code Changes**: The template adapts automatically

This pattern ensures the module works seamlessly in both standalone development and integrated production environments. 