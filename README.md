# BlogForge - Unified CMS

A comprehensive content management system built with Flask, featuring AI-powered content generation, workflow management, and multi-platform syndication.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis (optional, for caching)

### Installation
```bash
# Clone the repository
git clone https://github.com/AutoJenny/blog.git
cd blog

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp config/env.template .env
# Edit .env with your database credentials

# Start the unified application
python unified_app.py
```

The application will be available at `http://localhost:5000`

## 📚 Documentation

### Architecture Documentation
- **[Unified Architecture Overview](docs/temp/unified_architecture_overview.md)** - Complete architecture overview
- **[Database Architecture](docs/temp/database_architecture.md)** - Database structure and relationships
- **[API Reference](docs/temp/api_reference.md)** - Complete API documentation
- **[Quick Reference Guide](docs/temp/quick_reference.md)** - Quick start and troubleshooting

### Implementation Documentation
- **[Unified Server Implementation Plan](docs/temp/unified_server_implementation_plan.md)** - Complete migration overview
- **[Phase-by-Phase Implementation](docs/temp/)** - Detailed implementation phases
- **[Implementation Checklist](docs/temp/implementation_checklist.md)** - Progress tracking

### Quick Links
- **Homepage:** `http://localhost:5000`
- **Database Management:** `http://localhost:5000/db/`
- **Workflow System:** `http://localhost:5000/workflow/posts/53/planning/idea/initial_concept`
- **LLM Actions:** `http://localhost:5000/llm-actions/`
- **Launchpad:** `http://localhost:5000/launchpad/`
- **Auto-Replenish System:** `http://localhost:5000/launchpad/api/auto-replenish-all`

## 🏗️ Architecture

### Unified Server Design
The application has been migrated from a microservices architecture to a unified Flask application with the following structure:

```
blog/
├── unified_app.py          # Main Flask application
├── blueprints/             # Service blueprints
│   ├── core.py            # Core functionality (workflow, posts)
│   ├── database.py        # Database management interface
│   ├── launchpad.py       # Content syndication platform
│   ├── llm_actions.py     # AI/LLM integration
│   ├── post_sections.py   # Post content management
│   ├── post_info.py       # Post metadata management
│   ├── images.py          # Image processing and management
│   └── clan_api.py        # External API integration
├── config/                 # Configuration management
├── templates/             # Unified template system
├── static/               # Consolidated static assets
└── docs/                 # Documentation
```

### Key Features
- **Unified Interface:** Single application serving all functionality
- **Blueprint Architecture:** Modular service organization
- **Dark Theme:** Consistent UI across all modules
- **Database Management:** Comprehensive database interface with 82+ tables
- **AI Integration:** LLM-powered content generation and processing
- **Workflow System:** Structured content creation pipeline
- **Multi-Platform Syndication:** Social media and content distribution
- **Auto-Replenish System:** Automated queue management with daily replenishment

## 🛠️ Development

### Running Services
```bash
# Start unified application
python unified_app.py

# Or use the service scripts
./start_unified.sh
```

### Database Management
- Access the database interface at `/db/`
- View all 82 tables organized into logical groups
- Perform backups and restores
- Execute custom SQL queries

### Configuration
All configuration is centralized in `config/unified_config.py` with environment-specific settings.

## 📊 Database

The system uses PostgreSQL with 82+ tables organized into logical groups:
- **Core Content** (posts, sections, workflows)
- **Image Management** (processing, formats, styles)
- **Workflow System** (stages, steps, configurations)
- **LLM & AI** (models, prompts, interactions)
- **Platforms & Syndication** (social media, content distribution)
- **Credentials & Security** (API keys, user management)
- **Clan API Integration** (external product data)
- **UI & Configuration** (interface settings, preferences)

## 🔄 Auto-Replenish System

The auto-replenish system automatically maintains queue levels by adding content when queues fall below configured thresholds.

### Features
- **Daily Automation:** Runs every day at 9:00 AM via cron job
- **Multi-Queue Support:** Manages multiple queue types (product, blog, etc.)
- **Configurable Thresholds:** Set different thresholds per queue type
- **JSON Configuration:** Easy-to-edit configuration file
- **Comprehensive Logging:** All actions logged to `logs/auto-replenish.log`

### Configuration
Edit `config/queue_auto_replenish.json` to configure queue types, thresholds, and enable/disable individual queues.

### Manual Testing
```bash
# Test the system
./test-auto-replenish.sh

# Or call the endpoint directly
curl -X POST http://localhost:5000/launchpad/api/auto-replenish-all
```

### Documentation
- **[System Overview](docs/system-overview.md)** - Complete system architecture and features
- **[Quick Reference Guide](docs/quick-reference.md)** - Quick start and troubleshooting
- **[Auto-Replenish System Guide](docs/auto-replenish-system.md)** - Detailed auto-replenish documentation

## 🔧 Troubleshooting

### Common Issues
1. **Database Connection:** Ensure PostgreSQL is running and credentials are correct
2. **Port Conflicts:** Default port 5000, change in `unified_app.py` if needed
3. **Missing Dependencies:** Run `pip install -r requirements.txt`

### Logs
- Application logs: `unified_app.log`
- Service-specific logs: `logs/` directory

## 📝 License

This project is part of the BlogForge CMS system.

## 🤝 Contributing

Please refer to the architecture documentation in `docs/temp/` for detailed information about the system design and implementation.
