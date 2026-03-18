# Deprecated Field Mapping Endpoints

## Overview

The following endpoints are deprecated and should not be used in new code. Use the standardized endpoints from the [current field mapping API](../current/fields.md) instead.

## Deprecated Endpoints

### 1. `/api/settings/field-mapping` (GET, POST)
- **Location**: `app/main/routes.py`
- **Replacement**: `/api/workflow/fields/mappings`
- **Status**: Deprecated with warning
- **Usage**: Still used by some legacy UI components

### 2. `/workflow_field_mapping` (GET)
- **Location**: `app/routes/settings.py`
- **Replacement**: `/api/workflow/fields/mappings/ui`
- **Status**: Deprecated with warning
- **Usage**: Legacy settings panel interface

### 3. `/api/field-mapping` (POST)
- **Location**: `app/routes/settings.py`
- **Replacement**: `/api/workflow/fields/mappings`
- **Status**: Deprecated with warning
- **Usage**: Legacy field mapping updates

### 4. `/workflow/api/field_mappings/` (GET)
- **Location**: `app/workflow/routes.py`
- **Replacement**: `/api/workflow/fields/mappings`
- **Status**: Deprecated with error
- **Usage**: Old workflow field mapping queries

## Migration Guide

### 1. Update API Configuration

```javascript
// Old configuration
const OLD_API = {
    FIELD_MAPPING: '/api/settings/field-mapping'
};

// New configuration
const API_CONFIG = {
    BASE_URL: '/api/workflow',
    ENDPOINTS: {
        FIELDS: {
            MAPPINGS: '/fields/mappings',
            MAPPINGS_UI: '/fields/mappings/ui'
        }
    }
};
```

### 2. Update API Calls

```javascript
// Old way
async function getFieldMappings() {
    const resp = await fetch('/api/settings/field-mapping');
    return resp.ok ? await resp.json() : [];
}

// New way
async function getFieldMappings() {
    const response = await fetch(
        `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.FIELDS.MAPPINGS}`
    );
    return await response.json();
}
```

### 3. Update Templates

```html
<!-- Old way -->
<form action="/workflow_field_mapping" method="POST">

<!-- New way -->
<form action="/api/workflow/fields/mappings" method="POST">
```

## Response Format Changes

### Old Format
```json
{
    "success": true,
    "mappings": [
        {
            "field_name": "idea_seed",
            "stage": "planning",
            "substage": "idea",
            "order": 1
        }
    ]
}
```

### New Format
```json
{
    "status": "success",
    "data": [
        {
            "field_name": "idea_seed",
            "stage_id": 10,
            "stage_name": "planning",
            "substage_id": 1,
            "substage_name": "idea",
            "order_index": 1
        }
    ]
}
```

## Known Issues

1. **Legacy UI Components**
   - Some older UI components still use deprecated endpoints
   - These will trigger deprecation warnings
   - Plan to update these components in future sprints

2. **Response Format Differences**
   - Old endpoints use inconsistent response formats
   - New endpoints standardize on the common response format
   - May need response transformation layer during migration

3. **Database Field Names**
   - Old endpoints use different field naming conventions
   - New endpoints standardize on snake_case
   - Data migration may be needed

## Testing During Migration

1. **Verify Old Functionality**
```bash
# Test old endpoint
curl -X GET http://localhost:5000/api/settings/field-mapping
```

2. **Test New Endpoint**
```bash
# Test new endpoint
curl -X GET http://localhost:5000/api/workflow/fields/mappings
```

3. **Compare Responses**
```bash
# Compare response formats
diff <(curl -s http://localhost:5000/api/settings/field-mapping) \
     <(curl -s http://localhost:5000/api/workflow/fields/mappings)
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