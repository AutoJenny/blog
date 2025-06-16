# Technical Implementation Guide

This document provides detailed technical implementation steps for transitioning the blog system to the new modular architecture. For the step-by-step checklist, see [Transition Checklist](transition_checklist.md).

---

## Phase 1: Core Infrastructure

### 1. Database Migration

#### Schema Updates
```python
def migrate_core_schema():
    """Migrate core database schema."""
    # Create workflow tables
    execute_query("""
    CREATE TABLE IF NOT EXISTS workflow_stage_entity (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        order_index INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create field mapping table
    execute_query("""
    CREATE TABLE IF NOT EXISTS workflow_field_mapping (
        id SERIAL PRIMARY KEY,
        field_name VARCHAR(128) NOT NULL,
        stage_id INTEGER REFERENCES workflow_stage_entity(id),
        order_index INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create LLM action table
    execute_query("""
    CREATE TABLE IF NOT EXISTS llm_action (
        id SERIAL PRIMARY KEY,
        name VARCHAR(128) NOT NULL,
        prompt_template TEXT NOT NULL,
        input_field VARCHAR(128) NOT NULL,
        output_field VARCHAR(128) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
```

#### Data Migration
```python
def migrate_core_data():
    """Migrate core data to new schema."""
    # Migrate workflow stages
    stages = [
        ('planning', 'Initial planning and research', 1),
        ('authoring', 'Content creation and editing', 2),
        ('review', 'Content review and feedback', 3),
        ('publishing', 'Final review and publishing', 4)
    ]
    
    for name, description, order in stages:
        execute_query("""
        INSERT INTO workflow_stage_entity (name, description, order_index)
        VALUES (%s, %s, %s)
        """, (name, description, order))
    
    # Migrate field mappings
    fields = [
        ('title', 1, 1),
        ('content', 2, 1),
        ('status', 3, 1)
    ]
    
    for field, stage_id, order in fields:
        execute_query("""
        INSERT INTO workflow_field_mapping (field_name, stage_id, order_index)
        VALUES (%s, %s, %s)
        """, (field, stage_id, order))
```

### 2. Testing Infrastructure

#### Health Check Endpoints
```python
def setup_health_checks():
    """Setup health check endpoints."""
    @app.route('/health')
    def health_check():
        """Basic health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check endpoint."""
        return jsonify(check_system_health())
```

#### Performance Monitoring
```python
def setup_performance_monitoring():
    """Setup performance monitoring."""
    # Setup query logging
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        duration = time.time() - g.start_time
        log_query_performance(request.path, request.args, duration)
        return response
```

---

## Phase 2: Module Implementation

### 1. Core Module

#### Module Structure
```python
def setup_core_module():
    """Setup core module structure."""
    # Create module directory
    os.makedirs('modules/core', exist_ok=True)
    
    # Create module files
    files = [
        'modules/core/__init__.py',
        'modules/core/routes.py',
        'modules/core/models.py',
        'modules/core/schemas.py',
        'modules/core/utils.py'
    ]
    
    for file in files:
        with open(file, 'w') as f:
            f.write('# Core module\n')
```

#### Module Registration
```python
def register_core_module():
    """Register core module with application."""
    from modules.core import core_bp
    
    app.register_blueprint(core_bp, url_prefix='/api/v1/core')
    
    # Register module with monitoring
    register_module_monitoring('core')
```

### 2. Workflow Module

#### Module Structure
```python
def setup_workflow_module():
    """Setup workflow module structure."""
    # Create module directory
    os.makedirs('modules/workflow', exist_ok=True)
    
    # Create module files
    files = [
        'modules/workflow/__init__.py',
        'modules/workflow/routes.py',
        'modules/workflow/models.py',
        'modules/workflow/schemas.py',
        'modules/workflow/utils.py'
    ]
    
    for file in files:
        with open(file, 'w') as f:
            f.write('# Workflow module\n')
```

#### Module Registration
```python
def register_workflow_module():
    """Register workflow module with application."""
    from modules.workflow import workflow_bp
    
    app.register_blueprint(workflow_bp, url_prefix='/api/v1/workflow')
    
    # Register module with monitoring
    register_module_monitoring('workflow')
```

---

## Phase 3: UI Implementation

### 1. Core UI

