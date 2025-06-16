# Module Integration Guide

This document outlines the integration patterns and requirements for modules in the blog system, with a focus on database interactions and workflow management.

---

## Database Integration

### 1. Direct SQL Approach

All modules must use direct SQL for database operations. No ORM or migration tools are used.

```python
def get_db_conn():
    """Get database connection using environment variables."""
    from dotenv import load_dotenv
    import os
    import psycopg2
    
    # Always reload environment variables
    load_dotenv('assistant_config.env')
    
    return psycopg2.connect(os.getenv('DATABASE_URL'))
```

### 2. Database Access Patterns

#### Connection Management
```python
def execute_query(query, params=None):
    """Execute a database query with proper connection handling."""
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or {})
            if cur.description:  # SELECT query
                return cur.fetchall()
            conn.commit()
    finally:
        conn.close()
```

#### Error Handling
```python
def safe_db_operation(operation):
    """Wrapper for database operations with error handling."""
    try:
        return operation()
    except psycopg2.Error as e:
        # Log error
        raise DatabaseError(f"Database operation failed: {str(e)}")
```

### 3. Workflow Table Integration

#### Required Tables
- `workflow_stage_entity`: Main workflow stages
- `workflow_sub_stage_entity`: Sub-stages for each main stage
- `workflow_step_entity`: Steps within sub-stages
- `workflow_field_mapping`: Field mappings for UI

#### Field Mapping
```python
def get_workflow_fields(stage_id, sub_stage_id):
    """Get field mappings for a workflow stage/sub-stage."""
    query = """
    SELECT field_name, order_index 
    FROM workflow_field_mapping 
    WHERE stage_id = %s AND sub_stage_id = %s 
    ORDER BY order_index
    """
    return execute_query(query, (stage_id, sub_stage_id))
```

---

## Module Integration Patterns

### 1. Module Structure

Each module must follow this structure:
```
module_name/
├── __init__.py
├── routes.py
├── templates/
│   └── module_name/
├── static/
│   └── module_name/
└── tests/
    ├── unit/
    └── integration/
```

### 2. Route Integration

#### Blueprint Registration
```python
from flask import Blueprint

module_bp = Blueprint('module_name', __name__)

def init_module(app):
    """Initialize module with the main application."""
    app.register_blueprint(module_bp, url_prefix='/module_name')
```

#### Route Patterns
```python
@module_bp.route('/endpoint', methods=['GET'])
def handle_endpoint():
    """Handle module endpoint with proper error handling."""
    try:
        # Module logic
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 3. Workflow Integration

#### Stage Management
```python
def get_current_stage(post_id):
    """Get current workflow stage for a post."""
    query = """
    SELECT ws.stage, ws.status, ws.started_at, ws.completed_at
    FROM workflow ws
    WHERE ws.post_id = %s
    ORDER BY ws.created DESC
    LIMIT 1
    """
    return execute_query(query, (post_id,))
```

#### Field Persistence
```python
def save_workflow_fields(post_id, stage_id, fields):
    """Save workflow field mappings."""
    query = """
    INSERT INTO workflow_field_mapping 
    (post_id, stage_id, field_name, order_index)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (post_id, stage_id, field_name) 
    DO UPDATE SET order_index = EXCLUDED.order_index
    """
    for field in fields:
        execute_query(query, (post_id, stage_id, field['name'], field['order']))
```

---

## LLM Integration

### 1. Action Management

#### Action Definition
```python
def create_llm_action(name, prompt_template, model):
    """Create a new LLM action."""
    query = """
    INSERT INTO llm_action 
    (name, prompt_template, llm_model)
    VALUES (%s, %s, %s)
    RETURNING id
    """
    return execute_query(query, (name, prompt_template, model))
```

#### Action Execution
```python
def execute_llm_action(action_id, input_data):
    """Execute an LLM action with input data."""
    # Get action details
    action = get_llm_action(action_id)
    
    # Execute action
    result = call_llm(action['prompt_template'], input_data)
    
    # Log interaction
    log_llm_interaction(action_id, input_data, result)
    
    return result
```

### 2. Prompt Management

#### Prompt Structure
```python
def get_prompt_template(action_id):
    """Get prompt template for an action."""
    query = """
    SELECT prompt_text, prompt_json
    FROM llm_prompt
    WHERE id = (
        SELECT prompt_template_id 
        FROM llm_action 
        WHERE id = %s
    )
    """
    return execute_query(query, (action_id,))
```

#### Field Mapping
```python
def map_prompt_fields(prompt_template, input_fields):
    """Map input fields to prompt template."""
    # Replace [data:field] with actual values
    for field, value in input_fields.items():
        prompt_template = prompt_template.replace(
            f'[data:{field}]', 
            str(value)
        )
    return prompt_template
```

---

## Best Practices

### 1. Database Operations
- Always use parameterized queries
- Handle connections properly
- Implement proper error handling
- Use transactions when needed

### 2. Module Integration
- Follow the module structure
- Use blueprints for routes
- Implement proper error handling
- Document all endpoints

### 3. Workflow Management
- Use workflow tables correctly
- Implement field persistence
- Handle stage transitions
- Document field mappings

### 4. LLM Integration
- Use proper prompt templates
- Implement field mapping
- Log all interactions
- Handle errors properly

---

## Common Issues

### 1. Database Connection Issues
- Check environment variables
- Verify database permissions
- Check connection handling
- Verify error handling

### 2. Workflow Issues
- Verify stage transitions
- Check field mappings
- Verify data persistence
- Check UI integration

### 3. LLM Issues
- Verify prompt templates
- Check field mapping
- Verify model settings
- Check error handling

---

## References

### 1. Database
- [Schema Documentation](docs/database/schema.md)
- [SQL Management](docs/database/sql_management.md)

### 2. Workflow
- [Workflow Stages](docs/workflow/stages.md)
- [Field Mapping](docs/workflow/field_mapping.md)

### 3. LLM
- [LLM Actions](docs/llm/actions.md)
- [Prompt Templates](docs/llm/prompts.md) 