# LLM Panels - Saved Files from Main

This directory contains files saved from the main branch related to the LLM panels functionality.

## Directory Structure

```
modules/SAVED_FROM_MAIN/
├── templates/
│   └── _modular_llm_panels.html    # Main template for LLM panels
├── static/
│   ├── js/
│   │   └── panels.js               # JavaScript for panel interactions
│   └── css/
│       └── panels.css              # Styling for panels
└── python/
    ├── llm.py                      # LLM-related routes and endpoints
    └── api_routes.py               # General API routes
```

## Key Components

### Templates
- `_modular_llm_panels.html`: Main template file that provides the structure for the LLM workflow panels. Includes action selection, input/output fields, and post development fields.

### JavaScript
- `panels.js`: Handles accordion interactions, form submissions, API calls, and response handling. Key features include:
  - Panel initialization
  - Accordion functionality
  - Temperature control
  - API interactions

### CSS
- `panels.css`: Provides styling for the LLM panels, including:
  - Panel layout and structure
  - Accordion animations
  - Form element styling
  - Dark theme compatibility

### Python/API
- `llm.py`: Contains LLM-specific routes and endpoints
- `api_routes.py`: General API routes and endpoints

## API Endpoints Used

- GET /api/v1/llm/actions
- POST /api/v1/llm/actions/{action_id}/execute
- GET /api/v1/llm/prompts
- GET /api/v1/llm/models
- GET/POST /api/post_workflow_step_actions 