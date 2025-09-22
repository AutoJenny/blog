# Quick Reference Guide

## 🚀 Getting Started

### Start the Application
```bash
# Start unified application
python unified_app.py

# Or use the service script
./start_unified.sh
```

### Access Points
- **Main Application:** http://localhost:5000
- **Database Management:** http://localhost:5000/db/
- **Workflow System:** http://localhost:5000/workflow/posts/53/planning/idea/initial_concept
- **LLM Actions:** http://localhost:5000/llm-actions/
- **Launchpad:** http://localhost:5000/launchpad/

## 📁 Project Structure

```
blog/
├── unified_app.py          # Main Flask application
├── blueprints/             # Service blueprints
│   ├── core.py            # Core functionality
│   ├── database.py        # Database management
│   ├── launchpad.py       # Content syndication
│   ├── llm_actions.py     # AI/LLM integration
│   ├── post_sections.py   # Post content management
│   ├── post_info.py       # Post metadata
│   ├── images.py          # Image processing
│   └── clan_api.py        # External API integration
├── config/                 # Configuration management
├── templates/             # Unified templates
├── static/               # Static assets
└── docs/temp/            # Documentation
```

## 🗄️ Database Quick Reference

### Access Database Interface
1. Go to http://localhost:5000/db/
2. Browse tables by category
3. View table schemas and data
4. Execute custom queries
5. Perform backups/restores

### Key Tables
- **`post`** - Main content
- **`post_section`** - Content sections
- **`workflow`** - Workflow definitions
- **`image`** - Image metadata
- **`platforms`** - Social media platforms
- **`llm_interaction`** - AI interactions

### Common Queries
```sql
-- Get all posts with categories
SELECT p.*, c.name as category
FROM post p
LEFT JOIN post_categories pc ON p.id = pc.post_id
LEFT JOIN category c ON pc.category_id = c.id;

-- Get workflow progress
SELECT p.title, ws.name as stage, wss.name as sub_stage
FROM post p
JOIN post_workflow_stage pws ON p.id = pws.post_id
JOIN workflow_stage_entity ws ON pws.stage_id = ws.id
JOIN post_workflow_sub_stage pwss ON p.id = pwss.post_id
JOIN workflow_sub_stage_entity wss ON pwss.sub_stage_id = wss.id;
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://autojenny@localhost:5432/blog

# Application
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
DEBUG=True

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Configuration Files
- **`config/unified_config.py`** - Main configuration
- **`config/database.py`** - Database settings
- **`.env`** - Environment variables (create from template)

## 🛠️ Development

### Adding New Features
1. Create blueprint in `blueprints/`
2. Register blueprint in `unified_app.py`
3. Add templates in `templates/`
4. Add static assets in `static/`
5. Update documentation

### Testing
```bash
# Run test suite
python test_unified_app.py

# Test specific endpoint
curl http://localhost:5000/health
```

### Debugging
- Check `unified_app.log` for application logs
- Use database interface for data inspection
- Enable debug mode in configuration

## 📊 API Endpoints

### Core Endpoints
- `GET /` - Homepage
- `GET /health` - Health check
- `GET /posts` - Posts list

### Database API
- `GET /db/` - Database interface
- `GET /db/tables` - List all tables
- `POST /db/execute_query` - Execute SQL
- `POST /db/backup` - Create backup
- `POST /db/restore` - Restore backup

### Workflow API
- `GET /workflow/posts/{id}/planning/{stage}/{substage}` - Workflow interface

### LLM API
- `GET /llm-actions/` - LLM interface
- `GET /llm-actions/api/llm/providers` - Get providers
- `GET /llm-actions/api/llm/actions` - Get actions

### Launchpad API
- `GET /launchpad/` - Syndication interface
- `GET /launchpad/api/platforms` - Get platforms
- `GET /launchpad/syndication/{platform}/{channel}` - Channel config

## 🎨 UI Components

### Dark Theme
- Consistent dark theme across all interfaces
- Defined in `templates/base.html`
- CSS variables for easy customization

### Template Inheritance
```html
{% extends "base.html" %}
{% block title %}Page Title{% endblock %}
{% block content %}
  <!-- Page content -->
{% endblock %}
```

### Static Assets
```html
{% from 'macros/static_assets.html' import css_assets, js_assets %}
{{ css_assets(blueprint_name) }}
{{ js_assets(blueprint_name) }}
```

## 🔍 Troubleshooting

### Common Issues

#### Application Won't Start
- Check Python version (3.11+)
- Install dependencies: `pip install -r requirements.txt`
- Check database connection
- Verify port 5000 is available

#### Database Connection Issues
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in configuration
- Verify database credentials
- Test connection: `curl http://localhost:5000/db/test`

#### Template Not Found
- Check template path in blueprint
- Verify template exists in `templates/`
- Check blueprint registration in `unified_app.py`

#### Static Assets Not Loading
- Check file exists in `static/`
- Verify URL path in template
- Check blueprint static folder configuration

### Debug Commands
```bash
# Check application status
curl http://localhost:5000/health

# Test database connection
curl http://localhost:5000/db/test

# Check all endpoints
python test_unified_app.py

# View logs
tail -f unified_app.log
```

## 📚 Documentation

### Architecture Docs
- [Unified Architecture Overview](unified_architecture_overview.md)
- [Database Architecture](database_architecture.md)
- [API Reference](api_reference.md)
- [Implementation Plan](unified_server_implementation_plan.md)

### Phase Documentation
- [Phase 1: Foundation Setup](phase_1_foundation_setup.md)
- [Phase 2: Blueprint Migration](phase_2_blueprint_migration.md)
- [Phase 3: Static Assets](phase_3_static_assets_consolidation.md)
- [Phase 4: Configuration](phase_4_configuration_unification.md)
- [Phase 5: Testing](phase_5_testing_validation.md)

## 🚀 Deployment

### Production Checklist
- [ ] Set production configuration
- [ ] Configure environment variables
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Test all endpoints
- [ ] Verify security settings

### Environment Setup
```bash
# Production environment
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@host:port/db
export SECRET_KEY=your-production-secret-key
```

## 📞 Support

### Getting Help
1. Check this documentation
2. Review error logs
3. Test with curl commands
4. Check database interface
5. Verify configuration

### Common Commands
```bash
# Restart application
pkill -f unified_app.py
python unified_app.py

# Check processes
ps aux | grep unified_app

# View recent logs
tail -n 100 unified_app.log

# Test database
curl -s http://localhost:5000/db/tables | jq '.total_tables'
```
