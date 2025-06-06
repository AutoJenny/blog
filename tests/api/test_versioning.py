import pytest
from flask import Flask
from app.api.base import APIBlueprint
from app.api.llm import bp as llm_bp
from app.api.llm.models import Action, ActionRun
from app.api.llm.schemas import ActionSchema, ActionRunSchema
from app.api.llm.services import execute_action

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    return app

@pytest.fixture
def client(app):
    app.register_blueprint(llm_bp)
    return app.test_client()

def test_version_header(client):
    """Test that version header is properly handled."""
    # Test without version header
    response = client.get("/api/v1/llm/actions")
    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == "v1"
    
    # Test with version header
    response = client.get(
        "/api/v1/llm/actions",
        headers={"X-API-Version": "v1"}
    )
    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == "v1"
    
    # Test with invalid version header
    response = client.get(
        "/api/v1/llm/actions",
        headers={"X-API-Version": "invalid"}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "message" in data
    assert "Invalid API version" in data["message"]

def test_version_path(client):
    """Test that version in path is properly handled."""
    # Test with correct version
    response = client.get("/api/v1/llm/actions")
    assert response.status_code == 200
    
    # Test with incorrect version
    response = client.get("/api/v2/llm/actions")
    assert response.status_code == 404
    
    # Test with invalid version
    response = client.get("/api/invalid/llm/actions")
    assert response.status_code == 404

def test_version_deprecation(client):
    """Test that deprecated versions are properly handled."""
    # Test with deprecated version
    response = client.get(
        "/api/v1/llm/actions",
        headers={"X-API-Version": "v0"}
    )
    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == "v0"
    assert response.headers.get("X-API-Deprecated") == "true"
    assert "X-API-Sunset-Date" in response.headers

def test_version_sunset(client):
    """Test that sunset versions are properly handled."""
    # Test with sunset version
    response = client.get(
        "/api/v1/llm/actions",
        headers={"X-API-Version": "v0"}
    )
    assert response.status_code == 410
    data = response.get_json()
    assert data["status"] == "error"
    assert "message" in data
    assert "API version has been sunset" in data["message"]

def test_version_forwarding(client):
    """Test that version forwarding works correctly."""
    # Test with version forwarding
    response = client.get(
        "/api/v1/llm/actions",
        headers={"X-API-Version": "v2"}
    )
    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == "v2"
    assert response.headers.get("X-API-Forwarded") == "true"

def test_version_negotiation(client):
    """Test that version negotiation works correctly."""
    # Test with version negotiation
    response = client.get(
        "/api/v1/llm/actions",
        headers={"Accept": "application/json;version=2"}
    )
    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == "v2"
    assert response.headers.get("X-API-Negotiated") == "true"

def test_version_specific_endpoints(client):
    """Test that version-specific endpoints work correctly."""
    # Test v1 endpoint
    response = client.get("/api/v1/llm/actions")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data
    assert "data" in data
    
    # Test v2 endpoint
    response = client.get("/api/v2/llm/actions")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data
    assert "data" in data
    assert "metadata" in data  # v2 specific field

def test_version_specific_schemas(client):
    """Test that version-specific schemas work correctly."""
    # Test v1 schema
    response = client.get("/api/v1/llm/actions/1")
    assert response.status_code == 200
    data = response.get_json()
    assert "id" in data["data"]
    assert "name" in data["data"]
    assert "description" in data["data"]
    
    # Test v2 schema
    response = client.get("/api/v2/llm/actions/1")
    assert response.status_code == 200
    data = response.get_json()
    assert "id" in data["data"]
    assert "name" in data["data"]
    assert "description" in data["data"]
    assert "metadata" in data["data"]  # v2 specific field

def test_version_specific_errors(client):
    """Test that version-specific error responses work correctly."""
    # Test v1 error
    response = client.get("/api/v1/llm/actions/invalid")
    assert response.status_code == 400
    data = response.get_json()
    assert "status" in data
    assert "message" in data
    assert "errors" in data
    
    # Test v2 error
    response = client.get("/api/v2/llm/actions/invalid")
    assert response.status_code == 400
    data = response.get_json()
    assert "status" in data
    assert "message" in data
    assert "errors" in data
    assert "metadata" in data  # v2 specific field 