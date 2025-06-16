# Testing & Validation Guide

This document outlines the testing requirements, procedures, and validation criteria for all modules in the system. Following these guidelines ensures consistent quality and reliability across all modules.

---

## Testing Levels

### 1. Unit Testing

#### Requirements
- Test coverage > 90%
- All public functions must have tests
- Mock external dependencies
- Test edge cases and error conditions

#### Example Test Structure
```python
def test_nav_structure_endpoint():
    # Arrange
    client = create_test_client()
    
    # Act
    response = client.get('/api/nav/structure')
    
    # Assert
    assert response.status_code == 200
    assert 'current_stage' in response.json['data']
```

### 2. Integration Testing

#### Requirements
- Test module interactions
- Test database operations
- Test event handling
- Test configuration loading

#### Example Test Structure
```python
def test_llm_section_integration():
    # Arrange
    client = create_test_client()
    test_content = create_test_content()
    
    # Act
    response = client.post('/api/llm/process', json={
        'action_type': 'section_generate',
        'content_id': test_content.id
    })
    
    # Assert
    assert response.status_code == 200
    assert 'sections' in response.json['data']
```

### 3. End-to-End Testing

#### Requirements
- Test complete workflows
- Test user interactions
- Test error handling
- Test performance

#### Example Test Structure
```python
def test_complete_workflow():
    # Arrange
    client = create_test_client()
    
    # Act
    # 1. Create content
    content_response = client.post('/api/content/create', json={
        'title': 'Test Content'
    })
    
    # 2. Generate sections
    sections_response = client.post('/api/llm/process', json={
        'action_type': 'section_generate',
        'content_id': content_response.json['data']['id']
    })
    
    # 3. Reorder sections
    reorder_response = client.post('/api/sections/reorder', json={
        'content_id': content_response.json['data']['id'],
        'sections': sections_response.json['data']['sections']
    })
    
    # Assert
    assert content_response.status_code == 200
    assert sections_response.status_code == 200
    assert reorder_response.status_code == 200
```

---

## Test Data Management

### 1. Test Fixtures

#### Requirements
- Use consistent test data
- Reset data between tests
- Use realistic data
- Document test data structure

#### Example Fixture
```python
@pytest.fixture
def test_content():
    return {
        'id': 'test-content-1',
        'title': 'Test Content',
        'sections': [
            {
                'id': 'section-1',
                'title': 'Introduction',
                'content': 'Test content'
            }
        ]
    }
```

### 2. Database Testing

#### Requirements
- Use test database
- Reset database between tests
- Use transactions
- Clean up test data

#### Example Database Test
```python
def test_database_operations():
    # Arrange
    db = get_test_db()
    
    # Act
    with db.transaction():
        content_id = db.insert_content({
            'title': 'Test Content'
        })
        
    # Assert
    content = db.get_content(content_id)
    assert content['title'] == 'Test Content'
```

---

## Performance Testing

### 1. Load Testing

#### Requirements
- Test under expected load
- Monitor response times
- Monitor resource usage
- Test error handling under load

#### Example Load Test
```python
def test_api_load():
    # Arrange
    client = create_test_client()
    num_requests = 100
    
    # Act
    start_time = time.time()
    responses = []
    for _ in range(num_requests):
        response = client.get('/api/nav/structure')
        responses.append(response)
    
    # Assert
    total_time = time.time() - start_time
    assert total_time < 5.0  # 5 seconds for 100 requests
    assert all(r.status_code == 200 for r in responses)
```

### 2. Stress Testing

#### Requirements
- Test beyond expected load
- Monitor system behavior
- Test recovery
- Document limits

#### Example Stress Test
```python
def test_api_stress():
    # Arrange
    client = create_test_client()
    num_requests = 1000
    
    # Act
    start_time = time.time()
    responses = []
    for _ in range(num_requests):
        response = client.get('/api/nav/structure')
        responses.append(response)
    
    # Assert
    total_time = time.time() - start_time
    assert total_time < 30.0  # 30 seconds for 1000 requests
    assert sum(1 for r in responses if r.status_code == 200) > 950
```

---

## Validation Criteria

### 1. Code Quality

#### Requirements
- Follow PEP 8
- No code smells
- Proper documentation
- Proper error handling

#### Example Validation
```python
def validate_code_quality():
    # Run linters
    flake8_result = run_flake8()
    pylint_result = run_pylint()
    
    # Assert
    assert flake8_result.exit_code == 0
    assert pylint_result.score > 9.0
```

### 2. API Validation

#### Requirements
- Follow API contract
- Proper error responses
- Proper validation
- Proper documentation

#### Example Validation
```python
def validate_api_contract():
    # Get API spec
    spec = get_api_spec()
    
    # Validate endpoints
    for endpoint in spec['endpoints']:
        assert 'version' in endpoint
        assert 'method' in endpoint
        assert 'path' in endpoint
        assert 'responses' in endpoint
```

---

## Testing Tools

### 1. Required Tools
- pytest
- pytest-cov
- pytest-mock
- pytest-asyncio
- locust (for load testing)

### 2. Configuration

#### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=app --cov-report=term-missing
```

#### conftest.py
```python
import pytest

@pytest.fixture(scope='session')
def app():
    from app import create_app
    app = create_app('testing')
    return app

@pytest.fixture(scope='session')
def client(app):
    return app.test_client()
```

---

## CI/CD Integration

### 1. GitHub Actions

#### Requirements
- Run tests on push
- Run tests on PR
- Generate coverage report
- Enforce code quality

#### Example Workflow
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### 2. Pre-commit Hooks

#### Requirements
- Run linters
- Run tests
- Check formatting
- Check imports

#### Example Hook
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v3.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: https://github.com/psf/black
    rev: 21.5b2
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 3.9.2
    hooks:
      - id: flake8
```

---

## Reporting

### 1. Test Reports

#### Requirements
- Coverage report
- Test results
- Performance metrics
- Error logs

#### Example Report
```python
def generate_test_report():
    # Generate coverage report
    coverage_report = generate_coverage_report()
    
    # Generate test results
    test_results = generate_test_results()
    
    # Generate performance metrics
    performance_metrics = generate_performance_metrics()
    
    # Save report
    save_report({
        'coverage': coverage_report,
        'test_results': test_results,
        'performance': performance_metrics
    })
```

### 2. Performance Reports

#### Requirements
- Response times
- Resource usage
- Error rates
- Load metrics

#### Example Report
```python
def generate_performance_report():
    # Get metrics
    response_times = get_response_times()
    resource_usage = get_resource_usage()
    error_rates = get_error_rates()
    load_metrics = get_load_metrics()
    
    # Save report
    save_report({
        'response_times': response_times,
        'resource_usage': resource_usage,
        'error_rates': error_rates,
        'load_metrics': load_metrics
    })
```

---

## Best Practices

1. **Test Organization**
   - Group tests by module
   - Group tests by functionality
   - Use descriptive test names
   - Use proper test fixtures

2. **Test Data**
   - Use realistic test data
   - Reset data between tests
   - Use proper test databases
   - Clean up test data

3. **Test Coverage**
   - Aim for > 90% coverage
   - Test edge cases
   - Test error conditions
   - Test performance

4. **Test Maintenance**
   - Keep tests up to date
   - Remove obsolete tests
   - Update test data
   - Review test coverage

5. **Test Documentation**
   - Document test purpose
   - Document test data
   - Document test setup
   - Document test results 