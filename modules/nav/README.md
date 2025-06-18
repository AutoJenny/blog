# DO NOT EDIT THIS DIRECTORY IN MAIN BRANCH

This directory is firewalled. All edits must be made in its owning branch (e.g., workflow_navigation). In main or consuming branches, update only by merging from the owning branch.

---

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

---

**WARNING:**
This directory is firewalled. Do not edit in this branch. All changes must be made in the owning branch and merged in. 