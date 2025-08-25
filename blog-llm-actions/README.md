# blog-llm-actions

LLM processing microservice for the blog system with purple-themed interface and comprehensive API functionality.

## Overview

This is a **microservice designed to be embedded as an iframe** within the main blog-core workflow interface. It is **NOT designed to be accessed directly** as a standalone service.

## ⚠️ CRITICAL: Iframe-Based Architecture

**This service is designed to work ONLY when embedded as an iframe within the main workflow interface:**

- **Main Workflow URL**: `http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`
- **Iframe Embedding**: The main workflow embeds this service as an iframe with URL parameters
- **Required Parameters**: `stage`, `substage`, `step`, `post_id`, `step_id`
- **Direct Access**: Accessing `http://localhost:5002` directly will fail with "Missing required URL parameters"


### How It Works

1. **Main Workflow** (`http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`) loads
2. **blog-core** embeds this service as an iframe with proper URL parameters:
   ```
   http://localhost:5002/?stage=planning&substage=idea&step=initial_concept&post_id=1&step_id=41
   ```
3. **This service** receives context from URL parameters and initializes properly
4. **Direct access** to `http://localhost:5002` will fail because no parameters are provided

### Testing

**✅ CORRECT WAY TO TEST:**
```
http://localhost:5000/workflow/posts/1/planning/idea/initial_concept
```

**❌ INCORRECT WAY TO TEST:**
```
http://localhost:5002
```

This service provides complete LLM functionality for the blog system when properly embedded within the main workflow interface.

## Features

- **Purple-themed Interface**: Standalone web interface with consistent branding
- **Complete LLM API**: All LLM functionality exposed via REST APIs
- **Action Execution**: Execute LLM actions with full prompt processing
- **Test Interface**: Built-in comprehensive API testing page
- **Health Monitoring**: Health check endpoints for service monitoring
- **CORS Support**: Cross-origin requests enabled for integration
- **Modular JavaScript Architecture**: Robust, maintainable frontend with unified data flow

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database (shared with blog-core)
- Ollama (for LLM processing)

### Installation

1. **Clone/Setup Project**
   ```bash
   cd blog-llm-actions
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   # Copy and configure environment file
   cp config.env.example config.env
   # Edit config.env with your database connection
   ```

3. **Start Service**
   ```bash
   python app.py
   ```

4. **Verify Installation**
   ```bash
   curl http://localhost:5002/health
   # Should return: {"status": "healthy", "service": "llm-actions"}
   ```

## JavaScript Architecture

The frontend uses a modular, robust architecture with unified data flow to ensure reliable operation.

### Module Structure

```
static/js/
├── logger.js           # Centralized logging system
├── llm-actions.js      # Main orchestrator (entry point)
├── config-manager.js   # Unified configuration and state management
├── prompt-manager.js   # Prompt selection and persistence
├── ui-config.js        # UI updates and event handling
└── field-selector.js   # Field mapping management
```

### Data Flow Architecture

```
1. Orchestrator (llm-actions.js)
   ├── Extracts context from URL parameters
   ├── Resolves step_id from database API
   └── Initializes modules in dependency order

2. Config Manager (config-manager.js)
   ├── Loads actions (task prompts)
   ├── Loads system prompts
   ├── Loads step settings
   ├── Populates prompt text content
   └── Provides unified state management

3. Prompt Manager (prompt-manager.js)
   ├── Delegates to config manager for state
   ├── Handles database persistence
   └── Manages prompt selection workflow

4. UI Config (ui-config.js)
   ├── Waits for config manager to be ready
   ├── Populates dropdowns with data
   ├── Attaches event listeners
   └── Updates UI based on state changes

5. Field Selector (field-selector.js)
   ├── Manages field mapping dropdowns
   ├── Handles field value persistence
   └── Provides field selection API
```

### Key Features

- **Single Source of Truth**: All configuration data flows through the config manager
- **Sequential Loading**: Prevents race conditions with proper dependency management
- **Robust Error Handling**: Graceful degradation when APIs fail
- **Module Registration**: Dynamic module discovery and initialization
- **Context Validation**: Proper validation before data operations
- **Unified State Management**: Consistent state across all modules

### Module Responsibilities

#### **Config Manager** (`config-manager.js`)
- **Primary Role**: Centralized state management and data loading
- **Key Methods**: 
  - `initialize(context)` - Load all configuration data
  - `setTaskPrompt(promptId)` - Unified task prompt setting
  - `setSystemPrompt(promptId)` - Unified system prompt setting
  - `populatePromptText()` - Load prompt content from database
- **State**: `CONFIG_STATE` - Global configuration state

#### **Prompt Manager** (`prompt-manager.js`)
- **Primary Role**: Handle prompt persistence to database
- **Key Methods**:
  - `setTaskPrompt(promptId)` - Set and save task prompt
  - `setSystemPrompt(promptId)` - Set and save system prompt
  - `saveStepSettings()` - Persist settings to database
- **Dependencies**: Delegates to config manager for state management

#### **UI Config** (`ui-config.js`)
- **Primary Role**: Manage UI elements and user interactions
- **Key Methods**:
  - `initialize()` - Setup UI and event listeners
  - `populateDropdowns()` - Load dropdown options
  - `updateUI()` - Refresh UI based on current state
  - `attachEventListeners()` - Handle user interactions
