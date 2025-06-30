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

@pytest.fixture
def sample_format_template(client):
    """Create a sample format template for testing"""
    format_data = {
        "name": "UI Test Format",
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
    response = client.post("/api/formats/templates", json=format_data)
    assert response.status_code == 201
    return response.get_json()

def test_format_template_management_ui(browser, client, sample_format_template):
    """Test format template management UI interactions"""
    
    # 1. Navigate to format templates page
    browser.get("http://localhost:5000/settings/format_templates")
    
    # Wait for page to load
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "format-templates"))
    )
    
    # 2. Verify sample template is displayed
    template_name = browser.find_element(By.CLASS_NAME, "format-template-name")
    assert sample_format_template["name"] in template_name.text
    
    # 3. Test format template creation
    create_button = browser.find_element(By.ID, "create-format-template")
    create_button.click()
    
    # Wait for modal to appear
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "format-template-modal"))
    )
    
    # Fill in form
    browser.find_element(By.ID, "format-name").send_keys("New Test Format")
    browser.find_element(By.ID, "format-type").send_keys("output")
    browser.find_element(By.ID, "format-spec").send_keys(json.dumps({
        "type": "object",
        "properties": {
            "output": {"type": "string"}
        },
        "required": ["output"]
    }))
    
    # Submit form
    browser.find_element(By.ID, "save-format-template").click()
    
    # Wait for success message
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
    )
    
    # 4. Test format template editing
    edit_button = browser.find_element(By.CLASS_NAME, "edit-format-template")
    edit_button.click()
    
    # Wait for modal to appear
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "format-template-modal"))
    )
    
    # Update form
    name_field = browser.find_element(By.ID, "format-name")
    name_field.clear()
    name_field.send_keys("Updated Test Format")
    
    # Submit form
    browser.find_element(By.ID, "save-format-template").click()
    
    # Wait for success message
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
    )
    
    # Verify update
    template_name = browser.find_element(By.CLASS_NAME, "format-template-name")
    assert "Updated Test Format" in template_name.text

def test_workflow_format_configuration_ui(browser, client, sample_format_template):
    """Test workflow step format configuration UI"""
    
    # 1. Navigate to workflow step formats page
    browser.get("http://localhost:5000/settings/workflow_step_formats")
    
    # Wait for page to load
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "workflow-steps"))
    )
    
    # 2. Select a workflow step
    step_selector = browser.find_element(By.ID, "workflow-step-selector")
    step_selector.click()
    
    # Wait for dropdown options
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "step-option"))
    )
    
    # Select first step
    browser.find_element(By.CLASS_NAME, "step-option").click()
    
    # 3. Configure formats
    input_format_selector = browser.find_element(By.ID, "input-format-selector")
    input_format_selector.click()
    
    # Wait for format options
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "format-option"))
    )
    
    # Select sample format
    format_options = browser.find_elements(By.CLASS_NAME, "format-option")
    for option in format_options:
        if sample_format_template["name"] in option.text:
            option.click()
            break
    
    # Save configuration
    browser.find_element(By.ID, "save-step-formats").click()
    
    # Wait for success message
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
    )

def test_format_validation_ui(browser, client, sample_format_template):
    """Test format validation UI and feedback"""
    
    # 1. Navigate to format validation page
    browser.get("http://localhost:5000/settings/format_templates")
    
    # Wait for page to load
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "format-templates"))
    )
    
    # 2. Open validation modal
    validate_button = browser.find_element(By.CLASS_NAME, "validate-format")
    validate_button.click()
    
    # Wait for modal
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "validation-modal"))
    )
    
    # 3. Test valid input
    test_input = browser.find_element(By.ID, "test-input")
    test_input.send_keys(json.dumps({
        "title": "Test Title",
        "content": "Test Content"
    }))
    
    # Validate
    browser.find_element(By.ID, "validate-button").click()
    
    # Wait for success message
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "validation-success"))
    )
    
    # 4. Test invalid input
    test_input.clear()
    test_input.send_keys(json.dumps({
        "title": "Test Title"
        # Missing required content field
    }))
    
    # Validate
    browser.find_element(By.ID, "validate-button").click()
    
    # Wait for error message
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "validation-error"))
    )
    
    # Verify error details are shown
    error_details = browser.find_element(By.CLASS_NAME, "error-details")
    assert "required" in error_details.text.lower()
    assert "content" in error_details.text.lower()

def test_format_preview_ui(browser, client, sample_format_template):
    """Test format preview functionality in UI"""
    
    # 1. Navigate to format templates page
    browser.get("http://localhost:5000/settings/format_templates")
    
    # Wait for page to load
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "format-templates"))
    )
    
    # 2. Open preview modal
    preview_button = browser.find_element(By.CLASS_NAME, "preview-format")
    preview_button.click()
    
    # Wait for modal
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "preview-modal"))
    )
    
    # 3. Check format specification display
    format_spec = browser.find_element(By.CLASS_NAME, "format-spec-preview")
    spec_data = json.loads(format_spec.text)
    assert "properties" in spec_data
    assert "title" in spec_data["properties"]
    assert "content" in spec_data["properties"]
    
    # 4. Check example data
    example_data = browser.find_element(By.CLASS_NAME, "example-data")
    example = json.loads(example_data.text)
    assert "title" in example
    assert "content" in example
    
    # 5. Test live preview updates
    editor = browser.find_element(By.ID, "preview-editor")
    editor.clear()
    editor.send_keys(json.dumps({
        "title": "Preview Test",
        "content": "Testing preview functionality"
    }))
    
    # Wait for preview update
    time.sleep(1)  # Allow time for debounced preview update
    
    preview = browser.find_element(By.CLASS_NAME, "preview-output")
    preview_data = json.loads(preview.text)
    assert preview_data["title"] == "Preview Test"
    assert preview_data["content"] == "Testing preview functionality" 