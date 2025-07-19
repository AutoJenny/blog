# Rollback Procedures Documentation

**Date:** 2025-07-17  
**Purpose:** Comprehensive rollback procedures for project reorganization  
**Status:** Phase 1, Step 4 - Rollback Procedures Documentation  

---

## Overview

This document outlines comprehensive rollback procedures for the project reorganization. Rollback procedures are critical for maintaining system stability and data integrity during the migration process.

**Critical Principle:** Every step must have a corresponding rollback procedure that can be executed quickly and reliably.

---

## Database Rollback Procedures

### Full Database Rollback
**Scenario:** Complete database corruption or major data loss
**Trigger:** Database integrity check failure or data corruption detection

**Procedure:**
1. **Stop All Applications**
   ```bash
   # Stop all Flask applications
   pkill -f flask
   pkill -f python
   ```

2. **Create Emergency Backup** (if possible)
   ```bash
   pg_dump -h localhost -U nickfiddes -d blog > emergency_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Restore from Last Known Good Backup**
   ```bash
   # Drop and recreate database
   dropdb -h localhost -U nickfiddes blog
   createdb -h localhost -U nickfiddes blog
   
   # Restore from backup
   psql -h localhost -U nickfiddes -d blog < /path/to/last_good_backup.sql
   ```

4. **Verify Database Integrity**
   ```bash
   # Run integrity checks
   psql -h localhost -U nickfiddes -d blog -c "SELECT COUNT(*) FROM post;"
   psql -h localhost -U nickfiddes -d blog -c "SELECT COUNT(*) FROM post_section;"
   psql -h localhost -U nickfiddes -d blog -c "SELECT COUNT(*) FROM post_development;"
   ```

5. **Restart Applications**
   ```bash
   # Restart Flask applications
   cd /path/to/blog
   python run.py
   ```

**Test Script:** `test_database_rollback.py`

### Partial Database Rollback
**Scenario:** Specific tables or data corrupted
**Trigger:** Specific table corruption or data inconsistency

**Procedure:**
1. **Identify Affected Tables**
   ```bash
   # Check table integrity
   psql -h localhost -U nickfiddes -d blog -c "\dt"
   psql -h localhost -U nickfiddes -d blog -c "SELECT table_name, row_count FROM information_schema.tables WHERE table_schema = 'public';"
   ```

2. **Backup Affected Tables**
   ```bash
   # Backup specific tables
   pg_dump -h localhost -U nickfiddes -d blog -t post -t post_section > affected_tables_backup.sql
   ```

3. **Restore Specific Tables**
   ```bash
   # Drop and recreate specific tables
   psql -h localhost -U nickfiddes -d blog -c "DROP TABLE IF EXISTS post_section CASCADE;"
   psql -h localhost -U nickfiddes -d blog -c "DROP TABLE IF EXISTS post_development CASCADE;"
   
   # Restore from backup
   psql -h localhost -U nickfiddes -d blog < affected_tables_backup.sql
   ```

4. **Verify Table Integrity**
   ```bash
   # Check foreign key relationships
   psql -h localhost -U nickfiddes -d blog -c "SELECT * FROM post_section WHERE post_id NOT IN (SELECT id FROM post);"
   ```

**Test Script:** `test_partial_database_rollback.py`

### Schema Rollback
**Scenario:** Database schema changes cause issues
**Trigger:** Schema migration failure or compatibility issues

**Procedure:**
1. **Backup Current Schema**
   ```bash
   pg_dump -h localhost -U nickfiddes -d blog --schema-only > current_schema.sql
   ```

2. **Restore Previous Schema**
   ```bash
   # Apply previous schema
   psql -h localhost -U nickfiddes -d blog < /path/to/previous_schema.sql
   ```

3. **Verify Schema Compatibility**
   ```bash
   # Check table structure
   psql -h localhost -U nickfiddes -d blog -c "\d post"
   psql -h localhost -U nickfiddes -d blog -c "\d post_section"
   ```

**Test Script:** `test_schema_rollback.py`

---

## Code Rollback Procedures

### Git-Based Rollback
**Scenario:** Code changes cause application failures
**Trigger:** Application startup failure or critical bugs

**Procedure:**
1. **Identify Current Commit**
   ```bash
   git log --oneline -10
   git status
   ```

2. **Create Emergency Branch**
   ```bash
   git checkout -b emergency_rollback_$(date +%Y%m%d_%H%M%S)
   ```

3. **Revert to Last Known Good Commit**
   ```bash
   # Hard reset to last known good commit
   git reset --hard <last_good_commit_hash>
   
   # Or revert specific commits
   git revert <bad_commit_hash>
   ```

4. **Verify Code Integrity**
   ```bash
   # Check for syntax errors
   python -m py_compile app.py
   python -m py_compile config.py
   
   # Run basic tests
   python -m pytest tests/unit/ -v
   ```

5. **Restart Application**
   ```bash
   # Restart Flask application
   pkill -f flask
   python run.py
   ```

**Test Script:** `test_git_rollback.py`

### File-Based Rollback
**Scenario:** Specific files corrupted or modified incorrectly
**Trigger:** Specific file issues or manual changes

**Procedure:**
1. **Identify Affected Files**
   ```bash
   # Check file modifications
   git status
   git diff
   ```

2. **Restore Specific Files**
   ```bash
   # Restore specific files from Git
   git checkout HEAD -- app/workflow/routes.py
   git checkout HEAD -- config.py
   
   # Or restore from backup
   cp /path/to/backup/app/workflow/routes.py app/workflow/routes.py
   ```

3. **Verify File Integrity**
   ```bash
   # Check file syntax
   python -m py_compile app/workflow/routes.py
   python -m py_compile config.py
   ```

**Test Script:** `test_file_rollback.py`

### Dependency Rollback
**Scenario:** Package updates cause compatibility issues
**Trigger:** Import errors or dependency conflicts

**Procedure:**
1. **Backup Current Requirements**
   ```bash
   pip freeze > current_requirements.txt
   ```

2. **Restore Previous Requirements**
   ```bash
   # Uninstall current packages
   pip uninstall -r current_requirements.txt -y
   
   # Install previous requirements
   pip install -r requirements.backup.txt
   ```

3. **Verify Dependencies**
   ```bash
   # Check installed packages
   pip list
   
   # Test imports
   python -c "import flask; import psycopg2; print('Dependencies OK')"
   ```

**Test Script:** `test_dependency_rollback.py`

---

## Configuration Rollback Procedures

### Environment Variable Rollback
**Scenario:** Environment variable changes cause issues
**Trigger:** Configuration errors or missing variables

**Procedure:**
1. **Backup Current Configuration**
   ```bash
   cp assistant_config.env assistant_config.env.backup
   cp .env .env.backup 2>/dev/null || true
   ```

2. **Restore Previous Configuration**
   ```bash
   # Restore from backup
   cp assistant_config.env.backup assistant_config.env
   cp .env.backup .env 2>/dev/null || true
   ```

3. **Verify Configuration**
   ```bash
   # Test configuration loading
   python -c "from config import get_config; print('Config OK')"
   ```

**Test Script:** `test_configuration_rollback.py`

### Flask Configuration Rollback
**Scenario:** Flask configuration changes cause issues
**Trigger:** Application configuration errors

**Procedure:**
1. **Backup Current Config**
   ```bash
   cp config.py config.py.backup
   ```

2. **Restore Previous Config**
   ```bash
   cp config.py.backup config.py
   ```

3. **Verify Flask Config**
   ```bash
   # Test Flask configuration
   python -c "from config import get_config; config = get_config(); print('Flask Config OK')"
   ```

**Test Script:** `test_flask_config_rollback.py`

---

## Project-Specific Rollback Procedures

### blog-core Rollback
**Scenario:** Core infrastructure changes cause issues
**Trigger:** Database connection failures or shared utility errors

**Procedure:**
1. **Stop All Dependent Projects**
   ```bash
   # Stop all projects that depend on blog-core
   pkill -f blog-planning
   pkill -f blog-writing
   pkill -f blog-structuring
   pkill -f blog-images
   pkill -f blog-publishing
   ```

2. **Rollback blog-core**
   ```bash
   cd /path/to/blog-core
   git reset --hard <last_good_commit>
   ```

3. **Verify Core Functionality**
   ```bash
   # Test database connection
   python -c "from app.db import get_db_conn; conn = get_db_conn(); print('DB OK')"
   
   # Test configuration
   python -c "from config import get_config; print('Config OK')"
   ```

4. **Restart Dependent Projects**
   ```bash
   # Restart all projects
   cd /path/to/blog-planning && python run.py &
   cd /path/to/blog-writing && python run.py &
   cd /path/to/blog-structuring && python run.py &
   cd /path/to/blog-images && python run.py &
   cd /path/to/blog-publishing && python run.py &
   ```

**Test Script:** `test_blog_core_rollback.py`

### Stage Project Rollback
**Scenario:** Specific stage project changes cause issues
**Trigger:** Stage-specific functionality failures

**Procedure:**
1. **Stop Specific Project**
   ```bash
   pkill -f blog-planning  # or specific project
   ```

2. **Rollback Project**
   ```bash
   cd /path/to/blog-planning
   git reset --hard <last_good_commit>
   ```

3. **Verify Project Functionality**
   ```bash
   # Test project-specific functionality
   python -c "from app.workflow.routes import *; print('Project OK')"
   ```

4. **Restart Project**
   ```bash
   python run.py
   ```

**Test Script:** `test_stage_project_rollback.py`

---

## Cross-Project Rollback Procedures

### Multi-Project Rollback
**Scenario:** Changes across multiple projects cause issues
**Trigger:** Inter-project communication failures

**Procedure:**
1. **Stop All Projects**
   ```bash
   pkill -f blog-core
   pkill -f blog-planning
   pkill -f blog-writing
   pkill -f blog-structuring
   pkill -f blog-images
   pkill -f blog-publishing
   ```

2. **Rollback All Projects**
   ```bash
   # Rollback each project
   cd /path/to/blog-core && git reset --hard <last_good_commit>
   cd /path/to/blog-planning && git reset --hard <last_good_commit>
   cd /path/to/blog-writing && git reset --hard <last_good_commit>
   cd /path/to/blog-structuring && git reset --hard <last_good_commit>
   cd /path/to/blog-images && git reset --hard <last_good_commit>
   cd /path/to/blog-publishing && git reset --hard <last_good_commit>
   ```

3. **Verify Cross-Project Communication**
   ```bash
   # Test database sharing
   python -c "from app.db import get_db_conn; conn = get_db_conn(); print('DB Sharing OK')"
   
   # Test API communication
   curl -s http://localhost:5000/api/health
   ```

4. **Restart All Projects**
   ```bash
   # Restart in dependency order
   cd /path/to/blog-core && python run.py &
   sleep 5
   cd /path/to/blog-planning && python run.py &
   cd /path/to/blog-writing && python run.py &
   cd /path/to/blog-structuring && python run.py &
   cd /path/to/blog-images && python run.py &
   cd /path/to/blog-publishing && python run.py &
   ```

**Test Script:** `test_multi_project_rollback.py`

---

## Automated Rollback Scripts

### Emergency Rollback Script
**Location:** `scripts/emergency_rollback.sh`
**Purpose:** Automated emergency rollback for critical failures

**Script Content:**
```bash
#!/bin/bash
# Emergency rollback script

