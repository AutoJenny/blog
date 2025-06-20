# Imported Workflow Accordion System

This directory contains the imported accordion system from the main branch, organized for modular use.

## Component Structure

### 1. Templates (`/templates`)
- Base accordion template in `workflow/steps/planning_step.html`
- Extends through `basic_idea.html` and `provisional_title.html`
- Requires proper path adjustment for template inheritance

### 2. JavaScript Modules (`/static/js`)
Core functionality split into modules:
- `main.js`: Initialization and setup
- `actions.js`: LLM action execution
- `events.js`: Event handler registration
- `state.js`: State management
- `api.js`: API communication
- `render.js`: UI rendering
- `llm.js`: LLM-specific functionality

### 3. Configuration (`/config`)
- `planning_steps.json`: Defines step configurations, prompts, and LLM settings
- Must be properly referenced in Python routes

### 4. Python Backend (`/python`)
- Workflow routes and LLM processing
- Requires proper import path adjustment
- Database integration through models

### 5. Database (`/migrations`)
- SQL migrations for workflow step entity
- Must be run in correct order with existing migrations

## Integration Requirements

1. **Path Adjustments**
   - Update template paths in Python routes
   - Adjust static file references
   - Update import statements

2. **Database Setup**
   - Ensure workflow_step_entity table exists
   - Verify field mappings match schema

3. **JavaScript Dependencies**
   - Requires proper module loading
   - Check path references in imports

4. **Template Integration**
   - Base template must be available
   - Jinja2 inheritance chain must be maintained

5. **API Endpoints**
   Required endpoints:
   - `/api/workflow/posts/{post_id}/{stage}/{substage}/{step}`
   - `/workflow/api/run_llm/`
   - LLM-related endpoints

## Usage

1. Copy files maintaining directory structure
2. Update paths in all files
3. Run database migrations
4. Register routes in Flask app
5. Include static files in build process

## Dependencies

- Flask
- Jinja2
- PostgreSQL
- Tailwind CSS
- ES6 Modules support

## Notes

- All paths must be updated relative to new module location
- Database schema must match existing workflow tables
- LLM configuration must be properly set up
- Static files must be properly served

## File Origins

This module was imported from the main branch of the blog project. The original files were located in:

1. Templates:
   - app/templates/workflow/steps/planning_step.html
   - app/templates/workflow/steps/basic_idea.html
   - app/templates/workflow/steps/provisional_title.html

2. JavaScript:
   - archive2/js_workflow/main.js
   - archive2/js_workflow/actions.js
   - archive2/js_workflow/events.js
   - archive2/js_workflow/state.js
   - archive2/js_workflow/api.js
   - archive2/js_workflow/render.js
   - app/static/js/llm.js

3. Python:
   - app/workflow/routes.py
   - app/workflow/scripts/llm_processor.py
   - app/llm/routes.py

4. Configuration:
   - app/workflow/config/planning_steps.json

5. Database:
   - migrations/20240610_create_workflow_step_entity.sql 