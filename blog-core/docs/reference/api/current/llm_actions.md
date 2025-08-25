# LLM Actions Microservice API

## Overview

The LLM Actions microservice (`http://localhost:5002`) provides a complete LLM processing system with a purple-themed interface and comprehensive API endpoints. This service replicates all LLM functionality from the main blog application while providing a standalone, testable interface.

## Service Information

- **Base URL**: `http://localhost:5002`
- **Theme**: Purple-themed interface
- **Database**: Shared PostgreSQL database with blog-core
- **CORS**: Enabled for cross-origin requests
- **Health Endpoint**: `/health`

## Access Points

### Web Interfaces
- **Main Interface**: `http://localhost:5002/` - Purple-themed LLM Actions interface
- **Test Page**: `http://localhost:5002/test` - Comprehensive API testing interface
- **Static Files**: `http://localhost:5002/static/` - Static assets

### API Endpoints
- **API Base**: `http://localhost:5002/api/`
- **Health Check**: `http://localhost:5002/health`

## Core API Endpoints

### Health Check
- **URL**: `/health`
- **Method**: `GET`
- **Description**: Service health status
- **Response**:
  ```json
  {
    "status": "healthy",
    "service": "llm-actions"
  }
  ```
- **Status Codes**: `200`

### LLM Configuration

#### Get LLM Configuration
- **URL**: `/api/llm/config`
- **Method**: `GET`
- **Description**: Retrieves current LLM configuration from database
- **Response**:
  ```json
  {
    "provider_type": "ollama",
    "model_name": "mistral",
    "api_base": "http://localhost:11434",
    "is_active": true
  }
  ```
- **Status Codes**: `200`, `500`

### LLM Testing

#### Test LLM Connection
- **URL**: `/api/llm/test`
- **Method**: `POST`
- **Description**: Tests LLM connection and configuration
- **Request Body**:
  ```json
  {
    "prompt": "Hello, this is a test message. Please respond with a brief greeting.",
    "model": "mistral"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Connection successful",
    "response": "Hello! I'm here to help answer any questions..."
  }
  ```
- **Status Codes**: `200`, `500`

### LLM Providers

#### Get Providers
- **URL**: `/api/llm/providers`
- **Method**: `GET`
- **Description**: Retrieves all LLM providers from database
- **Response**:
  ```json
  [
    {
      "id": 1,
      "name": "Ollama",
      "type": "ollama",
      "api_url": "http://localhost:11434",
      "description": "Local Ollama provider",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
  ```
- **Status Codes**: `200`, `500`

### LLM Models

#### Get Models
- **URL**: `/api/llm/models`
- **Method**: `GET`
- **Description**: Retrieves all LLM models with provider information
- **Response**:
  ```json
  [
    {
      "id": "1",
      "name": "mistral",
      "provider": "Ollama",
      "capabilities": ["text-generation"],
      "description": "Mistral 7B model",
      "provider_type": "ollama"
    }
  ]
  ```
- **Status Codes**: `200`, `500`

### LLM Actions

#### Get Actions
- **URL**: `/api/llm/actions`
- **Method**: `GET`
- **Description**: Retrieves all LLM actions from database
- **Response**:
  ```json
  [
    {
      "id": 63,
      "field_name": "expand_idea",
      "prompt_template": "Short Idea:\\n[data:idea_seed]\\n\\nYour response should:\\n1. Focus specifically on Scottish cultural and historical aspects\\n2. Maintain academic accuracy while being accessible\\n3. Suggest clear angles and themes for development\\n4. Use UK-British spellings and idioms\\n5. Return only the expanded brief, with no additional commentary or formatting",
      "prompt_template_id": 58,
      "llm_model": "mistral",
      "provider_id": 5,
      "temperature": 0.7,
      "max_tokens": 1000,
      "input_field": "idea_seed",
      "output_field": "expanded_idea",
      "order": 0,
      "timeout": 60
    }
  ]
  ```
- **Status Codes**: `200`, `500`

#### Execute Action
- **URL**: `/api/llm/actions/<action_id>/execute`
- **Method**: `POST`
- **Description**: Executes a specific LLM action
- **URL Parameters**:
  - `action_id`: ID of the action to execute
- **Request Body**:
  ```json
  {
    "input_text": "Scottish storytelling traditions"
  }
  ```
- **Response**:
  ```json
  {
    "output": "Scottish storytelling traditions are a rich and vibrant part of the country's cultural heritage..."
  }
  ```
- **Status Codes**: `200`, `400`, `404`, `500`

### General LLM Execution

#### Run General LLM
- **URL**: `/api/run-llm`
- **Method**: `POST`
- **Description**: General LLM execution with context and task
- **Request Body**:
  ```json
  {
    "system_prompt": "Scottish Expert",
    "persona": "You are an expert in Scottish history",
    "task": "Tell me about Scottish castles"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "result": "Scotland is renowned for its rich historical heritage...",
    "output": "Scotland is renowned for its rich historical heritage..."
  }
  ```
- **Status Codes**: `200`, `500`

