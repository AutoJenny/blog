# Blog-Core API Reference

This document describes the API endpoints available in the blog-core service (port 5001).

## Base URL
- **Development**: `http://localhost:5001`
- **Production**: TBD

## Authentication
Currently, no authentication is required for these endpoints.

## Endpoints

### Core Endpoints

#### GET `/`
- **Description**: Main page with header and workflow navigation
- **Response**: HTML page

#### GET `/health`
- **Description**: Health check endpoint
- **Response**: JSON
```json
{
  "status": "healthy",
  "service": "blog-core"
}
```

### Workflow Endpoints

#### GET `/workflow/`
#### GET `/workflow/posts/<int:post_id>`
#### GET `/workflow/posts/<int:post_id>/<stage>`
#### GET `/workflow/posts/<int:post_id>/<stage>/<substage>`
- **Description**: Main workflow page with navigation
- **Parameters**:
  - `post_id`: Post ID (optional, defaults to first post)
  - `stage`: Workflow stage (optional, defaults to 'planning')
  - `substage`: Workflow substage (optional, defaults to 'idea')
  - `step`: Workflow step (optional, defaults to first step in substage)
- **Response**: HTML page with workflow interface

### API Workflow Endpoints

#### GET `/api/workflow/prompts/all`
- **Description**: Get all prompts from the llm_prompt table
- **Response**: JSON array of prompts
```json
[
  {
    "id": 93,
    "name": "B.10.WRITING ideas to include",
    "prompt_text": "",
    "type": "task"
  }
]
```

#### GET `/api/workflow/steps/<int:step_id>/prompts`
- **Description**: Get prompts for a specific step
- **Parameters**:
  - `step_id`: Workflow step ID
- **Response**: JSON object with prompt information
```json
{
  "system_prompt_id": 1,
  "system_prompt_name": "System Prompt Name",
  "system_prompt_content": "System prompt content...",
  "task_prompt_id": 2,
  "task_prompt_name": "Task Prompt Name",
  "task_prompt_content": "Task prompt content..."
}
```

#### POST `/api/workflow/steps/<int:step_id>/prompts`
- **Description**: Save prompts for a specific step
- **Parameters**:
  - `step_id`: Workflow step ID
- **Request Body**: JSON
```json
{
  "system_prompt_id": 1,
  "task_prompt_id": 2
}
```
- **Response**: JSON
```json
{
  "status": "success"
}
```

#### GET `/api/workflow/posts/<int:post_id>/development`
- **Description**: Get all development fields for a post
- **Parameters**:
  - `post_id`: Post ID
- **Response**: JSON object with field values
```json
{
  "basic_idea": "Post basic idea content",
  "idea_scope": "Post idea scope content",
  "section_headings": "JSON list of section headings"
}
```

#### GET `/api/workflow/fields/available`
- **Description**: Get all available fields from post_development table
- **Query Parameters**:
  - `step_id`: Workflow step ID (optional)
  - `substage_id`: Workflow substage ID (optional)
  - `stage_id`: Workflow stage ID (optional)
- **Response**: JSON object with available fields
```json
{
  "fields": [
    {
      "field_name": "basic_idea",
      "display_name": "Basic Idea",
      "db_table": "post_development",
      "db_field": "basic_idea",
      "description": ""
    }
  ],
  "groups": []
}
```

#### POST `/api/workflow/posts/<int:post_id>/fields/status`
- **Description**: Update post status
- **Parameters**:
  - `post_id`: Post ID
- **Request Body**: JSON
```json
{
  "status": "published"
}
```
- **Response**: JSON
```json
{
  "status": "success"
}
```

### LLM Actions Endpoints

#### GET `/api/llm-actions/content`
- **Description**: Get LLM actions content for embedding in workflow pages
- **Query Parameters**:
  - `stage`: Current workflow stage
  - `substage`: Current workflow substage
  - `step`: Current workflow step
  - `post_id`: Post ID
  - `step_id`: Step ID (optional)
