import pytest
from flask import Flask
from app import create_app
from app.db import get_db_conn
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def browser():
    """Setup headless Firefox browser for UI testing"""
    options = Options()
    options.add_argument("--headless")
    browser = Firefox(options=options)
    yield browser
    browser.quit()

def test_complete_workflow_journey(browser, client):
    """Test complete workflow journey from post creation to completion."""
    # 1. Create new post
    browser.get("http://localhost:5000/workflow/posts/new")
    
    # Wait for form
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "post-form"))
    )
    
    # Fill post details
    browser.find_element(By.ID, "post-title").send_keys("Integration Test Post")
    browser.find_element(By.ID, "create-post").click()
    
    # Wait for redirect to planning stage
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "planning-stage"))
    )
    
    # 2. Complete planning stage
    # Navigate through substages
    substages = ["idea", "scope", "title"]
    for substage in substages:
        # Navigate to substage
        browser.find_element(By.CLASS_NAME, f"substage-{substage}").click()
        
        # Wait for LLM panel
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "llm-panel"))
        )
        
        # Fill in required fields
        input_field = browser.find_element(By.CLASS_NAME, "llm-input")
        input_field.send_keys(f"Test input for {substage}")
        
        # Run LLM
        browser.find_element(By.ID, "run-llm").click()
        
        # Wait for results
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "llm-output"))
        )
        
        # Mark as complete
        browser.find_element(By.ID, "complete-substage").click()
        
        # Wait for completion
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "substage-complete"))
        )

def test_api_integration(client):
    """Test API integration across workflow stages."""
    # 1. Create post via API
    response = client.post("/api/workflow/posts", json={
        "title": "API Integration Test"
    })
    assert response.status_code == 201
    post_data = response.get_json()
    post_id = post_data["id"]
    
    # 2. Update field mappings
    response = client.post(f"/api/workflow/posts/{post_id}/fields", json={
        "title": "Updated Title",
        "idea_seed": "Test idea"
    })
    assert response.status_code == 200
    
    # 3. Run LLM action
    response = client.post(f"/api/workflow/posts/{post_id}/llm", json={
        "action": "generate_idea",
        "input": {
            "idea_seed": "Test idea"
        }
    })
    assert response.status_code == 200
    llm_result = response.get_json()
    assert "output" in llm_result
    
    # 4. Mark stage complete
    response = client.post(f"/api/workflow/posts/{post_id}/stages/planning/complete")
    assert response.status_code == 200

def test_error_recovery(browser, client):
    """Test error recovery in workflow."""
    # 1. Create post with missing data
    response = client.post("/api/workflow/posts", json={})
    assert response.status_code == 400
    error_data = response.get_json()
    assert "error" in error_data
    
    # 2. Test LLM error recovery
    browser.get("http://localhost:5000/workflow/posts/1/planning/idea")
    
    # Wait for LLM panel
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "llm-panel"))
    )
    
    # Trigger error
    browser.find_element(By.ID, "run-llm").click()
    
    # Wait for error message
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
    )
    
    # Check retry functionality
    retry_button = browser.find_element(By.ID, "retry-llm")
    assert retry_button is not None

def test_state_management(browser, client):
    """Test workflow state management."""
    # 1. Create test post
    response = client.post("/api/workflow/posts", json={
        "title": "State Test Post"
    })
    post_data = response.get_json()
    post_id = post_data["id"]
    
    # 2. Test stage progression
    stages = ["planning", "development", "review"]
    for stage in stages:
        # Check stage state
        response = client.get(f"/api/workflow/posts/{post_id}/stages/{stage}")
        assert response.status_code == 200
        stage_data = response.get_json()
        
        # Complete stage
        response = client.post(f"/api/workflow/posts/{post_id}/stages/{stage}/complete")
        assert response.status_code == 200
        
        # Verify completion
        response = client.get(f"/api/workflow/posts/{post_id}/stages/{stage}")
        updated_data = response.get_json()
        assert updated_data["status"] == "complete" 