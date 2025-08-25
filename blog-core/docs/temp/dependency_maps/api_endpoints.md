# API Endpoints Project Assignment Analysis

**Date:** 2025-07-17  
**Purpose:** Project assignment mapping for API endpoints during reorganization  
**Status:** Phase 1, Step 2 - API Endpoints Analysis  
**Note:** This document is for reorganization planning only. For detailed API documentation, see `/docs/reference/api/current/`

---

## Important Note

**This document is temporary analysis for project reorganization only.**

For complete, authoritative API documentation including:
- Detailed endpoint specifications
- Request/response examples  
- Error codes and status codes
- Curl examples
- Authentication details

**See the official API documentation:**
- `/docs/reference/api/current/README.md` - API overview and conventions
- `/docs/reference/api/current/posts.md` - Post management endpoints
- `/docs/reference/api/current/fields.md` - Field mapping endpoints  
- `/docs/reference/api/current/formats.md` - Format template endpoints
- `/docs/reference/api/current/llm.md` - LLM integration endpoints

---

## API Structure Overview

The blog system uses a hierarchical API structure with the following organization:

```
/api/                    # Main API prefix
├── base/               # Base API functionality
├── workflow/           # Workflow-specific endpoints
├── llm/                # LLM integration endpoints
├── images/             # Image management endpoints
├── v1/                 # Version 1 endpoints (deprecated)
└── deprecated/         # Deprecated endpoints
```

---

## API Endpoint Project Assignments

**Purpose:** This section maps existing endpoints to new projects based on their usage patterns and dependencies. For detailed endpoint specifications, refer to the official API documentation files listed above.

### Base API Endpoints (`/api/`)

#### Health Check
- **Endpoint:** `GET /api/health`
- **Purpose:** System health check
- **Used by:** All stages
- **Response:** JSON with system status
- **New Project Assignment:** blog-core

#### System Information
- **Endpoint:** `GET /api/system`
- **Purpose:** System information and performance metrics
- **Used by:** All stages
- **Response:** JSON with system metrics
- **New Project Assignment:** blog-core

---

## Workflow API Endpoints (`/api/workflow/`)

### Post Management

#### Get All Posts
- **Endpoint:** `GET /api/workflow/posts`
- **Purpose:** Retrieve all posts with workflow status
- **Used by:** All workflow stages
- **Response:** JSON array of posts
- **New Project Assignment:** blog-core

#### Get Single Post
- **Endpoint:** `GET /api/workflow/posts/<post_id>`
- **Purpose:** Retrieve specific post with workflow data
- **Used by:** All workflow stages
- **Response:** JSON post object
- **New Project Assignment:** blog-core

#### Create Post
- **Endpoint:** `POST /api/workflow/posts`
- **Purpose:** Create new post
- **Used by:** Planning stage
- **Request:** JSON post data
- **Response:** JSON created post
- **New Project Assignment:** blog-planning

#### Update Post
- **Endpoint:** `PUT /api/workflow/posts/<post_id>`
- **Purpose:** Update post data
- **Used by:** All workflow stages
- **Request:** JSON post data
- **Response:** JSON updated post
- **New Project Assignment:** blog-core

### Section Management

#### Get Post Sections
- **Endpoint:** `GET /api/workflow/posts/<post_id>/sections`
- **Purpose:** Retrieve all sections for a post
- **Used by:** Writing stage, Images stage
- **Response:** JSON array of sections
- **New Project Assignment:** blog-writing

#### Get Single Section
- **Endpoint:** `GET /api/workflow/posts/<post_id>/sections/<section_id>`
- **Purpose:** Retrieve specific section
- **Used by:** Writing stage, Images stage
- **Response:** JSON section object
- **New Project Assignment:** blog-writing

#### Create Section
- **Endpoint:** `POST /api/workflow/posts/<post_id>/sections`
- **Purpose:** Create new section
- **Used by:** Writing stage
- **Request:** JSON section data
- **Response:** JSON created section
- **New Project Assignment:** blog-writing

#### Update Section
- **Endpoint:** `PUT /api/workflow/posts/<post_id>/sections/<section_id>`
- **Purpose:** Update section data
- **Used by:** Writing stage, Images stage
- **Request:** JSON section data
- **Response:** JSON updated section
- **New Project Assignment:** blog-writing

