# LLM Panel Module Reference (DEV16)

This document maps all files that power the LLM panel module (the purple area with accordions) in DEV16.

## Core Templates

### Main Container
- `modules/llm_panel/templates/panel.html`
  - Primary container template
  - Includes all component templates
  - Loads JavaScript and defines base styles

### Component Templates
- `modules/llm_panel/templates/components/inputs.html`
  - "Inputs [basic_idea]" accordion
  - Field selection and display
- `modules/llm_panel/templates/components/prompt.html`
  - "Prompt" accordion
  - Shows refinement instructions
- `modules/llm_panel/templates/components/settings.html`
  - "Settings" accordion
  - Shows model, temperature, tokens
- `modules/llm_panel/templates/components/outputs.html`
  - "Outputs [refined_idea]" accordion
  - Output field selection and display

## Integration Points

### Workflow Templates
- `app/templates/workflow/index.html`
  - Main workflow page template
  - Includes the LLM panel via `panel.html`
  - Defines panel positioning and layout

### Routes and Controllers
- `app/routes/workflow.py`
  - Main workflow route handler
  - Provides context data for panels
  - Handles field mappings and updates

## Static Assets

### JavaScript
- `/llm/panel/static/llm_panel/js/accordion.js`
  - Accordion open/close behavior
  - Panel state management
- `/llm/panel/static/llm_panel/js/field_selector.js`
  - Field selection functionality
  - Field value updates

### CSS
- `modules/llm_panel/static/css/panel.css`
  - Panel styling
  - Dark theme variables
  - Accordion animations
  - Field input styling

## Database Integration

### Tables
- `workflow_step_entity`
  - Stores step configurations
  - Input/output field mappings
- `workflow_sub_stage_entity`
  - Substage definitions
  - Links steps to substages
- `post_development`
  - Stores actual field values
  - Referenced by input/output configurations

## Configuration

### Step Configuration (from workflow.py)
```json
{
    "inputs": {
        "basic_idea": {
            "type": "textarea",
            "db_field": "idea_seed",
            "db_table": "post_development"
        }
    },
    "outputs": {
        "refined_idea": {
            "type": "textarea",
            "db_field": "basic_idea",
            "db_table": "post_development"
        }
    },
    "settings": {
        "llm": {
            "model": "mistral",
            "task_prompt": "Refine the basic idea into a more detailed concept.",
            "input_mapping": {
                "basic_idea": "idea_seed"
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
        }
    }
}
```

## Required Context Variables
The following variables must be provided to the templates:
- `current_stage`
- `current_substage`
- `current_step`
- `step_config`
- `input_values`
- `output_values`
- `post.id`

## Note
This reference documents the LLM panel module as it exists in DEV16. This is the code that generates the purple area containing the four accordions (Inputs, Prompt, Settings, Outputs) in the workflow interface. 