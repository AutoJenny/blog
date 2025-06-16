# Testing Standards

This document outlines the testing standards for the blog system, focusing on unit testing, integration testing, and workflow testing.

---

## Unit Testing

### 1. Test Structure

#### Basic Test Structure
```python
def test_get_post():
    """Test getting a post."""
    # Arrange
    post_id = 1
    expected_post = {
        'id': post_id,
        'title': 'Test Post',
        'content': 'Test Content',
        'status': 'draft'
    }
    
    # Act
    result = get_post(post_id)
    
    # Assert
    assert result == expected_post
    assert result['id'] == post_id
    assert result['title'] == expected_post['title']
```

#### Workflow Test Structure
```python
def test_workflow_stage_transition():
    """Test workflow stage transition."""
    # Arrange
    post_id = 1
    stage_id = 2
    new_status = 'in_progress'
    
    # Act
    result = update_workflow_stage(post_id, stage_id, new_status)
    
    # Assert
    assert result['stage_id'] == stage_id
    assert result['status'] == new_status
    assert result['updated_at'] is not None
```

### 2. Test Fixtures

#### Database Fixtures
```python
@pytest.fixture
def test_db():
    """Create test database."""
    # Setup
    db = create_test_database()
    yield db
    # Teardown
    cleanup_test_database(db)

@pytest.fixture
def test_post(test_db):
    """Create test post."""
    return create_test_post(test_db)
```

#### Workflow Fixtures
```python
@pytest.fixture
def test_workflow(test_db):
    """Create test workflow."""
    return create_test_workflow(test_db)

@pytest.fixture
def test_stage(test_workflow):
    """Create test stage."""
    return create_test_stage(test_workflow)
```

---

## Integration Testing

### 1. API Testing

#### Endpoint Testing
```python
def test_get_post_endpoint(client, test_post):
    """Test get post endpoint."""
    # Arrange
    post_id = test_post['id']
    
    # Act
    response = client.get(f'/api/v1/posts/{post_id}')
    
    # Assert
    assert response.status_code == 200
    assert response.json['data']['id'] == post_id
    assert response.json['data']['title'] == test_post['title']
```

#### Workflow Endpoint Testing
```python
def test_update_workflow_stage_endpoint(client, test_workflow):
    """Test update workflow stage endpoint."""
    # Arrange
    post_id = test_workflow['post_id']
    stage_id = test_workflow['stage_id']
    new_status = 'in_progress'
    
    # Act
    response = client.post(
        f'/api/v1/workflow/{post_id}/stage/{stage_id}',
        json={'status': new_status}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json['data']['status'] == new_status
```

### 2. Database Integration

#### Query Testing
```python
def test_post_query(test_db, test_post):
    """Test post query."""
    # Arrange
    post_id = test_post['id']
    
    # Act
    result = execute_query(
        "SELECT * FROM post WHERE id = %s",
        (post_id,)
    )
    
    # Assert
    assert result['id'] == post_id
    assert result['title'] == test_post['title']
```

#### Transaction Testing
```python
def test_workflow_transaction(test_db, test_workflow):
    """Test workflow transaction."""
    # Arrange
    post_id = test_workflow['post_id']
    stage_id = test_workflow['stage_id']
    
    # Act
    with test_db.transaction():
        update_stage_status(post_id, stage_id, 'completed')
        update_post_status(post_id, 'published')
    
    # Assert
    assert get_stage_status(post_id, stage_id) == 'completed'
    assert get_post_status(post_id) == 'published'
```

---

## Workflow Testing

### 1. Stage Testing

#### Stage Validation
```python
def test_stage_validation(test_workflow):
    """Test stage validation."""
    # Arrange
    stage_data = {
        'title': '',
        'content': 'Test Content',
        'status': 'draft'
    }
    
    # Act/Assert
    with pytest.raises(ValidationError):
        validate_stage_data(stage_data)
```

#### Stage Transition
```python
def test_stage_transition(test_workflow):
    """Test stage transition."""
    # Arrange
    post_id = test_workflow['post_id']
    current_stage = test_workflow['stage_id']
    next_stage = current_stage + 1
    
    # Act
    result = transition_stage(post_id, current_stage, next_stage)
    
    # Assert
    assert result['current_stage'] == next_stage
    assert result['previous_stage'] == current_stage
```

### 2. LLM Testing

#### Action Testing
```python
def test_llm_action(test_workflow):
    """Test LLM action."""
    # Arrange
    action_name = 'generate_title'
    input_data = {'concept': 'Test Concept'}
    
    # Act
    result = execute_llm_action(action_name, input_data)
    
    # Assert
    assert 'title' in result
    assert len(result['title']) > 0
    assert len(result['title']) <= 100
```

#### Prompt Testing
```python
def test_llm_prompt(test_workflow):
    """Test LLM prompt."""
    # Arrange
    prompt_name = 'generate_title'
    input_data = {'concept': 'Test Concept'}
    
    # Act
    prompt = generate_prompt(prompt_name, input_data)
    
    # Assert
    assert 'system' in prompt
    assert 'user' in prompt
    assert 'Test Concept' in prompt['user']
```

---

## Best Practices

### 1. Unit Testing
- Test one thing at a time
- Use descriptive names
- Follow AAA pattern
- Use fixtures
- Clean up after tests

### 2. Integration Testing
- Test real interactions
- Use test database
- Test transactions
- Test error cases
- Clean up after tests

### 3. Workflow Testing
- Test all stages
- Test transitions
- Test validations
- Test error cases
- Test edge cases

### 4. LLM Testing
- Test all actions
- Test all prompts
- Test error cases
- Test timeouts
- Test retries

---

## Common Issues

### 1. Test Issues
- Missing tests
- Flaky tests
- Slow tests
- Unclear tests
- Duplicate tests

### 2. Database Issues
- Missing cleanup
- Transaction issues
- Connection issues
- Data issues
- Schema issues

### 3. Workflow Issues
- Missing stages
- Transition issues
- Validation issues
- State issues
- Error handling

### 4. LLM Issues
- Missing actions
- Prompt issues
- Timeout issues
- Error handling
- Retry issues

---

## References

### 1. Testing Documentation
- [Test Guide](docs/testing/guide.md)
- [Fixture Guide](docs/testing/fixtures.md)

### 2. API Testing
- [API Test Guide](docs/testing/api.md)
- [Endpoint Guide](docs/testing/endpoints.md)

### 3. Database Testing
- [Database Test Guide](docs/testing/database.md)
- [Query Guide](docs/testing/queries.md)

### 4. Workflow Testing
- [Workflow Test Guide](docs/testing/workflow.md)
- [Stage Guide](docs/testing/stages.md) 