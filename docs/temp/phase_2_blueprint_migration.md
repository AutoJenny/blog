# Phase 2: Blueprint Migration - Detailed Implementation

## 2.1 Core Blueprint (blog-core)

### Step 2.1.1: Create Core Blueprint Structure
- [ ] Create `blueprints/core.py` with basic structure
- [ ] Import necessary dependencies
- [ ] Set up blueprint registration
- [ ] Add error handling

**Code Template**:
```python
# blueprints/core.py
from flask import Blueprint, render_template, jsonify, request, redirect
from services.database import get_db_conn, get_db_cursor
from services.shared import get_all_posts_from_db
import logging

bp = Blueprint('core', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Main page with header and workflow navigation."""
    try:
        all_posts = get_all_posts_from_db()
        first_post_id = all_posts[0]['id'] if all_posts else 1
        return render_template('core/index.html', first_post_id=first_post_id)
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('core/error.html', error=str(e))

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "core"})
```

**Benchmark**: Core blueprint created and basic routes working
**Test**: `curl http://localhost:5000/core/` returns homepage

### Step 2.1.2: Migrate Workflow Routes
- [ ] Move workflow routes from `blog-core/app.py`
- [ ] Update route paths to use `/core/` prefix
- [ ] Update template references
- [ ] Test workflow functionality

**Routes to Migrate**:
- [ ] `@app.route('/workflow/')` → `@bp.route('/workflow/')`
- [ ] `@app.route('/workflow/posts/<int:post_id>/<stage>/<substage>/<step>')` → `@bp.route('/workflow/posts/<int:post_id>/<stage>/<substage>/<step>')`
- [ ] `@app.route('/workflow/posts/<int:post_id>/<stage>/<substage>')` → `@bp.route('/workflow/posts/<int:post_id>/<stage>/<substage>')`
- [ ] `@app.route('/workflow/posts/<int:post_id>')` → `@bp.route('/workflow/posts/<int:post_id>')`

**Benchmark**: All workflow routes migrated and working
**Test**: `curl http://localhost:5000/core/workflow/posts/53/planning/idea/provisional_title` returns workflow page

### Step 2.1.3: Migrate API Routes
- [ ] Move API routes from `blog-core/app.py`
- [ ] Update route paths to use `/core/` prefix
- [ ] Update database calls to use unified service
- [ ] Test API functionality

**API Routes to Migrate**:
- [ ] `@app.route('/api/posts')` → `@bp.route('/api/posts')`
- [ ] `@app.route('/api/workflow/posts/<int:post_id>/fields/status')` → `@bp.route('/api/workflow/posts/<int:post_id>/fields/status')`
- [ ] `@app.route('/api/llm-actions/content')` → `@bp.route('/api/llm-actions/content')`
- [ ] `@app.route('/api/llm-actions/config')` → `@bp.route('/api/llm-actions/config')`
- [ ] `@app.route('/api/llm-actions/actions')` → `@bp.route('/api/llm-actions/actions')`
- [ ] `@app.route('/api/llm-actions/test')` → `@bp.route('/api/llm-actions/test')`

**Benchmark**: All API routes migrated and working
**Test**: `curl http://localhost:5000/core/api/posts` returns posts data

### Step 2.1.4: Migrate Documentation Routes
- [ ] Move documentation routes from `blog-core/app.py`
- [ ] Update route paths to use `/core/` prefix
- [ ] Update template references
- [ ] Test documentation functionality

**Documentation Routes to Migrate**:
- [ ] `@app.route('/docs/')` → `@bp.route('/docs/')`
- [ ] `@app.route('/docs/<path:req_path>')` → `@bp.route('/docs/<path:req_path>')`
- [ ] `@app.route('/docs/view/<path:file_path>')` → `@bp.route('/docs/view/<path:file_path>')`

**Benchmark**: All documentation routes migrated and working
**Test**: `curl http://localhost:5000/core/docs/` returns documentation browser

## 2.2 Launchpad Blueprint (blog-launchpad)

### Step 2.2.1: Create Launchpad Blueprint Structure
- [ ] Create `blueprints/launchpad.py` with basic structure
- [ ] Import necessary dependencies
- [ ] Set up blueprint registration
- [ ] Add error handling

**Code Template**:
```python
# blueprints/launchpad.py
from flask import Blueprint, render_template, jsonify, request
from services.database import get_db_conn, get_db_cursor
import logging

bp = Blueprint('launchpad', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Launchpad homepage."""
    return render_template('launchpad/index.html')

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "launchpad"})
```

