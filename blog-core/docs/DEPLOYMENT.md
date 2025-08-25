# Deployment Guide

## Overview
This guide covers deployment procedures for the blog application, including the format system and workflow components.

## Pre-Deployment Checklist

### 1. Database Backup
Before any deployment, create a backup:
```bash
python3 scripts/backup_database.py
```

### 2. Environment Configuration
Ensure all required environment variables are set:
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `SECRET_KEY`
- `OPENAI_AUTH_TOKEN` (or other LLM provider settings)
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

### 3. Dependencies
Install all required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Database Migration
The application uses direct SQL connections, so migrations are handled manually. Ensure all required tables exist:
- `workflow_format_template`
- `workflow_step_format`
- `workflow_stage_format`
- `workflow_post_format`
- All other workflow and blog tables

## Format System Deployment

### Pre-Deployment Verification
Run the rollback test to ensure everything is ready:
```bash
python3 scripts/test_rollback.py
```

### Deployment Steps

1. **Stop the application server**
   ```bash
   ./scripts/dev/restart_flask_dev.sh
   ```

2. **Verify format system components**
   - API endpoints: `/api/workflow/formats/*`
   - JavaScript files: `/static/js/format_*.js`
   - Templates: `/templates/settings/format_*.html`
   - Tests: `/tests/test_format_*.py`

3. **Test the deployment**
   ```bash
   # Start the server
   ./scripts/dev/restart_flask_dev.sh
   
   # Run integration tests
   python3 -m pytest tests/test_format_integration.py -v
   
   # Test API endpoints
   curl http://localhost:5000/api/workflow/formats/templates
   ```

### Post-Deployment Verification

1. **Check API endpoints**
   - Format templates: `GET /api/workflow/formats/templates`
   - Format validation: `POST /api/workflow/formats/validate`
   - Step formats: `GET /api/workflow/steps/<id>/formats`

2. **Verify UI components**
   - Format management: `/settings/format_templates`
   - Format configuration: `/settings/workflow_step_formats`
   - Workflow panels with format integration

3. **Test workflow integration**
   - Create a workflow step with format validation
   - Test format reference resolution
   - Verify error handling

## Rollback Procedures

### Database Rollback
If database issues occur:
```bash
# Restore from backup
psql -h localhost -U <user> -d blog < backups/blog_backup_<timestamp>_pre_format_deployment.sql
```

### Code Rollback
If code issues occur:
```bash
# Revert to previous commit
git reset --hard HEAD~1
git clean -fd

# Restart server
./scripts/dev/restart_flask_dev.sh
```

## Monitoring and Troubleshooting

### Logs
Check application logs for errors:
- Flask application logs
- Database connection errors
- Format validation errors

### Common Issues

1. **Format validation failing**
   - Check format template structure
   - Verify field types and requirements
   - Test with format validator

2. **API endpoints not responding**
   - Check server status
   - Verify route registration
   - Check for JavaScript errors

3. **Database connection issues**
   - Verify database credentials
   - Check database server status
   - Test connection with psql

### Health Checks
Run these commands to verify system health:
```bash
# Database connection
python3 -c "from app.db import get_db_conn; conn = get_db_conn(); print('DB OK')"

# API endpoints
curl -f http://localhost:5000/api/workflow/formats/templates

# Format validation
curl -X POST http://localhost:5000/api/workflow/formats/validate \
  -H "Content-Type: application/json" \
  -d '{"fields":[{"name":"test","type":"string"}],"test_data":{"test":"value"}}'
```

## Production Deployment

### Environment Setup
1. Set `FLASK_ENV=production`
2. Configure production database
3. Set up SSL certificates
4. Configure reverse proxy (nginx)

### Performance Considerations
- Enable caching for format templates
- Monitor database query performance
- Use connection pooling
- Implement rate limiting for API endpoints

### Security
- Validate all format inputs
- Sanitize user-provided data
- Use HTTPS in production
- Implement proper access controls

## Support

For deployment issues:
1. Check this documentation
2. Review `/docs/workflow/formats.md` for format system details
3. Check `/docs/temp/format_system_implementation_plan.md` for implementation status
4. Review logs and error messages
5. Test with provided scripts and curl commands

## Recent Deployments

### 2025-06-28: Format System Integration
- **Feature**: Added format template selection to workflow UI
- **Database Changes**: Added `default_input_format_id` and `default_output_format_id` columns to `workflow_step_entity`
- **Migration**: `migrations/20250628_add_default_format_columns_to_workflow_step_entity.sql`
- **Backup**: `backups/blog_backup_YYYYMMDD_HHMMSS_pre_format_columns.sql`
- **Status**: ✅ Deployed and tested

#### Changes Made:
1. **Database Schema**: Added format template reference columns to workflow steps
2. **UI Components**: Added format template selectors to workflow settings panel
3. **JavaScript**: Created format selector functionality for template assignment
4. **API Integration**: Connected format assignment to workflow step configuration

#### Testing:
- Format templates API: ✅ Working
- Format assignment API: ✅ Working  
- Workflow UI format selectors: ✅ Ready for testing
- Database migration: ✅ Applied successfully

#### Files Modified:
- `app/templates/modules/llm_panel/templates/components/settings.html` - Added format selectors
- `app/static/js/format_selector.js` - New format selection JavaScript
- `app/templates/modules/llm_panel/templates/panel.html` - Added format selector import
- `docs/database/schema.md` - Updated schema documentation
- `migrations/20250628_add_default_format_columns_to_workflow_step_entity.sql` - New migration

## Previous Deployments 