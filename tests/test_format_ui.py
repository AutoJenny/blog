import pytest
from flask import Flask, url_for
from app import create_app
from app.db import get_db_conn
import json

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_format_template_page(client):
    """Test format template management page"""
    response = client.get("/settings/format_templates")
    assert response.status_code == 200
    assert b"Format Templates" in response.data
    assert b"Create New Format" in response.data

def test_format_template_creation_ui(client):
    """Test format template creation through UI"""
    # Get the page first
    response = client.get("/settings/format_templates")
    assert response.status_code == 200
    
    # Create a new format template
    format_data = {
        "name": "UI Test Format",
        "format_type": "input",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "test": {"type": "string"}
            }
        })
    }
    response = client.post("/api/formats/templates", json=format_data)
    assert response.status_code == 201
    
    # Verify it appears on the page
    response = client.get("/settings/format_templates")
    assert response.status_code == 200
    assert format_data["name"].encode() in response.data

def test_format_preview(client):
    """Test format preview functionality"""
    # Create a format template
    format_data = {
        "name": "Preview Test Format",
        "format_type": "input",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "test": {"type": "string"}
            },
            "required": ["test"]
        })
    }
    response = client.post("/api/formats/templates", json=format_data)
    assert response.status_code == 201
    template = response.get_json()
    
    # Test preview with valid data
    response = client.post("/api/formats/validate", json={
        "format_spec": format_data["format_spec"],
        "test_data": {"test": "value"}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["valid"] is True
    
    # Test preview with invalid data
    response = client.post("/api/formats/validate", json={
        "format_spec": format_data["format_spec"],
        "test_data": {}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["valid"] is False

def test_workflow_format_config_ui(client):
    """Test workflow step format configuration UI"""
    # Create input and output formats
    input_format = {
        "name": "Workflow Input Format",
        "format_type": "input",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "title": {"type": "string"}
            }
        })
    }
    response = client.post("/api/formats/templates", json=input_format)
    assert response.status_code == 201
    
    # Get the workflow step configuration page
    response = client.get("/settings/workflow_step_formats")
    assert response.status_code == 200
    assert b"Format Configuration" in response.data
    assert input_format["name"].encode() in response.data

def test_format_validation_feedback(client):
    """Test format validation feedback in UI"""
    # Create a format template
    format_data = {
        "name": "Validation Test Format",
        "format_type": "input",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "test": {"type": "string"}
            },
            "required": ["test"]
        })
    }
    response = client.post("/api/formats/templates", json=format_data)
    assert response.status_code == 201
    
    # Test validation feedback
    response = client.post("/api/formats/validate", json={
        "format_spec": format_data["format_spec"],
        "test_data": {}
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["valid"] is False
    assert any("required" in error for error in data["errors"]) 