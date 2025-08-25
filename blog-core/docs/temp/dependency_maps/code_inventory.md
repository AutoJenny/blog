# Code Inventory and Dependencies Analysis

**Date:** 2025-07-17  
**Purpose:** Comprehensive inventory of all Python files and their dependencies for project reorganization  
**Status:** Phase 1, Step 2 - Code Inventory and Dependencies  

---

## Application Structure Overview

The blog system is organized as a Flask application with the following structure:

```
/blog/
├── app.py                    # Main application entry point
├── config.py                 # Configuration management
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── db.py                # Database connection utilities
│   ├── main/                # Main routes and pages
│   ├── blog/                # Blog-specific functionality
│   ├── llm/                 # LLM integration
│   ├── workflow/            # Workflow management
│   ├── api/                 # API endpoints
│   ├── database/            # Database management
│   ├── preview/             # Preview system
│   ├── services/            # Shared services
│   ├── utils/               # Utility functions
│   ├── errors/              # Error handling
│   └── templates/           # HTML templates
├── modules/                 # External modules
├── scripts/                 # Utility scripts
└── docs/                    # Documentation
```

---

## Core Application Files

### Root Level Files

#### `app.py` - Main Application Entry Point
**Purpose:** Main Flask application entry point and configuration  
**Used by:** All stages  
**Dependencies:**
- Flask
- config.py
- app.main.bp
- app.blog.bp
- app.llm.bp
- app.workflow.init_workflow

**New Project Assignment:**
- **blog-core:** Main application factory and configuration

#### `config.py` - Configuration Management
**Purpose:** Application configuration and environment variable management  
**Used by:** All stages  
**Dependencies:**
- os
- dotenv
- Environment variables

**New Project Assignment:**
- **blog-core:** Configuration management

---

## Application Modules

### `app/__init__.py` - Flask App Factory
**Purpose:** Flask application factory and blueprint registration  
**Used by:** All stages  
**Dependencies:**
- Flask
- Flask-CORS
- Flask-Caching
- Flask-Migrate
- Celery
- app.db.get_db_conn
- All blueprint modules

**New Project Assignment:**
- **blog-core:** Application factory and blueprint management

### `app/db.py` - Database Connection Utilities
**Purpose:** Database connection management and utilities  
**Used by:** All stages  
**Dependencies:**
- psycopg2
- psycopg2.extras.RealDictCursor
- dotenv
- os

**New Project Assignment:**
- **blog-core:** Database connection utilities

---

## Main Application Modules

### `app/main/` - Main Routes and Pages
**Purpose:** Main application routes, home page, and general functionality  
**Used by:** All stages  
**Files:**
- `__init__.py` - Blueprint initialization
- `routes.py` - Main routes and pages
- `context_processors.py` - Template context processors

**Dependencies:**
- Flask
- psycopg2
- dotenv
- app.database.routes.get_db_conn
- app.utils.decorators

**New Project Assignment:**
- **blog-core:** Main application routes and pages

### `app/blog/` - Blog-Specific Functionality
**Purpose:** Blog post management and display  
**Used by:** All stages  
**Files:**
- `__init__.py` - Blueprint initialization
- `routes.py` - Blog routes
- `fields.py` - Workflow field definitions

**Dependencies:**
- Flask
- psycopg2
- dotenv
- slugify
- humanize
- pytz
- app.llm.services.LLMService
- app.utils.decorators

**New Project Assignment:**
- **blog-core:** Blog post management and display

---

## LLM Integration Module

### `app/llm/` - LLM Integration
**Purpose:** LLM service integration and prompt management  
**Used by:** All stages  
**Files:**
- `__init__.py` - Blueprint initialization
- `routes.py` - LLM routes
- `services.py` - LLM service implementation
- `actions/` - LLM action definitions
- `chains.py` - LLM processing chains

**Dependencies:**
- Flask
- httpx
- requests
- psycopg2
- app.database.routes.get_db_conn
- app.blog.fields.WORKFLOW_FIELDS
- app.utils.decorators

**New Project Assignment:**
- **blog-core:** LLM service and prompt management
- **All projects:** Read access to LLM services

---

## Workflow Management Module

### `app/workflow/` - Workflow Management
**Purpose:** Workflow stage management and UI  
**Used by:** Planning, Writing, Structuring stages  
**Files:**
- `__init__.py` - Blueprint initialization and workflow setup
- `routes.py` - Workflow routes
- `navigation.py` - Workflow navigation (deprecated)

**Dependencies:**
- Flask
- psycopg2
- app.db.get_db_conn
- app.api.workflow.decorators
- modules.nav.services.get_workflow_context
- app.services.shared
- app.llm.services.execute_llm_request

