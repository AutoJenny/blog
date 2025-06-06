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

def test_list_actions_forward_compatibility(client):
    """Test that list actions endpoint handles future changes gracefully."""
    # Test with additional fields
    response = client.get("/api/v1/llm/actions")
    assert response.status_code == 200
    data = response.get_json()
    
    # Check that additional fields don't break the response
    if data["data"]:
        action = data["data"][0]
        # Add future fields
        action["future_field1"] = "value1"
        action["future_field2"] = "value2"
        assert "id" in action
        assert "name" in action
        assert "description" in action
        assert "input_field" in action
        assert "output_field" in action
        assert "model" in action
        assert "status" in action

def test_get_action_forward_compatibility(client):
    """Test that get action endpoint handles future changes gracefully."""
    # Create test action
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    
    # Test with additional fields
    response = client.get(f"/api/v1/llm/actions/{action.id}")
    assert response.status_code == 200
    data = response.get_json()
    
    # Check that additional fields don't break the response
    action_data = data["data"]
    # Add future fields
    action_data["future_field1"] = "value1"
    action_data["future_field2"] = "value2"
    assert "id" in action_data
    assert "name" in action_data
    assert "description" in action_data
    assert "input_field" in action_data
    assert "output_field" in action_data
    assert "model" in action_data
    assert "status" in action_data

def test_execute_action_forward_compatibility(client):
    """Test that execute action endpoint handles future changes gracefully."""
    # Create test action
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    
    # Test with additional fields in request
    response = client.post(
        f"/api/v1/llm/actions/{action.id}/execute",
        json={
            "input_data": {
                "idea_seed": "Test idea",
                "future_field1": "value1",
                "future_field2": "value2"
            },
            "future_option1": "value1",
            "future_option2": "value2"
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    
    # Check that additional fields don't break the response
    run_data = data["data"]
    # Add future fields
    run_data["future_field1"] = "value1"
    run_data["future_field2"] = "value2"
    assert "id" in run_data
    assert "action_id" in run_data
    assert "input_data" in run_data
    assert "output_data" in run_data
    assert "status" in run_data

def test_list_runs_forward_compatibility(client):
    """Test that list runs endpoint handles future changes gracefully."""
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
    
    # Test with additional fields
    response = client.get(f"/api/v1/llm/actions/{action.id}/runs")
    assert response.status_code == 200
    data = response.get_json()
    
    # Check that additional fields don't break the response
    if data["data"]:
        run = data["data"][0]
        # Add future fields
        run["future_field1"] = "value1"
        run["future_field2"] = "value2"
        assert "id" in run
        assert "action_id" in run
        assert "input_data" in run
        assert "output_data" in run
        assert "status" in run

def test_get_run_forward_compatibility(client):
    """Test that get run endpoint handles future changes gracefully."""
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
    
    # Test with additional fields
    response = client.get(f"/api/v1/llm/actions/{action.id}/runs/{action_run.id}")
    assert response.status_code == 200
    data = response.get_json()
    
    # Check that additional fields don't break the response
    run_data = data["data"]
    # Add future fields
    run_data["future_field1"] = "value1"
    run_data["future_field2"] = "value2"
    assert "id" in run_data
    assert "action_id" in run_data
    assert "input_data" in run_data
    assert "output_data" in run_data
    assert "status" in run_data

def test_error_response_forward_compatibility(client):
    """Test that error responses handle future changes gracefully."""
    # Test 400 error with additional fields
    response = client.get("/api/v1/llm/actions/invalid-id")
    assert response.status_code == 400
    data = response.get_json()
    
    # Add future fields
    data["future_field1"] = "value1"
    data["future_field2"] = "value2"
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data
    assert "errors" in data
    
    # Test 401 error with additional fields
    response = client.get("/api/v1/llm/actions")
    assert response.status_code == 401
    data = response.get_json()
    
    # Add future fields
    data["future_field1"] = "value1"
    data["future_field2"] = "value2"
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data
    
    # Test 403 error with additional fields
    response = client.post(
        "/api/v1/llm/actions/1/execute",
        json={"input_data": {"idea_seed": "Test idea"}}
    )
    assert response.status_code == 403
    data = response.get_json()
    
    # Add future fields
    data["future_field1"] = "value1"
    data["future_field2"] = "value2"
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data
    
    # Test 404 error with additional fields
    response = client.get("/api/v1/llm/actions/999")
    assert response.status_code == 404
    data = response.get_json()
    
    # Add future fields
    data["future_field1"] = "value1"
    data["future_field2"] = "value2"
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data
    
    # Test 500 error with additional fields
    response = client.get("/api/v1/llm/actions/error")
    assert response.status_code == 500
    data = response.get_json()
    
    # Add future fields
    data["future_field1"] = "value1"
    data["future_field2"] = "value2"
    assert "status" in data
    assert data["status"] == "error"
    assert "message" in data 