set -e

echo "Starting emergency rollback..."

# Stop all applications
pkill -f flask || true
pkill -f python || true

# Create emergency backup
pg_dump -h localhost -U nickfiddes -d blog > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from last known good backup
dropdb -h localhost -U nickfiddes blog
createdb -h localhost -U nickfiddes blog
psql -h localhost -U nickfiddes -d blog < /path/to/last_good_backup.sql

# Rollback code
cd /path/to/blog
git reset --hard HEAD~1

# Restart application
python run.py &

echo "Emergency rollback completed"
```

### Database Rollback Script
**Location:** `scripts/database_rollback.sh`
**Purpose:** Automated database rollback

**Script Content:**
```bash
#!/bin/bash
# Database rollback script

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Rolling back database to $BACKUP_FILE..."

# Stop applications
pkill -f flask || true

# Restore database
dropdb -h localhost -U nickfiddes blog
createdb -h localhost -U nickfiddes blog
psql -h localhost -U nickfiddes -d blog < $BACKUP_FILE

# Verify integrity
psql -h localhost -U nickfiddes -d blog -c "SELECT COUNT(*) FROM post;"

# Restart application
python run.py &

echo "Database rollback completed"
```

### Configuration Rollback Script
**Location:** `scripts/config_rollback.sh`
**Purpose:** Automated configuration rollback

**Script Content:**
```bash
#!/bin/bash
# Configuration rollback script

