# API Reference

## Overview

The BlogForge CMS provides a comprehensive REST API through the unified Flask application. All endpoints are accessible through the main application at `http://localhost:5000`.

## Base URL
```
http://localhost:5000
```

## Authentication
Currently, the API does not require authentication for development. In production, API keys or session-based authentication should be implemented.

## Response Format
All API responses are in JSON format with the following structure:
```json
{
  "status": "success|error",
  "data": {...},
  "message": "Optional message",
  "error": "Error details if applicable"
}
```

## Core Endpoints

### Homepage
- **GET** `/`
- **Description:** Main application homepage
- **Response:** HTML page with unified interface

### Health Check
- **GET** `/health`
- **Description:** Application health status
- **Response:**
```json
{
  "status": "healthy",
  "service": "unified_app",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Database Management API

### Database Interface
- **GET** `/db/`
- **Description:** Database management interface
- **Response:** HTML page with database management tools

### List All Tables
- **GET** `/db/tables`
- **Description:** Get all database tables with metadata
- **Response:**
```json
{
  "groups": [
    {
      "group": "Core Content",
      "tables": [
        {
          "name": "post",
          "columns": [
            {
              "name": "id",
              "type": "integer",
              "nullable": false,
              "default": "nextval('post_id_seq'::regclass)"
            }
          ],
          "rows": [...],
          "row_count": 5
        }
      ]
    }
  ],
  "total_tables": 82,
  "total_groups": 10
}
```

### Get Table Data
- **GET** `/db/tables/{table_name}`
- **Description:** Get data from a specific table
- **Parameters:**
  - `table_name` (string): Name of the table
- **Response:** Array of table rows

### Execute Custom Query
- **POST** `/db/execute_query`
- **Description:** Execute a custom SQL query
- **Request Body:**
```json
{
  "query": "SELECT * FROM post LIMIT 10"
}
```
- **Response:** Query results or execution status

### Database Backup
- **POST** `/db/backup`
- **Description:** Create a database backup
- **Response:**
```json
{
  "message": "Backup created: backups/blog_backup_20240101_120000.sql",
  "file": "backups/blog_backup_20240101_120000.sql"
}
```

### Database Restore
- **POST** `/db/restore`
- **Description:** Restore database from backup
- **Request Body:**
```json
{
  "file": "backups/blog_backup_20240101_120000.sql"
}
```

## Workflow API

### Workflow Main
- **GET** `/workflow/posts/{post_id}/planning/{stage}/{substage}`
- **Description:** Main workflow interface
- **Parameters:**
  - `post_id` (integer): Post ID
  - `stage` (string): Workflow stage
  - `substage` (string): Workflow sub-stage
- **Response:** HTML workflow interface

### Workflow Redirects
- **GET** `/workflow/posts/{post_id}`
- **Description:** Redirect to workflow main page
- **GET** `/workflow/posts/{post_id}/planning/{stage}`
- **Description:** Redirect to workflow sub-stage

### Posts API
- **GET** `/posts`
- **Description:** Get posts list
- **Response:** Array of post objects

## LLM Actions API

### LLM Actions Interface
- **GET** `/llm-actions/`
- **Description:** LLM actions management interface
- **Response:** HTML interface

### LLM Health Check
- **GET** `/llm-actions/health`
- **Description:** LLM service health status

### Get LLM Providers
- **GET** `/llm-actions/api/llm/providers`
- **Description:** Get available LLM providers
- **Response:**
```json
[
  {
    "id": 1,
    "name": "OpenAI",
    "status": "active",
    "models": ["gpt-3.5-turbo", "gpt-4"]
  }
]
```

### Get LLM Actions
- **GET** `/llm-actions/api/llm/actions`
- **Description:** Get available LLM actions
- **Response:**
```json
[
  {
    "id": 1,
    "name": "Generate Content",
    "description": "Generate blog post content",
    "action_type": "content_generation"
  }
]
```

### Get Step Configuration
- **GET** `/llm-actions/api/step-config/{stage}/{substage}/{step}`
- **Description:** Get configuration for a specific workflow step
- **Parameters:**
  - `stage` (string): Workflow stage
  - `substage` (string): Workflow sub-stage
  - `step` (string): Workflow step
- **Response:** Step configuration object

## Launchpad API

### Launchpad Interface
- **GET** `/launchpad/`
- **Description:** Content syndication platform interface
- **Response:** HTML interface

### Social Media Platforms
- **GET** `/launchpad/api/platforms`
- **Description:** Get available social media platforms
- **Response:**
```json
[
  {
    "id": 1,
    "name": "facebook",
    "display_name": "Facebook",
    "logo_url": "/static/images/facebook.png"
  }
]
```

### Content Processes
- **GET** `/launchpad/api/content-processes`
- **Description:** Get content processing workflows
- **Response:**
```json
[
  {
    "id": 1,
    "platform_name": "Facebook",
    "channel_type": "blog_post",
    "name": "Facebook Blog Post Process"
  }
]
```

### Channel Configuration
- **GET** `/launchpad/syndication/{platform}/{channel_type}`
- **Description:** Get channel configuration interface
- **Parameters:**
  - `platform` (string): Platform name (e.g., "facebook")
  - `channel_type` (string): Channel type (e.g., "blog_post", "product_post")
- **Response:** HTML configuration interface

## Post Sections API

### Sections Interface
- **GET** `/post-sections/`
- **Description:** Post sections management interface
- **Response:** HTML interface

### Sections Panel
- **GET** `/post-sections/sections_panel`
- **Description:** Get sections panel HTML
- **Response:** HTML panel

### Sections Summary
- **GET** `/post-sections/sections_summary`
- **Description:** Get sections summary
- **Response:** HTML summary

### Test Sections
- **GET** `/post-sections/test`
- **Description:** Test sections functionality
- **Response:** Test results

## Post Info API

### Post Info Interface
- **GET** `/post-info/`
- **Description:** Post metadata management interface
- **Response:** HTML interface

### Get Post Info
- **GET** `/post-info/api/post-info/{post_id}`
- **Description:** Get post metadata
- **Parameters:**
  - `post_id` (integer): Post ID
- **Response:** Post metadata object

### Get Post SEO
- **GET** `/post-info/api/post-info/{post_id}/seo`
- **Description:** Get post SEO information
- **Parameters:**
  - `post_id` (integer): Post ID
- **Response:** SEO metadata object

### Create/Update Post Info
- **POST** `/post-info/api/post-info`
- **Description:** Create or update post metadata
- **Request Body:** Post metadata object
- **Response:** Success/error status

## Images API

### Images Interface
- **GET** `/images/`
- **Description:** Image management interface
- **Response:** HTML interface

### Upload Image
- **POST** `/images/upload`
- **Description:** Upload a new image
- **Request:** Multipart form data with image file
- **Response:** Upload status and image metadata

### Get Post Images
- **GET** `/images/api/images/{post_id}`
- **Description:** Get images for a specific post
- **Parameters:**
  - `post_id` (integer): Post ID
- **Response:** Array of image objects

### Get Section Images
- **GET** `/images/api/sections/{post_id}`
- **Description:** Get images for post sections
- **Parameters:**
  - `post_id` (integer): Post ID
- **Response:** Array of section image objects

## Clan API

### Clan API Interface
- **GET** `/clan-api/`
- **Description:** Clan API integration interface
- **Response:** HTML interface

### Test Clan API
- **GET** `/clan-api/test`
- **Description:** Test Clan API connection
- **Response:** Connection status

### Get Categories
- **GET** `/clan-api/api/categories`
- **Description:** Get product categories
- **Response:** Array of category objects

### Get Products
- **GET** `/clan-api/api/products`
- **Description:** Get products
- **Parameters:**
  - `limit` (integer, optional): Number of products to return
  - `offset` (integer, optional): Number of products to skip
- **Response:** Array of product objects

### Get Product Details
- **GET** `/clan-api/api/products/{product_id}`
- **Description:** Get specific product details
- **Parameters:**
  - `product_id` (integer): Product ID
- **Response:** Product object

### Get Product Images
- **GET** `/clan-api/api/products/{product_id}/images`
- **Description:** Get images for a product
- **Parameters:**
  - `product_id` (integer): Product ID
- **Response:** Array of image objects

## Error Handling

### Common Error Responses

#### 404 Not Found
```json
{
  "status": "error",
  "message": "Resource not found",
  "error": "The requested resource was not found"
}
```

#### 500 Internal Server Error
```json
{
  "status": "error",
  "message": "Internal server error",
  "error": "An unexpected error occurred"
}
```

#### 400 Bad Request
```json
{
  "status": "error",
  "message": "Bad request",
  "error": "Invalid request parameters"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting for API endpoints to prevent abuse.

## CORS

Cross-Origin Resource Sharing (CORS) is enabled for development. The allowed origins are configured in `config/unified_config.py`.

## Development

### Testing the API
Use the provided test suite:
```bash
python test_unified_app.py
```

### Adding New Endpoints
1. Create or update the appropriate blueprint in `blueprints/`
2. Register the blueprint in `unified_app.py`
3. Update this documentation
4. Add tests to `test_unified_app.py`

### API Versioning
Currently, no API versioning is implemented. For future versions, consider implementing versioning through URL prefixes (e.g., `/api/v1/`) or headers.
