# Project Dependencies

## Core Dependencies

### Web Framework
- Flask (3.1.0): Main web framework
- Werkzeug (3.1.3): WSGI utility library
- Gunicorn (23.0.0): WSGI HTTP Server

### Database
- SQLAlchemy (2.0.40): SQL toolkit and ORM
- Flask-SQLAlchemy (3.1.1): Flask integration for SQLAlchemy
- Flask-Migrate (4.1.0): Database migration support
- psycopg2-binary (2.9.10): PostgreSQL adapter

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
- pydantic (2.11.3): Data validation and settings management
- pydantic-settings (2.9.1): Settings management

### LLM Integration
- langchain (0.3.23): LLM framework
- langchain-community (0.3.21): Community components for LangChain
- langchain-core (0.3.55): Core LangChain functionality
- langchain-text-splitters (0.3.8): Text splitting utilities
- openai (1.75.0): OpenAI API client

### HTTP Client
- httpx (0.28.1): Async HTTP client
- httpx-sse (0.4.0): Server-Sent Events support
- requests (2.32.3): HTTP client library
- requests-toolbelt (1.0.0): Utilities for requests

### Content Processing
- python-frontmatter (1.0.1): Front matter parsing
- markdown (3.8): Markdown processing
- beautifulsoup4 (4.13.4): HTML parsing
- Pillow (11.2.1): Image processing

### Utilities
- python-dotenv (1.1.0): Environment variable management
- Flask-Mail (0.10.0): Email sending support
- Flask-Caching (2.3.1): Cache support
- python-slugify (8.0.4): URL slug generation
- PyYAML (6.0.2): YAML file processing

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