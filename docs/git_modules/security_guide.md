# Security & Access Control Guide

This document outlines the security practices and access control patterns for the blog system, emphasizing our no-login approach and database security measures.

---

## Core Security Principles

### 1. No Authentication System

The blog system explicitly does not use login or authentication systems. This is a core design principle that must be maintained.

```python
# DO NOT implement any of these:
# - User authentication
# - Login systems
# - Registration
# - Password management
# - Session handling
```

### 2. Database Access Control

#### Connection Security
```python
def get_db_conn():
    """Get database connection with proper security measures."""
    from dotenv import load_dotenv
    import os
    import psycopg2
    
    # Always reload environment variables
    load_dotenv('assistant_config.env')
    
    # Use SSL if available
    ssl_mode = 'require' if os.getenv('DB_SSL', 'false').lower() == 'true' else 'disable'
    
    return psycopg2.connect(
        os.getenv('DATABASE_URL'),
        sslmode=ssl_mode
    )
```

#### Query Security
```python
def safe_query(query, params=None):
    """Execute query with security measures."""
    # Validate query type
    if not query.strip().upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
        raise SecurityError("Invalid query type")
    
    # Use parameterized queries
    return execute_query(query, params or {})
```

---

## Environment Variable Management

### 1. Configuration Loading

```python
def load_config():
    """Load configuration with security measures."""
    from dotenv import load_dotenv
    import os
    
    # Always reload from file
    load_dotenv('assistant_config.env')
    
    # Required variables
    required = ['DATABASE_URL', 'FLASK_ENV']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")
```

### 2. Sensitive Data Handling

```python
def handle_sensitive_data(data):
    """Handle sensitive data with proper security measures."""
    # Never log sensitive data
    # Never store in plain text
    # Never expose in responses
    return {
        'id': data['id'],
        'status': data['status']
        # Exclude sensitive fields
    }
```

---

## Database Security

### 1. Connection Management

#### Connection Pooling
```python
def get_connection_pool():
    """Get database connection pool with security settings."""
    from psycopg2 import pool
    
    return pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=os.getenv('DATABASE_URL'),
        sslmode='require' if os.getenv('DB_SSL', 'false').lower() == 'true' else 'disable'
    )
```

#### Connection Cleanup
```python
def cleanup_connections():
    """Clean up database connections."""
    if hasattr(get_connection_pool, 'pool'):
        get_connection_pool.pool.closeall()
```

### 2. Query Security

#### Input Validation
```python
def validate_input(data):
    """Validate input data for security."""
    # Check for SQL injection attempts
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']
    for key, value in data.items():
        if any(keyword in str(value).upper() for keyword in sql_keywords):
            raise SecurityError("Potential SQL injection attempt")
    
    return data
```

#### Query Sanitization
```python
def sanitize_query(query):
    """Sanitize query for security."""
    # Remove comments
    query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    
    # Remove multiple statements
    if ';' in query:
        raise SecurityError("Multiple statements not allowed")
    
    return query
```

---

## Module Security

### 1. Route Security

#### Route Protection
```python
def secure_route(f):
    """Decorator for route security."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check request origin
        if not is_valid_origin(request):
            return jsonify({'error': 'Invalid origin'}), 403
        
        # Check request method
        if request.method not in ['GET', 'POST']:
            return jsonify({'error': 'Method not allowed'}), 405
        
        return f(*args, **kwargs)
    return decorated_function
```

#### Request Validation
```python
def validate_request():
    """Validate incoming request."""
    # Check content type
    if request.method == 'POST' and not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    # Check request size
    if request.content_length and request.content_length > 1024 * 1024:  # 1MB
        return jsonify({'error': 'Request too large'}), 413
```

### 2. Response Security

#### Response Headers
```python
def secure_response(response):
    """Add security headers to response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

#### Error Handling
```python
def handle_error(error):
    """Handle errors securely."""
    # Log error internally
    log_error(error)
    
    # Return safe error message
    return jsonify({
        'error': 'An error occurred',
        'status': 'error'
    }), 500
```

---

## Best Practices

### 1. General Security
- Never implement login/authentication
- Use environment variables for configuration
- Validate all input
- Sanitize all output
- Use parameterized queries
- Handle errors securely

### 2. Database Security
- Use connection pooling
- Implement query validation
- Use SSL for connections
- Clean up connections
- Validate database operations

### 3. Module Security
- Validate all requests
- Secure all responses
- Handle errors properly
- Log security events
- Monitor for issues

### 4. Environment Security
- Use secure configuration
- Protect sensitive data
- Monitor environment
- Update dependencies
- Review security regularly

---

## Common Issues

### 1. Security Misconfigurations
- Missing environment variables
- Incorrect permissions
- Insecure connections
- Unvalidated input

### 2. Database Issues
- Connection leaks
- Query injection
- Permission errors
- SSL issues

### 3. Module Issues
- Insecure routes
- Unvalidated requests
- Unsafe responses
- Error exposure

---

## References

### 1. Security
- [Database Security](docs/database/security.md)
- [Environment Security](docs/security/environment.md)

### 2. Configuration
- [Environment Variables](docs/configuration/env_vars.md)
- [Database Configuration](docs/database/configuration.md)

### 3. Best Practices
- [Security Checklist](docs/security/checklist.md)
- [Code Review Guide](docs/security/code_review.md) 