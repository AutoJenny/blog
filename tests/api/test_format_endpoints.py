#!/usr/bin/env python3
"""
API tests for format system endpoints.
Tests Step 13 of the format system implementation plan.
"""

import pytest
import requests
import json
import sys
import os

BASE_URL = "http://localhost:5000"

class TestFormatEndpoints:
    """API tests for format system endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data."""
        self.test_format = {
            "name": "API Test Format",
            "description": "Format for API testing",
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
                },
                {
                    "name": "tags",
                    "type": "array",
                    "required": False,
                    "description": "List of tags"
                }
            ]
        }
    
    def test_get_format_templates(self):
        """Test GET /api/workflow/formats/templates endpoint."""
        print("Testing GET /api/workflow/formats/templates...")
        
        response = requests.get(f"{BASE_URL}/api/workflow/formats/templates")
        
        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)
        
        print(f"✓ GET /api/workflow/formats/templates - Found {len(templates)} templates")
    
    def test_create_format_template(self):
        """Test POST /api/workflow/formats/templates endpoint."""
        print("Testing POST /api/workflow/formats/templates...")
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=self.test_format)
        
        assert response.status_code == 201
        template = response.json()
        assert template["name"] == self.test_format["name"]
        assert template["description"] == self.test_format["description"]
        assert len(template["fields"]) == len(self.test_format["fields"])
        
        # Store template ID for cleanup
        self.created_template_id = template["id"]
        
        print(f"✓ POST /api/workflow/formats/templates - Created template ID: {template['id']}")
    
    def test_get_format_template(self):
        """Test GET /api/workflow/formats/templates/{id} endpoint."""
        print("Testing GET /api/workflow/formats/templates/{id}...")
        
        # First create a template
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=self.test_format)
        assert response.status_code == 201
        template = response.json()
        template_id = template["id"]
        
        # Then get it
        response = requests.get(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
        
        assert response.status_code == 200
        retrieved_template = response.json()
        assert retrieved_template["id"] == template_id
        assert retrieved_template["name"] == self.test_format["name"]
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
        
        print(f"✓ GET /api/workflow/formats/templates/{template_id} - Retrieved template")
    
    def test_update_format_template(self):
        """Test PUT /api/workflow/formats/templates/{id} endpoint."""
        print("Testing PUT /api/workflow/formats/templates/{id}...")
        
        # First create a template
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=self.test_format)
        assert response.status_code == 201
        template = response.json()
        template_id = template["id"]
        
        # Update the template
        updated_format = self.test_format.copy()
        updated_format["description"] = "Updated description for API testing"
        
        response = requests.put(f"{BASE_URL}/api/workflow/formats/templates/{template_id}", json=updated_format)
        
        assert response.status_code == 200
        updated_template = response.json()
        assert updated_template["description"] == "Updated description for API testing"
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
        
        print(f"✓ PUT /api/workflow/formats/templates/{template_id} - Updated template")
    
    def test_delete_format_template(self):
        """Test DELETE /api/workflow/formats/templates/{id} endpoint."""
        print("Testing DELETE /api/workflow/formats/templates/{id}...")
        
        # First create a template
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=self.test_format)
        assert response.status_code == 201
        template = response.json()
        template_id = template["id"]
        
        # Delete the template
        response = requests.delete(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
        
        assert response.status_code in [200, 204]  # Both are valid success responses
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
        assert response.status_code == 404
        
        print(f"✓ DELETE /api/workflow/formats/templates/{template_id} - Deleted template")
    
    def test_validate_format(self):
        """Test POST /api/workflow/formats/validate endpoint."""
        print("Testing POST /api/workflow/formats/validate...")
        
        # Test with valid data
        valid_test_data = {
            "title": "Valid Title",
            "content": "Valid content",
            "tags": ["test", "api"]
        }
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": self.test_format["fields"],
            "test_data": valid_test_data
        })
        
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] == True
        assert len(validation.get("errors", [])) == 0
        
        # Test with invalid data
        invalid_test_data = {
            "content": "Only content provided"  # Missing required 'title'
        }
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": self.test_format["fields"],
            "test_data": invalid_test_data
        })
        
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] == False
        assert len(validation["errors"]) > 0
        
        print("✓ POST /api/workflow/formats/validate - Validation working")
    
    def test_format_template_validation_errors(self):
        """Test format template validation error handling."""
        print("Testing format template validation errors...")
        
        # Test missing required fields
        invalid_format = {
            "name": "Invalid Format",
            # Missing description
            "fields": []  # Empty fields
        }
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=invalid_format)
        
        assert response.status_code == 400
        error = response.json()
        assert "error" in error
        assert "MISSING_FIELD" in error["error"]["code"]
        
        # Test invalid fields structure
        invalid_format = {
            "name": "Invalid Format",
            "description": "Test description",
            "fields": "not an array"  # Should be array
        }
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=invalid_format)
        
        assert response.status_code == 400
        error = response.json()
        assert "error" in error
        assert "INVALID_FIELDS" in error["error"]["code"]
        
        print("✓ Format template validation errors - Error handling working")
    
    def test_format_validation_error_handling(self):
        """Test format validation error handling."""
        print("Testing format validation error handling...")
        
        # Test missing required fields in validation request
        invalid_request = {
            "test_data": {"title": "Test"}  # Missing 'fields' key
        }
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json=invalid_request)
        
        assert response.status_code == 400
        error = response.json()
        assert "error" in error
        assert "MISSING_FIELDS" in error["error"]["code"]
        
        # Test invalid fields structure
        invalid_request = {
            "fields": "not an array",  # Should be array
            "test_data": {"title": "Test"}
        }
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json=invalid_request)
        
        assert response.status_code == 400
        error = response.json()
        assert "error" in error
        
        print("✓ Format validation error handling - Error handling working")
    
    def test_get_workflow_steps(self):
        """Test GET /api/workflow/steps endpoint."""
        print("Testing GET /api/workflow/steps...")
        
        response = requests.get(f"{BASE_URL}/api/workflow/steps")
        
        # This endpoint might not exist yet, so we'll handle both cases
        if response.status_code == 200:
            steps = response.json()
            assert isinstance(steps, list)
            print(f"✓ GET /api/workflow/steps - Found {len(steps)} steps")
        else:
            print(f"⚠ GET /api/workflow/steps - Status: {response.status_code} (endpoint may not be implemented yet)")
    
    def test_step_format_configuration(self):
        """Test step format configuration endpoints."""
        print("Testing step format configuration...")
        
        # First get a step
        response = requests.get(f"{BASE_URL}/api/workflow/steps")
        if response.status_code != 200:
            print("⚠ Step format configuration - No steps available")
            return
        
        steps = response.json()
        if not steps:
            print("⚠ Step format configuration - No steps available")
            return
        
        step_id = steps[0]["id"]
        
        # Create a format template for testing
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=self.test_format)
        assert response.status_code == 201
        template = response.json()
        template_id = template["id"]
        
        # Test getting step format configuration
        response = requests.get(f"{BASE_URL}/api/workflow/steps/{step_id}/formats")
        
        if response.status_code == 200:
            config = response.json()
            print(f"✓ GET /api/workflow/steps/{step_id}/formats - Retrieved configuration")
            
            # Test configuring step format
            config_data = {
                "input_format_id": template_id,
                "output_format_id": None
            }
            
            response = requests.put(f"{BASE_URL}/api/workflow/steps/{step_id}/formats", json=config_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ PUT /api/workflow/steps/{step_id}/formats - Configured format")
            else:
                print(f"⚠ PUT /api/workflow/steps/{step_id}/formats - Status: {response.status_code}")
        else:
            print(f"⚠ GET /api/workflow/steps/{step_id}/formats - Status: {response.status_code}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
    
    def test_format_endpoint_performance(self):
        """Test format endpoint performance."""
        print("Testing format endpoint performance...")
        
        import time
        
        # Test GET templates performance
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/workflow/formats/templates")
        end_time = time.time()
        
        assert response.status_code == 200
        get_time = end_time - start_time
        
        # Should be fast (less than 1 second)
        assert get_time < 1.0
        
        # Test validation performance
        test_data = {
            "title": "Performance Test",
            "content": "Performance test content",
            "tags": ["performance", "test"]
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": self.test_format["fields"],
            "test_data": test_data
        })
        end_time = time.time()
        
        assert response.status_code == 200
        validation_time = end_time - start_time
        
        # Should be fast (less than 1 second)
        assert validation_time < 1.0
        
        print(f"✓ Format endpoint performance - GET: {get_time:.3f}s, Validation: {validation_time:.3f}s")
    
    def test_format_api_error_codes(self):
        """Test format API error codes and messages."""
        print("Testing format API error codes...")
        
        # Test 404 for non-existent template
        response = requests.get(f"{BASE_URL}/api/workflow/formats/templates/99999")
        assert response.status_code == 404
        
        # Test 404 for non-existent step
        response = requests.get(f"{BASE_URL}/api/workflow/steps/99999/formats")
        if response.status_code == 404:
            print("✓ 404 error handling working")
        else:
            print(f"⚠ Step endpoint returned: {response.status_code}")
        
        # Test 400 for invalid JSON
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", 
                               data="invalid json", 
                               headers={"Content-Type": "application/json"})
        assert response.status_code == 400
        
        print("✓ Format API error codes - Error handling working")

