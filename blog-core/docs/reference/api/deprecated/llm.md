# Deprecated LLM Endpoints

## Overview

The following endpoints are deprecated and should not be used in new code. Use the standardized endpoints from the [current LLM API](../current/llm.md) instead.

## Deprecated Endpoints

### 1. Provider Management

#### `/api/v1/llm/providers/start` (POST)
- **Location**: `app/main/routes.py`
- **Replacement**: `/api/workflow/providers/start`
- **Status**: Deprecated with warning
- **Usage**: Legacy provider initialization

#### `/api/v1/llm/providers/<provider_id>/test` (POST)
- **Location**: `app/main/routes.py`
- **Replacement**: `/api/workflow/providers/<provider_id>/test`
- **Status**: Deprecated with warning
- **Usage**: Legacy provider testing

#### `/api/v1/llm/test` (POST)
- **Location**: `app/llm/routes.py`
- **Replacement**: `/api/workflow/providers/<provider_id>/test`
- **Status**: Deprecated with warning
- **Usage**: Generic LLM testing endpoint

#### `/api/v1/llm/models` (GET)
- **Location**: `app/llm/routes.py`
- **Replacement**: `/api/workflow/providers/<provider_id>/models`
- **Status**: Deprecated with warning
- **Usage**: Legacy model listing

#### `/api/v1/llm/providers` (GET)
- **Location**: `app/llm/routes.py`
- **Replacement**: `/api/workflow/providers`
- **Status**: Deprecated with warning
- **Usage**: Legacy provider listing

### 2. Action Management

#### `/api/v1/llm/actions/<action_id>` (GET)
- **Location**: `app/llm/routes.py`
- **Replacement**: `/api/workflow/llm/actions/<action_id>`
- **Status**: Deprecated with warning
- **Usage**: Legacy action details endpoint

#### `/api/v1/workflow/run_llm/` (POST)
- **Location**: `app/workflow/routes.py`
- **Replacement**: `/api/workflow/llm/run`
- **Status**: Deprecated with error (410 Gone)
- **Usage**: Legacy action execution endpoint

## Migration Guide

### 1. Update API Configuration

```javascript
// Old configuration
const OLD_API = {
    LLM: {
        PROVIDERS: '/api/v1/llm/providers',
        ACTIONS: '/api/v1/llm/actions',
        RUN: '/api/v1/workflow/run_llm/'
    }
};

// New configuration
const API_CONFIG = {
    BASE_URL: '/api/workflow',
    ENDPOINTS: {
        PROVIDERS: '/providers',
        LLM: {
            ACTIONS: '/llm/actions',
            RUN: '/llm/run'
        }
    }
};
```

### 2. Update API Calls

```javascript
// Old way - List providers
fetch('/api/v1/llm/providers')
    .then(response => response.json());

// New way - List providers
fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PROVIDERS}`)
    .then(response => response.json());

// Old way - Run action
fetch('/api/v1/workflow/run_llm/', {
    method: 'POST',
    body: JSON.stringify({
        action: 'generate_idea',
        data: {}
    })
});

// New way - Run action
fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.LLM.RUN}`, {
    method: 'POST',
    body: JSON.stringify({
        action_id: 1,
        input_data: {}
    })
});
```

### 3. Response Format Changes

#### Old Provider Response Format
```json
{
    "providers": [
        {
            "id": 1,
            "name": "ollama",
            "url": "http://localhost:11434"
        }
    ]
}
```

#### New Provider Response Format
```json
{
    "status": "success",
    "data": {
        "providers": [
            {
                "id": 1,
                "name": "ollama",
                "endpoint": "http://localhost:11434",
                "status": "active",
                "models": ["llama2", "mistral"]
            }
        ]
    }
}
```

#### Old Action Response Format
```json
{
    "success": true,
    "result": "Generated content...",
    "error": null
}
```

#### New Action Response Format
```json
{
    "status": "success",
    "data": {
        "action_run": {
            "id": "abc123",
            "action_id": 1,
            "status": "completed",
            "output": {
                "content": "Generated content..."
            },
            "metrics": {
                "duration": 2.34,
                "tokens": 156
            }
        }
    }
}
```

## Known Issues

1. **Provider Configuration**
   - Old endpoints use inconsistent provider settings
   - Some hardcode provider URLs
   - Configuration not stored in database

2. **Action Parameters**
   - Old endpoints use varying parameter formats
   - Some lack proper validation
   - Error handling is inconsistent

3. **Response Formats**
   - Old endpoints use different response structures
   - Error formats vary between endpoints
   - Some lack proper status codes

## Testing During Migration

1. **Verify Old Functionality**
```bash
# Test old provider endpoint
curl -X GET http://localhost:5000/api/v1/llm/providers

# Test old action endpoint
curl -X POST http://localhost:5000/api/v1/workflow/run_llm/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "generate_idea",
    "data": {
      "topic": "test"
    }
  }'
```

2. **Test New Endpoints**
```bash
# Test new provider endpoint
curl -X GET http://localhost:5000/api/workflow/providers

# Test new action endpoint
curl -X POST http://localhost:5000/api/workflow/llm/run \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": 1,
    "input_data": {
      "topic": "test"
    }
  }'
```

## Database Changes

### Old Schema
```sql
CREATE TABLE llm_provider (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL
);

CREATE TABLE llm_action (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    provider_id INTEGER REFERENCES llm_provider(id)
);
```

### New Schema
```sql
CREATE TABLE llm_provider (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'inactive',
    config JSONB
);

CREATE TABLE llm_action (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    provider_id INTEGER REFERENCES llm_provider(id),
    input_schema JSONB,
    output_schema JSONB,
    examples JSONB[],
    version TEXT NOT NULL DEFAULT '1.0'
);
```

## Deprecation Timeline

1. **Phase 1 (Current)**
   - Deprecation warnings added
   - New endpoints available
   - Old endpoints still functional

2. **Phase 2 (Next Release)**
   - Error responses from old endpoints
   - Migration guide published
   - Legacy support ending

3. **Phase 3 (Future)**
   - Old endpoints removed
   - All systems using new endpoints
   - Complete migration required

## Support

For migration assistance:
1. Check the current API documentation
2. Review this deprecation guide
3. Test thoroughly with curl
4. Contact maintainers if needed 