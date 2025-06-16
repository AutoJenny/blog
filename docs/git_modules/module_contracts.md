# Module API Contracts

This document defines the API contracts, data structures, and integration points for each module in the system. All modules must adhere to these contracts to ensure proper integration and operation.

---

## Core Principles

1. **Isolation**: Each module must be self-contained and not directly import from other modules
2. **Interface First**: All module interactions must go through defined interfaces
3. **Error Handling**: Consistent error response format across all modules
4. **Data Validation**: All data must be validated at module boundaries
5. **Versioning**: All APIs must support versioning

---

## Common Data Structures

### Error Response Format
```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": object,
        "module": "string"
    }
}
```

### Success Response Format
```json
{
    "data": object,
    "meta": {
        "timestamp": "ISO8601",
        "version": "string"
    }
}
```

---

## Module Contracts

### 1. Navigation Module (`nav`)

#### API Endpoints

##### GET /api/nav/structure
Returns the navigation structure for the current workflow stage.

**Request:**
- No parameters required

**Response:**
```json
{
    "data": {
        "current_stage": "string",
        "stages": [
            {
                "id": "string",
                "name": "string",
                "status": "string",
                "substages": [
                    {
                        "id": "string",
                        "name": "string",
                        "status": "string"
                    }
                ]
            }
        ]
    }
}
```

#### Events

##### nav:stage_changed
Emitted when the current stage changes.

**Payload:**
```json
{
    "old_stage": "string",
    "new_stage": "string",
    "timestamp": "ISO8601"
}
```

---

### 2. LLM Action Module (`llm_action`)

#### API Endpoints

##### POST /api/llm/process
Process an LLM action request.

**Request:**
```json
{
    "action_type": "string",
    "input_data": object,
    "config": {
        "model": "string",
        "temperature": number,
        "max_tokens": number
    }
}
```

**Response:**
```json
{
    "data": {
        "result": object,
        "processing_time": number,
        "tokens_used": number
    }
}
```

#### Events

##### llm:processing_started
Emitted when LLM processing begins.

**Payload:**
```json
{
    "action_type": "string",
    "timestamp": "ISO8601"
}
```

##### llm:processing_completed
Emitted when LLM processing completes.

**Payload:**
```json
{
    "action_type": "string",
    "result": object,
    "processing_time": number,
    "timestamp": "ISO8601"
}
```

---

### 3. Sections Module (`sections`)

#### API Endpoints

##### GET /api/sections/list
Get list of sections for current content.

**Request:**
- Query Parameters:
  - `content_id`: string (required)

**Response:**
```json
{
    "data": {
        "sections": [
            {
                "id": "string",
                "title": "string",
                "content": "string",
                "order": number,
                "status": "string"
            }
        ]
    }
}
```

##### POST /api/sections/reorder
Update section order.

**Request:**
```json
{
    "content_id": "string",
    "sections": [
        {
            "id": "string",
            "order": number
        }
    ]
}
```

#### Events

##### sections:reordered
Emitted when sections are reordered.

**Payload:**
```json
{
    "content_id": "string",
    "old_order": array,
    "new_order": array,
    "timestamp": "ISO8601"
}
```

---

## Integration Points

### 1. Database Integration

Each module must:
- Use the shared database connection pool
- Follow the defined schema for its tables
- Not modify tables owned by other modules
- Use transactions for multi-table operations

### 2. Event System

All modules must:
- Use the shared event bus
- Document all events they emit
- Handle all events they subscribe to
- Include timestamps in all events

### 3. Configuration

Each module must:
- Load configuration from environment variables
- Support configuration overrides
- Document all configuration options
- Validate configuration on startup

---

## Versioning

### API Versioning
- All API endpoints must include version in URL: `/api/v1/module/endpoint`
- Breaking changes require new version
- Support at least one previous version

### Module Versioning
- Each module must have a version number
- Version format: `major.minor.patch`
- Document breaking changes
- Support backward compatibility where possible

---

## Error Handling

### Error Codes
- `VALIDATION_ERROR`: 400
- `AUTHENTICATION_ERROR`: 401
- `AUTHORIZATION_ERROR`: 403
- `NOT_FOUND`: 404
- `CONFLICT`: 409
- `INTERNAL_ERROR`: 500

### Error Response Format
All error responses must follow the common error response format.

---

## Testing Requirements

Each module must provide:
1. Unit tests for all API endpoints
2. Integration tests for database operations
3. Event handling tests
4. Error handling tests
5. Performance benchmarks

---

## Documentation Requirements

Each module must provide:
1. API documentation
2. Event documentation
3. Configuration documentation
4. Database schema documentation
5. Example usage

---

## Security Requirements

1. Input validation at all boundaries
2. Proper error handling (no sensitive data in errors)
3. Rate limiting
4. Authentication where required
5. Authorization checks

---

## Performance Requirements

1. Response time < 200ms for API endpoints
2. Event processing < 100ms
3. Database queries < 50ms
4. Memory usage < 100MB per module
5. CPU usage < 10% per module 