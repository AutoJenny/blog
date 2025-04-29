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