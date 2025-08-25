# System Access Points Reference

## Overview

This document provides a comprehensive reference for all access points in the blog microservices system. It covers web interfaces, API endpoints, health checks, and development tools for both blog-core and llm-actions services.

## Service Overview

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| **blog-core** | `http://localhost:5001` | 5001 | Main application server |
| **blog-llm-actions** | `http://localhost:5002` | 5002 | LLM processing microservice |

## blog-core Access Points

### Web Interfaces

#### Main Application
- **URL**: `http://localhost:5001/`
- **Description**: Main application dashboard
- **Features**: Navigation, workflow access, settings

#### Workflow System
- **URL**: `http://localhost:5001/workflow/`
- **Description**: Workflow management interface
- **Features**: Planning, authoring, publishing stages

#### Settings
- **URL**: `http://localhost:5001/settings/`
- **Description**: System configuration interface
- **Features**: Field mappings, format templates, workflow configuration

#### Documentation
- **URL**: `http://localhost:5001/docs/`
- **Description**: Project documentation access
- **Features**: API docs, schema docs, workflow docs

### API Endpoints

#### Health Check
- **URL**: `http://localhost:5001/health`
- **Method**: `GET`
- **Description**: Service health status
- **Response**: `{"status": "healthy", "service": "blog-core"}`

#### LLM API
- **Base URL**: `http://localhost:5001/api/llm/`
- **Endpoints**:
  - `GET /api/llm/config` - LLM configuration
  - `GET /api/llm/providers` - LLM providers
  - `GET /api/llm/models` - LLM models
  - `GET /api/llm/actions` - LLM actions
  - `POST /api/llm/actions/<id>/execute` - Execute action

#### Workflow API
- **Base URL**: `http://localhost:5001/api/workflow/`
- **Endpoints**:
  - `GET /api/workflow/posts` - Post management
  - `GET /api/workflow/fields` - Field mapping
  - `POST /api/workflow/posts/<id>/<stage>/<substage>/llm` - Workflow LLM execution

#### Images API
- **Base URL**: `http://localhost:5001/api/images/`
- **Endpoints**:
  - `GET /api/images/settings` - Image settings
  - `POST /api/images/generate` - Image generation

### Development Tools

#### API Testing
- **URL**: `http://localhost:5001/api/health`
- **Description**: Health check endpoint for testing

#### Database Access
- **Connection**: PostgreSQL via `DATABASE_URL` environment variable
- **Schema**: Shared with blog-llm-actions microservice

## blog-llm-actions Access Points

### Web Interfaces

#### Main Interface
- **URL**: `http://localhost:5002/`
- **Description**: Purple-themed LLM Actions interface
- **Features**:
  - Context management
  - Task management
  - Action selection
  - LLM execution
  - Real-time output display

#### Test Page
- **URL**: `http://localhost:5002/test`
- **Description**: Comprehensive API testing interface
- **Features**:
  - Health check testing
  - Configuration display
  - Actions list retrieval
  - LLM connection testing
  - Action execution testing
  - General LLM execution testing
  - Real-time results with success/error indicators

#### Static Files
- **URL**: `http://localhost:5002/static/`
- **Description**: Static assets and files
- **Features**: CSS, JavaScript, images, test files

### API Endpoints

#### Health Check
- **URL**: `http://localhost:5002/health`
- **Method**: `GET`
- **Description**: Service health status
- **Response**: `{"status": "healthy", "service": "llm-actions"}`

#### LLM Configuration
- **URL**: `http://localhost:5002/api/llm/config`
- **Method**: `GET`
- **Description**: Get LLM configuration from database
- **Response**: Provider type, model name, API base, status

#### LLM Testing
- **URL**: `http://localhost:5002/api/llm/test`
- **Method**: `POST`
- **Description**: Test LLM connection and configuration
- **Request**: `{"prompt": "test message", "model": "mistral"}`
- **Response**: Connection status and test response

#### LLM Providers
- **URL**: `http://localhost:5002/api/llm/providers`
- **Method**: `GET`
- **Description**: Get all LLM providers from database
- **Response**: Array of provider objects

#### LLM Models
- **URL**: `http://localhost:5002/api/llm/models`
- **Method**: `GET`
- **Description**: Get all LLM models with provider information
- **Response**: Array of model objects

#### LLM Actions
- **URL**: `http://localhost:5002/api/llm/actions`
- **Method**: `GET`
- **Description**: Get all LLM actions from database
- **Response**: Array of action objects

#### Execute Action
- **URL**: `http://localhost:5002/api/llm/actions/<action_id>/execute`
- **Method**: `POST`
- **Description**: Execute a specific LLM action
- **Request**: `{"input_text": "input for action"}`
- **Response**: Action output

#### General LLM
- **URL**: `http://localhost:5002/api/run-llm`
- **Method**: `POST`
- **Description**: General LLM execution with context and task
- **Request**: `{"system_prompt": "...", "persona": "...", "task": "..."}`
- **Response**: LLM result and output

#### Context Management
- **URL**: `http://localhost:5002/api/context`
- **Method**: `GET` / `POST`
- **Description**: Context data management (placeholder implementation)
- **Response**: Context data or update status

#### Task Management
- **URL**: `http://localhost:5002/api/task`
- **Method**: `GET` / `POST`
- **Description**: Task data management (placeholder implementation)
- **Response**: Task data or update status

### Development Tools

#### Test Interface
- **URL**: `http://localhost:5002/test`
- **Description**: Built-in API testing interface
- **Features**: All API endpoints with interactive testing