**Benchmark**: Launchpad blueprint created and basic routes working
**Test**: `curl http://localhost:5000/launchpad/` returns launchpad homepage

### Step 2.2.2: Migrate Syndication Routes
- [ ] Move syndication routes from `blog-launchpad/app.py`
- [ ] Update route paths to use `/launchpad/` prefix
- [ ] Update database calls to use unified service
- [ ] Test syndication functionality

**Syndication Routes to Migrate**:
- [ ] `@app.route('/syndication')` → `@bp.route('/syndication')`
- [ ] `@app.route('/syndication/dashboard')` → `@bp.route('/syndication/dashboard')`
- [ ] `@app.route('/syndication/facebook/product_post')` → `@bp.route('/syndication/facebook/product_post')`
- [ ] `@app.route('/syndication/facebook/blog_post')` → `@bp.route('/syndication/facebook/blog_post')`

**Benchmark**: All syndication routes migrated and working
**Test**: `curl http://localhost:5000/launchpad/syndication/facebook/product_post` returns product post page

### Step 2.2.3: Migrate API Routes
- [ ] Move API routes from `blog-launchpad/app.py`
- [ ] Update route paths to use `/launchpad/` prefix
- [ ] Update database calls to use unified service
- [ ] Test API functionality

**API Routes to Migrate**:
- [ ] `@app.route('/api/posts')` → `@bp.route('/api/posts')`
- [ ] `@app.route('/api/daily-product-posts/today-status')` → `@bp.route('/api/daily-product-posts/today-status')`
- [ ] `@app.route('/api/syndication/pieces')` → `@bp.route('/api/syndication/pieces')`
- [ ] `@app.route('/api/social-media/timeline')` → `@bp.route('/api/social-media/timeline')`
- [ ] `@app.route('/api/syndication/facebook/credentials')` → `@bp.route('/api/syndication/facebook/credentials')`

**Benchmark**: All API routes migrated and working
**Test**: `curl http://localhost:5000/launchpad/api/posts` returns posts data

## 2.3 LLM Actions Blueprint (blog-llm-actions)

### Step 2.3.1: Create LLM Actions Blueprint Structure
- [ ] Create `blueprints/llm_actions.py` with basic structure
- [ ] Import necessary dependencies
- [ ] Set up blueprint registration
- [ ] Add error handling

**Code Template**:
```python
# blueprints/llm_actions.py
from flask import Blueprint, render_template, jsonify, request
from services.database import get_db_conn, get_db_cursor
from services.llm import LLMService
import logging

bp = Blueprint('llm_actions', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """LLM Actions interface."""
    return render_template('llm_actions/index.html')

@bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "llm_actions"})
```

**Benchmark**: LLM Actions blueprint created and basic routes working
**Test**: `curl http://localhost:5000/llm_actions/` returns LLM actions interface

### Step 2.3.2: Migrate LLM API Routes
- [ ] Move LLM API routes from `blog-llm-actions/app.py`
- [ ] Update route paths to use `/llm_actions/` prefix
- [ ] Update database calls to use unified service
- [ ] Test LLM functionality

**LLM API Routes to Migrate**:
- [ ] `@app.route('/api/run-llm')` → `@bp.route('/api/run-llm')`
- [ ] `@app.route('/api/llm/actions')` → `@bp.route('/api/llm/actions')`
- [ ] `@app.route('/api/llm/config')` → `@bp.route('/api/llm/config')`
- [ ] `@app.route('/api/llm/test')` → `@bp.route('/api/llm/test')`
- [ ] `@app.route('/api/step-config/<stage>/<substage>/<step>')` → `@bp.route('/api/step-config/<stage>/<substage>/<step>')`

**Benchmark**: All LLM API routes migrated and working
**Test**: `curl http://localhost:5000/llm_actions/api/run-llm` returns LLM response

### Step 2.3.3: Migrate LLM Service Logic
- [ ] Move LLM service logic from `blog-llm-actions/app.py`
- [ ] Create `services/llm.py` for LLM functionality
- [ ] Update database calls to use unified service
- [ ] Test LLM processing

**LLM Service Logic to Migrate**:
- [ ] `class LLMService` → `services/llm.py`
- [ ] LLM configuration logic
- [ ] LLM processing logic
- [ ] LLM testing logic