- **Features**: Waits for config manager, prevents duplicate listeners

#### **Field Selector** (`field-selector.js`)
- **Primary Role**: Manage field mapping selections
- **Key Methods**:
  - `initialize(context)` - Setup field selection system
  - `loadFieldData()` - Load field values and mappings
  - `saveFieldMapping()` - Persist field selections
- **Features**: Robust error handling, graceful API failures

#### **Orchestrator** (`llm-actions.js`)
- **Primary Role**: Coordinate module initialization and lifecycle
- **Key Methods**:
  - `initialize()` - Main entry point
  - `resolveStepId()` - Get step ID from database
  - `initModules()` - Initialize modules in correct order
  - `waitForModules()` - Ensure all modules are registered
- **Features**: Module registration system, proper initialization order

### Error Handling

The system implements comprehensive error handling:

- **Graceful Degradation**: Continues operation when non-critical APIs fail
- **Validation**: Checks for required data before operations
- **Logging**: Detailed logging for debugging and monitoring
- **User Feedback**: Clear error messages for users
- **State Recovery**: Initializes empty states on failures

### Performance Features

- **Sequential Loading**: Prevents race conditions
- **Module Registration**: Dynamic module discovery
- **Context Validation**: Prevents invalid operations
- **Error Recovery**: Continues operation despite failures
- **State Management**: Efficient state updates

## Access Points

### Web Interfaces
- **Main Interface**: `http://localhost:5002/` - Purple-themed LLM interface
- **Test Page**: `http://localhost:5002/test` - Comprehensive API testing

### API Endpoints
- **Health Check**: `http://localhost:5002/health`
- **LLM Config**: `http://localhost:5002/api/llm/config`
- **LLM Test**: `http://localhost:5002/api/llm/test`
- **LLM Actions**: `http://localhost:5002/api/llm/actions`
- **Execute Action**: `http://localhost:5002/api/llm/actions/<id>/execute`
- **General LLM**: `http://localhost:5002/api/run-llm`

## API Documentation

For complete API documentation, see:
- [LLM Actions Microservice API](../blog-core/docs/reference/api/current/llm_actions.md)
- [System Access Points Reference](../blog-core/docs/reference/access_points.md)

## Database Integration

This service shares the same PostgreSQL database as blog-core:
- **Tables**: `llm_action`, `llm_provider`, `llm_model`, `llm_prompt`, `llm_config`
- **Connection**: Via `DATABASE_URL` environment variable
- **Access**: Direct SQL via psycopg2

## Development

### Project Structure
```
blog-llm-actions/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── config.env         # Environment configuration
├── templates/         # HTML templates
│   └── index.html     # Main interface
├── static/            # Static assets
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript modules
│   │   ├── logger.js           # Logging system
│   │   ├── llm-actions.js      # Main orchestrator
│   │   ├── config-manager.js   # State management
│   │   ├── prompt-manager.js   # Prompt persistence
│   │   ├── ui-config.js        # UI management
│   │   └── field-selector.js   # Field mappings
│   └── test_api.html # Test interface
└── app/              # Application modules (if any)
```

### Testing

1. **Health Check**
   ```bash
   curl http://localhost:5002/health
   ```

2. **API Testing**
   - Visit `http://localhost:5002/test` for interactive testing
   - Use the built-in test interface for all endpoints

3. **LLM Testing**
   ```bash
   curl -X POST http://localhost:5002/api/llm/test \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello", "model": "mistral"}'
   ```

4. **Frontend Testing**
   - Open browser console to view detailed logging
   - Check for module initialization messages
   - Verify dropdown population and persistence

## Integration with blog-core

This service is designed to integrate with the main blog-core application:
- **API Communication**: REST APIs for inter-service communication
- **CORS Configuration**: Enabled for cross-origin requests
- **Shared Database**: Same PostgreSQL database as blog-core
- **Health Monitoring**: blog-core can monitor this service's health

## Environment Variables

### Required
```bash
DATABASE_URL=postgresql://username@localhost/blog
SECRET_KEY=your-secret-key
PORT=5002
```

### Optional
```bash
OLLAMA_API_URL=http://localhost:11434
OPENAI_API_KEY=your-openai-key
DEFAULT_LLM_MODEL=mistral
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 5002
   lsof -i :5002
   # Kill the process or use a different port
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   psql $DATABASE_URL -c "SELECT 1;"
   ```

3. **Ollama Not Running**
   ```bash
   # Start Ollama
   ollama serve
   # Or check if it's running
   curl http://localhost:11434/api/tags
   ```

4. **JavaScript Module Issues**
   ```bash
   # Check browser console for module loading errors
   # Verify all JS files are loading in correct order
   # Check for CORS issues if loading from different domain
   ```

### Debug Tools

- **Test Interface**: `http://localhost:5002/test`
- **Health Check**: `http://localhost:5002/health`
- **Logs**: Check console output for detailed logging
- **Browser Console**: View JavaScript module initialization and errors

## Related Documentation

- [Microservices Architecture Overview](../blog-core/docs/reference/microservices_overview.md)
- [Workflow System Integration](../blog-core/docs/workflow/README.md)
- [Database Schema](../blog-core/docs/reference/database/schema.md)
- [API Reference](../blog-core/docs/reference/api/current/README.md)

## License

This project is part of the blog system and follows the same licensing terms. 