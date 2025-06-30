import pytest
from flask import Flask
from app import create_app
from app.db import get_db_conn

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_post_endpoints(client):
    """Test workflow post endpoints."""
    # Test post list
    response = client.get("/api/workflow/posts")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

    # Test single post
    if data:
        post_id = data[0]["id"]
        response = client.get(f"/api/workflow/posts/{post_id}")
        assert response.status_code == 200
        post = response.get_json()
        assert post["id"] == post_id

def test_field_mapping_endpoints(client):
    """Test field mapping endpoints."""
    # Test get mappings
    response = client.get("/api/workflow/fields/mappings")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)

    # Test update mapping
    mapping = {
        "field": "test_field",
        "value": "test_value"
    }
    response = client.post("/api/workflow/fields/mappings",
                         json=mapping)
    assert response.status_code == 200
    result = response.get_json()
    assert result["success"] is True

def test_prompt_endpoints(client):
    """Test workflow prompt endpoints."""
    # Test prompt list
    response = client.get("/api/workflow/prompts")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

    # Test single prompt
    if data:
        prompt_id = data[0]["id"]
        response = client.get(f"/api/workflow/prompts/{prompt_id}")
        assert response.status_code == 200
        prompt = response.get_json()
        assert prompt["id"] == prompt_id

def test_llm_endpoints(client):
    """Test LLM integration endpoints."""
    # Test LLM execution
    payload = {
        "prompt": "Test prompt",
        "parameters": {
            "max_tokens": 100
        }
    }
    response = client.post("/api/workflow/llm/execute",
                         json=payload)
    assert response.status_code == 200
    result = response.get_json()
    assert "output" in result

def test_error_handling(client):
    """Test error handling in workflow endpoints."""
    # Test 404 for non-existent post
    response = client.get("/api/workflow/posts/99999")
    assert response.status_code == 404
    
    # Test validation error
    response = client.post("/api/workflow/fields/mappings",
                         json={})
    assert response.status_code == 400
    
    # Test invalid prompt parameters
    response = client.post("/api/workflow/llm/execute",
                         json={})
    assert response.status_code == 400

def test_endpoint_consistency(client):
    """Test consistency of endpoint responses."""
    endpoints = [
        "/api/workflow/posts",
        "/api/workflow/fields/mappings",
        "/api/workflow/prompts",
        "/api/workflow/llm/status"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in [200, 404]  # Either succeeds or not found
        assert response.content_type == "application/json" 