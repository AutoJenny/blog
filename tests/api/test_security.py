import pytest
import jwt
from datetime import datetime, timedelta
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

def test_unauthorized_access(client):
    """Test that unauthorized access is denied."""
    # Test without token
    response = client.get("/api/v1/llm/actions")
    assert response.status_code == 401
    
    # Test with invalid token
    response = client.get(
        "/api/v1/llm/actions",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401
    
    # Test with expired token
    expired_token = jwt.encode(
        {
            "sub": 1,
            "exp": datetime.utcnow() - timedelta(hours=1)
        },
        "test-secret-key",
        algorithm="HS256"
    )
    response = client.get(
        "/api/v1/llm/actions",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401

def test_csrf_protection(client):
    """Test that CSRF protection is in place."""
    # Test without CSRF token
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        json={"input_data": {"idea_seed": "Test idea"}}
    )
    assert response.status_code == 401
    
    # Test with invalid CSRF token
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        json={"input_data": {"idea_seed": "Test idea"}},
        headers={"X-CSRF-Token": "invalid-token"}
    )
    assert response.status_code == 401

def test_sql_injection_prevention(client):
    """Test that SQL injection attempts are prevented."""
    # Test with SQL injection in input
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        json={
            "input_data": {
                "idea_seed": "'; DROP TABLE actions; --"
            }
        }
    )
    assert response.status_code == 400
    
    # Test with SQL injection in query parameters
    response = client.get("/api/v1/llm/actions?name='; DROP TABLE actions; --")
    assert response.status_code == 400

def test_xss_prevention(client):
    """Test that XSS attacks are prevented."""
    # Test with XSS in input
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        json={
            "input_data": {
                "idea_seed": "<script>alert('xss')</script>"
            }
        }
    )
    assert response.status_code == 400
    
    # Test with XSS in query parameters
    response = client.get("/api/v1/llm/actions?name=<script>alert('xss')</script>")
    assert response.status_code == 400

def test_rate_limiting(client):
    """Test that rate limiting is in place."""
    # Make multiple requests in quick succession
    for _ in range(100):
        response = client.get("/api/v1/llm/actions")
    
    # The last request should be rate limited
    assert response.status_code == 429

def test_input_validation(client):
    """Test that input validation prevents malicious data."""
    # Test with invalid JSON
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        data="invalid json",
        content_type="application/json"
    )
    assert response.status_code == 400
    
    # Test with missing required fields
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        json={}
    )
    assert response.status_code == 400
    
    # Test with invalid field types
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        json={"input_data": {"idea_seed": 123}}  # Should be string
    )
    assert response.status_code == 400

def test_file_upload_security(client):
    """Test that file uploads are properly secured."""
    # Test with malicious file
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        data={
            "input_data": {
                "idea_seed": "Test idea",
                "file": (b"malicious content", "malicious.exe")
            }
        },
        content_type="multipart/form-data"
    )
    assert response.status_code == 400
    
    # Test with file too large
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        data={
            "input_data": {
                "idea_seed": "Test idea",
                "file": (b"x" * 1000000, "large.txt")  # 1MB file
            }
        },
        content_type="multipart/form-data"
    )
    assert response.status_code == 400

def test_headers_security(client):
    """Test that security headers are properly set."""
    response = client.get("/api/v1/llm/actions")
    
    # Check for security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Strict-Transport-Security") is not None
    assert response.headers.get("Content-Security-Policy") is not None 