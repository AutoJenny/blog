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