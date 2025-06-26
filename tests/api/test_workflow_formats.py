import pytest
from flask import Flask
from app.api.workflow import workflow_bp
from app.api.formats import formats_bp
import json

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    app.register_blueprint(workflow_bp)
    app.register_blueprint(formats_bp)
    return app.test_client()

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
    input_response = client.post("/api/formats/templates", json=sample_format)
    assert input_response.status_code == 201
    input_format = input_response.get_json()
    
    output_format = dict(sample_format)
    output_format["name"] = "Test Output Format"
    output_format["format_type"] = "output"
    output_response = client.post("/api/formats/templates", json=output_format)
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
    response = client.post("/api/formats/templates", json=sample_format)
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
    response = client.post("/api/formats/validate", json={
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
    response = client.post("/api/formats/validate", json={
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