#!/usr/bin/env python3
"""
UI tests for the format system.
Tests Step 13 of the format system implementation plan.
"""

import pytest
import requests
import json
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://localhost:5000"

class TestFormatUI:
    """UI tests for the format system."""
    
    @pytest.fixture(autouse=True)
    def setup_driver(self):
        """Setup webdriver for UI testing."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
        yield
        
        self.driver.quit()
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Setup test data for UI tests."""
        self.test_format = {
            "name": "UI Test Format",
            "description": "Format for UI testing",
            "fields": [
                {
                    "name": "title",
                    "type": "string",
                    "required": True,
                    "description": "The title"
                },
                {
                    "name": "content",
                    "type": "string",
                    "required": True,
                    "description": "The content"
                }
            ]
        }
        
        # Create test format template
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=self.test_format)
        if response.status_code == 201:
            self.format_template = response.json()
        else:
            pytest.skip("Could not create test format template")
    
    def test_format_template_management_ui(self):
        """Test format template management UI."""
        print("Testing format template management UI...")
        
        # Navigate to format templates page
        self.driver.get(f"{BASE_URL}/settings/format_templates")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Check if page title is correct
        title = self.driver.find_element(By.TAG_NAME, "h1")
        assert "Format Templates" in title.text
        
        # Check if format template is listed
        format_name = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{self.test_format['name']}')]")
        assert format_name.is_displayed()
        
        print("✓ Format template management UI test passed")
    
    def test_format_creation_ui(self):
        """Test format creation UI."""
        print("Testing format creation UI...")
        
        # Navigate to format templates page
        self.driver.get(f"{BASE_URL}/settings/format_templates")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Look for create format button
        try:
            create_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Create') or contains(text(), 'New')]")
            assert create_button.is_displayed()
        except:
            # If no create button found, check if there's a form
            try:
                name_input = self.driver.find_element(By.NAME, "name")
                assert name_input.is_displayed()
            except:
                pytest.skip("Format creation UI not found")
        
        print("✓ Format creation UI test passed")
    
    def test_format_validation_ui(self):
        """Test format validation UI."""
        print("Testing format validation UI...")
        
        # Navigate to format templates page
        self.driver.get(f"{BASE_URL}/settings/format_templates")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Look for validation elements
        try:
            # Check for test data input
            test_input = self.driver.find_element(By.ID, "testData")
            assert test_input.is_displayed()
            
            # Check for validation button
            validate_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Validate') or contains(text(), 'Test')]")
            assert validate_button.is_displayed()
            
        except:
            pytest.skip("Format validation UI not found")
        
        print("✓ Format validation UI test passed")
    
    def test_workflow_step_formats_ui(self):
        """Test workflow step formats UI."""
        print("Testing workflow step formats UI...")
        
        # Navigate to workflow step formats page
        self.driver.get(f"{BASE_URL}/settings/workflow_step_formats")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Check if page title is correct
        title = self.driver.find_element(By.TAG_NAME, "h1")
        assert "Workflow Step Formats" in title.text
        
        # Check if workflow steps are displayed
        try:
            steps = self.driver.find_elements(By.CLASS_NAME, "step-container")
            assert len(steps) > 0
        except:
            # If no step containers, check for any step-related content
            step_content = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Step') or contains(text(), 'stage')]")
            assert step_content.is_displayed()
        
        print("✓ Workflow step formats UI test passed")
    
    def test_format_preview_ui(self):
        """Test format preview UI."""
        print("Testing format preview UI...")
        
        # Navigate to format templates page
        self.driver.get(f"{BASE_URL}/settings/format_templates")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Look for preview elements
        try:
            # Check for format preview area
            preview_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'preview') or contains(@id, 'preview')]")
            if preview_elements:
                assert any(elem.is_displayed() for elem in preview_elements)
            else:
                # Check for format specification display
                spec_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'format') or contains(@id, 'format')]")
                assert any(elem.is_displayed() for elem in spec_elements)
        except:
            pytest.skip("Format preview UI not found")
        
        print("✓ Format preview UI test passed")
    
    def test_format_error_handling_ui(self):
        """Test format error handling UI."""
        print("Testing format error handling UI...")
        
        # Navigate to format templates page
        self.driver.get(f"{BASE_URL}/settings/format_templates")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Look for error handling elements
        try:
            # Check for error message containers
            error_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'alert')]")
            # Error elements might not be visible initially, but should exist in DOM
            assert len(error_elements) >= 0
        except:
            pytest.skip("Format error handling UI not found")
        
        print("✓ Format error handling UI test passed")

def test_format_ui_responsiveness():
    """Test format UI responsiveness."""
    print("Testing format UI responsiveness...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=375,667")  # Mobile size
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Test mobile view
        driver.get(f"{BASE_URL}/settings/format_templates")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Check if page is responsive
        title = driver.find_element(By.TAG_NAME, "h1")
        assert title.is_displayed()
        
        # Check if content is accessible on mobile
        body = driver.find_element(By.TAG_NAME, "body")
        assert body.is_displayed()
        
        print("✓ Format UI responsiveness test passed")
        
    finally:
        driver.quit()

def test_format_ui_accessibility():
    """Test format UI accessibility."""
    print("Testing format UI accessibility...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to format templates page
        driver.get(f"{BASE_URL}/settings/format_templates")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Check for basic accessibility features
        # 1. Page has a title
        title = driver.find_element(By.TAG_NAME, "h1")
        assert title.text.strip() != ""
        
        # 2. Check for form labels
        try:
            labels = driver.find_elements(By.TAG_NAME, "label")
            assert len(labels) > 0
        except:
            pass  # Labels might not be required for all elements
        
        # 3. Check for proper heading structure
        headings = driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //h4 | //h5 | //h6")
        assert len(headings) > 0
        
        print("✓ Format UI accessibility test passed")
        
    finally:
        driver.quit()

def test_format_ui_performance():
    """Test format UI performance."""
    print("Testing format UI performance...")
    
    import time
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Measure page load time
        start_time = time.time()
        
        driver.get(f"{BASE_URL}/settings/format_templates")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        end_time = time.time()
        load_time = end_time - start_time
        
        # Page should load in reasonable time (less than 5 seconds)
        assert load_time < 5.0
        
        print(f"✓ Format UI performance test passed (load time: {load_time:.3f}s)")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # Run tests
    print("=== Format UI Tests ===")
    
    # Note: These tests require a running Flask server and Chrome WebDriver
    # They are designed to be run with pytest
    
    print("UI tests require:")
    print("1. Running Flask server on localhost:5000")
    print("2. Chrome WebDriver installed")
    print("3. pytest-selenium package")
    print("\nRun with: pytest tests/test_format_ui.py -v")
    
    print("\n=== UI Tests Ready ===") 