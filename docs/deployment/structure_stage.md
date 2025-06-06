# Structure Stage Deployment Checklist

## Pre-Deployment

### Database
- [ ] Backup current database
- [ ] Verify post_section table schema
  - [ ] section_description field exists
  - [ ] ideas_to_include and facts_to_include are JSON type
  - [ ] section_order is integer
- [ ] Test database migrations
- [ ] Verify indexes and constraints

### Frontend Assets
- [ ] Build and minify JavaScript
  - [ ] structure_stage.js
  - [ ] sortable.min.js
- [ ] Verify CSS classes
- [ ] Test responsive design
- [ ] Check browser compatibility
  - [ ] Chrome
  - [ ] Firefox
  - [ ] Safari
  - [ ] Edge

### Backend
- [ ] Verify API endpoints
  - [ ] /api/v1/structure/plan
  - [ ] /api/v1/structure/save/<post_id>
  - [ ] /api/v1/post/<post_id>/structure
- [ ] Test error handling
- [ ] Verify authentication
- [ ] Check rate limiting
- [ ] Test LLM integration

## Deployment Steps

### 1. Database
```sql
-- Verify current schema
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'post_section';

-- Backup existing data
CREATE TABLE post_section_backup AS 
SELECT * FROM post_section;

-- Add new column if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'post_section' 
        AND column_name = 'section_description'
    ) THEN
        ALTER TABLE post_section 
        ADD COLUMN section_description TEXT;
    END IF;
END $$;
```

### 2. Frontend
```bash
# Build assets
npm run build

# Verify file sizes
ls -lh app/static/js/workflow/structure_stage.js
ls -lh app/static/js/workflow/sortable.min.js

# Update cache busting
sed -i 's/version=.*/version='$(date +%s)'/' app/templates/workflow/planning/structure/index.html
```

### 3. Backend
```bash
# Deploy API endpoints
git pull origin main
flask db upgrade
flask run

# Verify endpoints
curl -X POST http://localhost:5000/api/v1/structure/plan \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","idea":"Test","facts":["Test"]}'

curl -X POST http://localhost:5000/api/v1/structure/save/1 \
  -H "Content-Type: application/json" \
  -d '{"sections":[{"title":"Test","description":"Test","ideas":[],"facts":[]}]}'
```

## Post-Deployment

### Verification
- [ ] Test all user flows
  1. Create new post
  2. Enter inputs
  3. Generate sections
  4. Edit sections
  5. Save structure
- [ ] Verify data persistence
- [ ] Check error handling
- [ ] Monitor performance

### Monitoring
- [ ] Set up error tracking
  - [ ] Frontend errors
  - [ ] API errors
  - [ ] LLM errors
- [ ] Configure performance monitoring
  - [ ] Response times
  - [ ] Resource usage
  - [ ] Database queries
- [ ] Set up alerts
  - [ ] Error rate thresholds
  - [ ] Performance thresholds
  - [ ] LLM service status

### Rollback Plan
1. Database
```sql
-- Restore from backup
DROP TABLE post_section;
CREATE TABLE post_section AS 
SELECT * FROM post_section_backup;
```

2. Frontend
```bash
# Revert to previous version
git checkout HEAD^
npm run build
```

3. Backend
```bash
# Revert API changes
git checkout HEAD^
flask db downgrade
```

## Success Criteria
- [ ] All endpoints respond within 200ms
- [ ] No JavaScript errors in console
- [ ] All user flows complete successfully
- [ ] Data persists correctly
- [ ] Error handling works as expected
- [ ] Monitoring is active
- [ ] Documentation is up to date

## Future Considerations
1. Performance optimization
   - [ ] Lazy loading
   - [ ] Caching
   - [ ] Query optimization
2. Feature enhancements
   - [ ] Undo/redo
   - [ ] Templates
   - [ ] Analytics
3. Maintenance
   - [ ] Regular backups
   - [ ] Performance reviews
   - [ ] Security updates 