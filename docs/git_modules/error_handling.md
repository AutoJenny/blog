# Error Handling & Recovery Guide

This document outlines the error handling patterns and recovery procedures for the blog system, with a focus on database operations and module error handling.

---

## Database Error Handling

### 1. Connection Errors

#### Connection Recovery
```python
def get_db_conn_with_retry(max_retries=3, delay=1):
    """Get database connection with retry logic."""
    from time import sleep
    import psycopg2
    
    for attempt in range(max_retries):
        try:
            return get_db_conn()
        except psycopg2.OperationalError as e:
            if attempt == max_retries - 1:
                raise DatabaseError(f"Failed to connect after {max_retries} attempts: {str(e)}")
            sleep(delay)
```

#### Connection Pool Recovery
```python
def get_pool_connection():
    """Get connection from pool with recovery."""
    try:
        return get_connection_pool().getconn()
    except psycopg2.pool.PoolError:
        # Recreate pool
        cleanup_connections()
        return get_connection_pool().getconn()
```

### 2. Query Errors

#### Query Error Handling
```python
def execute_query_with_error_handling(query, params=None):
    """Execute query with comprehensive error handling."""
    conn = None
    try:
        conn = get_db_conn_with_retry()
        with conn.cursor() as cur:
            cur.execute(query, params or {})
            if cur.description:  # SELECT query
                return cur.fetchall()
            conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise DatabaseError(f"Query failed: {str(e)}")
    finally:
        if conn:
            conn.close()
```

#### Transaction Error Handling
```python
def execute_transaction(operations):
    """Execute multiple operations in a transaction."""
    conn = None
    try:
        conn = get_db_conn_with_retry()
        with conn.cursor() as cur:
            for operation in operations:
                cur.execute(operation['query'], operation.get('params'))
            conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise DatabaseError(f"Transaction failed: {str(e)}")
    finally:
        if conn:
            conn.close()
```

---

## Module Error Handling

### 1. Route Error Handling

#### Route Error Decorator
```python
def handle_route_errors(f):
    """Decorator for route error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except DatabaseError as e:
            return jsonify({'error': 'Database error', 'details': str(e)}), 500
        except ValidationError as e:
            return jsonify({'error': 'Validation error', 'details': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal error', 'details': str(e)}), 500
    return decorated_function
```

#### Request Validation
```python
def validate_request_data(data, schema):
    """Validate request data against schema."""
    try:
        return schema.validate(data)
    except ValidationError as e:
        raise ValidationError(f"Invalid request data: {str(e)}")
```

### 2. LLM Error Handling

#### LLM Action Error Handling
```python
def execute_llm_action_with_retry(action_id, input_data, max_retries=3):
    """Execute LLM action with retry logic."""
    for attempt in range(max_retries):
        try:
            return execute_llm_action(action_id, input_data)
        except LLMError as e:
            if attempt == max_retries - 1:
                raise LLMError(f"LLM action failed after {max_retries} attempts: {str(e)}")
            sleep(1)
```

#### Prompt Error Handling
```python
def validate_prompt_template(template):
    """Validate prompt template."""
    if not template:
        raise ValidationError("Prompt template is required")
    
    if not isinstance(template, (str, dict)):
        raise ValidationError("Prompt template must be string or dict")
    
    return template
```

---

## Recovery Procedures

### 1. Database Recovery

#### Backup Procedure
```python
def backup_database():
    """Create database backup."""
    import subprocess
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'blog_backup_{timestamp}.sql'
    
    try:
        subprocess.run([
            'pg_dump',
            '-U', os.getenv('DB_USER'),
            '-d', os.getenv('DB_NAME'),
            '-f', backup_file
        ], check=True)
        return backup_file
    except subprocess.CalledProcessError as e:
        raise BackupError(f"Backup failed: {str(e)}")
```

#### Restore Procedure
```python
def restore_database(backup_file):
    """Restore database from backup."""
    import subprocess
    
    try:
        subprocess.run([
            'psql',
            '-U', os.getenv('DB_USER'),
            '-d', os.getenv('DB_NAME'),
            '-f', backup_file
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise RestoreError(f"Restore failed: {str(e)}")
```

### 2. Module Recovery

#### Module State Recovery
```python
def recover_module_state(module_name):
    """Recover module state after error."""
    try:
        # Reset module state
        reset_module_state(module_name)
        
        # Reload module configuration
        reload_module_config(module_name)
        
        # Verify module health
        verify_module_health(module_name)
    except Exception as e:
        raise RecoveryError(f"Module recovery failed: {str(e)}")
```

#### Workflow Recovery
```python
def recover_workflow_state(post_id):
    """Recover workflow state after error."""
    try:
        # Get last known good state
        last_state = get_last_known_state(post_id)
        
        # Restore workflow state
        restore_workflow_state(post_id, last_state)
        
        # Verify workflow health
        verify_workflow_health(post_id)
    except Exception as e:
        raise RecoveryError(f"Workflow recovery failed: {str(e)}")
```

---

## Error Monitoring

### 1. Error Logging

#### Error Logger
```python
def log_error(error, context=None):
    """Log error with context."""
    import logging
    
    logging.error({
        'error': str(error),
        'type': type(error).__name__,
        'context': context or {},
        'timestamp': datetime.now().isoformat()
    })
```

#### Error Metrics
```python
def track_error_metrics(error_type):
    """Track error metrics."""
    # Increment error counter
    increment_error_counter(error_type)
    
    # Update error rate
    update_error_rate(error_type)
    
    # Check error thresholds
    check_error_thresholds(error_type)
```

### 2. Error Reporting

#### Error Report
```python
def generate_error_report():
    """Generate error report."""
    return {
        'total_errors': get_total_errors(),
        'error_types': get_error_types(),
        'error_rates': get_error_rates(),
        'recent_errors': get_recent_errors()
    }
```

#### Health Check
```python
def check_system_health():
    """Check system health."""
    return {
        'database': check_database_health(),
        'modules': check_modules_health(),
        'workflow': check_workflow_health(),
        'llm': check_llm_health()
    }
```

---

## Best Practices

### 1. Error Handling
- Use specific error types
- Implement retry logic
- Handle all exceptions
- Log errors properly
- Monitor error rates

### 2. Recovery
- Create regular backups
- Test restore procedures
- Implement state recovery
- Verify system health
- Document recovery steps

### 3. Monitoring
- Track error metrics
- Set error thresholds
- Generate error reports
- Monitor system health
- Alert on issues

### 4. Documentation
- Document error types
- Document recovery steps
- Document monitoring
- Document alerts
- Document thresholds

---

## Common Issues

### 1. Database Issues
- Connection failures
- Query timeouts
- Transaction errors
- Backup failures
- Restore issues

### 2. Module Issues
- State corruption
- Configuration errors
- Workflow errors
- LLM errors
- Recovery failures

### 3. Monitoring Issues
- Missing logs
- False alerts
- Metric gaps
- Report delays
- Threshold issues

---

## References

### 1. Error Handling
- [Database Errors](docs/database/errors.md)
- [Module Errors](docs/modules/errors.md)

### 2. Recovery
- [Database Recovery](docs/database/recovery.md)
- [Module Recovery](docs/modules/recovery.md)

### 3. Monitoring
- [Error Monitoring](docs/monitoring/errors.md)
- [Health Checks](docs/monitoring/health.md) 