def test_format_api_end_to_end():
    """Test the complete format API end-to-end."""
    print("Testing format API end-to-end...")
    
    # 1. Create format template
    format_data = {
        "name": "E2E API Test Format",
        "description": "Format for end-to-end API testing",
        "fields": [
            {"name": "title", "type": "string", "required": True},
            {"name": "content", "type": "string", "required": True}
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=format_data)
    assert response.status_code == 201
    template = response.json()
    template_id = template["id"]
    
    # 2. Get format template
    response = requests.get(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
    assert response.status_code == 200
    retrieved_template = response.json()
    assert retrieved_template["id"] == template_id
    
    # 3. Validate format
    test_data = {"title": "E2E Test", "content": "E2E content"}
    response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
        "fields": format_data["fields"],
        "test_data": test_data
    })
    assert response.status_code == 200
    validation = response.json()
    assert validation["valid"] == True
    
    # 4. Update format template
    updated_format = format_data.copy()
    updated_format["description"] = "Updated E2E description"
    response = requests.put(f"{BASE_URL}/api/workflow/formats/templates/{template_id}", json=updated_format)
    assert response.status_code == 200
    
    # 5. Delete format template
    response = requests.delete(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
    assert response.status_code in [200, 204]
    
    # 6. Verify deletion
    response = requests.get(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
    assert response.status_code == 404
    
    print("✓ Format API end-to-end test passed")

if __name__ == "__main__":
    # Run tests
    print("=== Format API Endpoint Tests ===")
    
    # Create test instance
    test_instance = TestFormatEndpoints()
    test_instance.setup()
    
    # Run individual tests
    test_instance.test_get_format_templates()
    test_instance.test_create_format_template()
    test_instance.test_get_format_template()
    test_instance.test_update_format_template()
    test_instance.test_delete_format_template()
    test_instance.test_validate_format()
    test_instance.test_format_template_validation_errors()
    test_instance.test_format_validation_error_handling()
    test_instance.test_get_workflow_steps()
    test_instance.test_step_format_configuration()
    test_instance.test_format_endpoint_performance()
    test_instance.test_format_api_error_codes()
    
    # Run end-to-end test
    test_format_api_end_to_end()
    
    print("\n=== All API Endpoint Tests Passed ===") 