#### Delete Section
- **Endpoint:** `DELETE /api/workflow/posts/<post_id>/sections/<section_id>`
- **Purpose:** Delete section
- **Used by:** Writing stage
- **Response:** JSON success message
- **New Project Assignment:** blog-writing

### Workflow Stage Management

#### Get Workflow Stages
- **Endpoint:** `GET /api/workflow/stages`
- **Purpose:** Retrieve all workflow stages
- **Used by:** All workflow stages
- **Response:** JSON array of stages
- **New Project Assignment:** blog-core

#### Get Post Workflow Status
- **Endpoint:** `GET /api/workflow/posts/<post_id>/status`
- **Purpose:** Retrieve workflow status for post
- **Used by:** All workflow stages
- **Response:** JSON workflow status
- **New Project Assignment:** blog-core

#### Update Workflow Status
- **Endpoint:** `PUT /api/workflow/posts/<post_id>/status`
- **Purpose:** Update workflow status
- **Used by:** All workflow stages
- **Request:** JSON status data
- **Response:** JSON updated status
- **New Project Assignment:** blog-core

### LLM Integration

#### Execute LLM Request
- **Endpoint:** `POST /api/workflow/posts/<post_id>/llm`
- **Purpose:** Execute LLM processing for post
- **Used by:** All workflow stages
- **Request:** JSON LLM request data
- **Response:** JSON LLM response
- **New Project Assignment:** blog-core

#### Get LLM Actions
- **Endpoint:** `GET /api/workflow/llm/actions`
- **Purpose:** Retrieve available LLM actions
- **Used by:** All workflow stages
- **Response:** JSON array of actions
- **New Project Assignment:** blog-core

#### Get LLM Action
- **Endpoint:** `GET /api/workflow/llm/actions/<action_id>`
- **Purpose:** Retrieve specific LLM action
- **Used by:** All workflow stages
- **Response:** JSON action object
- **New Project Assignment:** blog-core

### Format Management

#### Get Step Formats
- **Endpoint:** `GET /api/workflow/posts/<post_id>/steps/<step_id>/formats`
- **Purpose:** Retrieve formats for workflow step
- **Used by:** All workflow stages
- **Response:** JSON array of formats
- **New Project Assignment:** blog-core

#### Update Step Format
- **Endpoint:** `PUT /api/workflow/posts/<post_id>/steps/<step_id>/formats`
- **Purpose:** Update format for workflow step
- **Used by:** All workflow stages
- **Request:** JSON format data
- **Response:** JSON updated format
- **New Project Assignment:** blog-core

---

## Image Management API Endpoints (`/api/images/`)

### Image Generation

#### Generate Image
- **Endpoint:** `POST /api/images/generate`
- **Purpose:** Generate image using LLM
- **Used by:** Images stage
- **Request:** JSON generation parameters
- **Response:** JSON generation result
- **New Project Assignment:** blog-images

#### Get Image Settings
- **Endpoint:** `GET /api/images/settings`
- **Purpose:** Retrieve image generation settings
- **Used by:** Images stage
- **Response:** JSON settings object
- **New Project Assignment:** blog-images

#### Update Image Settings
- **Endpoint:** `PUT /api/images/settings`
- **Purpose:** Update image generation settings
- **Used by:** Images stage
- **Request:** JSON settings data
- **Response:** JSON updated settings
- **New Project Assignment:** blog-images

### Image Management

#### Upload Image
- **Endpoint:** `POST /api/images/upload`
- **Purpose:** Upload image file
- **Used by:** Images stage
- **Request:** Multipart form data
- **Response:** JSON upload result
- **New Project Assignment:** blog-images

#### Get Image Styles
- **Endpoint:** `GET /api/images/styles`
- **Purpose:** Retrieve available image styles
- **Used by:** Images stage
- **Response:** JSON array of styles
- **New Project Assignment:** blog-images

#### Get Image Formats
- **Endpoint:** `GET /api/images/formats`
- **Purpose:** Retrieve available image formats
- **Used by:** Images stage
- **Response:** JSON array of formats
- **New Project Assignment:** blog-images

