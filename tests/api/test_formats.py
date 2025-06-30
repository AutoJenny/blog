import pytest
from flask import Flask
from app.api.workflow.formats import formats_bp
from app.db import get_db_conn
from psycopg2.extras import RealDictCursor
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
            app.register_blueprint(formats_bp)
            yield client

@pytest.fixture
def sample_format():
    return {
        "name": "Test Format",
        "format_type": "input",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "test": {"type": "string"}
            },
            "required": ["test"]
        })
    }

def test_create_format_template(client):
    """Test creating a new format template"""
    sample_format = {
        'name': 'Test Input Format',
        'description': 'A test input format',
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
    
    response = client.post("/api/workflow/formats/templates", json=sample_format)
    assert response.status_code == 201
    
    data = response.get_json()
    assert data['name'] == 'Test Input Format'
    assert data['description'] == 'A test input format'
    assert len(data['fields']) == 2
    assert data['fields'][0]['name'] == 'title'
    assert data['fields'][0]['type'] == 'string'
    assert data['fields'][0]['required'] == True

def test_get_format_template(client):
    """Test getting a specific format template"""
    # First create a template
    sample_format = {
        'name': 'Test Format',
        'description': 'A test format',
        'fields': [
            {
                'name': 'test_field',
                'type': 'string',
                'required': False
            }
        ]
    }
    
    create_response = client.post("/api/workflow/formats/templates", json=sample_format)
    template_id = create_response.get_json()['id']
    
    # Then get it
    response = client.get(f"/api/workflow/formats/templates/{template_id}")
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['name'] == 'Test Format'
    assert data['description'] == 'A test format'
    assert len(data['fields']) == 1

def test_update_format_template(client):
    """Test updating a format template"""
    # First create a template
    sample_format = {
        'name': 'Original Format',
        'description': 'Original description',
        'fields': [
            {
                'name': 'original_field',
                'type': 'string',
                'required': False
            }
        ]
    }
    
    create_response = client.post("/api/workflow/formats/templates", json=sample_format)
    template_id = create_response.get_json()['id']
    
    # Then update it
    updated_data = {
        'name': 'Updated Format',
        'description': 'Updated description',
        'fields': [
            {
                'name': 'updated_field',
                'type': 'string',
                'required': True,
                'description': 'Updated field description'
            }
        ]
    }
    
    response = client.put(f"/api/workflow/formats/templates/{template_id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['name'] == 'Updated Format'
    assert data['description'] == 'Updated description'
    assert len(data['fields']) == 1
    assert data['fields'][0]['name'] == 'updated_field'
    assert data['fields'][0]['required'] == True

def test_delete_format_template(client):
    """Test deleting a format template"""
    # First create a template
    sample_format = {
        'name': 'To Delete',
        'description': 'Will be deleted',
        'fields': [
            {
                'name': 'temp_field',
                'type': 'string',
                'required': False
            }
        ]
    }
    
    create_response = client.post("/api/workflow/formats/templates", json=sample_format)
    template_id = create_response.get_json()['id']
    
    # Then delete it
    response = client.delete(f"/api/workflow/formats/templates/{template_id}")
    assert response.status_code == 200
    
    # Verify it's gone
    get_response = client.get(f"/api/workflow/formats/templates/{template_id}")
    assert get_response.status_code == 404

def test_validate_format(client):
    """Test format validation"""
    # Test with valid data
    test_data = {
        'fields': [
            {
                'name': 'title',
                'type': 'string',
                'required': True
            }
        ],
        'test_data': {
            'title': 'Test Title'
        }
    }
    
    response = client.post("/api/workflow/formats/validate", json=test_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['valid'] == True
    assert len(data['errors']) == 0
    
    # Test with invalid data
    invalid_test_data = {
        'fields': [
            {
                'name': 'title',
                'type': 'string',
                'required': True
            }
        ],
        'test_data': {
            'wrong_field': 'Test Title'
        }
    }
    
    response = client.post("/api/workflow/formats/validate", json=invalid_test_data)
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['valid'] == False
    assert len(data['errors']) > 0

def test_create_format_missing_fields(client):
    """Test creating format template with missing required fields"""
    # Missing name
    invalid_format = {
        'description': 'Missing name',
        'fields': [
            {
                'name': 'test',
                'type': 'string',
                'required': False
            }
        ]
    }
    
    response = client.post("/api/workflow/formats/templates", json=invalid_format)
    assert response.status_code == 400
    
    # Missing fields
    invalid_format = {
        'name': 'Missing fields',
        'description': 'No fields array'
    }
    
    response = client.post("/api/workflow/formats/templates", json=invalid_format)
    assert response.status_code == 400

def test_create_format_invalid_fields(client):
    """Test creating format template with invalid fields structure"""
    invalid_format = {
        'name': 'Invalid fields',
        'description': 'Fields not an array',
        'fields': 'not an array'
    }
    
    response = client.post("/api/workflow/formats/templates", json=invalid_format)
    assert response.status_code == 400

def test_format_error_handling(client):
    """Test error handling in format endpoints"""
    # Test invalid format type
    response = client.post("/api/workflow/formats/templates", json={
        "name": "Invalid Format",
        "format_type": "invalid",
        "format_spec": "{}"
    })
    assert response.status_code == 400
    
    # Test invalid JSON schema
    response = client.post("/api/workflow/formats/templates", json={
        "name": "Invalid Schema",
        "format_type": "input",
        "format_spec": "invalid json"
    })
    assert response.status_code == 400
    
    # Test missing required fields
    response = client.post("/api/workflow/formats/templates", json={
        "name": "Missing Fields"
    })
    assert response.status_code == 400 