# Template Structure

The Blog CMS uses Jinja2 templates for all HTML rendering. This document describes the organization and usage of templates.

## Main Template Locations
- `app/templates/base.html`: Main site layout, includes Tailwind CSS and global blocks.
- `app/templates/blog/`: Blog-specific templates (post, list, develop, etc.)
- `app/templates/llm/`: LLM-related templates
- `app/templates/email/`: Email templates
- `app/templates/errors/`: Error pages
- `app/templates/preview/`: Preview UI templates
- `app/templates/db/`: Database-related templates

## Static Assets
- CSS: Referenced via `{{ url_for('static', filename='css/dist/main.css') }}`
- Images: `{{ url_for('static', filename='images/<path>') }}`
- JS: `{{ url_for('static', filename='js/<file>.js') }}`

## Extending Templates
- Use `{% extends 'base.html' %}` for consistent layout and styling.
- Define blocks for content, scripts, and styles as needed.

## Customization
- Add new templates in the appropriate subdirectory.
- Use Tailwind utility classes for styling. 