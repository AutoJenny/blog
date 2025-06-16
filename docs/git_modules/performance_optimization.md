# Performance Optimization Guide

This document outlines performance optimization strategies for the blog system, focusing on database optimization, caching, and workflow performance.

---

## Database Optimization

### 1. Query Optimization

#### Index Usage
```python
def create_post_indexes():
    """Create indexes for post table."""
    queries = [
        "CREATE INDEX IF NOT EXISTS idx_post_status ON post(status)",
        "CREATE INDEX IF NOT EXISTS idx_post_created ON post(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_post_updated ON post(updated_at)"
    ]
    
    for query in queries:
        execute_query(query)
```

#### Query Optimization
```python
def get_posts_by_status(status, limit=10):
    """Get posts by status with optimized query."""
    query = """
    SELECT p.*, 
           COUNT(c.id) as comment_count,
           MAX(c.created_at) as last_comment
    FROM post p
    LEFT JOIN comment c ON p.id = c.post_id
    WHERE p.status = %s
    GROUP BY p.id
    ORDER BY p.updated_at DESC
    LIMIT %s
    """
    return execute_query(query, (status, limit))
```

### 2. Connection Management

#### Connection Pooling
```python
def get_db_pool():
    """Get database connection pool."""
    return psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def get_db_connection():
    """Get database connection from pool."""
    return db_pool.getconn()
```

#### Connection Cleanup
```python
def release_db_connection(conn):
    """Release database connection back to pool."""
    db_pool.putconn(conn)

def cleanup_db_connections():
    """Cleanup database connections."""
    db_pool.closeall()
```

---

## Caching Strategy

### 1. Response Caching

#### API Response Cache
```python
def cache_api_response(key, data, ttl=300):
    """Cache API response."""
    cache_key = f'api:{key}'
    cache.set(cache_key, data, ttl)

def get_cached_response(key):
    """Get cached API response."""
    cache_key = f'api:{key}'
    return cache.get(cache_key)
```

#### Workflow Cache
```python
def cache_workflow_data(post_id, stage_id, data, ttl=300):
    """Cache workflow data."""
    cache_key = f'workflow:{post_id}:{stage_id}'
    cache.set(cache_key, data, ttl)

def get_cached_workflow(post_id, stage_id):
    """Get cached workflow data."""
    cache_key = f'workflow:{post_id}:{stage_id}'
    return cache.get(cache_key)
```

### 2. Query Caching

#### Query Result Cache
```python
def cache_query_result(query, params, result, ttl=300):
    """Cache query result."""
    cache_key = f'query:{hash(query + str(params))}'
    cache.set(cache_key, result, ttl)

def get_cached_query(query, params):
    """Get cached query result."""
    cache_key = f'query:{hash(query + str(params))}'
    return cache.get(cache_key)
```

#### LLM Result Cache
```python
def cache_llm_result(prompt, result, ttl=3600):
    """Cache LLM result."""
    cache_key = f'llm:{hash(prompt)}'
    cache.set(cache_key, result, ttl)

def get_cached_llm_result(prompt):
    """Get cached LLM result."""
    cache_key = f'llm:{hash(prompt)}'
    return cache.get(cache_key)
```

---

## Workflow Performance

### 1. Stage Optimization

#### Stage Data Loading
```python
def load_stage_data(post_id, stage_id):
    """Load stage data efficiently."""
    # Load basic stage data
    stage_data = get_stage_data(post_id, stage_id)
    
    # Load related data in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        field_future = executor.submit(get_stage_fields, post_id, stage_id)
        history_future = executor.submit(get_stage_history, post_id, stage_id)
        status_future = executor.submit(get_stage_status, post_id, stage_id)
    
    # Combine results
    stage_data.update({
        'fields': field_future.result(),
        'history': history_future.result(),
        'status': status_future.result()
    })
    
    return stage_data
```

#### Stage Validation
```python
def validate_stage_data(data):
    """Validate stage data efficiently."""
    # Validate required fields
    required_fields = {'title', 'content', 'status'}
    if not all(field in data for field in required_fields):
        raise ValidationError("Missing required fields")
    
    # Validate field types
    if not isinstance(data['title'], str):
        raise ValidationError("Title must be string")
    
    # Validate field lengths
    if len(data['title']) > 255:
        raise ValidationError("Title too long")
    
    return True
```

### 2. LLM Optimization

#### Prompt Optimization
```python
def optimize_prompt(prompt):
    """Optimize LLM prompt."""
    # Remove unnecessary whitespace
    prompt = ' '.join(prompt.split())
    
    # Remove redundant instructions
    prompt = remove_redundant_instructions(prompt)
    
    # Optimize format
    prompt = optimize_prompt_format(prompt)
    
    return prompt
```

#### Response Optimization
```python
def optimize_llm_response(response):
    """Optimize LLM response."""
    # Remove unnecessary whitespace
    response = ' '.join(response.split())
    
    # Remove redundant content
    response = remove_redundant_content(response)
    
    # Optimize format
    response = optimize_response_format(response)
    
    return response
```

---

## Best Practices

### 1. Database Optimization
- Use indexes effectively
- Optimize queries
- Use connection pooling
- Clean up connections
- Monitor performance

### 2. Caching Strategy
- Cache API responses
- Cache query results
- Cache LLM results
- Set appropriate TTL
- Monitor cache usage

### 3. Workflow Performance
- Load data efficiently
- Validate data efficiently
- Use parallel processing
- Optimize prompts
- Monitor performance

### 4. General Optimization
- Profile code
- Monitor resources
- Optimize algorithms
- Use appropriate tools
- Document optimizations

---

## Common Issues

### 1. Database Issues
- Slow queries
- Connection leaks
- Missing indexes
- Lock contention
- Resource exhaustion

### 2. Caching Issues
- Cache misses
- Stale data
- Memory usage
- Cache invalidation
- Performance impact

### 3. Workflow Issues
- Slow stages
- Data loading
- Validation overhead
- LLM latency
- Resource usage

### 4. General Issues
- Memory leaks
- CPU usage
- Network latency
- Disk I/O
- Resource limits

---

## References

### 1. Database Optimization
- [Query Guide](docs/database/queries.md)
- [Index Guide](docs/database/indexes.md)

### 2. Caching Strategy
- [Cache Guide](docs/cache/guide.md)
- [TTL Guide](docs/cache/ttl.md)

### 3. Workflow Performance
- [Stage Guide](docs/workflow/stages.md)
- [LLM Guide](docs/workflow/llm.md)

### 4. General Optimization
- [Profile Guide](docs/performance/profile.md)
- [Monitor Guide](docs/performance/monitor.md) 