**New Project Assignment:**
- **blog-planning:** Planning stage workflow
- **blog-writing:** Writing stage workflow
- **blog-structuring:** Structuring stage workflow

---

## API Module

### `app/api/` - API Endpoints
**Purpose:** RESTful API endpoints for all functionality  
**Used by:** All stages  
**Files:**
- `__init__.py` - API blueprint initialization
- `base.py` - Base API blueprint class
- `routes.py` - General API routes
- `workflow/` - Workflow API endpoints
- `llm.py` - LLM API endpoints (deprecated)
- `v1/` - Version 1 API endpoints (deprecated)

**Dependencies:**
- Flask
- marshmallow
- flask_jwt_extended
- flask_cors
- flasgger
- psycopg2
- app.database.routes.get_db_conn
- app.llm.services.LLMService

**New Project Assignment:**
- **blog-core:** Base API functionality
- **blog-planning:** Planning stage APIs
- **blog-writing:** Writing stage APIs
- **blog-structuring:** Structuring stage APIs
- **blog-images:** Image management APIs
- **blog-publishing:** Publishing APIs

### `app/api/workflow/` - Workflow API
**Purpose:** Workflow-specific API endpoints  
**Used by:** Planning, Writing, Structuring stages  
**Files:**
- `__init__.py` - Workflow API blueprint
- `routes.py` - Basic workflow routes
- `step_formats.py` - Step format management
- `format_routes.py` - Format system routes
- `steps.py` - Step management routes
- `formats.py` - Format management
- `stage_formats.py` - Stage format management
- `post_formats.py` - Post format management
- `decorators.py` - API decorators

**Dependencies:**
- Flask
- psycopg2
- app.db.get_db_conn
- app.llm.services.execute_llm_request
- app.utils.decorators

**New Project Assignment:**
- **blog-planning:** Planning stage workflow APIs
- **blog-writing:** Writing stage workflow APIs
- **blog-structuring:** Structuring stage workflow APIs

---

## Database Management Module

### `app/database/` - Database Management
**Purpose:** Database management and utilities  
**Used by:** All stages  
**Files:**
- `__init__.py` - Module initialization
- `routes.py` - Database management routes

**Dependencies:**
- Flask
- psycopg2
- dotenv
- subprocess
- pathlib
- json
- logging

**New Project Assignment:**
- **blog-core:** Database management utilities

---

## Preview System Module

### `app/preview/` - Preview System
**Purpose:** Post preview functionality  
**Used by:** All stages  
**Files:**
- `__init__.py` - Blueprint initialization
- Preview functionality

**Dependencies:**
- Flask
- psycopg2
- app.db.get_db_conn

**New Project Assignment:**
- **blog-workflow:** Preview system (shared across planning, writing, structuring)

---

## Services Module

### `app/services/` - Shared Services
**Purpose:** Shared business logic and services  
**Used by:** All stages  
**Files:**
- `__init__.py` - Module initialization
- `llm_service.py` - LLM service implementation
- `shared.py` - Shared utilities

**Dependencies:**
- psycopg2
- app.db.get_db_conn
- Various utility libraries

**New Project Assignment:**
- **blog-core:** Shared services and utilities

---

## Utilities Module

### `app/utils/` - Utility Functions
**Purpose:** Shared utility functions and decorators  
**Used by:** All stages  
**Files:**
- `__init__.py` - Module initialization
- `decorators.py` - Utility decorators
- Other utility files

**Dependencies:**
- Flask
- functools
- Various utility libraries

**New Project Assignment:**
- **blog-core:** Utility functions and decorators

---

## Error Handling Module

### `app/errors/` - Error Handling
**Purpose:** Application error handling  
**Used by:** All stages  
**Files:**
- `__init__.py` - Module initialization
- `handlers.py` - Error handlers

**Dependencies:**
- Flask

**New Project Assignment:**
- **blog-core:** Error handling

---

## External Modules

### `modules/` - External Modules
**Purpose:** External modules and integrations  
**Used by:** All stages  
**Files:**
- `nav/` - Navigation module
- `llm_panel/` - LLM panel module

**Dependencies:**
- Flask
- Various utility libraries

**New Project Assignment:**
- **blog-core:** External modules

---

## Scripts

### `scripts/` - Utility Scripts
**Purpose:** Utility scripts for development and maintenance  
**Used by:** Development and maintenance  
**Files:**
- `backup_database.py` - Database backup
- `check_dependencies.py` - Dependency checking
- `dev/restart_flask_dev.sh` - Development server restart
- `llm/` - LLM-related scripts

**Dependencies:**
- Various system utilities
- psycopg2
- dotenv

**New Project Assignment:**
- **blog-core:** Utility scripts

---

## Import Dependencies Analysis

