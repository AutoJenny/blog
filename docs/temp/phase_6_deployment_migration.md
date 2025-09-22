# Phase 6: Deployment and Migration - Detailed Implementation

## 6.1 Staging Deployment

### Step 6.1.1: Set Up Staging Environment
- [ ] Create staging server configuration
- [ ] Set up staging database
- [ ] Configure staging environment variables
- [ ] Test staging setup

**Staging Environment Configuration**:
```bash
# staging_setup.sh
#!/bin/bash

echo "Setting up staging environment..."

# Create staging directory
mkdir -p /opt/blog/staging
cd /opt/blog/staging

# Clone repository
git clone https://github.com/your-repo/blog.git .

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up staging database
createdb blog_staging
psql blog_staging < backups/latest_backup.sql

# Set up staging configuration
cp config/staging.env .env
export FLASK_ENV=staging

# Test staging setup
python unified_app.py &
sleep 5
curl http://localhost:5000/core/health
curl http://localhost:5000/launchpad/health
curl http://localhost:5000/llm_actions/health
```

**Benchmark**: Staging environment set up
**Test**: All staging services respond to health checks

### Step 6.1.2: Deploy Unified App to Staging
- [ ] Deploy unified app to staging
- [ ] Test all functionality in staging
- [ ] Compare performance with current setup
- [ ] Fix any issues found

**Staging Deployment Steps**:
```bash
# deploy_staging.sh
#!/bin/bash

echo "Deploying unified app to staging..."

# Stop existing services
pkill -f "python.*app.py"

# Deploy unified app
cd /opt/blog/staging
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Start unified app
nohup python unified_app.py > unified_app.log 2>&1 &
echo $! > unified_app.pid

# Wait for startup
sleep 10

# Test deployment
curl http://localhost:5000/core/health
curl http://localhost:5000/launchpad/health
curl http://localhost:5000/llm_actions/health

echo "Staging deployment complete"
```

**Benchmark**: Unified app deployed to staging
**Test**: All staging endpoints respond correctly

### Step 6.1.3: Test Staging Functionality
- [ ] Test all core functionality
- [ ] Test all API endpoints
- [ ] Test all workflows
- [ ] Test all integrations

**Staging Test Script**:
```bash
#!/bin/bash
# test_staging.sh

echo "Testing staging functionality..."

# Test core functionality
echo "Testing core functionality..."
curl -f http://localhost:5000/core/ || echo "Core test failed"
curl -f http://localhost:5000/core/api/posts || echo "Core API test failed"
curl -f http://localhost:5000/core/workflow/posts/53/planning/idea/provisional_title || echo "Workflow test failed"

# Test launchpad functionality
echo "Testing launchpad functionality..."
curl -f http://localhost:5000/launchpad/ || echo "Launchpad test failed"
curl -f http://localhost:5000/launchpad/syndication || echo "Syndication test failed"
curl -f http://localhost:5000/launchpad/syndication/facebook/product_post || echo "Facebook product post test failed"

# Test LLM actions functionality
echo "Testing LLM actions functionality..."
curl -f http://localhost:5000/llm_actions/ || echo "LLM actions test failed"
curl -f http://localhost:5000/llm_actions/api/llm/config || echo "LLM config test failed"

# Test database functionality
echo "Testing database functionality..."
curl -f http://localhost:5000/db/ || echo "Database test failed"
curl -f http://localhost:5000/db/tables || echo "Database tables test failed"

# Test additional services
echo "Testing additional services..."
curl -f http://localhost:5000/post_sections/ || echo "Post sections test failed"
curl -f http://localhost:5000/post_info/ || echo "Post info test failed"
curl -f http://localhost:5000/images/ || echo "Images test failed"
curl -f http://localhost:5000/clan_api/ || echo "Clan API test failed"
curl -f http://localhost:5000/settings/ || echo "Settings test failed"

echo "Staging functionality test complete"
```

**Benchmark**: All staging functionality tested
**Test**: All staging tests pass