- **Response**: HTML content for LLM actions panel

#### POST `/api/llm-actions/execute/<int:action_id>`
- **Description**: Execute a specific LLM action
- **Parameters**:
  - `action_id`: Action ID to execute
- **Request Body**: JSON with action parameters
- **Response**: JSON with execution results

#### GET `/api/llm-actions/config`
- **Description**: Get LLM actions configuration
- **Response**: JSON configuration object

#### GET `/api/llm-actions/actions`
- **Description**: Get list of available LLM actions
- **Response**: JSON array of available actions

#### POST `/api/llm-actions/test`
- **Description**: Test LLM actions functionality
- **Request Body**: JSON test parameters
- **Response**: JSON test results

#### GET `/api/llm-actions/field-mappings`
- **Description**: Get field mappings for LLM actions
- **Response**: JSON object with field mappings

### LLM Actions Microservice Endpoints (Port 5002)

#### POST `/api/run-llm`
- **Description**: Execute LLM processing with context-aware behavior
- **Request Body**: JSON
```json
{
  "system_prompt": "System prompt content",
  "persona": "Persona description",
  "task": "User's task message",
  "post_id": "53",
  "output_field": "image_concepts",
  "section_id": "123",
  "stage": "writing",
  "substage": "sections"
}
```
- **Response**: JSON
```json
{
  "status": "success",
  "output": "LLM generated content",
  "result": "LLM generated content"
}
```
- **Notes**: 
  - For `substage: "sections"`, processes individual sections if `section_id` provided
  - For other substages, processes at post level
  - Automatically saves to appropriate database table based on `output_field`

#### GET `/api/llm/actions`
- **Description**: Get all task prompts organized by workflow stages
- **Response**: JSON array of prompts with stage/substage/step organization
- **Notes**: Same structure as workflow_prompts page

#### POST `/api/llm/actions/<int:action_id>/execute`
- **Description**: Execute a specific task prompt
- **Parameters**:
  - `action_id`: Task prompt ID
- **Request Body**: JSON
```json
{
  "input_text": "Input content",
  "post_id": "53",
  "output_field": "field_name",
  "section_id": "123"
}
```
- **Response**: JSON with execution results
- **Notes**: Supports section-specific processing when `section_id` provided

### Documentation Endpoints

#### GET `/docs/`
#### GET `/docs/<path:req_path>`
- **Description**: Documentation pages
- **Parameters**:
  - `req_path`: Documentation file path (optional)
- **Response**: HTML documentation page

#### GET `/docs/nav/`
- **Description**: Documentation navigation
- **Response**: JSON navigation structure

#### GET `/docs/view/<path:file_path>`
- **Description**: View specific documentation file
- **Parameters**:
  - `file_path`: Path to documentation file
- **Response**: HTML content of documentation file

### Service Status Endpoints

#### GET `/api/services/status`
- **Description**: Get status of all microservices
- **Response**: JSON object with service statuses
```json
{
  "blog-core": "healthy",
  "blog-llm-actions": "healthy",
  "blog": "healthy"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Missing required fields"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

### 503 Service Unavailable
```json
{
  "error": "LLM Actions service unavailable: connection error"
}
```

## Notes

- The blog-core service acts as a proxy for some LLM actions functionality, forwarding requests to the blog-llm-actions service (port 5002)
- All database operations use PostgreSQL with psycopg2
- The service uses DictCursor for database queries to return results as dictionaries
- Workflow endpoints support the microservice architecture with proper error handling
- **CORS Support**: All microservices have CORS enabled for cross-origin communication between localhost ports (5000, 5001, 5002, 5003)
- **Iframe Communication**: The sections substage uses `postMessage` API for secure cross-origin communication between iframes
- **Fallback Mechanisms**: If iframe communication fails, the system falls back to direct API calls for section processing 