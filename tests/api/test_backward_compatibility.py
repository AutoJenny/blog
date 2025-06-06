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

def test_list_actions_backward_compatibility(client):
    """Test that list actions endpoint maintains backward compatibility."""
    # Test old response format
    response = client.get("/api/v1/llm/actions")
    assert response.status_code == 200
    data = response.get_json()
    
    # Check old response structure
    assert "status" in data
    assert "data" in data
    assert isinstance(data["data"], list)
    
    # Check old field names
    if data["data"]:
        action = data["data"][0]
        assert "id" in action
        assert "name" in action
        assert "description" in action
        assert "input_field" in action
        assert "output_field" in action
        assert "model" in action
        assert "status" in action

def test_get_action_backward_compatibility(client):
    """Test that get action endpoint maintains backward compatibility."""
    # Create test action
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    
    # Test old response format
    response = client.get(f"/api/v1/llm/actions/{action.id}")
    assert response.status_code == 200
    data = response.get_json()
    
    # Check old response structure
    assert "status" in data
    assert "data" in data
    assert isinstance(data["data"], dict)
    
    # Check old field names
    action_data = data["data"]
    assert "id" in action_data
    assert "name" in action_data
    assert "description" in action_data
    assert "input_field" in action_data
    assert "output_field" in action_data
    assert "model" in action_data
    assert "status" in action_data

def test_execute_action_backward_compatibility(client):
    """Test that execute action endpoint maintains backward compatibility."""
    # Create test action
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    
    # Test old request format
    response = client.post(
        f"/api/v1/llm/actions/{action.id}/execute",
        json={"input": {"idea_seed": "Test idea"}}  # Old format
    )
    assert response.status_code == 200
    data = response.get_json()
    
    # Check old response structure
    assert "status" in data
    assert "data" in data
    assert isinstance(data["data"], dict)
    
    # Check old field names
    run_data = data["data"]
    assert "id" in run_data
    assert "action_id" in run_data
    assert "input_data" in run_data
    assert "output_data" in run_data
    assert "status" in run_data

def test_list_runs_backward_compatibility(client):
    """Test that list runs endpoint maintains backward compatibility."""
    # Create test action and run
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    action_run = ActionRun(
        action_id=action.id,
        input_data={"idea_seed": "Test idea"},
        output_data={"summary": "Test summary"},
        status="completed"
    )
    
    # Test old response format
    response = client.get(f"/api/v1/llm/actions/{action.id}/runs")
    assert response.status_code == 200
    data = response.get_json()
    
    # Check old response structure
    assert "status" in data
    assert "data" in data
    assert isinstance(data["data"], list)
    
    # Check old field names
    if data["data"]:
        run = data["data"][0]
        assert "id" in run
        assert "action_id" in run
        assert "input_data" in run
        assert "output_data" in run
        assert "status" in run

def test_get_run_backward_compatibility(client):
    """Test that get run endpoint maintains backward compatibility."""
    # Create test action and run
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    action_run = ActionRun(
        action_id=action.id,
        input_data={"idea_seed": "Test idea"},
        output_data={"summary": "Test summary"},
        status="completed"
    )
    
    # Test old response format
    response = client.get(f"/api/v1/llm/actions/{action.id}/runs/{action_run.id}")
    assert response.status_code == 200
    data = response.get_json()
    
    # Check old response structure
    assert "status" in data
    assert "data" in data
    assert isinstance(data["data"], dict)
    
    # Check old field names
    run_data = data["data"]
    assert "id" in run_data
    assert "action_id" in run_data
    assert "input_data" in run_data
    assert "output_data" in run_data
    assert "status" in run_data

def test_error_response_backward_compatibility(client):
    """Test that error responses maintain backward compatibility."""
    # Test 400 error
    response = client.get("/api/v1/llm/actions/invalid-id")
    assert response.status_code == 400
    data = response.get_json()
    
    # Check old error response structure
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data
    assert "errors" in data
    
    # Test 401 error
    response = client.get("/api/v1/llm/actions")
    assert response.status_code == 401
    data = response.get_json()
    
    # Check old error response structure
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data
    
    # Test 403 error
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        json={"input_data": {"idea_seed": "Test idea"}}
    )
    assert response.status_code == 403
    data = response.get_json()
    
    # Check old error response structure
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data
    
    # Test 404 error
    response = client.get("/api/v1/llm/actions/999")
    assert response.status_code == 404
    data = response.get_json()
    
    # Check old error response structure
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data
    
    # Test 500 error
    response = client.get("/api/v1/llm/actions/error")
    assert response.status_code == 500
    data = response.get_json()
    
    # Check old error response structure
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data 