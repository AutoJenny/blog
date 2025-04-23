# Blog Documentation

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