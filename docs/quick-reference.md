# BlogForge CMS - Quick Reference Guide

## 🚀 Quick Start

### Start the Application
```bash
# Start unified application
python unified_app.py

# Or use service script
./start_unified.sh
```

### Access Points
- **Homepage:** http://localhost:5000
- **Database Management:** http://localhost:5000/db/
- **Launchpad (Syndication):** http://localhost:5000/launchpad/
- **LLM Actions:** http://localhost:5000/llm-actions/
- **Workflow System:** http://localhost:5000/workflow/

## 🔄 Auto-Replenish System

### Quick Commands
```bash
# Test auto-replenish manually
./test-auto-replenish.sh

# Call endpoint directly
curl -X POST http://localhost:5000/launchpad/api/auto-replenish-all

# Check cron job
crontab -l

# View auto-replenish logs
tail -f logs/auto-replenish.log
```

### Configuration
Edit `config/queue_auto_replenish.json`:
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
    }
  ]
}
```

### Cron Job Management
```bash
# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Remove all cron jobs
crontab -r
```

## 🗄️ Database Management

### Quick Database Commands
```bash
# Access database interface
open http://localhost:5000/db/

# Check database connection
python -c "from config.database import db_manager; print('DB OK' if db_manager.get_connection() else 'DB Error')"

# View table structure
python -c "
from config.database import db_manager
with db_manager.get_cursor() as cursor:
    cursor.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name\")
    tables = cursor.fetchall()
    for table in tables:
        print(table['table_name'])
"
```

### Key Tables
- `posting_queue` - Content scheduling
- `clan_products` - Product data
- `ui_session_state` - UI state
- `workflow_stage_entity` - Workflows
- `llm_prompts` - AI prompts

## 📱 Syndication Platform (Launchpad)

### Product Post Creation
1. Go to http://localhost:5000/launchpad/syndication/facebook/product_post
2. Select a product from the browser
3. Generate AI content
4. Add to queue

### Queue Management
- **View Queue:** http://localhost:5000/launchpad/syndication/facebook/product_post
- **Add 10 Items:** Use "Add 10 items" button
- **Auto-Replenish:** Runs daily at 9 AM

### API Endpoints
```bash
# Get queue status
curl http://localhost:5000/launchpad/api/queue

# Generate content
curl -X POST -H "Content-Type: application/json" \
  -d '{"product_id": 123, "content_type": "product"}' \
  http://localhost:5000/launchpad/api/syndication/generate-social-content

# Auto-replenish
curl -X POST http://localhost:5000/launchpad/api/auto-replenish-all
```

## 🤖 AI/LLM Integration

### Ollama Setup
```bash
# Start Ollama service
ollama serve

# Pull models
ollama pull mistral
ollama pull llama2

# Test model
ollama run mistral "Hello, how are you?"
```

### LLM Actions Interface
- **Access:** http://localhost:5000/llm-actions/
- **Models:** mistral, llama2, codellama
- **Prompts:** Configurable in database

## 🔧 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Install dependencies
pip install -r requirements.txt

# Check port availability
lsof -i :5000
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
brew services list | grep postgresql

# Test connection
psql -d blog -c "SELECT 1;"

# Check credentials in config
cat config/unified_config.py
```

#### Auto-Replenish Not Working
```bash
# Check cron service
sudo service cron status

# Check cron job
crontab -l

# Test manually
./test-auto-replenish.sh

# Check logs
tail -f logs/auto-replenish.log
```

#### Queue Issues
```bash
# Check queue status
curl http://localhost:5000/launchpad/api/queue

# Check database
python -c "
from config.database import db_manager
with db_manager.get_cursor() as cursor:
    cursor.execute('SELECT COUNT(*) FROM posting_queue')
    print('Queue count:', cursor.fetchone()['count'])
"
```

### Log Files
- `unified_app.log` - Main application log
- `logs/auto-replenish.log` - Auto-replenish system log
- `logs/` - Service-specific logs

### Health Checks
```bash
# Application health
curl http://localhost:5000/launchpad/health

# Database health
curl http://localhost:5000/db/health
```

## 📊 Monitoring

### Key Metrics
- Queue levels (should stay above thresholds)
- Database connection status
- Cron job execution
- Application response times

### Monitoring Commands
```bash
# Check queue levels
curl -s http://localhost:5000/launchpad/api/queue | python -m json.tool

# Check auto-replenish status
curl -s -X POST http://localhost:5000/launchpad/api/auto-replenish-all | python -m json.tool

# Monitor logs
tail -f unified_app.log
tail -f logs/auto-replenish.log
```

## 🚨 Emergency Procedures

### Application Down
1. Check logs: `tail -f unified_app.log`
2. Restart application: `python unified_app.py`
3. Check database connection
4. Verify port availability

### Database Issues
1. Check PostgreSQL service: `brew services list | grep postgresql`
2. Test connection: `psql -d blog -c "SELECT 1;"`
3. Check credentials in config
4. Restore from backup if needed

### Auto-Replenish Failure
1. Check cron service: `sudo service cron status`
2. Test manually: `./test-auto-replenish.sh`
3. Check configuration: `cat config/queue_auto_replenish.json`
4. Review logs: `tail -f logs/auto-replenish.log`

## 📚 Additional Resources

- **[System Overview](system-overview.md)** - Complete system documentation
- **[Auto-Replenish Guide](auto-replenish-system.md)** - Detailed auto-replenish documentation
- **[README](../README.md)** - Main project documentation
- **[Architecture Docs](temp/)** - Detailed architecture documentation
