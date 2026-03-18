# BlogForge Architecture Overview

## Current Architecture (2025)

BlogForge has evolved from a monolithic structure to a microservice architecture. This document describes the current system structure and supersedes all previous monolithic documentation.

## Service Architecture

### Service Overview

| Service | Port | Directory | Purpose |
|---------|------|-----------|---------|
| **blog-core** | 5001 | `/blog-core` | Main orchestrator, workflow pages, navigation |
| **blog-llm-actions** | 5002 | `/blog-llm-actions` | LLM panel microservice (purple section) |
| **blog-post-sections** | 5003 | `/blog-post-sections` | Sections panel microservice (green section) |
| **blog** | 5000 | `/ZZblog` | Legacy monolithic service (deprecated) |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                blog-core (Port 5001)                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Main Workflow Page                      │    │
│  │  ┌─────────────────┐  ┌─────────────────────────────┐ │    │
│  │  │   Navigation    │  │      Content Area           │ │    │
│  │  │   (Header/Nav)  │  │  ┌─────────┐ ┌─────────────┐ │ │    │
│  │  └─────────────────┘  │  │ Purple  │ │   Green     │ │ │    │
│  │                       │  │  LLM    │ │  Sections   │ │ │    │
│  │                       │  │ Panel   │ │   Panel     │ │ │    │
│  │                       │  │(iframe) │ │  (iframe)   │ │ │    │
│  │                       │  └─────────┘ └─────────────┘ │ │    │
│  │                       └─────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─────────────────┐
                      │                 │
                      ▼                 ▼
        ┌─────────────────────┐ ┌─────────────────────┐
        │ blog-llm-actions    │ │ blog-post-sections  │
        │ (Port 5002)         │ │ (Port 5003)         │
        │                     │ │                     │
        │ • LLM Configuration │ │ • Section Management│
        │ • Field Selectors   │ │ • Drag & Drop       │
        │ • Context Setup     │ │ • CRUD Operations   │
        │ • Prompt Management │ │ • Order Management  │
        │ • API Endpoints     │ │ • API Endpoints     │
        └─────────────────────┘ └─────────────────────┘
```

## Detailed Service Descriptions

### 1. blog-core (Port 5001) - Main Orchestrator

**Purpose:** Central workflow orchestrator and page container

**Key Responsibilities:**
- Serves main workflow pages (`/workflow/posts/<id>/<stage>/<substage>/<step>`)
- Provides navigation and header components
- Orchestrates iframe embedding of microservices
- Handles workflow context and routing
- Manages database connections and core APIs

**Key Files:**
- `app.py` - Main Flask application and route handlers
- `templates/workflow.html` - Main workflow page template
- `templates/nav/` - Navigation components
- `static/` - CSS, JS, and static assets

**Route Example:**
```
GET /workflow/posts/53/writing/content/ideas_to_include
```

### 2. blog-llm-actions (Port 5002) - LLM Panel Microservice

**Purpose:** Provides the purple LLM panel interface

**Key Responsibilities:**
- LLM configuration and management
- Field selectors and context setup
- Prompt management and execution
- API endpoints for LLM operations

**Embedding:**
- Embedded as iframe in main workflow page
- URL: `http://localhost:5002/?stage=writing&substage=content&step=ideas_to_include&post_id=53`

**Key Features:**
- Complete LLM panel interface
- Field mapping and selection
- Context configuration
- System prompts and user prompts
- LLM execution and response handling

### 3. blog-post-sections (Port 5003) - Sections Panel Microservice

**Purpose:** Provides the green sections management panel

**Key Responsibilities:**
- Section CRUD operations
- Drag-and-drop section ordering
- Section content management
- API endpoints for section operations

**Embedding:**
- Embedded as iframe in main workflow page
- URL: `http://localhost:5003/?stage=writing&substage=content&step=ideas_to_include&post_id=53`

**Key Features:**
- Section creation, editing, deletion
- Section reordering via drag-and-drop
- Section content management
- Integration with main workflow

## Data Flow

### Page Load Flow

1. **User requests:** `http://localhost:5001/workflow/posts/53/writing/content/ideas_to_include`

2. **blog-core (5001) processes:**
   - Route handler in `app.py` extracts parameters
   - Queries database for step configuration
   - Loads workflow context and navigation
   - Renders `workflow.html` template

3. **Template renders:**
   - Header and navigation components
   - Two-column layout for writing stage
   - Left iframe: `http://localhost:5002/?stage=writing&substage=content&step=ideas_to_include&post_id=53`
   - Right iframe: `http://localhost:5003/?stage=writing&substage=content&step=ideas_to_include&post_id=53`

4. **Microservices load:**
   - **blog-llm-actions (5002):** Renders purple LLM panel
   - **blog-post-sections (5003):** Renders green sections panel

### API Communication

- **blog-core (5001):** Provides core workflow APIs and database access
- **blog-llm-actions (5002):** Handles its own LLM-related APIs
- **blog-post-sections (5003):** Handles its own section-related APIs
- **Cross-service communication:** Via iframe embedding and URL parameters

## Legacy System

### blog (Port 5000) - Deprecated Monolithic Service

**Status:** Deprecated, renamed to `/ZZblog`
**Purpose:** Was the original monolithic blog system
**Current Role:** Reference only, not actively used in workflow

**Note:** This service has been superseded by the microservice architecture. All active development should use the new services.

## Development Guidelines

### Adding New Features

1. **Workflow pages:** Add to blog-core (5001)
2. **LLM functionality:** Add to blog-llm-actions (5002)
3. **Section management:** Add to blog-post-sections (5003)
4. **Cross-service communication:** Use iframe embedding or API calls

### Service Independence

Each microservice should:
- Handle its own database connections
- Provide its own API endpoints
- Manage its own static assets
- Be independently deployable

### Testing

- Test each service independently
- Test iframe integration
- Test cross-service API communication
- Verify URL parameter passing

## Migration Notes

This architecture supersedes the previous monolithic structure where all functionality was contained in the `/blog` directory on port 5000. The migration provides:

- **Better separation of concerns**
- **Independent service development**
- **Improved scalability**
- **Easier maintenance**

## Related Documentation

- `api.md` - API reference for all services
- `microservices_overview.md` - Detailed microservice documentation
- `legacy_system_overview.md` - Information about the old monolithic system 