#### Get Prompt Examples
- **Endpoint:** `GET /api/images/prompt_examples`
- **Purpose:** Retrieve image prompt examples
- **Used by:** Images stage
- **Response:** JSON array of examples
- **New Project Assignment:** blog-images

---

## LLM API Endpoints (`/api/llm/`)

### LLM Configuration

#### Get LLM Config
- **Endpoint:** `GET /api/llm/config`
- **Purpose:** Retrieve LLM configuration
- **Used by:** All stages
- **Response:** JSON config object
- **New Project Assignment:** blog-core

#### Update LLM Config
- **Endpoint:** `PUT /api/llm/config`
- **Purpose:** Update LLM configuration
- **Used by:** All stages
- **Request:** JSON config data
- **Response:** JSON updated config
- **New Project Assignment:** blog-core

### LLM Processing

#### Process Text
- **Endpoint:** `POST /api/llm/process`
- **Purpose:** Process text with LLM
- **Used by:** All stages
- **Request:** JSON processing parameters
- **Response:** JSON processing result
- **New Project Assignment:** blog-core

#### Get LLM History
- **Endpoint:** `GET /api/llm/history`
- **Purpose:** Retrieve LLM interaction history
- **Used by:** All stages
- **Response:** JSON array of interactions
- **New Project Assignment:** blog-core

---

## Deprecated API Endpoints (`/api/v1/`)

### Deprecated LLM Endpoints
- **Endpoint:** `GET /api/v1/llm/config`
- **Status:** Deprecated
- **Replacement:** `/api/llm/config`
- **New Project Assignment:** Remove from all projects

### Deprecated Image Endpoints
- **Endpoint:** `POST /api/v1/images/generate`
- **Status:** Deprecated
- **Replacement:** `/api/images/generate`
- **New Project Assignment:** Remove from all projects

- **Endpoint:** `GET /api/v1/images/settings`
- **Status:** Deprecated
- **Replacement:** `/api/images/settings`
- **New Project Assignment:** Remove from all projects

---

## Database API Endpoints (`/api/db/`)

### Database Management

#### Get Database Status
- **Endpoint:** `GET /api/db/status`
- **Purpose:** Retrieve database connection status
- **Used by:** All stages
- **Response:** JSON status object
- **New Project Assignment:** blog-core

#### Backup Database
- **Endpoint:** `POST /api/db/backup`
- **Purpose:** Create database backup
- **Used by:** All stages
- **Response:** JSON backup result
- **New Project Assignment:** blog-core

#### Restore Database
- **Endpoint:** `POST /api/db/restore`
- **Purpose:** Restore database from backup
- **Used by:** All stages
- **Request:** JSON restore parameters
- **Response:** JSON restore result
- **New Project Assignment:** blog-core

---

## Stage-Specific API Mapping

### Planning Stage (blog-planning)
**Primary Endpoints:**
- `POST /api/workflow/posts` (Create post)
- `PUT /api/workflow/posts/<post_id>` (Update planning data)
- `POST /api/workflow/posts/<post_id>/llm` (LLM processing)
- `GET /api/workflow/llm/actions` (Get LLM actions)
- `PUT /api/workflow/posts/<post_id>/status` (Update workflow status)

**Dependencies:**
- blog-core for database and LLM services
- blog-core for workflow stage management

### Writing Stage (blog-writing)
**Primary Endpoints:**
- `GET /api/workflow/posts/<post_id>/sections` (Get sections)
- `POST /api/workflow/posts/<post_id>/sections` (Create section)
- `PUT /api/workflow/posts/<post_id>/sections/<section_id>` (Update section)
- `DELETE /api/workflow/posts/<post_id>/sections/<section_id>` (Delete section)
- `POST /api/workflow/posts/<post_id>/llm` (LLM processing)
- `PUT /api/workflow/posts/<post_id>/status` (Update workflow status)

**Dependencies:**
- blog-core for database and LLM services
- blog-core for workflow stage management

