import pytest
from flask import Flask
from app.api.formats import formats_bp
from app.db import get_db_conn
from psycopg2.extras import RealDictCursor
import json

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    app.register_blueprint(formats_bp)
    return app.test_client()

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

def test_create_format_template(client, sample_format):
    """Test creating a format template"""
    response = client.post("/api/formats/templates", json=sample_format)
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == sample_format["name"]
    assert data["format_type"] == sample_format["format_type"]
    assert data["format_spec"] == sample_format["format_spec"]
    assert "id" in data
    return data["id"]

def test_get_format_template(client, sample_format):
    """Test retrieving a format template"""
    # Create a template first
    template_id = test_create_format_template(client, sample_format)
    
    # Get the template
    response = client.get(f"/api/formats/templates/{template_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == sample_format["name"]
    assert data["format_type"] == sample_format["format_type"]
    assert data["format_spec"] == sample_format["format_spec"]

def test_update_format_template(client, sample_format):
    """Test updating a format template"""
    # Create a template first
    template_id = test_create_format_template(client, sample_format)
    
    # Update the template
    updated_data = {
        "name": "Updated Format",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "test": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["test"]
        })
    }
    
    response = client.patch(f"/api/formats/templates/{template_id}", json=updated_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == updated_data["name"]
    assert data["format_spec"] == updated_data["format_spec"]

def test_delete_format_template(client, sample_format):
    """Test deleting a format template"""
    # Create a template first
    template_id = test_create_format_template(client, sample_format)
    
    # Delete the template
    response = client.delete(f"/api/formats/templates/{template_id}")
    assert response.status_code == 204
    
    # Verify it's gone
    response = client.get(f"/api/formats/templates/{template_id}")
    assert response.status_code == 404

def test_validate_format(client):
    """Test format validation"""
    format_spec = {
        "type": "object",
        "properties": {
            "test": {"type": "string"}
        },
        "required": ["test"]
    }
    
    # Test valid data
    response = client.post("/api/formats/validate", json={
        "format_spec": json.dumps(format_spec),
        "test_data": {"test": "value"}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["valid"] is True
    assert len(data["errors"]) == 0
    
    # Test invalid data
    response = client.post("/api/formats/validate", json={
        "format_spec": json.dumps(format_spec),
        "test_data": {"test": 123}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0

def test_format_error_handling(client):
    """Test error handling in format endpoints"""
    # Test invalid format type
    response = client.post("/api/formats/templates", json={
        "name": "Invalid Format",
        "format_type": "invalid",
        "format_spec": "{}"
    })
    assert response.status_code == 400
    
    # Test invalid JSON schema
    response = client.post("/api/formats/templates", json={
        "name": "Invalid Schema",
        "format_type": "input",
        "format_spec": "invalid json"
    })
    assert response.status_code == 400
    
    # Test missing required fields
    response = client.post("/api/formats/templates", json={
        "name": "Missing Fields"
    })
    assert response.status_code == 400 