### Context Management

#### Get Context
- **URL**: `/api/context`
- **Method**: `GET`
- **Description**: Retrieves context data (placeholder implementation)
- **Response**:
  ```json
  {
    "system_prompt": "Scottish HISTORY Expert",
    "persona": "You are an expert researcher and author in Scottish history and culture...",
    "additional_fields": []
  }
  ```
- **Status Codes**: `200`

#### Update Context
- **URL**: `/api/context`
- **Method**: `POST`
- **Description**: Updates context data (placeholder implementation)
- **Request Body**:
  ```json
  {
    "system_prompt": "New system prompt",
    "persona": "New persona description",
    "additional_fields": []
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Context updated"
  }
  ```
- **Status Codes**: `200`

### Task Management

#### Get Task
- **URL**: `/api/task`
- **Method**: `GET`
- **Description**: Retrieves task data (placeholder implementation)
- **Response**:
  ```json
  {
    "current_task": "Generate initial concept for blog post",
    "task_history": []
  }
  ```
- **Status Codes**: `200`

#### Update Task
- **URL**: `/api/task`
- **Method**: `POST`
- **Description**: Updates task data (placeholder implementation)
- **Request Body**:
  ```json
  {
    "current_task": "New task description",
    "task_history": []
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Task updated"
  }
  ```
- **Status Codes**: `200`

## Error Handling

### Error Response Format
All endpoints return errors in the following format:
```json
{
  "error": "Error message description"
}
```

### Common Status Codes
- `200`: Success
- `400`: Bad Request - Invalid input parameters
- `404`: Not Found - Resource does not exist
- `500`: Internal Server Error - Server-side error

## CORS Configuration

The service is configured with CORS enabled for the following origins:
- `http://localhost:5001` (blog-core)
- `http://localhost:5002` (llm-actions)

### CORS Headers
- `Access-Control-Allow-Origin`: Configured for allowed origins
- `Access-Control-Allow-Methods`: GET, POST, PUT, DELETE, OPTIONS
- `Access-Control-Allow-Headers`: Content-Type, Authorization

## Database Integration

### Shared Database
- **Database**: Same PostgreSQL database as blog-core
- **Connection**: Uses `DATABASE_URL` environment variable
- **Tables**: Access to all existing LLM-related tables:
  - `llm_action`
  - `llm_provider`
  - `llm_model`
  - `llm_prompt`
  - `llm_action_history`
  - `llm_config`

### Database Operations
- **Direct SQL**: All database operations use psycopg2
- **Connection Management**: Proper connection handling with context managers
- **Error Handling**: Comprehensive error handling for database operations

## LLM Service Features

### LLMService Class
- **Ollama Support**: Full Ollama integration with local models
- **OpenAI Support**: Stubbed OpenAI integration for future use
- **Prompt Processing**: Modular and tagged prompt processing
- **Error Handling**: Comprehensive error handling and logging

### Prompt Processing
- **Modular Prompts**: Support for JSON-based modular prompts
- **Tagged Prompts**: Support for role-based tagged prompts
- **Field Substitution**: Dynamic field substitution in prompts
- **Canonical Format**: Conversion to canonical prompt format

## Testing and Development

### Test Page
- **URL**: `http://localhost:5002/test`
- **Features**:
  - Health check testing
  - Configuration display
  - Actions list retrieval
  - LLM connection testing
  - Action execution testing
  - General LLM execution testing
  - Real-time results with success/error indicators

### Development Tools
- **Logging**: Comprehensive logging with configurable levels
- **Error Tracking**: Detailed error messages and stack traces
- **API Testing**: Built-in test interface for all endpoints
- **Browser Tools**: Full browser developer tools support

## Integration with blog-core

### Workflow Integration
- **Embedded Interface**: Can be embedded in blog-core workflow pages
- **API Communication**: JavaScript-based communication between services
- **Context Sharing**: Shared session and context data
- **Result Processing**: Structured output handling

### Service Discovery
- **Health Monitoring**: blog-core monitors llm-actions health
- **Status Display**: Service status shown in blog-core interface
- **Fallback Behavior**: Graceful degradation when service unavailable

## Deployment

### Requirements
- **Python Dependencies**: See `requirements.txt`
- **Database**: PostgreSQL with blog schema
- **Ollama**: Local Ollama installation for LLM processing
- **Environment Variables**: `DATABASE_URL`, `SECRET_KEY`

### Environment Variables
```bash
DATABASE_URL=postgresql://username@localhost/blog
SECRET_KEY=your-secret-key
PORT=5002
```

### Service Management
- **Start Service**: `python app.py`
- **Health Check**: `curl http://localhost:5002/health`
- **Test Interface**: Visit `http://localhost:5002/test`

## Related Documentation

- [Microservices Architecture Overview](../microservices_overview.md)
- [Workflow System Integration](../../workflow/README.md)
- [Database Schema](../database/schema.md)
- [LLM API Reference](llm.md)
- [Deployment Guide](../../DEPLOYMENT.md) 