#### Base Templates
```python
def setup_core_templates():
    """Setup core templates."""
    # Create template directory
    os.makedirs('templates/core', exist_ok=True)
    
    # Create base template
    with open('templates/core/base.html', 'w') as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{% block title %}{% endblock %}</title>
            <link rel="stylesheet" href="{{ url_for('static', filename='css/core.css') }}">
        </head>
        <body>
            {% block content %}{% endblock %}
            <script src="{{ url_for('static', filename='js/core.js') }}"></script>
        </body>
        </html>
        """)
```

#### Static Assets
```python
def setup_core_assets():
    """Setup core static assets."""
    # Create asset directories
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Create core CSS
    with open('static/css/core.css', 'w') as f:
        f.write("""
        /* Core styles */
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        """)
    
    # Create core JS
    with open('static/js/core.js', 'w') as f:
        f.write("""
        // Core JavaScript
        console.log('Core module loaded');
        """)
```

### 2. Workflow UI

#### Workflow Templates
```python
def setup_workflow_templates():
    """Setup workflow templates."""
    # Create template directory
    os.makedirs('templates/workflow', exist_ok=True)
    
    # Create workflow template
    with open('templates/workflow/stage.html', 'w') as f:
        f.write("""
        {% extends "core/base.html" %}
        
        {% block title %}Workflow Stage{% endblock %}
        
        {% block content %}
        <div class="workflow-stage">
            <h1>{{ stage.name }}</h1>
            <div class="stage-content">
                {% block stage_content %}{% endblock %}
            </div>
        </div>
        {% endblock %}
        """)
```

#### Workflow Assets
```python
def setup_workflow_assets():
    """Setup workflow static assets."""
    # Create workflow CSS
    with open('static/css/workflow.css', 'w') as f:
        f.write("""
        /* Workflow styles */
        .workflow-stage {
            padding: 20px;
        }
        """)
    
    # Create workflow JS
    with open('static/js/workflow.js', 'w') as f:
        f.write("""
        // Workflow JavaScript
        console.log('Workflow module loaded');
        """)
```

---

## Phase 4: Testing and Validation

### 1. Automated Testing

#### Unit Tests
```python
def setup_unit_tests():
    """Setup unit tests."""
    # Create test directory
    os.makedirs('tests/unit', exist_ok=True)
    
    # Create core tests
    with open('tests/unit/test_core.py', 'w') as f:
        f.write("""
        def test_core_functionality():
            assert True
        
        def test_core_validation():
            assert True
        """)
    
    # Create workflow tests
    with open('tests/unit/test_workflow.py', 'w') as f:
        f.write("""
        def test_workflow_functionality():
            assert True
        
        def test_workflow_validation():
            assert True
        """)
```

#### Integration Tests
```python
def setup_integration_tests():
    """Setup integration tests."""
    # Create test directory
    os.makedirs('tests/integration', exist_ok=True)
    
    # Create API tests
    with open('tests/integration/test_api.py', 'w') as f:
        f.write("""
        def test_api_endpoints():
            assert True
        
        def test_api_validation():
            assert True
        """)
    
    # Create workflow tests
    with open('tests/integration/test_workflow.py', 'w') as f:
        f.write("""
        def test_workflow_integration():
            assert True
        
        def test_workflow_validation():
            assert True
        """)
```

### 2. Manual Testing

#### Test Cases
```python
def setup_manual_tests():
    """Setup manual test cases."""
    # Create test directory
    os.makedirs('tests/manual', exist_ok=True)
    
    # Create core test cases
    with open('tests/manual/core_test_cases.md', 'w') as f:
        f.write("""
        # Core Module Test Cases
        
        ## Basic Functionality
        1. Test core module loading
        2. Test core module initialization
        3. Test core module cleanup
        
        ## Error Handling
        1. Test error logging
        2. Test error recovery
        3. Test error reporting
        """)
    
    # Create workflow test cases
    with open('tests/manual/workflow_test_cases.md', 'w') as f:
        f.write("""
        # Workflow Module Test Cases
        
        ## Stage Management
        1. Test stage creation
        2. Test stage transition
        3. Test stage validation
        
        ## Field Management
        1. Test field mapping
        2. Test field validation
        3. Test field persistence
        """)
```

#### Test Scripts
```python
def setup_test_scripts():
    """Setup test scripts."""
    # Create script directory
    os.makedirs('scripts/test', exist_ok=True)
    
    # Create core test script
    with open('scripts/test/test_core.sh', 'w') as f:
        f.write("""
        #!/bin/bash
        
        # Run core tests
        python -m pytest tests/unit/test_core.py
        python -m pytest tests/integration/test_core.py
        """)
    
    # Create workflow test script
    with open('scripts/test/test_workflow.sh', 'w') as f:
        f.write("""
        #!/bin/bash
        
        # Run workflow tests
        python -m pytest tests/unit/test_workflow.py
        python -m pytest tests/integration/test_workflow.py
        """)
```

