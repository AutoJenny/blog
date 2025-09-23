# BlogForge CMS - System Overview

## Overview

BlogForge is a unified content management system built with Flask, featuring AI-powered content generation, workflow management, and multi-platform syndication. The system has been migrated from a microservices architecture to a single, cohesive Flask application.

## Architecture

### Unified Server Design

The application uses a blueprint-based architecture with the following structure:

```
blog/
├── unified_app.py              # Main Flask application
├── blueprints/                 # Service blueprints
│   ├── core.py                # Core functionality (workflow, posts)
│   ├── database.py            # Database management interface
│   ├── launchpad.py           # Content syndication platform
│   ├── llm_actions.py         # AI/LLM integration
│   ├── post_sections.py       # Post content management
│   ├── post_info.py           # Post metadata management
│   ├── images.py              # Image processing and management
│   └── clan_api.py            # External API integration
├── config/                     # Configuration management
│   ├── unified_config.py      # Main configuration
│   └── queue_auto_replenish.json # Auto-replenish configuration
├── templates/                  # Unified template system
├── static/                     # Consolidated static assets
├── docs/                       # Documentation
└── logs/                       # Application logs
```

## Core Components

### 1. Content Management System
- **Workflow System:** Structured content creation pipeline
- **Post Management:** Complete post lifecycle management
- **Section Management:** Modular content organization
- **Image Processing:** Automated image optimization and management

### 2. AI Integration
- **LLM Actions:** AI-powered content generation
- **Prompt Management:** Configurable AI prompts
- **Content Generation:** Automated social media content creation
- **Ollama Integration:** Local LLM processing

### 3. Syndication Platform (Launchpad)
- **Multi-Platform Support:** Facebook, Instagram, and more
- **Queue Management:** Automated content scheduling
- **Auto-Replenish System:** Automatic queue maintenance
- **Content Generation:** AI-powered social media posts

### 4. Database Management
- **82+ Tables:** Comprehensive data organization
- **Web Interface:** Database management UI
- **Backup/Restore:** Automated database operations
- **Query Interface:** Custom SQL execution

## Auto-Replenish System

### Overview
The auto-replenish system automatically maintains queue levels by adding content when queues fall below configured thresholds.

### Key Features
- **Daily Automation:** Runs every day at 9:00 AM via cron job
- **Multi-Queue Support:** Manages multiple queue types (product, blog, etc.)
- **Configurable Thresholds:** Set different thresholds per queue type
- **JSON Configuration:** Easy-to-edit configuration file
- **Comprehensive Logging:** All actions logged to `logs/auto-replenish.log`

### Configuration
The system uses `config/queue_auto_replenish.json` for configuration:

```json
{
  "enabled": true,
  "queues": [
    {
      "type": "product",
      "platform": "facebook",
      "threshold": 9,
      "add_count": 10,
      "enabled": true
    },
    {
      "type": "blog",
      "platform": "facebook", 
      "threshold": 5,
      "add_count": 8,
      "enabled": true
    }
  ]
}
```

### API Endpoints
- `POST /launchpad/api/auto-replenish-all` - Manual trigger for auto-replenish

### Monitoring
- **Logs:** `logs/auto-replenish.log`
- **Manual Testing:** `./test-auto-replenish.sh`
- **Cron Job:** Daily at 9:00 AM

## Database Architecture

### Table Categories
- **Core Content** (posts, sections, workflows)
- **Image Management** (processing, formats, styles)
- **Workflow System** (stages, steps, configurations)
- **LLM & AI** (models, prompts, interactions)
- **Platforms & Syndication** (social media, content distribution)
- **Credentials & Security** (API keys, user management)
- **Clan API Integration** (external product data)
- **UI & Configuration** (interface settings, preferences)

### Key Tables
- `posting_queue` - Content scheduling and management
- `clan_products` - External product data
- `workflow_stage_entity` - Workflow management
- `llm_prompts` - AI prompt templates
- `ui_session_state` - User interface state

## API Reference

### Core Endpoints
- `GET /` - Homepage
- `GET /db/` - Database management interface
- `GET /workflow/` - Workflow system
- `GET /llm-actions/` - AI/LLM interface
- `GET /launchpad/` - Syndication platform

### Syndication Endpoints
- `GET /launchpad/syndication/facebook/product_post` - Product post interface
- `POST /launchpad/api/queue` - Queue management
- `POST /launchpad/api/syndication/generate-social-content` - Content generation
- `POST /launchpad/api/auto-replenish-all` - Auto-replenish trigger

### Database Endpoints
- `GET /db/tables/` - List all tables
- `POST /db/backup/` - Create database backup
- `POST /db/restore/` - Restore database

## Configuration

### Environment Variables
- Database connection settings
- API keys and credentials
- Service configuration
- Logging levels

### Configuration Files
- `config/unified_config.py` - Main application configuration
- `config/queue_auto_replenish.json` - Auto-replenish system configuration
- `requirements.txt` - Python dependencies

## Deployment

### Development
```bash
# Start the application
python unified_app.py

# Or use service scripts
./start_unified.sh
```

### Production Considerations
- Database connection pooling
- Log rotation and management
- Cron job monitoring
- Error handling and recovery
- Performance optimization

## Monitoring and Maintenance

### Logs
- `unified_app.log` - Main application log
- `logs/auto-replenish.log` - Auto-replenish system log
- Service-specific logs in `logs/` directory

### Health Checks
- `GET /launchpad/health` - Launchpad service health
- Database connection monitoring
- Cron job execution monitoring

### Backup Strategy
- Daily database backups
- Configuration file backups
- Log file rotation
- Disaster recovery procedures

## Security

### Authentication
- Session-based authentication
- API key management
- Database access controls

### Data Protection
- Encrypted database connections
- Secure API endpoints
- Input validation and sanitization

## Troubleshooting

### Common Issues
1. **Database Connection:** Check PostgreSQL service and credentials
2. **Port Conflicts:** Verify port 5000 availability
3. **Missing Dependencies:** Run `pip install -r requirements.txt`
4. **Cron Job Issues:** Check cron service status and permissions
5. **Auto-Replenish Failures:** Check logs and configuration

### Debug Tools
- Database management interface
- Manual testing scripts
- Comprehensive logging
- Health check endpoints

## Future Enhancements

### Planned Features
- Additional platform support
- Enhanced AI capabilities
- Advanced workflow customization
- Real-time monitoring dashboard
- API rate limiting and optimization

### Scalability Considerations
- Horizontal scaling support
- Database optimization
- Caching implementation
- Load balancing preparation