### Critical Dependencies

#### Database Connection Pattern
**Pattern:** Multiple files implement their own `get_db_conn()` function
**Files with this pattern:**
- `app/main/routes.py`
- `app/blog/routes.py`
- `app/database/routes.py`
- `app/llm/routes.py`

**Issue:** Code duplication and potential inconsistency
**Solution:** Centralize in `app/db.py` and import from there

#### Environment Variable Loading
**Pattern:** Multiple files load environment variables independently
**Files with this pattern:**
- `app/main/routes.py`
- `app/blog/routes.py`
- `app/database/routes.py`
- `app/llm/routes.py`

**Issue:** Inconsistent environment variable loading
**Solution:** Centralize in `config.py` and use Flask config

#### LLM Service Integration
**Pattern:** Multiple files import and use LLM services
**Files with this pattern:**
- `app/blog/routes.py`
- `app/llm/routes.py`
- `app/api/routes.py`
- `app/workflow/routes.py`

**Issue:** Scattered LLM integration
**Solution:** Centralize in `app/llm/services.py`

---

## Stage-Specific Code Mapping

### Planning Stage (blog-planning)
**Primary Files:**
- `app/workflow/routes.py` (planning-specific routes)
- `app/api/workflow/` (planning API endpoints)
- Templates for planning stage

**Dependencies:**
- `app/db.py` (database connection)
- `app/llm/services.py` (LLM processing)
- `app/services/shared.py` (shared utilities)

### Writing Stage (blog-writing)
**Primary Files:**
- `app/workflow/routes.py` (writing-specific routes)
- `app/api/workflow/` (writing API endpoints)
- Templates for writing stage

**Dependencies:**
- `app/db.py` (database connection)
- `app/llm/services.py` (LLM processing)
- `app/services/shared.py` (shared utilities)

### Structuring Stage (blog-structuring)
**Primary Files:**
- `app/workflow/routes.py` (structuring-specific routes)
- `app/api/workflow/` (structuring API endpoints)
- Templates for structuring stage

**Dependencies:**
- `app/db.py` (database connection)
- `app/llm/services.py` (LLM processing)
- `app/services/shared.py` (shared utilities)

### Images Stage (blog-images)
**Primary Files:**
- `app/api/routes.py` (image generation endpoints)
- `app/api/v1/images/` (image management endpoints)
- Templates for image management

**Dependencies:**
- `app/db.py` (database connection)
- Image processing libraries
- LLM services for prompt generation

### Publishing Stage (blog-publishing)
**Primary Files:**
- Publishing-specific routes (to be created)
- Publishing API endpoints (to be created)
- Templates for publishing

**Dependencies:**
- `app/db.py` (database connection)
- Publishing APIs (clan.com, social media)
- Content transformation utilities

---

## Shared Code Analysis

### Core Shared Components
**Components that must be shared across all projects:**

1. **Database Connection (`app/db.py`)**
   - All projects need database access
   - Must be consistent across projects

2. **Configuration Management (`config.py`)**
   - Environment variables and settings
   - Must be accessible to all projects

3. **LLM Services (`app/llm/services.py`)**
   - LLM processing functionality
   - Used by all content generation stages

4. **Utility Functions (`app/utils/`)**
   - Common utility functions
   - Used across multiple projects

5. **Error Handling (`app/errors/`)**
   - Consistent error handling
   - Used across all projects

### Stage-Specific Components
**Components that can be isolated per project:**

1. **Workflow Routes (`app/workflow/routes.py`)**
   - Different UI and logic per stage
   - Can be isolated per project

2. **API Endpoints (`app/api/workflow/`)**
   - Stage-specific API functionality
   - Can be isolated per project

3. **Templates (`app/templates/workflow/`)**
   - Stage-specific UI templates
   - Can be isolated per project

4. **Static Files (`app/static/js/workflow/`)**
   - Stage-specific JavaScript
   - Can be isolated per project

---

## Migration Strategy

### Phase 1: Core Infrastructure
1. **Extract shared components** to `blog-core`
2. **Centralize database connection** in `app/db.py`
3. **Standardize configuration** in `config.py`
4. **Create shared utility modules**

### Phase 2: Stage Isolation
1. **Extract planning stage** to `blog-planning`
2. **Extract writing stage** to `blog-writing`
3. **Extract structuring stage** to `blog-structuring`
4. **Extract images stage** to `blog-images`
5. **Extract publishing stage** to `blog-publishing`

### Phase 3: Integration
1. **Establish cross-project communication**
2. **Test end-to-end workflows**
3. **Validate data consistency**
4. **Performance optimization**

---

**Status:** Step 2 Complete - Code inventory and dependencies documented  
**Next Step:** Step 3 - Configuration Analysis 