**Benchmark**: LLM service logic migrated and working
**Test**: LLM processing works through unified service

## 2.4 Additional Blueprints

### Step 2.4.1: Create Post Sections Blueprint
- [ ] Create `blueprints/post_sections.py`
- [ ] Move routes from `blog-post-sections/app.py`
- [ ] Update database calls to use unified service
- [ ] Test post sections functionality

**Benchmark**: Post sections blueprint created and working
**Test**: `curl http://localhost:5000/post_sections/` returns post sections interface

### Step 2.4.2: Create Post Info Blueprint
- [ ] Create `blueprints/post_info.py`
- [ ] Move routes from `blog-post-info/app.py`
- [ ] Update database calls to use unified service
- [ ] Test post info functionality

**Benchmark**: Post info blueprint created and working
**Test**: `curl http://localhost:5000/post_info/` returns post info interface

### Step 2.4.3: Create Images Blueprint
- [ ] Create `blueprints/images.py`
- [ ] Move routes from `blog-images/app.py`
- [ ] Update database calls to use unified service
- [ ] Test image processing functionality

**Benchmark**: Images blueprint created and working
**Test**: `curl http://localhost:5000/images/` returns images interface

### Step 2.4.4: Create Clan API Blueprint
- [ ] Create `blueprints/clan_api.py`
- [ ] Move routes from `blog-clan-api/app.py`
- [ ] Update database calls to use unified service
- [ ] Test clan API functionality

**Benchmark**: Clan API blueprint created and working
**Test**: `curl http://localhost:5000/clan_api/` returns clan API interface

## 2.5 Database and Settings Blueprints

### Step 2.5.1: Create Database Blueprint
- [ ] Create `blueprints/database.py`
- [ ] Move database routes from `blog-core/routes.py`
- [ ] Update database calls to use unified service
- [ ] Test database functionality

**Benchmark**: Database blueprint created and working
**Test**: `curl http://localhost:5000/db/` returns database interface

### Step 2.5.2: Create Settings Blueprint
- [ ] Create `blueprints/settings.py`
- [ ] Move settings routes from `blog-core/settings.py`
- [ ] Update database calls to use unified service
- [ ] Test settings functionality

**Benchmark**: Settings blueprint created and working
**Test**: `curl http://localhost:5000/settings/` returns settings interface

## 2.6 Blueprint Registration

### Step 2.6.1: Register All Blueprints
- [ ] Update `unified_app.py` to register all blueprints
- [ ] Set up URL prefixes for each blueprint
- [ ] Test blueprint registration
- [ ] Verify all routes accessible

**Code Template**:
```python
# unified_app.py
from blueprints.core import bp as core_bp
from blueprints.launchpad import bp as launchpad_bp
from blueprints.llm_actions import bp as llm_actions_bp
from blueprints.post_sections import bp as post_sections_bp
from blueprints.post_info import bp as post_info_bp
from blueprints.images import bp as images_bp
from blueprints.clan_api import bp as clan_api_bp
from blueprints.database import bp as database_bp
from blueprints.settings import bp as settings_bp

def create_app():
    app = Flask(__name__, 
                template_folder="templates", 
                static_folder="static")
    
    # Register blueprints with URL prefixes
    app.register_blueprint(core_bp, url_prefix='/core')
    app.register_blueprint(launchpad_bp, url_prefix='/launchpad')
    app.register_blueprint(llm_actions_bp, url_prefix='/llm_actions')
    app.register_blueprint(post_sections_bp, url_prefix='/post_sections')
    app.register_blueprint(post_info_bp, url_prefix='/post_info')
    app.register_blueprint(images_bp, url_prefix='/images')
    app.register_blueprint(clan_api_bp, url_prefix='/clan_api')
    app.register_blueprint(database_bp, url_prefix='/db')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    return app
```

**Benchmark**: All blueprints registered and accessible
**Test**: All blueprint routes return 200 status codes

## Phase 2 Completion Checklist

- [ ] All blueprints created
- [ ] All routes migrated
- [ ] All database calls updated
- [ ] All API endpoints working
- [ ] All templates accessible
- [ ] All tests passing

**Overall Benchmark**: All microservices functionality available through unified app
**Test**: All original endpoints work with new URL prefixes

---

**Next Phase**: Phase 3 - Static Assets Consolidation
**Estimated Time**: 2 days
**Dependencies**: Phase 2 complete
