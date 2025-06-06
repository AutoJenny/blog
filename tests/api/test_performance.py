import pytest
import time
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

def test_list_actions_performance(client):
    """Test the performance of listing actions."""
    # Create test actions
    actions = [
        Action(
            name=f"Test Action {i}",
            description=f"Test Description {i}",
            input_field="idea_seed",
            output_field="summary",
            model="gpt-4",
            status="active"
        )
        for i in range(100)
    ]
    
    # Measure response time
    start_time = time.time()
    response = client.get("/api/v1/llm/actions")
    end_time = time.time()
    
    # Assert response time is within acceptable range (e.g., < 100ms)
    assert end_time - start_time < 0.1
    assert response.status_code == 200

def test_execute_action_performance(client):
    """Test the performance of executing an action."""
    # Create test action
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    
    # Measure response time
    start_time = time.time()
    response = client.post(
        f"/api/v1/llm/actions/{action.id}/execute",
        json={"input_data": {"idea_seed": "Test idea"}}
    )
    end_time = time.time()
    
    # Assert response time is within acceptable range (e.g., < 500ms)
    assert end_time - start_time < 0.5
    assert response.status_code == 200

def test_get_action_run_performance(client):
    """Test the performance of getting an action run."""
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
    
    # Measure response time
    start_time = time.time()
    response = client.get(f"/api/v1/llm/actions/{action.id}/runs/{action_run.id}")
    end_time = time.time()
    
    # Assert response time is within acceptable range (e.g., < 100ms)
    assert end_time - start_time < 0.1
    assert response.status_code == 200

def test_concurrent_requests_performance(client):
    """Test the performance under concurrent requests."""
    import threading
    import queue
    
    # Create test action
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    
    # Function to make request
    def make_request(q):
        start_time = time.time()
        response = client.get("/api/v1/llm/actions")
        end_time = time.time()
        q.put(end_time - start_time)
    
    # Make concurrent requests
    threads = []
    times = queue.Queue()
    for _ in range(10):
        t = threading.Thread(target=make_request, args=(times,))
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Get response times
    response_times = []
    while not times.empty():
        response_times.append(times.get())
    
    # Assert all response times are within acceptable range
    for t in response_times:
        assert t < 0.1

def test_large_payload_performance(client):
    """Test the performance with large payloads."""
    # Create large input data
    large_input = {
        "idea_seed": "Test idea" * 1000,  # 1000 repetitions
        "additional_data": {
            "key": "value" * 1000  # 1000 repetitions
        }
    }
    
    # Create test action
    action = Action(
        name="Test Action",
        description="Test Description",
        input_field="idea_seed",
        output_field="summary",
        model="gpt-4",
        status="active"
    )
    
    # Measure response time
    start_time = time.time()
    response = client.post(
        f"/api/v1/llm/actions/{action.id}/execute",
        json={"input_data": large_input}
    )
    end_time = time.time()
    
    # Assert response time is within acceptable range (e.g., < 1s)
    assert end_time - start_time < 1.0
    assert response.status_code == 200 