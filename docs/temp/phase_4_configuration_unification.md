# Phase 4: Configuration Unification - Detailed Implementation

## 4.1 Environment Configuration

### Step 4.1.1: Analyze Current Configuration Files
- [ ] List all configuration files from each service
- [ ] Identify configuration conflicts
- [ ] Document configuration dependencies
- [ ] Plan unification strategy

**Current Configuration Files Analysis**:
```
blog-core/assistant_config.env:
- DATABASE_URL=postgresql://autojenny@localhost:5432/blog
- SECRET_KEY=your-secret-key-here-change-in-production
- DEBUG=True

blog-launchpad/assistant_config.env:
- DATABASE_URL=postgresql://autojenny@localhost:5432/blog
- SECRET_KEY=your-secret-key-here-change-in-production
- DEBUG=True

blog-llm-actions/config.env:
- DATABASE_URL=postgresql://autojenny@localhost:5432/blog
- SECRET_KEY=dev-secret-key
- DEBUG=True

blog-post-sections/assistant_config.env:
- DATABASE_URL=postgresql://autojenny@localhost:5432/blog
- SECRET_KEY=your-secret-key-here-change-in-production
- DEBUG=True

blog-post-info/assistant_config.env:
- DATABASE_URL=postgresql://autojenny@localhost:5432/blog
- SECRET_KEY=your-secret-key-here-change-in-production
- DEBUG=True

blog-images/assistant_config.env:
- DATABASE_URL=postgresql://autojenny@localhost:5432/blog
- SECRET_KEY=your-secret-key-here-change-in-production
- DEBUG=True

blog-clan-api/assistant_config.env:
- DATABASE_URL=postgresql://autojenny@localhost:5432/blog
- SECRET_KEY=your-secret-key-here-change-in-production
- DEBUG=True
```

**Benchmark**: Configuration files catalogued and conflicts identified
**Test**: `find . -name "*.env" -type f` lists all configuration files

### Step 4.1.2: Create Unified Configuration System
- [ ] Create `config/` directory structure
- [ ] Create unified configuration files
- [ ] Set up configuration loading
- [ ] Test configuration access

**Directory Structure**:
```
config/
├── __init__.py
├── settings.py              # Configuration classes
├── assistant_config.env     # Environment variables
├── development.env          # Development settings
├── production.env           # Production settings
└── staging.env              # Staging settings
```

**Benchmark**: Unified configuration system created
**Test**: `ls -la config/` shows organized structure

### Step 4.1.3: Create Configuration Classes
- [ ] Create `config/settings.py` with configuration classes
- [ ] Set up environment-specific configurations
- [ ] Add configuration validation
- [ ] Test configuration loading

**Configuration Classes**:
```python
# config/settings.py
import os
from dotenv import load_dotenv

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database configuration
    DB_NAME = os.getenv('DB_NAME', 'blog')
    DB_USER = os.getenv('DB_USER', 'autojenny')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    # Service-specific configurations
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'unified_app.log')
    
    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class StagingConfig(Config):
    """Staging configuration."""
    DEBUG = True
    LOG_LEVEL = 'INFO'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}
```

**Benchmark**: Configuration classes created and working
**Test**: `python -c "from config.settings import config; print(config['default'].DATABASE_URL)"`

### Step 4.1.4: Create Unified Environment File
- [ ] Create `config/assistant_config.env` with all settings
- [ ] Consolidate all environment variables
- [ ] Set up environment-specific values
- [ ] Test environment loading

**Unified Environment File**:
```env
# config/assistant_config.env
# Database Configuration
DATABASE_URL=postgresql://autojenny@localhost:5432/blog
DB_NAME=blog
DB_USER=autojenny
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

# Application Configuration
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
LOG_LEVEL=INFO
LOG_FILE=unified_app.log

# CORS Configuration
CORS_ORIGINS=*

# Service-specific Configuration
OLLAMA_API_URL=http://localhost:11434
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=

# Environment
FLASK_ENV=development
```

**Benchmark**: Unified environment file created
**Test**: `python -c "from dotenv import load_dotenv; load_dotenv('config/assistant_config.env'); print('Environment loaded')"`

### Step 4.1.5: Update Configuration Loading
- [ ] Update all services to use unified configuration
- [ ] Update database connection to use unified config
- [ ] Update all configuration references
- [ ] Test configuration loading

