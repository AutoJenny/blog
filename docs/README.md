# BlogForge CMS Documentation

Welcome to the BlogForge CMS documentation. This directory contains comprehensive documentation for the unified content management system.

## 📚 Documentation Index

### Core Documentation
- **[README](../README.md)** - Main project overview and quick start
- **[System Overview](system-overview.md)** - Complete system architecture and features
- **[Quick Reference Guide](quick-reference.md)** - Quick start, commands, and troubleshooting

### Feature Documentation
- **[Auto-Replenish System](auto-replenish-system.md)** - Automated queue management system
- **[Image Storage Migration](image_storage_migration_summary.md)** - Image system migration details

### Architecture Documentation (Legacy)
The `temp/` directory contains detailed architecture documentation from the migration process:

- **[Unified Architecture Overview](temp/unified_architecture_overview.md)** - Complete architecture overview
- **[Database Architecture](temp/database_architecture.md)** - Database structure and relationships
- **[API Reference](temp/api_reference.md)** - Complete API documentation
- **[Implementation Checklist](temp/implementation_checklist.md)** - Progress tracking

### Migration Documentation
- **[Unified Server Implementation Plan](temp/unified_server_implementation_plan.md)** - Complete migration overview
- **[Phase-by-Phase Implementation](temp/)** - Detailed implementation phases
- **[Unification Complete Summary](temp/unification_complete_summary.md)** - Migration completion summary

## 🚀 Quick Start

### For New Users
1. Start with the **[README](../README.md)** for project overview
2. Follow the **[Quick Reference Guide](quick-reference.md)** for setup
3. Review the **[System Overview](system-overview.md)** for architecture understanding

### For Developers
1. Read the **[System Overview](system-overview.md)** for complete architecture
2. Check **[API Reference](temp/api_reference.md)** for endpoint documentation
3. Review **[Database Architecture](temp/database_architecture.md)** for data structure

### For Operations
1. Use the **[Quick Reference Guide](quick-reference.md)** for daily operations
2. Check **[Auto-Replenish System](auto-replenish-system.md)** for queue management
3. Review troubleshooting sections in all guides

## 🔄 Auto-Replenish System

The auto-replenish system is a key feature that automatically maintains queue levels:

- **Daily Automation:** Runs every day at 9:00 AM via cron job
- **Multi-Queue Support:** Manages multiple queue types
- **Configurable:** JSON-based configuration
- **Comprehensive Logging:** All actions logged

### Quick Commands
```bash
# Test the system
./test-auto-replenish.sh

# Manual trigger
curl -X POST http://localhost:5000/launchpad/api/auto-replenish-all

# Check logs
tail -f logs/auto-replenish.log
```

## 🗄️ Database Management

The system includes a comprehensive database management interface:

- **Web Interface:** http://localhost:5000/db/
- **82+ Tables:** Organized into logical groups
- **Backup/Restore:** Automated operations
- **Query Interface:** Custom SQL execution

## 📱 Syndication Platform

The Launchpad syndication platform provides:

- **Multi-Platform Support:** Facebook, Instagram, and more
- **AI Content Generation:** Automated social media posts
- **Queue Management:** Scheduled content distribution
- **Auto-Replenish:** Automatic queue maintenance

## 🤖 AI Integration

AI capabilities include:

- **LLM Actions:** AI-powered content generation
- **Ollama Integration:** Local LLM processing
- **Prompt Management:** Configurable AI prompts
- **Content Generation:** Automated social media content

## 🔧 Troubleshooting

### Common Issues
1. **Application Won't Start:** Check Python version and dependencies
2. **Database Connection:** Verify PostgreSQL service and credentials
3. **Auto-Replenish Issues:** Check cron service and configuration
4. **Queue Problems:** Verify database and API endpoints

### Getting Help
- Check the **[Quick Reference Guide](quick-reference.md)** for common solutions
- Review logs in the `logs/` directory
- Use health check endpoints for system status
- Consult the **[System Overview](system-overview.md)** for architecture details

## 📊 Monitoring

### Key Metrics
- Queue levels (should stay above thresholds)
- Database connection status
- Cron job execution
- Application response times

### Health Checks
- Application: http://localhost:5000/launchpad/health
- Database: http://localhost:5000/db/health
- Auto-replenish: Manual testing via scripts

## 📝 Contributing

When contributing to the documentation:

1. Update the relevant documentation files
2. Update this index if adding new documents
3. Test all commands and examples
4. Ensure consistency across all documents
5. Update the main README if needed

## 🔗 External Resources

- **GitHub Repository:** [BlogForge CMS](https://github.com/AutoJenny/blog)
- **Main Application:** http://localhost:5000
- **Database Interface:** http://localhost:5000/db/
- **Syndication Platform:** http://localhost:5000/launchpad/
