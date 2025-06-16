# Monitoring and Logging Guide

This document outlines monitoring and logging standards for the blog system, focusing on system monitoring, error tracking, and performance logging.

---

## System Monitoring

### 1. Health Checks

#### Basic Health Check
```python
def check_system_health():
    """Check system health."""
    checks = {
        'database': check_database_health(),
        'cache': check_cache_health(),
        'llm': check_llm_health(),
        'disk': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    return {
        'status': 'healthy' if all(checks.values()) else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    }
```

#### Detailed Health Check
```python
def check_database_health():
    """Check database health."""
    try:
        # Check connection
        conn = get_db_connection()
        
        # Check query performance
        start_time = time.time()
        execute_query("SELECT 1")
        query_time = time.time() - start_time
        
        # Check connection pool
        pool_stats = get_connection_pool_stats()
        
        return {
            'status': 'healthy',
            'query_time': query_time,
            'pool_stats': pool_stats
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
```

### 2. Resource Monitoring

#### System Resources
```python
def monitor_system_resources():
    """Monitor system resources."""
    return {
        'cpu': {
            'usage': psutil.cpu_percent(),
            'count': psutil.cpu_count()
        },
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'free': psutil.disk_usage('/').free,
            'percent': psutil.disk_usage('/').percent
        }
    }
```

#### Application Resources
```python
def monitor_application_resources():
    """Monitor application resources."""
    return {
        'database': {
            'connections': get_db_connection_count(),
            'queries': get_query_count(),
            'cache_hits': get_cache_hit_count()
        },
        'workflow': {
            'active_stages': get_active_stage_count(),
            'pending_tasks': get_pending_task_count(),
            'llm_requests': get_llm_request_count()
        }
    }
```

---

## Error Tracking

### 1. Error Logging

#### Basic Error Logging
```python
def log_error(error, context=None):
    """Log error with context."""
    error_data = {
        'error': str(error),
        'type': type(error).__name__,
        'timestamp': datetime.now().isoformat(),
        'context': context or {}
    }
    
    # Log to file
    with open('logs/errors.log', 'a') as f:
        json.dump(error_data, f)
        f.write('\n')
    
    # Log to monitoring system
    log_to_monitoring_system('error', error_data)
    
    return error_data
```

#### Detailed Error Logging
```python
def log_workflow_error(error, post_id, stage_id):
    """Log workflow error with details."""
    error_data = {
        'error': str(error),
        'type': type(error).__name__,
        'timestamp': datetime.now().isoformat(),
        'post_id': post_id,
        'stage_id': stage_id,
        'stage_data': get_stage_data(post_id, stage_id),
        'workflow_state': get_workflow_state(post_id)
    }
    
    # Log to file
    with open('logs/workflow_errors.log', 'a') as f:
        json.dump(error_data, f)
        f.write('\n')
    
    # Log to monitoring system
    log_to_monitoring_system('workflow_error', error_data)
    
    return error_data
```

### 2. Error Analysis

#### Error Aggregation
```python
def aggregate_errors(timeframe='1h'):
    """Aggregate errors by type and frequency."""
    query = """
    SELECT error_type, COUNT(*) as count
    FROM error_log
    WHERE timestamp > NOW() - INTERVAL %s
    GROUP BY error_type
    ORDER BY count DESC
    """
    return execute_query(query, (timeframe,))
```

#### Error Trends
```python
def analyze_error_trends(timeframe='24h'):
    """Analyze error trends over time."""
    query = """
    SELECT 
        date_trunc('hour', timestamp) as hour,
        error_type,
        COUNT(*) as count
    FROM error_log
    WHERE timestamp > NOW() - INTERVAL %s
    GROUP BY hour, error_type
    ORDER BY hour DESC
    """
    return execute_query(query, (timeframe,))
```

---

## Performance Logging

### 1. Query Performance

#### Query Timing
```python
def log_query_performance(query, params, duration):
    """Log query performance."""
    query_data = {
        'query': query,
        'params': params,
        'duration': duration,
        'timestamp': datetime.now().isoformat()
    }
    
    # Log to file
    with open('logs/query_performance.log', 'a') as f:
        json.dump(query_data, f)
        f.write('\n')
    
    # Log to monitoring system
    log_to_monitoring_system('query_performance', query_data)
    
    return query_data
```

#### Query Analysis
```python
def analyze_query_performance(timeframe='1h'):
    """Analyze query performance."""
    query = """
    SELECT 
        query,
        AVG(duration) as avg_duration,
        MAX(duration) as max_duration,
        COUNT(*) as execution_count
    FROM query_performance_log
    WHERE timestamp > NOW() - INTERVAL %s
    GROUP BY query
    ORDER BY avg_duration DESC
    """
    return execute_query(query, (timeframe,))
```

### 2. Workflow Performance

#### Stage Timing
```python
def log_stage_performance(post_id, stage_id, duration):
    """Log stage performance."""
    stage_data = {
        'post_id': post_id,
        'stage_id': stage_id,
        'duration': duration,
        'timestamp': datetime.now().isoformat()
    }
    
    # Log to file
    with open('logs/stage_performance.log', 'a') as f:
        json.dump(stage_data, f)
        f.write('\n')
    
    # Log to monitoring system
    log_to_monitoring_system('stage_performance', stage_data)
    
    return stage_data
```

#### LLM Performance
```python
def log_llm_performance(action, prompt, duration):
    """Log LLM performance."""
    llm_data = {
        'action': action,
        'prompt_length': len(prompt),
        'duration': duration,
        'timestamp': datetime.now().isoformat()
    }
    
    # Log to file
    with open('logs/llm_performance.log', 'a') as f:
        json.dump(llm_data, f)
        f.write('\n')
    
    # Log to monitoring system
    log_to_monitoring_system('llm_performance', llm_data)
    
    return llm_data
```

---

## Best Practices

### 1. System Monitoring
- Monitor system health
- Track resource usage
- Set up alerts
- Monitor performance
- Track errors

### 2. Error Tracking
- Log all errors
- Include context
- Track trends
- Set up alerts
- Analyze patterns

### 3. Performance Logging
- Log query performance
- Track stage timing
- Monitor LLM usage
- Analyze trends
- Set up alerts

### 4. General Monitoring
- Use appropriate tools
- Set up dashboards
- Configure alerts
- Regular analysis
- Document issues

---

## Common Issues

### 1. Monitoring Issues
- Missing metrics
- False alerts
- Resource usage
- Data retention
- Alert fatigue

### 2. Error Issues
- Missing context
- Duplicate errors
- Alert spam
- Error patterns
- Resolution tracking

### 3. Performance Issues
- Slow queries
- Stage delays
- LLM latency
- Resource limits
- Bottlenecks

### 4. General Issues
- Log rotation
- Storage limits
- Data analysis
- Alert management
- Documentation

---

## References

### 1. System Monitoring
- [Health Guide](docs/monitoring/health.md)
- [Resource Guide](docs/monitoring/resources.md)

### 2. Error Tracking
- [Error Guide](docs/monitoring/errors.md)
- [Analysis Guide](docs/monitoring/analysis.md)

### 3. Performance Logging
- [Query Guide](docs/monitoring/queries.md)
- [Stage Guide](docs/monitoring/stages.md)

### 4. General Monitoring
- [Tool Guide](docs/monitoring/tools.md)
- [Alert Guide](docs/monitoring/alerts.md) 