**Configuration Loading Updates**:
```python
# services/database.py
from config.settings import config
import os

def get_db_conn():
    """Unified database connection for all services."""
    try:
        # Load configuration
        config_class = config[os.getenv('FLASK_ENV', 'default')]
        
        # Get database URL
        database_url = config_class.DATABASE_URL
        if database_url:
            return psycopg.connect(database_url)
        
        # Fallback to individual config values
        return psycopg.connect(
            dbname=config_class.DB_NAME,
            user=config_class.DB_USER,
            password=config_class.DB_PASSWORD,
            host=config_class.DB_HOST,
            port=config_class.DB_PORT
        )
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise
```

**Benchmark**: All services use unified configuration
**Test**: All services load configuration without errors

## 4.2 CORS Removal

### Step 4.2.1: Analyze Current CORS Configuration
- [ ] List all CORS configurations from each service
- [ ] Identify CORS dependencies
- [ ] Document CORS usage
- [ ] Plan removal strategy

**Current CORS Configuration Analysis**:
```
blog-core/app.py:
- CORS(app, origins=["http://localhost:5002", "http://localhost:5005"], supports_credentials=True)

blog-launchpad/app.py:
- CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003", "http://localhost:5004"])

blog-llm-actions/app.py:
- CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003", "http://localhost:5004"])

blog-post-sections/app.py:
- CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003", "http://localhost:5004"])

blog-post-info/app.py:
- CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003", "http://localhost:5004"])

blog-images/app.py:
- CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003", "http://localhost:5004"])

blog-clan-api/app.py:
- CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003", "http://localhost:5004"])
```

**Benchmark**: CORS configurations catalogued and dependencies identified
**Test**: `grep -r "CORS" . --include="*.py"` lists all CORS configurations

### Step 4.2.2: Remove CORS Configurations
- [ ] Remove CORS imports from all services
- [ ] Remove CORS configurations from all services
- [ ] Update unified app to not use CORS
- [ ] Test without CORS

**CORS Removal Steps**:
- [ ] Remove `from flask_cors import CORS` from all services
- [ ] Remove `CORS(app, ...)` configurations from all services
- [ ] Update `unified_app.py` to not use CORS
- [ ] Remove `flask-cors` from requirements.txt

**Unified App Update**:
```python
# unified_app.py
from flask import Flask, render_template, jsonify, request
# Remove: from flask_cors import CORS
import os
import logging

def create_app():
    app = Flask(__name__, 
                template_folder="templates", 
                static_folder="static")
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')
    
    # Remove: CORS(app, origins=["*"], supports_credentials=True)
    
    # Register blueprints...
    
    return app
```

**Benchmark**: All CORS configurations removed
**Test**: All services start without CORS errors

### Step 4.2.3: Update JavaScript API Calls
- [ ] Update all JavaScript to use same-origin requests
- [ ] Remove cross-origin headers
- [ ] Update fetch calls to use relative URLs
- [ ] Test API functionality

**JavaScript API Call Updates**:
```javascript
// Before
const response = await fetch('http://localhost:5002/api/run-llm', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    },
    body: JSON.stringify(payload)
});

// After
const response = await fetch('/llm_actions/api/run-llm', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
});
```

**Benchmark**: All JavaScript API calls updated to use same-origin requests
**Test**: All API calls work without CORS errors

### Step 4.2.4: Test Same-Origin Functionality
- [ ] Test all API endpoints work with same-origin requests
- [ ] Test all JavaScript functionality works
- [ ] Test all cross-service communication works
- [ ] Verify no CORS errors

**Test Commands**:
```bash
# Test API endpoints
curl http://localhost:5000/core/api/posts
curl http://localhost:5000/launchpad/api/posts
curl http://localhost:5000/llm_actions/api/run-llm

# Test JavaScript functionality
# Open browser and test all interactive features
```

**Benchmark**: All functionality works without CORS
**Test**: All API calls and JavaScript functionality work

## 4.3 Logging Unification

### Step 4.3.1: Analyze Current Logging Configuration
- [ ] List all logging configurations from each service
- [ ] Identify logging conflicts
- [ ] Document logging dependencies
- [ ] Plan unification strategy

