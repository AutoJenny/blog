# API Documentation Standards

This document outlines the standards for documenting APIs, database fields, and workflow stages in the blog system.

---

## API Endpoint Documentation

### 1. Endpoint Structure

#### Basic Endpoint Documentation
```python
"""
@api {get} /api/v1/posts/:id Get Post
@apiName GetPost
@apiGroup Posts
@apiVersion 1.0.0

@apiParam {Number} id Post unique ID

@apiSuccess {Object} data Post data
@apiSuccess {Number} data.id Post ID
@apiSuccess {String} data.title Post title
@apiSuccess {String} data.content Post content
@apiSuccess {String} data.status Post status

@apiError {Object} error Error object
@apiError {String} error.message Error message
"""
```

#### Workflow Endpoint Documentation
```python
"""
@api {post} /api/v1/workflow/:post_id/stage/:stage_id Update Workflow Stage
@apiName UpdateWorkflowStage
@apiGroup Workflow
@apiVersion 1.0.0

@apiParam {Number} post_id Post unique ID
@apiParam {Number} stage_id Stage unique ID
@apiParam {String} status New stage status
@apiParam {Object} fields Stage field mappings

@apiSuccess {Object} data Updated stage data
@apiSuccess {Number} data.stage_id Stage ID
@apiSuccess {String} data.status New status
@apiSuccess {Object} data.fields Updated fields

@apiError {Object} error Error object
@apiError {String} error.message Error message
"""
```

### 2. Response Format

#### Standard Response Structure
```python
def format_api_response(data=None, error=None):
    """Format standard API response."""
    response = {
        'success': error is None,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    if error is not None:
        response['error'] = {
            'message': str(error),
            'type': type(error).__name__
        }
    
    return response
```

#### Error Response Structure
```python
def format_error_response(error):
    """Format error response."""
    return {
        'success': False,
        'error': {
            'message': str(error),
            'type': type(error).__name__,
            'code': get_error_code(error)
        },
        'timestamp': datetime.now().isoformat()
    }
```

---

## Database Field Documentation

### 1. Field Documentation Structure

#### Table Documentation
```python
"""
@db_table post
@db_description Stores blog post content and metadata

@db_field id SERIAL Primary key
@db_field title VARCHAR(255) Post title
@db_field content TEXT Post content
@db_field status VARCHAR(50) Post status
@db_field created_at TIMESTAMP Creation timestamp
@db_field updated_at TIMESTAMP Last update timestamp
"""
```

#### Workflow Field Documentation
```python
"""
@db_table workflow_stage_entity
@db_description Canonical list of workflow stages

@db_field id SERIAL Primary key
@db_field name VARCHAR(100) Stage name
@db_field description TEXT Stage description
@db_field order_index INTEGER Display order
@db_field created_at TIMESTAMP Creation timestamp
"""
```

### 2. Field Mapping Documentation

#### Field Mapping Structure
```python
"""
@field_mapping workflow_field_mapping
@description Maps post development fields to workflow stages

@mapping_field field_name VARCHAR(128) Name of the post development field
@mapping_field stage_id INTEGER References workflow_stage_entity
@mapping_field order_index INTEGER Display order
@mapping_field created_at TIMESTAMP Creation timestamp
"""
```

#### LLM Field Documentation
```python
"""
@db_table llm_action
@db_description Stores LLM action templates

@db_field id SERIAL Primary key
@db_field name VARCHAR(128) Action name
@db_field prompt_template TEXT Prompt template
@db_field input_field VARCHAR(128) Input field name
@db_field output_field VARCHAR(128) Output field name
@db_field created_at TIMESTAMP Creation timestamp
"""
```

---

## Workflow Stage Documentation

### 1. Stage Documentation

#### Main Stage Documentation
```python
"""
@workflow_stage planning
@description Initial planning and research stage

@stage_field idea TEXT Initial post idea
@stage_field research TEXT Research notes
@stage_field structure TEXT Post structure
@stage_field status VARCHAR(50) Stage status
"""
```

#### Sub-Stage Documentation
```python
"""
@workflow_substage planning.idea
@description Initial idea development

@substage_field title TEXT Post title
@substage_field concept TEXT Post concept
@substage_field keywords TEXT[] Key topics
@substage_field status VARCHAR(50) Sub-stage status
"""
```

### 2. Stage Transition Documentation

#### Transition Rules
```python
"""
@workflow_transition planning -> authoring
@description Transition from planning to authoring

@transition_rule All required fields must be filled
@transition_rule Status must be 'completed'
@transition_rule No pending tasks
"""
```

#### Stage Validation
```python
"""
@workflow_validation planning
@description Validation rules for planning stage

@validation_rule title Required and non-empty
@validation_rule concept Required and non-empty
@validation_rule keywords At least one keyword
@validation_rule structure Required and non-empty
"""
```

---

## LLM Action Documentation

### 1. Action Template Documentation

#### Action Structure
```python
"""
@llm_action generate_title
@description Generate post title from concept

@action_input concept TEXT Post concept
@action_output title TEXT Generated title
@action_prompt Generate a compelling title for a blog post about {concept}
"""
```

#### Prompt Documentation
```python
"""
@llm_prompt generate_title
@description Title generation prompt template

@prompt_part system You are a blog title generator
@prompt_part user Generate a title for: {concept}
@prompt_part assistant I'll generate a title based on the concept
"""
```

### 2. Field Mapping Documentation

#### Input/Output Mapping
```python
"""
@field_mapping generate_title
@description Field mapping for title generation

@input_mapping concept -> post_development.concept
@output_mapping title -> post_development.title
@validation_mapping title.length <= 100
"""
```

#### Action Configuration
```python
"""
@action_config generate_title
@description Configuration for title generation

@config_field model llama3:latest
@config_field temperature 0.7
@config_field max_tokens 50
@config_field timeout 30
"""
```

---

## Best Practices

### 1. API Documentation
- Use consistent format
- Document all parameters
- Document all responses
- Document error cases
- Keep docs up to date

### 2. Database Documentation
- Document all tables
- Document all fields
- Document relationships
- Document constraints
- Document indexes

### 3. Workflow Documentation
- Document all stages
- Document transitions
- Document validations
- Document field mappings
- Document requirements

### 4. LLM Documentation
- Document all actions
- Document all prompts
- Document field mappings
- Document configurations
- Document validations

---

## Common Issues

### 1. Documentation Issues
- Missing documentation
- Outdated documentation
- Inconsistent format
- Missing examples
- Unclear descriptions

### 2. API Issues
- Undocumented endpoints
- Missing parameters
- Unclear responses
- Missing error cases
- Inconsistent formats

### 3. Database Issues
- Undocumented tables
- Missing field docs
- Unclear relationships
- Missing constraints
- Unclear indexes

### 4. Workflow Issues
- Undocumented stages
- Missing transitions
- Unclear validations
- Missing mappings
- Unclear requirements

---

## References

### 1. API Documentation
- [API Guide](docs/api/guide.md)
- [Response Format](docs/api/response.md)

### 2. Database Documentation
- [Schema Guide](docs/database/schema.md)
- [Field Guide](docs/database/fields.md)

### 3. Workflow Documentation
- [Stage Guide](docs/workflow/stages.md)
- [Transition Guide](docs/workflow/transitions.md)

### 4. LLM Documentation
- [Action Guide](docs/llm/actions.md)
- [Prompt Guide](docs/llm/prompts.md) 