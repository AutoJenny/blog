# Navigation System Implementation Plan

## Critical Safety Rules

1. **NEVER proceed to the next step if the current step fails**
2. **ALWAYS verify with curl after each change**
3. **ALWAYS have a backup and rollback plan ready**
4. **Test key workflow paths after EVERY change**

## Key Test URLs
```bash
# Test these URLs after EVERY change:
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
curl http://localhost:5000/workflow/22/planning/research/Main/
curl http://localhost:5000/workflow/22/planning/structure/Main/
```

## Phase 0: Preparation and Backup

### 0.1 Database Backup
```bash
# Create backup
pg_dump -U nickfiddes -d blog > nav_rescue_backup_$(date +%Y%m%d_%H%M%S).sql

# Test restore in separate DB
createdb -U nickfiddes blog_test
psql -U nickfiddes -d blog_test -f nav_rescue_backup_*.sql
```

### 0.2 Git Safety Net
```bash
# Create rescue branch
git checkout -b nav-rescue-implementation
git add .
git commit -m "Pre-navigation rescue snapshot"
git tag pre-nav-rescue
```

## Phase 1: Remove Non-Compliant Files

### 1.1 Legacy Step Templates
```bash
# First verify replacements exist
ls -l app/templates/workflow/steps/Idea\ Seed.html
ls -l app/templates/workflow/steps/Provisional\ Title.html

# Then remove old files
rm app/templates/workflow/steps/basic_idea.html
rm app/templates/workflow/steps/provisional_title.html

# Test key workflow paths
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
```

### 1.2 Legacy Configuration
```bash
# Verify data exists in workflow_stage_entity
psql -U nickfiddes -d blog -c "SELECT * FROM workflow_stage_entity;"

# Remove old config
rm app/workflow/config/planning_steps.json

# Test key workflow paths
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
```

If any test fails:
```bash
git reset --hard pre-nav-rescue
psql -U nickfiddes -d blog -f nav_rescue_backup_*.sql
```

## Phase 2: Update Core Navigation

### 2.1 Navigation Service
1. Create backup of current navigation.py
```bash
cp app/workflow/navigation.py app/workflow/navigation.py.bak
```

2. Update navigation.py to use workflow entity tables:
```python
def get_workflow_structure():
    """Get complete hierarchy from workflow entity tables."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    s.id as stage_id, s.name as stage_name,
                    ss.id as substage_id, ss.name as substage_name,
                    st.id as step_id, st.name as step_name
                FROM workflow_stage_entity s
                JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id
                JOIN workflow_step_entity st ON st.sub_stage_id = ss.id
                ORDER BY s.stage_order, ss.sub_stage_order, st.step_order
            """)
            return cur.fetchall()
```

3. Test after each change:
```bash
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
```

4. If failure:
```bash
mv app/workflow/navigation.py.bak app/workflow/navigation.py
```

### 2.2 Template Structure
1. Create backup of workflow templates
```bash
cp -r app/templates/workflow app/templates/workflow.bak
```

2. Update base template:
```bash
# Verify template exists
ls -l app/templates/workflow/base.html

# Make changes
# Test after EACH change
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
```

3. If failure:
```bash
rm -rf app/templates/workflow
mv app/templates/workflow.bak app/templates/workflow
```

## Phase 3: Database Access Layer

### 3.1 Update Database Functions
1. Backup current db.py
```bash
cp app/db.py app/db.py.bak
```

2. Add new functions:
```python
def get_workflow_step(stage_name, substage_name, step_name):
    """Get step details, validating full path exists."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT st.* 
                FROM workflow_step_entity st
                JOIN workflow_sub_stage_entity ss ON st.sub_stage_id = ss.id
                JOIN workflow_stage_entity s ON ss.stage_id = s.id
                WHERE s.name = %s 
                AND ss.name = %s 
                AND st.name = %s
            """, (stage_name, substage_name, step_name))
            return cur.fetchone()
```

3. Test after each change:
```bash
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
```

4. If failure:
```bash
mv app/db.py.bak app/db.py
```

## Phase 4: Route Updates

### 4.1 Workflow Routes
1. Backup routes
```bash
cp app/workflow/routes.py app/workflow/routes.py.bak
```

2. Update route validation:
```python
@bp.route('/<int:post_id>/<stage_name>/<substage_name>/<step_name>/')
def step(post_id, stage_name, substage_name, step_name):
    """Handle workflow step display with database validation."""
    step = get_workflow_step(stage_name, substage_name, step_name)
    if not step:
        abort(404)
    # ... rest of function
```

3. Test after each change:
```bash
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
```

4. If failure:
```bash
mv app/workflow/routes.py.bak app/workflow/routes.py
```

## Phase 5: Template Organization

### 5.1 Step Templates
1. Create new structure:
```bash
mkdir -p app/templates/workflow/steps/Planning/Idea
mkdir -p app/templates/workflow/steps/Planning/Research
mkdir -p app/templates/workflow/steps/Planning/Structure
```

2. Move templates:
```bash
# Move with verification after each
mv "app/templates/workflow/steps/Idea Seed.html" \
   "app/templates/workflow/steps/Planning/Idea/Idea Seed.html"

# Test after EACH move
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
```

## Phase 6: Testing and Verification

### 6.1 Database Verification
```sql
-- Verify workflow structure
SELECT s.name as stage, ss.name as substage, st.name as step
FROM workflow_stage_entity s
JOIN workflow_sub_stage_entity ss ON ss.stage_id = s.id
JOIN workflow_step_entity st ON st.sub_stage_id = ss.id
ORDER BY s.stage_order, ss.sub_stage_order, st.step_order;
```

### 6.2 Route Testing
Test all key workflow paths:
```bash
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
curl http://localhost:5000/workflow/22/planning/research/Main/
curl http://localhost:5000/workflow/22/planning/structure/Main/
```

### 6.3 Template Verification
```bash
# Verify all templates exist in correct locations
find app/templates/workflow/steps -type f -name "*.html"
```

## Emergency Rollback Procedure

If any phase fails catastrophically:

1. Stop the server:
```bash
./scripts/dev/restart_flask_dev.sh
```

2. Reset git:
```bash
git reset --hard pre-nav-rescue
```

3. Restore database:
```bash
psql -U nickfiddes -d blog -f nav_rescue_backup_*.sql
```

4. Restart server:
```bash
./scripts/dev/restart_flask_dev.sh
```

5. Verify key paths:
```bash
curl http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
```

## Success Criteria

1. All key workflow paths return 200:
```bash
curl -I http://localhost:5000/workflow/22/planning/idea/Idea%20Seed/
curl -I http://localhost:5000/workflow/22/planning/research/Main/
curl -I http://localhost:5000/workflow/22/planning/structure/Main/
```

2. Database queries show correct structure:
```sql
SELECT COUNT(*) FROM workflow_stage_entity;
SELECT COUNT(*) FROM workflow_sub_stage_entity;
SELECT COUNT(*) FROM workflow_step_entity;
```

3. All templates exist in correct locations:
```bash
find app/templates/workflow/steps -type f -name "*.html"
```

4. No references to old paths:
```bash
grep -r "basic_idea" .
grep -r "provisional_title" .
```

## Final Verification

Before considering implementation complete:

1. Test all workflow paths
2. Verify database consistency
3. Check all templates exist
4. Ensure no old references remain
5. Verify navigation works
6. Test LLM integration

Only merge if ALL criteria are met. 