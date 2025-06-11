# Checklist: Adding a New Step/Tab to Workflow

## 1. Update the Step Configuration
- [ ] Add the new step to the correct substage in `app/workflow/config/planning_steps.json`.
  - Include: `title`, `description`, `inputs`, `outputs`, and `settings` (LLM, etc).

## 2. Database Preparation
- [ ] Ensure all referenced fields in `inputs` and `outputs` exist in the relevant database table (e.g., `post_development`).
  - If not, add them via migration or direct SQL.

## 3. Template Creation (Modular Architecture)
- [ ] Create a new template in `app/templates/workflow/steps/` named after the step (e.g., `concepts.html`).
- [ ] The template should extend `planning_step.html` and **only override**:
  - `{% block step_heading %}` for the step's heading/title
  - `{% block step_description %}` for the step's description
- [ ] **Do NOT override** `{% block workflow_content %}` or duplicate navigation/content logic.
- [ ] The navigation is handled by including `_workflow_nav.html` in `planning_step.html`.
- [ ] The main content (inputs, outputs, prompt, settings, accordions) is handled by including `_workflow_content.html` in `planning_step.html`.
- [ ] The content module is a robust, reusable unit—never duplicate or override its logic in step templates.

### Modular Structure Reference
- `planning_step.html` (extends `workflow/base.html`):
  - Includes both navigation and content modules
  - Provides blocks for step heading and description
- `_workflow_nav.html`: Navigation module (breadcrumbs, post selector, stage icons)
- `_workflow_content.html`: Content module (inputs, outputs, prompt, settings, accordions)
- Step templates: Only override heading/description blocks

## 4. Route/Context Update
- [ ] In `app/workflow/routes.py`, ensure the step route:
  - Loads the correct `step_config` from the config file.
  - Passes all required context variables to `render_template`:
    - `post_id`
    - `current_stage`
    - `current_substage`
    - `current_step`
    - `all_posts`
    - `step_config`
    - `input_values`
    - `output_values`
    - `output_titles` (if needed)
    - `post`
    - Any other variables used in templates.

## 5. Navigation
- [ ] Update navigation templates (e.g., `_workflow_nav.html`) to include the new step/tab if needed.
- [ ] Ensure links point to the correct route and step.

## 6. Test the Step
- [ ] Use `curl` or browser to visit the new step's URL and check for:
  - No template errors (e.g., undefined variables).
  - No template inheritance errors (e.g., "block defined twice").
  - Correct display of navigation and all content sections (inputs, outputs, prompt, settings, accordions).
  - Navigation works as expected.
  - Template blocks render in the correct order.

## 7. LLM/Backend Integration
- [ ] If the step uses LLM or backend logic, ensure the API endpoints and scripts are updated to handle the new step.

## 8. Documentation
- [ ] Update the checklist and `/docs` as needed to reflect any new conventions or requirements.

## 9. Data Logging and Input Population
- [ ] Log the input field (e.g., `basic_idea`) at a data level.
- [ ] Ensure that the input field is populated as part of the step addition process.
- [ ] Verify that the input data is correctly passed to the step's template and used in the content module.

## Common Template Inheritance Pitfalls to Avoid
- [ ] Never define the same block twice in a template
- [ ] Don't nest blocks unnecessarily
- [ ] Don't override blocks that don't need to be changed
- [ ] Don't mix block definitions with content
- [ ] Don't forget to pass required context variables
- [ ] Don't assume block content will be rendered in a specific order
- [ ] Don't duplicate navigation or content modules—use the provided includes
- [ ] Don't forget to test with `curl` before claiming functionality works 