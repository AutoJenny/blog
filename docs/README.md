# Blog Documentation

## Overview
This is a Flask-based blog system with integrated AI assistance, workflow management, and clan.com integration. The system supports rich content management, media handling, and automated content generation.

## Documentation Sections

### [Project Setup](project/README.md)
- Installation and dependencies
- Configuration guide
- Development setup
- Deployment procedures
- Testing guide

### [Database](database/README.md)
- Schema and models
- Relationships
- Migrations
- Backup and replication
- Best practices

### [API Reference](api/README.md)
- Endpoints
- Authentication
- Request/Response formats
- Error handling
- Integration examples

### [Models](models/README.md)
- Data models
- Relationships
- Validation
- Usage examples

### [User Guides](guides/README.md)
- Content creation workflow
- Media management
- AI assistance
- Publishing process
- System administration

## Quick Start

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
5. Initialize database:
   ```bash
   flask db upgrade
   ```
6. Run development server:
   ```bash
   ./run_server.sh
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| FLASK_ENV | Environment (development/production) | development |
| DATABASE_URL | PostgreSQL connection URL | postgresql://postgres:postgres@localhost/blog |
| SECRET_KEY | Flask secret key | hard-to-guess-string |
| OPENAI_API_KEY | OpenAI API key | None |
| MAIL_SERVER | SMTP server | None |
| CELERY_BROKER_URL | Redis URL for Celery | redis://localhost:6379/0 |

## System Requirements
- Python 3.12+
- PostgreSQL 14+
- Redis (for Celery)
- Node.js 18+ (for frontend builds)

## Documentation Structure

```
docs/
├── README.md                    # This file - overview and navigation
├── api/                        # API documentation
│   ├── README.md               # API overview and authentication
│   ├── posts.md                # Blog post endpoints
│   ├── media.md                # Media handling endpoints
│   ├── taxonomy.md             # Category and tag endpoints
│   ├── auth.md                 # Authentication endpoints
│   ├── llm.md                  # LLM integration endpoints
│   └── monitoring.md           # Health and monitoring endpoints
├── database/                   # Database documentation
│   ├── README.md               # Database architecture overview
│   ├── post.md                 # Post model documentation
│   ├── media.md                # Media model documentation
│   └── metadata.md             # JSON metadata structures
├── guides/                     # User and developer guides
│   ├── user_guide.md           # Content management guide
│   ├── technical_setup.md      # Development environment setup
│   └── migration.md            # Data migration guide
└── project/                    # Project documentation
    ├── PROJECT_PLAN.md         # Project roadmap and milestones
    ├── architecture.md         # System architecture overview
    └── llm_architecture.md     # LLM integration architecture
```

## Quick Links

### For Content Creators
- [User Guide](guides/user_guide.md) - Content creation and management
- [Media Guide](api/media.md) - Image and file management
- [LLM Features](api/llm.md) - AI-assisted content creation

### For Developers
- [Technical Setup](guides/technical_setup.md) - Development environment setup
- [API Documentation](api/README.md) - Complete API reference
- [Database Models](database/README.md) - Data structure documentation

### For System Administrators
- [Monitoring](api/monitoring.md) - System health and metrics
- [Migration Guide](guides/migration.md) - Data migration procedures
- [Architecture Overview](project/architecture.md) - System architecture

## Core Components

### API Endpoints
The system provides RESTful APIs for:
- Content Management (posts, sections)
- Media Handling (images, files)
- Authentication & Authorization
- [LLM Integration](api/llm.md) - AI-assisted features
- System Monitoring

See [API documentation](api/README.md) for complete details.

### Database Models
Core data structures include:
- Posts and Sections
- Media Assets
- Categories and Tags
- User Management
- Metadata Schemas

See [database documentation](database/README.md) for complete schema details.

### LLM Integration
AI-assisted features include:
- Content Generation
- Text Analysis
- SEO Optimization
- Content Enhancement

For details, see:
- [LLM API Documentation](api/llm.md) - API endpoints and usage
- [LLM Architecture](project/llm_architecture.md) - Implementation details

## Notes
- SQLite is no longer supported. PostgreSQL is required for all environments.
- When building or editing workflow UI, always bind each sub-stage field to its corresponding value in the backend's stage_data for the current post. 