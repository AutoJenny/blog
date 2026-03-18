# Deprecated Workflow Endpoints

## Overview

The following endpoints are deprecated and should not be used in new code. Use the standardized endpoints from the current API documentation instead.

## Deprecated Endpoints

### 1. LLM Related Endpoints

#### `/api/v1/workflow/run_llm/` (POST)
- **Location**: `app/workflow/routes.py`
- **Replacement**: `/api/workflow/llm/run`
- **Status**: Deprecated with error (410 Gone)
- **Usage**: Legacy LLM execution endpoint

#### `/api/workflow/llm/` (POST)
- **Location**: `app/workflow/routes.py`
- **Replacement**: `/api/workflow/llm/run`
- **Status**: Deprecated with error (410 Gone)
- **Usage**: Legacy LLM endpoint

### 2. Post Development Endpoints

#### `/blog/api/v1/post/<post_id>/development` (GET, POST)
- **Location**: `app/llm/routes.py`
- **Replacement**: `/api/workflow/posts/<post_id>/development`
- **Status**: Deprecated with warning
- **Usage**: Legacy post development data endpoint

#### `/api/v1/post/<post_id>/development` (GET, POST)
- **Location**: Multiple files
- **Replacement**: `/api/workflow/posts/<post_id>/development`
- **Status**: Deprecated with warning
- **Usage**: Duplicate post development endpoint

#### `/api/v1/posts/<post_id>/development` (GET, POST)
- **Location**: Multiple files
- **Replacement**: `/api/workflow/posts/<post_id>/development`
- **Status**: Deprecated with warning
- **Usage**: Another duplicate post development endpoint

### 3. Structure Related Endpoints

#### `/api/v1/structure/plan` (POST)
- **Location**: `archive2/js_workflow/structure_stage.js`
- **Replacement**: `/api/workflow/posts/<post_id>/structure/plan`
- **Status**: Deprecated with warning
- **Usage**: Legacy structure planning endpoint

#### `/api/v1/structure/save/<post_id>` (POST)
- **Location**: `archive2/js_workflow/structure_stage.js`
- **Replacement**: `/api/workflow/posts/<post_id>/structure/save`
- **Status**: Deprecated with warning
- **Usage**: Legacy structure saving endpoint

### 4. Title Order Endpoints

#### `/api/v1/workflow/title_order/` (POST)
- **Location**: `app/workflow/routes.py`
- **Replacement**: `/api/workflow/posts/<post_id>/title_order`
- **Status**: Deprecated with error (410 Gone)
- **Usage**: Legacy title order update endpoint

## Migration Guide

### 1. Update API Configuration

```javascript
// Old configuration
const OLD_API = {
    WORKFLOW: {
        RUN_LLM: '/api/v1/workflow/run_llm/',
        STRUCTURE: '/api/v1/structure/'
    }
};

// New configuration
const API_CONFIG = {
    BASE_URL: '/api/workflow',
    ENDPOINTS: {
        LLM: '/llm/run',
        POSTS: '/posts',
        STRUCTURE: '/structure'
    }
};
```

### 2. Update API Calls

```javascript
// Old way - LLM
fetch('/api/v1/workflow/run_llm/', {
    method: 'POST',
    body: JSON.stringify(data)
});

// New way - LLM
fetch(`${API_CONFIG.BASE_URL}/llm/run`, {
    method: 'POST',
    body: JSON.stringify(data)
});

// Old way - Structure
fetch('/api/v1/structure/plan', {
    method: 'POST',
    body: JSON.stringify(data)
});

// New way - Structure
fetch(`${API_CONFIG.BASE_URL}/posts/${postId}/structure/plan`, {
    method: 'POST',
    body: JSON.stringify(data)
});
```

### 3. Response Format Changes

#### Old Format (varies by endpoint)
```json
{
    "success": true,
    "data": {},
    "error": null
}
```

#### New Format (standardized)
```json
{
    "status": "success",
    "data": {},
    "message": "Optional message",
    "errors": []
}
```

## Known Issues

1. **Inconsistent Response Formats**
   - Old endpoints use varying response formats
   - Some return `success`, others use `status`
   - Error handling differs between endpoints

2. **Missing Parameters**
   - Some old endpoints lack proper validation
   - Required parameters may not be enforced
   - Error responses may be inconsistent

3. **Database Inconsistencies**
   - Old endpoints may use outdated table schemas
   - Some field names differ from current standards
   - Foreign key relationships may be missing

## Testing During Migration

1. **Verify Old Functionality**
```bash
# Test old LLM endpoint
curl -X POST http://localhost:5000/api/v1/workflow/run_llm/ \
  -H "Content-Type: application/json" \
  -d '{"action": "test"}'

# Test old structure endpoint
curl -X POST http://localhost:5000/api/v1/structure/plan \
  -H "Content-Type: application/json" \
  -d '{"post_id": 1}'
```

2. **Test New Endpoints**
```bash
# Test new LLM endpoint
curl -X POST http://localhost:5000/api/workflow/llm/run \
  -H "Content-Type: application/json" \
  -d '{"action_id": 1}'

# Test new structure endpoint
curl -X POST http://localhost:5000/api/workflow/posts/1/structure/plan \
  -H "Content-Type: application/json" \
  -d '{}'
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