#### Logging
- **Level**: Configurable logging levels
- **Output**: Console and file logging
- **Features**: Error tracking, performance monitoring

## Cross-Service Communication

### CORS Configuration

#### blog-core
- **Allowed Origins**: `http://localhost:5001`
- **Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Headers**: Content-Type, Authorization

#### blog-llm-actions
- **Allowed Origins**: 
  - `http://localhost:5001` (blog-core)
  - `http://localhost:5002` (blog-llm-actions)
- **Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Headers**: Content-Type, Authorization

### Service Discovery

#### Health Monitoring
- **blog-core**: `http://localhost:5001/health`
- **llm-actions**: `http://localhost:5002/health`
- **Purpose**: Service status monitoring and health checks

#### Status Display
- **Location**: blog-core interface
- **Purpose**: Display microservice status to users
- **Features**: Real-time status updates, error reporting

## Database Access

### Shared Database
- **Database**: PostgreSQL
- **Connection**: `DATABASE_URL` environment variable
- **Schema**: Unified schema shared across all services
- **Access**: Direct SQL via psycopg2

### Database Tables
- **LLM Tables**: `llm_action`, `llm_provider`, `llm_model`, `llm_prompt`, `llm_action_history`, `llm_config`
- **Workflow Tables**: `workflow_stage_entity`, `workflow_sub_stage_entity`, `workflow_step_entity`
- **Content Tables**: `post_development`, `post_section`, `workflow_field_mapping`

## Environment Configuration

### Required Environment Variables

#### blog-core
```bash
DATABASE_URL=postgresql://username@localhost/blog
SECRET_KEY=your-secret-key
PORT=5001
```

#### llm-actions
```bash
DATABASE_URL=postgresql://username@localhost/blog
SECRET_KEY=your-secret-key
PORT=5002
OLLAMA_API_URL=http://localhost:11434
```

### Optional Environment Variables
```bash
OPENAI_API_KEY=your-openai-key
DEFAULT_LLM_MODEL=mistral
```

## Service Management

### Starting Services

#### blog-core
```bash
cd blog-core
python app.py
```

#### blog-llm-actions
```bash
cd blog-llm-actions
python app.py
```

### Health Checks

#### Manual Health Checks
```bash
# blog-core health
curl http://localhost:5001/health

# llm-actions health
curl http://localhost:5002/health
```

#### Automated Monitoring
- **Health Endpoints**: Both services provide `/health` endpoints
- **Status Monitoring**: blog-core can monitor llm-actions health
- **Error Reporting**: Comprehensive error logging and reporting

## Testing and Development

### API Testing

#### curl Examples
```bash
# Test blog-core health
curl http://localhost:5001/health

# Test blog-llm-actions health
curl http://localhost:5002/health

# Test LLM configuration
curl http://localhost:5002/api/llm/config

# Test LLM connection
curl -X POST http://localhost:5002/api/llm/test \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "model": "mistral"}'

# Execute LLM action
curl -X POST http://localhost:5002/api/llm/actions/63/execute \
  -H "Content-Type: application/json" \
  -d '{"input_text": "Scottish storytelling"}'
```

#### Browser Testing
- **blog-core**: Visit `http://localhost:5001/` for main interface
- **llm-actions**: Visit `http://localhost:5002/` for LLM interface
- **Test Page**: Visit `http://localhost:5002/test` for API testing

### Development Tools

#### Browser Developer Tools
- **Network Tab**: Monitor API requests and responses
- **Console**: View JavaScript logs and errors
- **Application Tab**: Check CORS and storage

#### Logging
- **Console Output**: Real-time service logs
- **Error Tracking**: Comprehensive error messages
- **Performance Monitoring**: Response time tracking

## Security Considerations

### CORS Security
- **Origin Restrictions**: Limited to localhost development
- **Method Restrictions**: Only necessary HTTP methods allowed
- **Header Restrictions**: Controlled header access

### API Security
- **Input Validation**: All API inputs validated
- **Error Handling**: No sensitive information in error messages
- **Rate Limiting**: Consider implementation for production

### Database Security
- **Connection Security**: Secure database connections
- **SQL Injection Prevention**: Parameterized queries
- **Access Control**: Database user permissions

## Troubleshooting

### Common Issues

#### Service Not Starting
- **Check Ports**: Ensure ports 5001 and 5002 are available
- **Check Dependencies**: Verify Python packages installed
- **Check Environment**: Verify environment variables set

#### Database Connection Issues
- **Check Database**: Ensure PostgreSQL is running
- **Check Connection String**: Verify `DATABASE_URL` is correct
- **Check Permissions**: Verify database user permissions

#### CORS Issues
- **Check Origins**: Verify CORS origins configured correctly
- **Check Headers**: Ensure proper headers in requests
- **Check Browser**: Clear browser cache and try again

#### LLM Issues
- **Check Ollama**: Ensure Ollama is running on port 11434
- **Check Models**: Verify required models are installed
- **Check Network**: Verify network connectivity

### Debug Tools

#### Health Checks
```bash
# Quick health check
curl http://localhost:5001/health && curl http://localhost:5002/health
```

#### Service Status
```bash
# Check running processes
ps aux | grep python

# Check port usage
lsof -i :5001 && lsof -i :5002
```

#### Database Connection
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"
```

## Related Documentation

- [Microservices Architecture Overview](microservices_overview.md)
- [LLM Actions Microservice API](api/current/llm_actions.md)
- [Workflow System Integration](workflow/README.md)
- [Database Schema](database/schema.md)
- [API Reference](api/current/README.md)
- [Deployment Guide](DEPLOYMENT.md) 