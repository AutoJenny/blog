import pytest
from flask import Flask
from app.api.base import APIBlueprint
from app.api.llm import bp as llm_bp
from app.api.llm.models import Action, ActionRun
from app.api.llm.schemas import ActionSchema, ActionRunSchema
from app.api.llm.services import execute_action
from flasgger import Swagger

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    app.config["SWAGGER"] = {
        "title": "LLM API",
        "uiversion": 3,
        "openapi": "3.0.2",
        "info": {
            "title": "LLM API",
            "version": "1.0.0",
            "description": "API for managing LLM actions and runs"
        }
    }
    return app

@pytest.fixture
def client(app):
    app.register_blueprint(llm_bp)
    Swagger(app)
    return app.test_client()

def test_swagger_documentation(client):
    """Test that Swagger documentation is available."""
    response = client.get("/apidocs")
    assert response.status_code == 200
    assert "swagger" in response.get_data(as_text=True)

def test_openapi_spec(client):
    """Test that OpenAPI specification is available."""
    response = client.get("/apispec_1.json")
    assert response.status_code == 200
    spec = response.get_json()
    
    # Check basic OpenAPI structure
    assert "openapi" in spec
    assert "info" in spec
    assert "paths" in spec
    assert "components" in spec
    
    # Check paths
    paths = spec["paths"]
    assert "/api/v1/llm/actions" in paths
    assert "/api/v1/llm/actions/{id}" in paths
    assert "/api/v1/llm/actions/{id}/execute" in paths
    assert "/api/v1/llm/actions/{id}/runs" in paths
    assert "/api/v1/llm/actions/{id}/runs/{run_id}" in paths

def test_endpoint_documentation(client):
    """Test that each endpoint has proper documentation."""
    response = client.get("/apispec_1.json")
    spec = response.get_json()
    paths = spec["paths"]
    
    # Check list actions endpoint
    list_actions = paths["/api/v1/llm/actions"]
    assert "get" in list_actions
    assert "summary" in list_actions["get"]
    assert "description" in list_actions["get"]
    assert "parameters" in list_actions["get"]
    assert "responses" in list_actions["get"]
    
    # Check get action endpoint
    get_action = paths["/api/v1/llm/actions/{id}"]
    assert "get" in get_action
    assert "summary" in get_action["get"]
    assert "description" in get_action["get"]
    assert "parameters" in get_action["get"]
    assert "responses" in get_action["get"]
    
    # Check execute action endpoint
    execute_action = paths["/api/v1/llm/actions/{id}/execute"]
    assert "post" in execute_action
    assert "summary" in execute_action["post"]
    assert "description" in execute_action["post"]
    assert "requestBody" in execute_action["post"]
    assert "responses" in execute_action["post"]
    
    # Check list runs endpoint
    list_runs = paths["/api/v1/llm/actions/{id}/runs"]
    assert "get" in list_runs
    assert "summary" in list_runs["get"]
    assert "description" in list_runs["get"]
    assert "parameters" in list_runs["get"]
    assert "responses" in list_runs["get"]
    
    # Check get run endpoint
    get_run = paths["/api/v1/llm/actions/{id}/runs/{run_id}"]
    assert "get" in get_run
    assert "summary" in get_run["get"]
    assert "description" in get_run["get"]
    assert "parameters" in get_run["get"]
    assert "responses" in get_run["get"]

def test_schema_documentation(client):
    """Test that schemas are properly documented."""
    response = client.get("/apispec_1.json")
    spec = response.get_json()
    schemas = spec["components"]["schemas"]
    
    # Check Action schema
    assert "Action" in schemas
    action_schema = schemas["Action"]
    assert "type" in action_schema
    assert "properties" in action_schema
    assert "required" in action_schema
    
    # Check ActionRun schema
    assert "ActionRun" in schemas
    action_run_schema = schemas["ActionRun"]
    assert "type" in action_run_schema
    assert "properties" in action_run_schema
    assert "required" in action_run_schema

def test_response_documentation(client):
    """Test that responses are properly documented."""
    response = client.get("/apispec_1.json")
    spec = response.get_json()
    paths = spec["paths"]
    
    # Check list actions responses
    list_actions = paths["/api/v1/llm/actions"]["get"]
    responses = list_actions["responses"]
    assert "200" in responses
    assert "401" in responses
    assert "403" in responses
    assert "500" in responses
    
    # Check execute action responses
    execute_action = paths["/api/v1/llm/actions/{id}/execute"]["post"]
    responses = execute_action["responses"]
    assert "200" in responses
    assert "400" in responses
    assert "401" in responses
    assert "403" in responses
    assert "404" in responses
    assert "500" in responses

def test_parameter_documentation(client):
    """Test that parameters are properly documented."""
    response = client.get("/apispec_1.json")
    spec = response.get_json()
    paths = spec["paths"]
    
    # Check path parameters
    get_action = paths["/api/v1/llm/actions/{id}"]
    parameters = get_action["get"]["parameters"]
    assert any(p["name"] == "id" and p["in"] == "path" for p in parameters)
    
    # Check query parameters
    list_actions = paths["/api/v1/llm/actions"]
    parameters = list_actions["get"]["parameters"]
    assert any(p["name"] == "page" and p["in"] == "query" for p in parameters)
    assert any(p["name"] == "per_page" and p["in"] == "query" for p in parameters)

def test_security_documentation(client):
    """Test that security requirements are properly documented."""
    response = client.get("/apispec_1.json")
    spec = response.get_json()
    
    # Check security schemes
    assert "securitySchemes" in spec["components"]
    security_schemes = spec["components"]["securitySchemes"]
    assert "bearerAuth" in security_schemes
    
    # Check security requirements
    paths = spec["paths"]
    for path in paths.values():
        for operation in path.values():
            assert "security" in operation
            assert any("bearerAuth" in req for req in operation["security"]) 