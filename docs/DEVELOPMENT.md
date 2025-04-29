# Development Guide

## Project Structure

```
blog/
├── app/                    # Main application package
│   ├── api/               # API endpoints
│   ├── blog/              # Blog functionality
│   ├── db/                # Database management
│   ├── llm/               # LLM integration
│   ├── main/              # Core routes
│   └── workflow/          # Workflow management
├── docs/                  # Documentation
├── migrations/           # Database migrations
├── scripts/             # Utility scripts
├── static/              # Static assets
├── templates/           # Template files
└── tests/              # Test suite
```

## Development Environment Setup

1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

## Running the Application

1. Start the development server:
   ```bash
   ./run_server.sh
   ```
   The server will run on http://localhost:5000
   
   Note: The script will automatically:
   - Check if the virtual environment is activated
   - Activate it if needed
   - Display helpful error messages if the virtual environment is not found
   - Ensure Python runs from the correct environment

2. For background tasks (Celery):
   ```bash
   celery -A app.celery worker --loglevel=info
   celery -A app.celery beat --loglevel=info
   ```

## Development Workflow

### 1. Making Changes

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Follow these guidelines:
   - Keep changes focused and atomic
   - Update tests for new functionality
   - Update documentation as needed
   - Follow Python style guide (PEP 8)

### 2. Testing

1. Run the test suite:
   ```bash
   pytest
   ```

2. Check code quality:
   ```bash
   flake8
   black .
   ```

### 3. Documentation

- Update relevant documentation in `/docs`
- Include docstrings for new functions/classes
- Update API documentation if endpoints change

### 4. Code Review Process

1. Self-review checklist:
   - [ ] Code follows style guide
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No debug statements
   - [ ] Error handling in place
   - [ ] Migrations added if needed

2. Create pull request with:
   - Clear description of changes
   - Steps to test
   - Related issues/tickets

## Common Tasks

### Database Management

1. Create migration:
   ```bash
   flask db migrate -m "Description of changes"
   ```

2. Apply migrations:
   ```bash
   flask db upgrade
   ```

### Seeding Workflow Tables

Before using the workflow system, you must seed the workflow tables with stages and sub-stages:

```bash
python scripts/update_workflow.py
```

This script now ensures all `WorkflowStageEntity` and `WorkflowSubStageEntity` rows are present in the database, matching the `WORKFLOW_STAGES` constant. It uses the correct model parameters for stage and sub-stage creation, and prints a summary of created or already present entities.

The workflow system is now fully normalized in SQL. All workflow logic, transitions, and sub-stage updates use the normalized tables. Legacy JSON-based workflow fields are deprecated and will be removed after migration is complete.

### Adding New Dependencies

1. Add to `requirements.txt`
2. Document in `docs/DEPENDENCIES.md`
3. Update setup instructions if needed

### Troubleshooting

Common issues and solutions:

1. Port already in use:
   ```bash
   ./run_server.sh  # Automatically handles port conflicts
   ```

2. Database errors:
   - Check connection settings in `.env`
   - Ensure migrations are up to date
   - Check logs in `logs/flask.log`

## Monitoring and Logging

- Application logs: `logs/flask.log`
- Debug mode: Enabled by default in development
- Error emails: Configured for production

## Security Considerations

- Never commit `.env` files
- Keep dependencies updated
- Use environment variables for sensitive data
- Regular security audits

> **Workflow Initialization:** All workflow stages and sub-stages are now initialized for every post at creation, enabling asynchronous editing. The seeding script (`scripts/update_workflow.py`) defines and ensures the presence of all stages and sub-stages in the database. There is no longer any sequential or partial initialization—authors can work on any stage or sub-stage at any time.

## Template Management
Templates are managed through a dropdown interface in the development environment. The system provides:
- Automatic synchronization between template selection and the prompt textarea
- Persistent storage of template selections and settings
- Real-time saving of associated settings (LLM model, temperature, max tokens)
- User feedback on save operations through visual indicators
- Error handling for failed save operations

When working with templates:
1. Select a template from the dropdown to load its content
2. The system automatically:
   - Updates the prompt textarea with the template content
   - Saves your template selection
   - Persists related settings (LLM model, temperature, max tokens)
   - Provides visual feedback on the save operation status
3. If a save operation fails:
   - An error message is displayed
   - The system maintains the current state
   - Users can retry the operation

The template management system uses event listeners to ensure:
- Immediate UI updates on template selection
- Reliable state synchronization between components
- Proper error handling and user feedback
- Clean state management during modal operations

## LLM Integration

The blog system integrates with Language Learning Models (LLM) to assist in content generation. Key components include:

### Template Management

- Templates are stored in the database and managed through the development interface
- Template selection is synchronized between dropdown and textarea elements
- Settings (template, source field, model, temperature, tokens) are automatically saved on selection

### Content Generation

The development interface supports LLM-assisted content generation for:
- Idea Scope
- Provisional Title
- Other configurable fields

Generation requests are handled asynchronously with user feedback.

## Client-Side Development Interface

The development interface (`app/templates/blog/development.html`) provides a rich editing environment with several key features:

### Modal Management
- LLM action modals for template selection and generation
- Show/hide logic with proper cleanup

### Field Management
- Automatic saving of global and section-specific fields
- Real-time feedback on save operations
- Template synchronization between selection and display

### Section Management
- Accordion functionality for collapsible sections
- Proper state management for section visibility

### Event Handling
- Debounced save operations
- Proper cleanup of event listeners
- Error handling with user feedback 