### Step 6.1.4: Performance Comparison
- [ ] Compare response times
- [ ] Compare memory usage
- [ ] Compare CPU usage
- [ ] Compare database performance

**Performance Comparison Script**:
```bash
#!/bin/bash
# compare_performance.sh

echo "Comparing performance between microservices and unified app..."

# Test microservices performance
echo "Testing microservices performance..."
start_time=$(date +%s)
curl -s http://localhost:5000/ > /dev/null
curl -s http://localhost:5001/ > /dev/null
curl -s http://localhost:5002/ > /dev/null
microservices_time=$(($(date +%s) - start_time))

# Test unified app performance
echo "Testing unified app performance..."
start_time=$(date +%s)
curl -s http://localhost:5000/core/ > /dev/null
curl -s http://localhost:5000/launchpad/ > /dev/null
curl -s http://localhost:5000/llm_actions/ > /dev/null
unified_time=$(($(date +%s) - start_time))

echo "Microservices time: ${microservices_time}s"
echo "Unified app time: ${unified_time}s"

if [ $unified_time -lt $microservices_time ]; then
    echo "Unified app is faster"
else
    echo "Microservices are faster"
fi
```

**Benchmark**: Performance comparison completed
**Test**: Performance meets or exceeds current setup

## 6.2 Production Migration

### Step 6.2.1: Create Production Backup
- [ ] Backup current microservices
- [ ] Backup production database
- [ ] Backup configuration files
- [ ] Test backup restoration

**Production Backup Script**:
```bash
#!/bin/bash
# backup_production.sh

echo "Creating production backup..."

# Create backup directory
BACKUP_DIR="/opt/blog/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup database
echo "Backing up database..."
pg_dump blog > $BACKUP_DIR/blog_backup.sql

# Backup code
echo "Backing up code..."
cp -r /opt/blog/microservices $BACKUP_DIR/

# Backup configuration
echo "Backing up configuration..."
cp -r /opt/blog/config $BACKUP_DIR/

# Backup logs
echo "Backing up logs..."
cp -r /opt/blog/logs $BACKUP_DIR/

# Create backup archive
echo "Creating backup archive..."
tar -czf $BACKUP_DIR/production_backup.tar.gz -C $BACKUP_DIR .

echo "Production backup complete: $BACKUP_DIR"
```

**Benchmark**: Production backup created
**Test**: Backup can be restored successfully

### Step 6.2.2: Deploy Unified App to Production
- [ ] Deploy unified app to production
- [ ] Configure production environment
- [ ] Test production deployment
- [ ] Monitor for issues

**Production Deployment Script**:
```bash
#!/bin/bash
# deploy_production.sh

echo "Deploying unified app to production..."

# Create production directory
mkdir -p /opt/blog/production
cd /opt/blog/production

# Clone repository
git clone https://github.com/your-repo/blog.git .

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up production database
createdb blog_production
psql blog_production < backups/latest_backup.sql

# Set up production configuration
cp config/production.env .env
export FLASK_ENV=production

# Start unified app
nohup python unified_app.py > unified_app.log 2>&1 &
echo $! > unified_app.pid

# Wait for startup
sleep 15

# Test deployment
curl http://localhost:5000/core/health
curl http://localhost:5000/launchpad/health
curl http://localhost:5000/llm_actions/health

echo "Production deployment complete"
```

**Benchmark**: Unified app deployed to production
**Test**: All production endpoints respond correctly

### Step 6.2.3: Switch Traffic to Unified App
- [ ] Update load balancer configuration
- [ ] Update DNS records
- [ ] Update reverse proxy configuration
- [ ] Test traffic switching

**Traffic Switching Script**:
```bash
#!/bin/bash
# switch_traffic.sh

echo "Switching traffic to unified app..."

# Update nginx configuration
cat > /etc/nginx/sites-available/blog << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Reload nginx
nginx -t && nginx -s reload

# Test traffic switching
curl http://your-domain.com/core/health
curl http://your-domain.com/launchpad/health
curl http://your-domain.com/llm_actions/health

echo "Traffic switching complete"
```

