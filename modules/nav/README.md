# Workflow Navigation Module

This module provides the navigation interface for the workflow system. It handles stage, substage, and step navigation, as well as post selection.

## Features

- Breadcrumb navigation
- Post selector dropdown
- Stage icons with visual grouping
- Substage tabs
- Active state indicators
- Error handling for missing context

## Structure

```
modules/nav/
├── static/
│   ├── css/
│   │   └── nav.css        # Navigation styles
│   └── js/
│       └── nav.js         # Navigation behavior
├── templates/
│   └── nav.html          # Navigation template
├── routes.py             # Navigation routes
├── services.py           # Navigation services
└── __init__.py          # Module initialization
```

## Usage

1. Include the navigation template in your workflow pages:
```jinja
{% include 'nav.html' %}
```

2. Include the required static files:
```html
<link rel="stylesheet" href="{{ url_for('workflow_nav.static', filename='css/nav.css') }}">
<script src="{{ url_for('workflow_nav.static', filename='js/nav.js') }}"></script>
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

# Nav Module Service Layer Integration

## Hybrid Service Layer Pattern

- **Shared services** for DB access and workflow logic are defined in `app/services/shared.py` in MAIN_HUB.
- **Module-specific services** in `modules/nav/services.py` import and use these shared services when available.
- If MAIN_HUB is not present (standalone mode), nav module falls back to local demo data.

## Integration
- MAIN_HUB integration code (e.g., `app/routes/workflow.py`) must always call the nav module's service functions for data access and mutation.
- This ensures a single source of truth and consistent behavior in both standalone and integrated modes.

## Fallback Logic
- If `app/services/shared.py` is not importable, nav module uses fallback demo data for posts and workflow stages.

## Testing
- Test `/workflow/` for MAIN_HUB integration (should show real DB posts).
- Test `/modules/nav/` for standalone mode (should show demo data if MAIN_HUB is not present, or real data if integrated).

## Architecture Summary
- Shared DB connection: `app/database/routes.py:get_db_conn()`
- Shared services: `app/services/shared.py`
- Nav module services: `modules/nav/services.py`
- Integration: `app/routes/workflow.py`

---

_Last updated: [date]_ 