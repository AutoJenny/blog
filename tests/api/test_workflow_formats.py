import pytest
from flask import Flask
from app.api.workflow import workflow_bp
from app.api.workflow.formats import formats_bp
import json
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app):
    with app.test_client() as client:
        with app.app_context():
            app.register_blueprint(workflow_bp)
            app.register_blueprint(formats_bp)
            yield client

@pytest.fixture
def sample_format():
    return {
        "name": "Test Workflow Format",
        "format_type": "input",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["title", "content"]
        })
    }

def test_workflow_step_format_configuration(client, sample_format):
    """Test configuring formats for workflow steps"""
    # Create input and output formats
    input_response = client.post("/api/workflow/formats/templates", json=sample_format)
    assert input_response.status_code == 201
    input_format = input_response.get_json()
    
    output_format = dict(sample_format)
    output_format["name"] = "Test Output Format"
    output_format["format_type"] = "output"
    output_response = client.post("/api/workflow/formats/templates", json=output_format)
    assert output_response.status_code == 201
    output_format = output_response.get_json()
    
    # Configure step formats
    response = client.put("/api/workflow/steps/1/formats", json={
        "input_format_id": input_format["id"],
        "output_format_id": output_format["id"]
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["input_format_id"] == input_format["id"]
    assert data["output_format_id"] == output_format["id"]

def test_workflow_format_validation(client, sample_format):
    """Test format validation in workflow context"""
    # Create a format template
    response = client.post("/api/workflow/formats/templates", json=sample_format)
    assert response.status_code == 201
    format_data = response.get_json()
    
    # Configure step format
    response = client.put("/api/workflow/steps/1/formats", json={
        "input_format_id": format_data["id"],
        "output_format_id": None
    })
    assert response.status_code == 200
    
    # Test valid input data
    valid_data = {
        "title": "Test Title",
        "content": "Test Content"
    }
    response = client.post("/api/workflow/formats/validate", json={
        "format_spec": sample_format["format_spec"],
        "test_data": valid_data
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["valid"] is True
    
    # Test invalid input data
    invalid_data = {
        "title": "Test Title"
        # Missing required content field
    }
    response = client.post("/api/workflow/formats/validate", json={
        "format_spec": sample_format["format_spec"],
        "test_data": invalid_data
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["valid"] is False

def test_workflow_format_error_handling(client):
    """Test error handling in workflow format integration"""
    # Test invalid format IDs
    response = client.put("/api/workflow/steps/1/formats", json={
        "input_format_id": 9999,  # Non-existent format
        "output_format_id": None
    })
    assert response.status_code == 400
    
    # Test missing format IDs
    response = client.put("/api/workflow/steps/1/formats", json={})
    assert response.status_code == 400
    
    # Test invalid step ID
    response = client.put("/api/workflow/steps/9999/formats", json={
        "input_format_id": 1,
        "output_format_id": None
    })
    assert response.status_code == 404

def test_create_input_and_output_formats(client):
    """Test creating both input and output format templates"""
    # Create input format
    sample_format = {
        'name': 'Test Input Format',
        'description': 'Input format for testing',
        'fields': [
            {
                'name': 'title',
                'type': 'string',
                'required': True,
                'description': 'The title of the content'
            },
            {
                'name': 'content',
                'type': 'string',
                'required': True,
                'description': 'The main content'
            }
        ]
    }
    
    input_response = client.post("/api/workflow/formats/templates", json=sample_format)
    assert input_response.status_code == 201
    
    # Create output format
    output_format = {
        'name': 'Test Output Format',
        'description': 'Output format for testing',
        'fields': [
            {
                'name': 'result',
                'type': 'string',
                'required': True,
                'description': 'The processed result'
            },
            {
                'name': 'metadata',
                'type': 'object',
                'required': False,
                'description': 'Additional metadata'
            }
        ]
    }
    
    output_response = client.post("/api/workflow/formats/templates", json=output_format)
    assert output_response.status_code == 201
    
    # Verify both formats were created
    input_data = input_response.get_json()
    output_data = output_response.get_json()
    
    assert input_data['name'] == 'Test Input Format'
    assert output_data['name'] == 'Test Output Format'
    assert len(input_data['fields']) == 2
    assert len(output_data['fields']) == 2

def test_format_template_crud_operations(client):
    """Test complete CRUD operations on format templates"""
    # Create
    sample_format = {
        'name': 'CRUD Test Format',
        'description': 'Format for CRUD testing',
        'fields': [
            {
                'name': 'test_field',
                'type': 'string',
                'required': True
            }
        ]
    }
    
    response = client.post("/api/workflow/formats/templates", json=sample_format)
    assert response.status_code == 201
    template_id = response.get_json()['id']
    
    # Read
    get_response = client.get(f"/api/workflow/formats/templates/{template_id}")
    assert get_response.status_code == 200
    data = get_response.get_json()
    assert data['name'] == 'CRUD Test Format'
    
    # Update
    updated_format = {
        'name': 'Updated CRUD Format',
        'description': 'Updated description',
        'fields': [
            {
                'name': 'updated_field',
                'type': 'string',
                'required': False
            }
        ]
    }
    
    update_response = client.put(f"/api/workflow/formats/templates/{template_id}", json=updated_format)
    assert update_response.status_code == 200
    updated_data = update_response.get_json()
    assert updated_data['name'] == 'Updated CRUD Format'
    
    # Delete
    delete_response = client.delete(f"/api/workflow/formats/templates/{template_id}")
    assert delete_response.status_code == 200
    
    # Verify deletion
    verify_response = client.get(f"/api/workflow/formats/templates/{template_id}")
    assert verify_response.status_code == 404

def test_format_validation_with_complex_schemas(client):
    """Test format validation with complex field types"""
    # Test with valid data
    test_data = {
        'fields': [
            {
                'name': 'title',
                'type': 'string',
                'required': True
            },
            {
                'name': 'count',
                'type': 'number',
                'required': False
            },
            {
                'name': 'tags',
                'type': 'array',
                'required': False
            }
        ],
        'test_data': {
            'title': 'Test Title',
            'count': 42,
            'tags': ['tag1', 'tag2']
        }
    }
    
    response = client.post("/api/workflow/formats/validate", json=test_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['valid'] == True
    assert len(data['errors']) == 0
    
    # Test with invalid data (missing required field)
    invalid_test_data = {
        'fields': [
            {
                'name': 'title',
                'type': 'string',
                'required': True
            }
        ],
        'test_data': {
            'count': 42  # Missing required 'title' field
        }
    }
    
    response = client.post("/api/workflow/formats/validate", json=invalid_test_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['valid'] == False
    assert len(data['errors']) > 0

def test_format_template_listing(client):
    """Test listing all format templates"""
    # Create a few templates first
    templates = [
        {
            'name': 'Template 1',
            'description': 'First template',
            'fields': [{'name': 'field1', 'type': 'string', 'required': False}]
        },
        {
            'name': 'Template 2',
            'description': 'Second template',
            'fields': [{'name': 'field2', 'type': 'string', 'required': True}]
        }
    ]
    
    for template in templates:
        response = client.post("/api/workflow/formats/templates", json=template)
        assert response.status_code == 201
    
    # List all templates
    list_response = client.get("/api/workflow/formats/templates")
    assert list_response.status_code == 200
    
    data = list_response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least the ones we just created
    
    # Verify template structure
    for template in data:
        assert 'id' in template
        assert 'name' in template
        assert 'description' in template
        assert 'fields' in template
        assert isinstance(template['fields'], list)

def test_format_validation_error_handling(client):
    """Test error handling in format validation"""
    # Test with missing fields
    invalid_request = {
        'test_data': {'title': 'Test'}
        # Missing 'fields' key
    }
    
    response = client.post("/api/workflow/formats/validate", json=invalid_request)
    assert response.status_code == 400
    
    # Test with invalid fields structure
    invalid_request = {
        'fields': 'not an array',
        'test_data': {'title': 'Test'}
    }
    
    response = client.post("/api/workflow/formats/validate", json=invalid_request)
    assert response.status_code == 400 