# API and Route Reference Documentation

## Overview

This directory contains comprehensive documentation for all API endpoints and routes in the system. It is organized to clearly distinguish between current (standardized) endpoints and deprecated ones that should be avoided.

## Directory Structure

```
/reference/
├── api/
│   ├── current/          # Current standardized API endpoints
│   └── deprecated/       # Old endpoints that must be avoided
└── routes/              # UI route documentation
    ├── current/         # Current route structure
    └── deprecated/      # Old routes to avoid
```

## Key Principles

1. **API Standardization**
   - All new endpoints use `/api/` prefix
   - Consistent RESTful patterns
   - Standard response formats
   - Proper error handling

2. **Route Organization**
   - Clear separation of concerns
   - Consistent naming conventions
   - Logical grouping by function

3. **Database Integration**
   - Direct SQL via psycopg2 (no ORM)
   - PostgreSQL only
   - Proper connection management

## Common Response Format

All API endpoints follow this standard response format:

```json
{
    "status": "success|error",
    "data": {
        // Response data object
    },
    "message": "Optional status message",
    "errors": [
        // Array of error messages if status is "error"
    ]
}
```

## Important Notes

1. **Authentication**
   - This system does NOT use authentication or login
   - Never add authentication-related code

2. **Database**
   - PostgreSQL only
   - No SQLite support
   - No ORM (SQLAlchemy removed)

3. **LLM Integration**
   - Local LLM provider (e.g., Ollama)
   - Provider configuration via database
   - No hardcoded provider settings

## Navigation

- [Current API Documentation](api/current/)
- [Deprecated APIs](api/deprecated/)
- [Current Routes](routes/current/)
- [Deprecated Routes](routes/deprecated/)
- **[Flask Logging Guide](flask_logging_guide.md)** - Critical for debugging and development
- **[Logging Quick Reference](logging_quick_reference.md)** - Fast reference for immediate use

## Usage Guidelines

1. **For New Development**
   - Always use endpoints from `/api/current/`
   - Follow the standardized patterns
   - Use proper error handling
   - Test with curl before implementation

2. **Dealing with Legacy Code**
   - Check deprecated documentation
   - Use migration guides
   - Follow upgrade paths
   - Test thoroughly when replacing old endpoints

3. **Testing Requirements**
   - All endpoints must be tested with curl
   - Document all test cases
   - Include error scenarios
   - Verify response formats

4. **Logging Requirements**
   - **ALWAYS use direct file logging for debugging** (see [Flask Logging Guide](flask_logging_guide.md))
   - Never rely on Flask's built-in logging system
   - Test logging before claiming functionality works
   - Use descriptive log messages with timestamps

## Support

For technical issues:
1. Check this reference documentation
2. Review relevant migration guides
3. Test endpoints with curl
4. Contact project maintainers 