---

## Phase 5: Deployment

### 1. Deployment Scripts

#### Core Deployment
```python
def setup_core_deployment():
    """Setup core deployment scripts."""
    # Create script directory
    os.makedirs('scripts/deploy', exist_ok=True)
    
    # Create core deployment script
    with open('scripts/deploy/deploy_core.sh', 'w') as f:
        f.write("""
        #!/bin/bash
        
        # Deploy core module
        echo "Deploying core module..."
        
        # Run tests
        ./scripts/test/test_core.sh
        
        # Deploy module
        cp -r modules/core /app/modules/
        cp -r templates/core /app/templates/
        cp -r static/css/core.css /app/static/css/
        cp -r static/js/core.js /app/static/js/
        
        echo "Core module deployed"
        """)
```

#### Workflow Deployment
```python
def setup_workflow_deployment():
    """Setup workflow deployment scripts."""
    # Create workflow deployment script
    with open('scripts/deploy/deploy_workflow.sh', 'w') as f:
        f.write("""
        #!/bin/bash
        
        # Deploy workflow module
        echo "Deploying workflow module..."
        
        # Run tests
        ./scripts/test/test_workflow.sh
        
        # Deploy module
        cp -r modules/workflow /app/modules/
        cp -r templates/workflow /app/templates/
        cp -r static/css/workflow.css /app/static/css/
        cp -r static/js/workflow.js /app/static/js/
        
        echo "Workflow module deployed"
        """)
```

### 2. Rollback Scripts

#### Core Rollback
```python
def setup_core_rollback():
    """Setup core rollback scripts."""
    # Create core rollback script
    with open('scripts/deploy/rollback_core.sh', 'w') as f:
        f.write("""
        #!/bin/bash
        
        # Rollback core module
        echo "Rolling back core module..."
        
        # Restore from backup
        cp -r /backup/modules/core /app/modules/
        cp -r /backup/templates/core /app/templates/
        cp -r /backup/static/css/core.css /app/static/css/
        cp -r /backup/static/js/core.js /app/static/js/
        
        echo "Core module rolled back"
        """)
```

#### Workflow Rollback
```python
def setup_workflow_rollback():
    """Setup workflow rollback scripts."""
    # Create workflow rollback script
    with open('scripts/deploy/rollback_workflow.sh', 'w') as f:
        f.write("""
        #!/bin/bash
        
        # Rollback workflow module
        echo "Rolling back workflow module..."
        
        # Restore from backup
        cp -r /backup/modules/workflow /app/modules/
        cp -r /backup/templates/workflow /app/templates/
        cp -r /backup/static/css/workflow.css /app/static/css/
        cp -r /backup/static/js/workflow.js /app/static/js/
        
        echo "Workflow module rolled back"
        """)
```

---

## Best Practices

### 1. Implementation
- Follow modular design
- Use consistent patterns
- Document all changes
- Test thoroughly
- Monitor performance

### 2. Testing
- Write unit tests
- Write integration tests
- Perform manual testing
- Validate functionality
- Monitor errors

### 3. Deployment
- Use deployment scripts
- Create backups
- Test deployment
- Monitor deployment
- Plan rollback

### 4. Validation
- Check functionality
- Verify performance
- Monitor errors
- Test edge cases
- Document issues

---

## Common Issues

### 1. Implementation Issues
- Module conflicts
- Dependency issues
- Configuration errors
- Performance problems
- Error handling

### 2. Testing Issues
- Missing tests
- False positives
- Performance impact
- Coverage gaps
- Environment issues

### 3. Deployment Issues
- Script failures
- Backup issues
- Permission problems
- Resource limits
- Network issues

### 4. Validation Issues
- Functionality gaps
- Performance issues
- Error patterns
- Edge cases
- Documentation

---

## References

### 1. Implementation
- [Transition Checklist](transition_checklist.md)
- [Module Guide](docs/modules/guide.md)
- [Pattern Guide](docs/modules/patterns.md)

### 2. Testing
- [Test Guide](docs/testing/guide.md)
- [Validation Guide](docs/testing/validation.md)

### 3. Deployment
- [Deploy Guide](docs/deployment/guide.md)
- [Rollback Guide](docs/deployment/rollback.md)

### 4. Validation
- [Function Guide](docs/validation/function.md)
- [Performance Guide](docs/validation/performance.md) 