set -e

echo "Rolling back configuration..."

# Restore configuration files
cp assistant_config.env.backup assistant_config.env
cp .env.backup .env 2>/dev/null || true
cp config.py.backup config.py

# Verify configuration
python -c "from config import get_config; print('Configuration restored')"

echo "Configuration rollback completed"
```

---

## Rollback Testing Procedures

### Pre-Rollback Testing
**Purpose:** Verify rollback procedures work before deployment

**Procedure:**
1. **Create Test Environment**
   ```bash
   # Create test database
   createdb -h localhost -U nickfiddes blog_test
   ```

2. **Test Rollback Procedures**
   ```bash
   # Test database rollback
   ./scripts/database_rollback.sh test_backup.sql
   
   # Test code rollback
   git reset --hard HEAD~1
   
   # Test configuration rollback
   ./scripts/config_rollback.sh
   ```

3. **Verify Functionality**
   ```bash
   # Run tests
   python -m pytest tests/unit/
   python -m pytest tests/integration/
   ```

### Post-Rollback Testing
**Purpose:** Verify system functionality after rollback

**Procedure:**
1. **Verify Database Integrity**
   ```bash
   # Check table counts
   psql -h localhost -U nickfiddes -d blog -c "SELECT COUNT(*) FROM post;"
   psql -h localhost -U nickfiddes -d blog -c "SELECT COUNT(*) FROM post_section;"
   ```

2. **Verify Application Functionality**
   ```bash
   # Test basic functionality
   curl -s http://localhost:5000/api/health
   curl -s http://localhost:5000/workflow/
   ```

3. **Run Critical Tests**
   ```bash
   # Run critical test cases
   python -m pytest tests/critical/ -v
   ```

---

## Rollback Documentation

### Rollback Log
**Location:** `logs/rollback.log`
**Purpose:** Track all rollback operations

**Log Format:**
```
2025-07-17 14:30:00 - ROLLBACK - Database rollback initiated
2025-07-17 14:30:05 - ROLLBACK - Database restored from backup_20250717_143000.sql
2025-07-17 14:30:10 - ROLLBACK - Application restarted successfully
2025-07-17 14:30:15 - ROLLBACK - Rollback verification completed
```

### Rollback Checklist
**Location:** `docs/rollback_checklist.md`
**Purpose:** Step-by-step rollback checklist

**Checklist Items:**
- [ ] Stop all applications
- [ ] Create emergency backup
- [ ] Execute rollback procedure
- [ ] Verify data integrity
- [ ] Test functionality
- [ ] Document rollback
- [ ] Notify stakeholders

---

## Rollback Communication

### Emergency Contacts
**Purpose:** Contact information for emergency rollbacks

**Contacts:**
- **Primary:** System Administrator
- **Secondary:** Development Team Lead
- **Tertiary:** Project Manager

### Rollback Notifications
**Purpose:** Notify stakeholders of rollback operations

**Notification Process:**
1. **Immediate:** Email to emergency contacts
2. **Within 1 hour:** Status update to all stakeholders
3. **Within 24 hours:** Post-mortem analysis

---

**Status:** Step 4 Complete - Rollback procedures documented  
**Next Step:** Step 5 - Project Structure Design 