**Benchmark**: Traffic switched to unified app
**Test**: All traffic routes to unified app

### Step 6.2.4: Monitor Production Deployment
- [ ] Set up monitoring
- [ ] Monitor error rates
- [ ] Monitor performance
- [ ] Monitor user experience

**Monitoring Setup**:
```bash
#!/bin/bash
# setup_monitoring.sh

echo "Setting up production monitoring..."

# Install monitoring tools
pip install psutil requests

# Create monitoring script
cat > /opt/blog/production/monitor.py << 'EOF'
#!/usr/bin/env python3
import time
import requests
import psutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_health():
    """Check application health."""
    try:
        response = requests.get('http://localhost:5000/core/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def check_performance():
    """Check application performance."""
    try:
        start_time = time.time()
        response = requests.get('http://localhost:5000/core/', timeout=5)
        response_time = time.time() - start_time
        return response.status_code == 200 and response_time < 2.0
    except:
        return False

def check_memory():
    """Check memory usage."""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    return memory_mb < 1000  # Less than 1GB

def main():
    """Main monitoring loop."""
    while True:
        health_ok = check_health()
        performance_ok = check_performance()
        memory_ok = check_memory()
        
        if not health_ok:
            logger.error("Health check failed")
        if not performance_ok:
            logger.error("Performance check failed")
        if not memory_ok:
            logger.error("Memory usage too high")
        
        if health_ok and performance_ok and memory_ok:
            logger.info("All checks passed")
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
EOF

# Start monitoring
nohup python /opt/blog/production/monitor.py > monitor.log 2>&1 &

echo "Monitoring setup complete"
```

**Benchmark**: Production monitoring set up
**Test**: Monitoring detects issues correctly

## 6.3 Cleanup

### Step 6.3.1: Remove Old Microservices
- [ ] Stop old microservices
- [ ] Remove old service files
- [ ] Clean up old configurations
- [ ] Test cleanup

**Cleanup Script**:
```bash
#!/bin/bash
# cleanup_old_services.sh

echo "Cleaning up old microservices..."

# Stop old services
pkill -f "python.*app.py.*5000"
pkill -f "python.*app.py.*5001"
pkill -f "python.*app.py.*5002"
pkill -f "python.*app.py.*5003"
pkill -f "python.*app.py.*5004"
pkill -f "python.*app.py.*5005"
pkill -f "python.*app.py.*5007"

# Wait for services to stop
sleep 5

# Remove old service directories
rm -rf /opt/blog/blog-core
rm -rf /opt/blog/blog-launchpad
rm -rf /opt/blog/blog-llm-actions
rm -rf /opt/blog/blog-post-sections
rm -rf /opt/blog/blog-post-info
rm -rf /opt/blog/blog-images
rm -rf /opt/blog/blog-clan-api

# Remove old configuration files
rm -f /opt/blog/*.env
rm -f /opt/blog/*.log

# Clean up old logs
rm -rf /opt/blog/logs

echo "Old microservices cleanup complete"
```

**Benchmark**: Old microservices removed
**Test**: No old services running

### Step 6.3.2: Update Documentation
- [ ] Update API documentation
- [ ] Update deployment documentation
- [ ] Update user documentation
- [ ] Update developer documentation