### Structuring Stage (blog-structuring)
**Primary Endpoints:**
- `PUT /api/workflow/posts/<post_id>` (Update structuring data)
- `POST /api/workflow/posts/<post_id>/llm` (LLM processing)
- `PUT /api/workflow/posts/<post_id>/status` (Update workflow status)
- `GET /api/workflow/posts/<post_id>/sections` (Get sections for context)

**Dependencies:**
- blog-core for database and LLM services
- blog-core for workflow stage management
- blog-writing for section data access

### Images Stage (blog-images)
**Primary Endpoints:**
- `POST /api/images/generate` (Generate images)
- `POST /api/images/upload` (Upload images)
- `GET /api/images/settings` (Get settings)
- `PUT /api/images/settings` (Update settings)
- `GET /api/images/styles` (Get styles)
- `GET /api/images/formats` (Get formats)
- `GET /api/images/prompt_examples` (Get examples)
- `GET /api/workflow/posts/<post_id>/sections` (Get sections for image context)
- `PUT /api/workflow/posts/<post_id>/sections/<section_id>` (Update section with image data)

**Dependencies:**
- blog-core for database services
- blog-writing for section data access
- blog-core for LLM services (prompt generation)

### Publishing Stage (blog-publishing)
**Primary Endpoints:**
- `PUT /api/workflow/posts/<post_id>` (Update publishing data)
- `PUT /api/workflow/posts/<post_id>/status` (Update workflow status)
- Publishing-specific endpoints (to be created)

**Dependencies:**
- blog-core for database services
- blog-core for workflow stage management
- External publishing APIs (clan.com, social media)

---

## Cross-Project API Communication

### Internal Communication
**Pattern:** Projects communicate via shared database and HTTP APIs
**Security:** No authentication required (internal communication)
**Error Handling:** Standard JSON error responses

### External Communication
**Pattern:** Projects communicate with external services via HTTP APIs
**Security:** API keys and authentication as required
**Error Handling:** Graceful degradation and retry mechanisms

---

## API Response Standards

### Success Response Format
```json
{
    "status": "success",
    "data": {
        // Response data
    },
    "message": "Optional success message"
}
```

### Error Response Format
```json
{
    "status": "error",
    "message": "Error description",
    "errors": [
        {
            "field": "field_name",
            "message": "Field-specific error"
        }
    ]
}
```

### Pagination Format
```json
{
    "status": "success",
    "data": {
        "items": [],
        "pagination": {
            "page": 1,
            "per_page": 10,
            "total": 100,
            "pages": 10
        }
    }
}
```

---

## API Versioning Strategy

### Current Version
- **Prefix:** `/api/` (current)
- **Status:** Active development
- **Documentation:** This document

### Deprecated Versions
- **Prefix:** `/api/v1/` (deprecated)
- **Status:** Deprecated, will be removed
- **Migration:** All endpoints moved to `/api/`

### Future Versions
- **Strategy:** Semantic versioning
- **Backward Compatibility:** Maintained for one major version
- **Migration Path:** Clear migration documentation

---

## API Security Considerations

### Authentication
- **Current:** No authentication (internal system)
- **Future:** JWT tokens for external access
- **Implementation:** Flask-JWT-Extended

### Rate Limiting
- **Current:** No rate limiting
- **Future:** Implement rate limiting for external APIs
- **Implementation:** Flask-Limiter

### Input Validation
- **Current:** Basic validation
- **Future:** Comprehensive validation with Marshmallow
- **Implementation:** Marshmallow schemas

---

## API Testing Strategy

### Unit Testing
- **Framework:** pytest
- **Coverage:** All endpoints
- **Mocking:** Database and external services

### Integration Testing
- **Framework:** pytest with Flask test client
- **Coverage:** End-to-end API workflows
- **Database:** Test database with fixtures

### Performance Testing
- **Framework:** Locust
- **Metrics:** Response time, throughput
- **Targets:** All critical endpoints

---

**Status:** Step 2 Complete - API endpoints documented  
**Next Step:** Step 3 - Configuration Analysis

---

## Document Status

- **Type:** Temporary analysis document
- **Purpose:** Project reorganization planning only
- **Authoritative API docs:** `/docs/reference/api/current/`
- **Should not replace:** Official API documentation
- **Should be archived:** After project reorganization is complete 