**Current Logging Configuration Analysis**:
```
blog-core/app.py:
- logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('blog-core.log')])

blog-launchpad/app.py:
- logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('blog-launchpad.log')])

blog-llm-actions/app.py:
- logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('blog-llm-actions.log')])

blog-post-sections/app.py:
- logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('blog-post-sections.log')])

blog-post-info/app.py:
- logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('blog-post-info.log')])

blog-images/app.py:
- logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('blog-images.log')])

blog-clan-api/app.py:
- logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('blog-clan-api.log')])
```

**Benchmark**: Logging configurations catalogued and conflicts identified
**Test**: `grep -r "logging.basicConfig" . --include="*.py"` lists all logging configurations

### Step 4.3.2: Create Unified Logging System
- [ ] Create `utils/logging.py` with unified logging configuration
- [ ] Set up centralized logging
- [ ] Add log rotation
- [ ] Test logging functionality

**Unified Logging System**:
```python
# utils/logging.py
import logging
import os
from logging.handlers import RotatingFileHandler
from config.settings import config

def setup_logging(app):
    """Set up unified logging for the application."""
    if not app.debug and not app.testing:
        # Production logging
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/unified_app.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Unified app startup')
```

**Benchmark**: Unified logging system created
**Test**: `python -c "from utils.logging import setup_logging; print('Logging system ready')"`

### Step 4.3.3: Update All Services to Use Unified Logging
- [ ] Remove individual logging configurations
- [ ] Update all services to use unified logging
- [ ] Test logging functionality
- [ ] Verify log output

**Logging Updates**:
```python
# unified_app.py
from utils.logging import setup_logging

def create_app():
    app = Flask(__name__, 
                template_folder="templates", 
                static_folder="static")
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')
    
    # Set up unified logging
    setup_logging(app)
    
    # Register blueprints...
    
    return app
```

**Benchmark**: All services use unified logging
**Test**: All services log to unified log file

## 4.4 Error Handling Unification

### Step 4.4.1: Analyze Current Error Handling
- [ ] List all error handling from each service
- [ ] Identify error handling patterns
- [ ] Document error handling dependencies
- [ ] Plan unification strategy

**Current Error Handling Analysis**:
```
blog-core/app.py:
- Basic error handling in routes
- No centralized error handling

blog-launchpad/app.py:
- Basic error handling in routes
- No centralized error handling

blog-llm-actions/app.py:
- Basic error handling in routes
- No centralized error handling

blog-post-sections/app.py:
- Basic error handling in routes
- No centralized error handling

blog-post-info/app.py:
- Basic error handling in routes
- No centralized error handling

blog-images/app.py:
- Basic error handling in routes
- No centralized error handling

blog-clan-api/app.py:
- Basic error handling in routes
- No centralized error handling
```

**Benchmark**: Error handling patterns catalogued
**Test**: `grep -r "except" . --include="*.py"` lists all error handling

### Step 4.4.2: Create Unified Error Handling
- [ ] Create `utils/errors.py` with unified error handling
- [ ] Set up centralized error handlers
- [ ] Add error logging
- [ ] Test error handling

**Unified Error Handling**:
```python
# utils/errors.py
from flask import render_template, jsonify
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Register unified error handlers for the application."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        logger.error(f"404 error: {error}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        logger.error(f"403 error: {error}")
        return render_template('errors/403.html'), 403
```

**Benchmark**: Unified error handling created
**Test**: `python -c "from utils.errors import register_error_handlers; print('Error handling ready')"`

### Step 4.4.3: Update All Services to Use Unified Error Handling
- [ ] Remove individual error handling
- [ ] Update all services to use unified error handling
- [ ] Test error handling functionality
- [ ] Verify error responses

**Error Handling Updates**:
```python
# unified_app.py
from utils.errors import register_error_handlers

def create_app():
    app = Flask(__name__, 
                template_folder="templates", 
                static_folder="static")
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')
    
    # Set up unified logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints...
    
    return app
```

**Benchmark**: All services use unified error handling
**Test**: All services handle errors consistently

## Phase 4 Completion Checklist

- [ ] All configuration files unified
- [ ] All CORS configurations removed
- [ ] All logging unified
- [ ] All error handling unified
- [ ] All services use unified configuration
- [ ] All tests passing

**Overall Benchmark**: All configuration unified and working
**Test**: All services start and run with unified configuration

---

**Next Phase**: Phase 5 - Testing and Validation
**Estimated Time**: 0.5 days
**Dependencies**: Phase 4 complete