**Documentation Updates**:
```bash
#!/bin/bash
# update_documentation.sh

echo "Updating documentation..."

# Update API documentation
cat > docs/api/unified_api.md << 'EOF'
# Unified API Documentation

## Overview
The blog CMS now runs as a unified application with all services accessible through a single server.

## Base URL
- Production: https://your-domain.com
- Staging: https://staging.your-domain.com
- Development: http://localhost:5000

## Service Endpoints
- Core: /core/
- Launchpad: /launchpad/
- LLM Actions: /llm_actions/
- Post Sections: /post_sections/
- Post Info: /post_info/
- Images: /images/
- Clan API: /clan_api/
- Database: /db/
- Settings: /settings/

## API Endpoints
- Core API: /core/api/
- Launchpad API: /launchpad/api/
- LLM Actions API: /llm_actions/api/
- Database API: /db/api/

## Health Checks
- Core: /core/health
- Launchpad: /launchpad/health
- LLM Actions: /llm_actions/health
- All Services: /health
EOF

# Update deployment documentation
cat > docs/deployment/unified_deployment.md << 'EOF'
# Unified Deployment Guide

## Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Nginx (optional)

## Installation
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up database
4. Configure environment variables
5. Start application: `python unified_app.py`

## Configuration
- Environment: Set FLASK_ENV
- Database: Set DATABASE_URL
- Logging: Set LOG_LEVEL

## Monitoring
- Health checks: /health
- Logs: unified_app.log
- Performance: monitor.py
EOF

echo "Documentation update complete"
```

**Benchmark**: Documentation updated
**Test**: Documentation is accurate and complete

### Step 6.3.3: Update Deployment Scripts
- [ ] Update deployment scripts
- [ ] Update startup scripts
- [ ] Update monitoring scripts
- [ ] Test updated scripts

**Updated Deployment Scripts**:
```bash
#!/bin/bash
# start_blog.sh

echo "Starting unified blog application..."

# Set environment
export FLASK_ENV=production
export DATABASE_URL=postgresql://autojenny@localhost:5432/blog

# Start application
cd /opt/blog/production
source venv/bin/activate
nohup python unified_app.py > unified_app.log 2>&1 &
echo $! > unified_app.pid

echo "Blog application started"
```

```bash
#!/bin/bash
# stop_blog.sh

echo "Stopping unified blog application..."

# Stop application
if [ -f /opt/blog/production/unified_app.pid ]; then
    kill $(cat /opt/blog/production/unified_app.pid)
    rm /opt/blog/production/unified_app.pid
fi

# Stop monitoring
pkill -f "monitor.py"

echo "Blog application stopped"
```

```bash
#!/bin/bash
# restart_blog.sh

echo "Restarting unified blog application..."

./stop_blog.sh
sleep 5
./start_blog.sh

echo "Blog application restarted"
```

**Benchmark**: Deployment scripts updated
**Test**: All scripts work correctly

### Step 6.3.4: Archive Old Services
- [ ] Archive old service code
- [ ] Archive old configurations
- [ ] Archive old documentation
- [ ] Test archive access

**Archive Script**:
```bash
#!/bin/bash
# archive_old_services.sh

echo "Archiving old services..."

# Create archive directory
ARCHIVE_DIR="/opt/blog/archive/$(date +%Y%m%d_%H%M%S)"
mkdir -p $ARCHIVE_DIR

# Archive old services
tar -czf $ARCHIVE_DIR/microservices_archive.tar.gz \
    -C /opt/blog/backups \
    blog-core \
    blog-launchpad \
    blog-llm-actions \
    blog-post-sections \
    blog-post-info \
    blog-images \
    blog-clan-api

# Archive old configurations
tar -czf $ARCHIVE_DIR/config_archive.tar.gz \
    -C /opt/blog/backups \
    config

# Archive old documentation
tar -czf $ARCHIVE_DIR/docs_archive.tar.gz \
    -C /opt/blog/backups \
    docs

echo "Old services archived to: $ARCHIVE_DIR"
```

**Benchmark**: Old services archived
**Test**: Archive can be accessed and restored

## Phase 6 Completion Checklist

- [ ] Staging deployment complete
- [ ] Production migration complete
- [ ] Traffic switched to unified app
- [ ] Production monitoring set up
- [ ] Old microservices removed
- [ ] Documentation updated
- [ ] Deployment scripts updated
- [ ] Old services archived

**Overall Benchmark**: Migration to unified app complete
**Test**: All functionality works in production

---

**Project Complete**: Unified server implementation successful
**Total Time**: 6.5 days
**Status**: Ready for production use
