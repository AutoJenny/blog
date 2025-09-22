# Phase 1: Foundation Setup - Detailed Implementation

## 1.1 Create Unified Application Structure

### Step 1.1.1: Create Main Application File
- [ ] Create `unified_app.py` with basic Flask structure
- [ ] Set up CORS configuration
- [ ] Configure logging
- [ ] Set up error handling

**Code Template**:
```python
# unified_app.py
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import logging
from datetime import datetime

def create_app():
    app = Flask(__name__, 
                template_folder="templates", 
                static_folder="static")
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')
    
    # Enable CORS for all routes
    CORS(app, origins=["*"], supports_credentials=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('unified_app.log')
        ]
    )
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
```

**Benchmark**: Main app file created and runs without errors
**Test**: `python unified_app.py` starts Flask server on port 5000

### Step 1.1.2: Create Directory Structure
- [ ] Create `blueprints/` directory
- [ ] Create `services/` directory
- [ ] Create `utils/` directory
- [ ] Create `config/` directory
- [ ] Create `templates/` directory
- [ ] Create `static/` directory

**Commands**:
```bash
mkdir -p blueprints services utils config templates static
mkdir -p templates/core templates/launchpad templates/llm_actions
mkdir -p static/css static/js static/images
```

**Benchmark**: All directories created
**Test**: `ls -la blueprints/ services/ utils/ config/ templates/ static/`

### Step 1.1.3: Create Blueprint Structure
- [ ] Create `blueprints/__init__.py`
- [ ] Create `blueprints/core.py`
- [ ] Create `blueprints/launchpad.py`
- [ ] Create `blueprints/llm_actions.py`
- [ ] Create `blueprints/post_sections.py`
- [ ] Create `blueprints/post_info.py`
- [ ] Create `blueprints/images.py`
- [ ] Create `blueprints/clan_api.py`
- [ ] Create `blueprints/database.py`
- [ ] Create `blueprints/settings.py`

**Benchmark**: All blueprint files created
**Test**: `ls -la blueprints/*.py` shows all blueprint files

## 1.2 Consolidate Dependencies

### Step 1.2.1: Analyze Current Dependencies
- [ ] Extract dependencies from all `requirements.txt` files
- [ ] Identify version conflicts
- [ ] List all unique packages needed

**Current Dependencies Analysis**:
```
blog-core: Flask==3.0.0, flask-cors==4.0.0, psycopg2-binary==2.9.9, python-dotenv==1.0.0, humanize==4.9.0, pytz==2024.1, requests==2.31.0, markdown==3.5.2
blog-launchpad: Flask==2.3.3, psycopg2-binary==2.9.7, requests==2.31.0, python-dotenv==1.0.0, humanize==4.8.0, pytz==2023.3, facebook-sdk==3.1.0
blog-llm-actions: Flask==3.0.0, Flask-CORS==4.0.0, python-dotenv==1.0.0, requests==2.31.0, psycopg2-binary==2.9.9
blog-post-sections: Flask==3.0.0, Flask-CORS==4.0.0, python-dotenv==1.0.0, requests==2.31.0, psycopg2-binary==2.9.9
blog-post-info: Flask==3.0.0, Flask-CORS==4.0.0, psycopg2-binary==2.9.9, python-dotenv==1.0.0, requests==2.31.0
blog-images: Flask==3.0.0, psycopg2-binary==2.9.9, python-dotenv==1.0.0, Pillow==10.1.0
blog-clan-api: Flask==2.3.3, requests==2.31.0
```

### Step 1.2.2: Create Unified Requirements
- [ ] Create `requirements.txt` with resolved versions
- [ ] Use latest compatible versions
- [ ] Include all necessary packages

**Unified Requirements**:
```txt
Flask==3.0.0
Flask-CORS==4.0.0
psycopg[binary]==3.1.0
python-dotenv==1.0.0
humanize==4.9.0
pytz==2024.1
requests==2.31.0
markdown==3.5.2
facebook-sdk==3.1.0
Pillow==10.1.0
```

**Benchmark**: Single requirements.txt with resolved versions
**Test**: `pip install -r requirements.txt` succeeds without conflicts

### Step 1.2.3: Install Dependencies
- [ ] Install unified requirements
- [ ] Verify all packages installed correctly
- [ ] Test imports for all packages

**Commands**:
```bash
pip install -r requirements.txt
python -c "import flask, psycopg, requests, markdown, PIL; print('All imports successful')"
```

**Benchmark**: All dependencies installed and importable
**Test**: All import statements work without errors

## 1.3 Database Connection Unification

### Step 1.3.1: Create Unified Database Service
- [ ] Create `services/__init__.py`
- [ ] Create `services/database.py` with unified connection logic
- [ ] Handle psycopg2 to psycopg3 migration
- [ ] Add connection pooling
- [ ] Add error handling

**Code Template**:
```python
# services/database.py
import psycopg
from psycopg.rows import dict_row
import os
from dotenv import dotenv_values
import logging

logger = logging.getLogger(__name__)

def get_db_conn():
    """Unified database connection for all services."""
    try:
        # Load configuration
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'assistant_config.env')
        config = dotenv_values(config_path)
        
        database_url = config.get('DATABASE_URL')
        if database_url:
            return psycopg.connect(database_url)
        
        # Fallback to environment variables
        return psycopg.connect(
            dbname=os.getenv('DB_NAME', 'blog'),
            user=os.getenv('DB_USER', 'autojenny'),
            password=os.getenv('DB_PASSWORD', ''),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def get_db_cursor():
    """Get database cursor with dict_row factory."""
    conn = get_db_conn()
    return conn.cursor(row_factory=dict_row)
```

**Benchmark**: Unified database service created
**Test**: `python -c "from services.database import get_db_conn; conn = get_db_conn(); print('Connected')"`

### Step 1.3.2: Create Configuration System
- [ ] Create `config/__init__.py`
- [ ] Create `config/settings.py` with unified configuration
- [ ] Create `config/assistant_config.env` with all settings
- [ ] Add environment variable handling

**Code Template**:
```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://autojenny@localhost:5432/blog')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Service-specific configurations
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
    
    # Database configuration
    DB_NAME = os.getenv('DB_NAME', 'blog')
    DB_USER = os.getenv('DB_USER', 'autojenny')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
```

**Benchmark**: Configuration system created
**Test**: `python -c "from config.settings import Config; print(Config.DATABASE_URL)"`

### Step 1.3.3: Test Database Connectivity
- [ ] Test connection from unified app
- [ ] Test all database operations
- [ ] Verify psycopg3 compatibility
- [ ] Test error handling

**Test Commands**:
```bash
python -c "from services.database import get_db_conn; conn = get_db_conn(); print('Connected')"
python -c "from services.database import get_db_cursor; cur = get_db_cursor(); cur.execute('SELECT 1'); print('Query successful')"
```

**Benchmark**: All database operations work through unified service
**Test**: All database tests pass

## Phase 1 Completion Checklist

- [ ] Unified application structure created
- [ ] All dependencies consolidated and installed
- [ ] Database connection unified
- [ ] Configuration system created
- [ ] All tests passing
- [ ] Documentation updated

**Overall Benchmark**: Foundation setup complete and ready for blueprint migration
**Test**: `python unified_app.py` starts successfully and can connect to database

---

**Next Phase**: Phase 2 - Blueprint Migration
**Estimated Time**: 1 day
**Dependencies**: Phase 1 complete
