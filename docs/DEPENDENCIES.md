# Project Dependencies

## Core Dependencies

### Web Framework
- Flask (3.1.0): Main web framework
- Werkzeug (3.1.3): WSGI utility library

### Database
- SQLAlchemy (2.0.40): SQL toolkit and ORM
- Flask-SQLAlchemy (3.1.1): Flask integration for SQLAlchemy
- Flask-Migrate (4.1.0): Database migration support
- psycopg2-binary (2.9.10): PostgreSQL adapter

### Authentication & Security
- Flask-Login (0.6.3): User session management
- bcrypt (4.3.0): Password hashing
- PyJWT (2.10.1): JSON Web Token implementation

### Task Queue
- Celery (5.5.1): Distributed task queue
- Redis (5.2.1): Message broker and result backend

### Templates & Forms
- Jinja2 (3.1.6): Template engine
- WTForms (3.2.1): Form validation and rendering
- Flask-WTF (1.2.2): Flask integration for WTForms

### API & Documentation
- Flasgger (0.9.7): Swagger/OpenAPI integration
- marshmallow (3.26.1): Object serialization/deserialization

### LLM Integration
- langchain (0.3.23): LLM framework
- openai (1.75.0): OpenAI API client

### Utilities
- python-dotenv (1.1.0): Environment variable management
- Flask-Mail (0.10.0): Email sending support
- Flask-Caching (2.3.1): Cache support

## Development Dependencies

### Testing
- pytest (8.3.5): Testing framework
- pytest-cov (6.1.1): Coverage reporting

### Code Quality
- black: Code formatting
- flake8: Style guide enforcement
- mypy: Static type checking

### Documentation
- Sphinx: Documentation generator
- sphinx-rtd-theme: Documentation theme

## Version Management

All dependencies are pinned to specific versions in `requirements.txt` to ensure reproducible builds. To update dependencies:

1. Check for updates:
   ```bash
   pip list --outdated
   ```

2. Test updates in development:
   ```bash
   pip install --upgrade package-name
   ```

3. Update requirements.txt:
   ```bash
   pip freeze > requirements.txt
   ```

## Adding New Dependencies

When adding new dependencies:

1. Document the purpose in this file
2. Add to requirements.txt with specific version
3. Update setup instructions if needed
4. Test in development environment
5. Update CI/CD configuration if necessary

## Security

- Dependencies are regularly audited for security vulnerabilities
- Updates are tested before deployment
- Security patches are applied promptly
- Dependency conflicts are resolved carefully 