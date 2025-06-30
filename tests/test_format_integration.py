#!/usr/bin/env python3
"""
Integration tests for the format system.
Tests Step 13 of the format system implementation plan.
"""

import pytest
import requests
import json
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import get_db_conn
from app.api.workflow.format_validator import FormatValidator

BASE_URL = "http://localhost:5000"

class TestFormatIntegration:
    """Integration tests for the format system."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up test data for all tests."""
        self.test_format = {
            "fields": [
                {"name": "title", "type": "string", "required": True, "description": "The title"},
                {"name": "content", "type": "string", "required": True, "description": "The content"},
                {"name": "tags", "type": "array", "required": False, "description": "Tags"},
                {"name": "metadata", "type": "object", "required": False, "description": "Metadata"}
            ]
        }
        
        # Get a format template for testing
        try:
            response = requests.get(f"{BASE_URL}/api/workflow/formats/templates")
            if response.status_code == 200:
                templates = response.json()
                if templates:
                    self.format_template = templates[0]
                else:
                    self.format_template = None
            else:
                self.format_template = None
        except:
            self.format_template = None
    
    def test_format_workflow_integration(self):
        """Test format integration with workflow processing."""
        print("Testing format workflow integration...")
        
        # Test that format validation works in workflow context
        test_data = {
            "title": "Test Title",
            "content": "Test content for workflow integration",
            "tags": ["test", "integration"],
            "metadata": {"author": "test", "version": 1}
        }
        
        # Validate against format
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": self.test_format["fields"],
            "test_data": test_data
        })
        
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] == True
        assert len(validation.get("errors", [])) == 0
        
        print("✓ Format workflow integration test passed")
    
    def test_format_reference_resolution(self):
        """Test format reference resolution in prompts."""
        print("Testing format reference resolution...")
        
        # Test data with references
        available_data = {
            "previous_step_output": "Previous step result",
            "user_input": "User provided input",
            "system_config": {"setting": "value"}
        }
        
        # Test prompt with references
        test_prompt = "Process the following: [data:previous_step_output] with input: [data:user_input]"
        
        # Test reference validation
        validator = FormatValidator()
        is_valid, errors = validator.validate_references(test_prompt, available_data)
        
        assert is_valid == True
        assert len(errors) == 0
        
        # Test prompt with missing references
        invalid_prompt = "Process: [data:missing_field] and [data:another_missing]"
        is_valid, errors = validator.validate_references(invalid_prompt, available_data)
        
        assert is_valid == False
        assert len(errors) > 0
        assert any("missing_field" in error for error in errors)
        assert any("another_missing" in error for error in errors)
        
        print("✓ Format reference resolution test passed")
    
    def test_format_validation_errors(self):
        """Test format validation error handling."""
        print("Testing format validation errors...")
        
        # Test missing required fields
        invalid_data = {
            "content": "Only content provided",  # Missing required 'title'
            "tags": ["test"]
        }
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": self.test_format["fields"],
            "test_data": invalid_data
        })
        
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] == False
        assert len(validation["errors"]) > 0
        assert any("title" in error.lower() for error in validation["errors"])
        
        # Test wrong data types
        invalid_types = {
            "title": 123,  # Should be string
            "content": "Valid content",
            "tags": "not an array",  # Should be array
            "metadata": "not an object"  # Should be object
        }
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": self.test_format["fields"],
            "test_data": invalid_types
        })
        
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] == False
        assert len(validation["errors"]) > 0
        
        print("✓ Format validation errors test passed")
    
    def test_format_template_crud_integration(self):
        """Test format template CRUD operations integration."""
        print("Testing format template CRUD integration...")
        
        # Test create
        new_format = {
            "name": "CRUD Test Format",
            "description": "Format for CRUD testing",
            "fields": [
                {"name": "test_field", "type": "string", "required": True}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=new_format)
        assert response.status_code == 201
        created_format = response.json()
        assert created_format["name"] == new_format["name"]
        
        format_id = created_format["id"]
        
        # Test read
        response = requests.get(f"{BASE_URL}/api/workflow/formats/templates/{format_id}")
        assert response.status_code == 200
        retrieved_format = response.json()
        assert retrieved_format["id"] == format_id
        
        # Test update
        updated_format = new_format.copy()
        updated_format["description"] = "Updated description"
        
        response = requests.put(f"{BASE_URL}/api/workflow/formats/templates/{format_id}", json=updated_format)
        assert response.status_code == 200
        updated_result = response.json()
        assert updated_result["description"] == "Updated description"
        
        # Test delete
        response = requests.delete(f"{BASE_URL}/api/workflow/formats/templates/{format_id}")
        assert response.status_code in [200, 204]  # Both are valid success responses
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/api/workflow/formats/templates/{format_id}")
        assert response.status_code == 404
        
        print("✓ Format template CRUD integration test passed")
    
    def test_format_step_configuration_integration(self):
        """Test format step configuration integration."""
        print("Testing format step configuration integration...")
        
        # Get a step to work with
        response = requests.get(f"{BASE_URL}/api/workflow/steps")
        if response.status_code != 200:
            pytest.skip("Could not get workflow steps")
        
        steps = response.json()
        if not steps:
            pytest.skip("No workflow steps available")
        
        step_id = steps[0]["id"]
        
        # Configure step format
        config_data = {
            "input_format_id": self.format_template["id"],
            "output_format_id": None
        }
        
        response = requests.put(f"{BASE_URL}/api/workflow/steps/{step_id}/formats", json=config_data)
        assert response.status_code == 200
        
        # Verify configuration
        response = requests.get(f"{BASE_URL}/api/workflow/steps/{step_id}/formats")
        assert response.status_code == 200
        config = response.json()
        assert config.get("input_format_id") == self.format_template["id"]
        
        print("✓ Format step configuration integration test passed")
    
    def test_format_validation_performance(self):
        """Test format validation performance with large datasets."""
        print("Testing format validation performance...")
        
        # Create a large format template
        large_format = {
            "name": "Large Test Format",
            "description": "Format with many fields for performance testing",
            "fields": []
        }
        
        # Add 50 fields
        for i in range(50):
            field_type = ["string", "number", "boolean", "array", "object"][i % 5]
            large_format["fields"].append({
                "name": f"field_{i}",
                "type": field_type,
                "required": i % 3 == 0,  # Every 3rd field is required
                "description": f"Field {i} for performance testing"
            })
        
        # Create the format template
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=large_format)
        assert response.status_code == 201
        large_format_template = response.json()
        
        # Generate test data
        test_data = {}
        for i in range(50):
            field_type = large_format["fields"][i]["type"]
            if field_type == "string":
                test_data[f"field_{i}"] = f"value_{i}"
            elif field_type == "number":
                test_data[f"field_{i}"] = i
            elif field_type == "boolean":
                test_data[f"field_{i}"] = i % 2 == 0
            elif field_type == "array":
                test_data[f"field_{i}"] = [f"item_{i}_1", f"item_{i}_2"]
            elif field_type == "object":
                test_data[f"field_{i}"] = {"key": f"value_{i}"}
        
        # Test validation performance
        import time
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": large_format["fields"],
            "test_data": test_data
        })
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        assert response.status_code == 200
        validation = response.json()
        assert validation["valid"] == True
        
        # Performance should be reasonable (less than 1 second)
        assert validation_time < 1.0
        
        print(f"✓ Format validation performance test passed (time: {validation_time:.3f}s)")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/workflow/formats/templates/{large_format_template['id']}")

def test_format_system_end_to_end():
    """Test the complete format system end-to-end."""
    print("Testing format system end-to-end...")
    
    # 1. Create format template
    format_data = {
        "name": "E2E Test Format",
        "description": "Format for end-to-end testing",
        "fields": [
            {"name": "title", "type": "string", "required": True},
            {"name": "content", "type": "string", "required": True},
            {"name": "tags", "type": "array", "required": False}
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=format_data)
    assert response.status_code == 201
    format_template = response.json()
    
    # 2. Validate format
    test_data = {
        "title": "E2E Test Title",
        "content": "E2E test content",
        "tags": ["e2e", "test"]
    }
    
    response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
        "fields": format_data["fields"],
        "test_data": test_data
    })
    assert response.status_code == 200
    validation = response.json()
    assert validation["valid"] == True
    
    # 3. Test reference resolution
    validator = FormatValidator()
    prompt = "Generate content with title: [data:title] and tags: [data:tags]"
    available_data = {"title": "Test Title", "tags": ["test"]}
    
    is_valid, errors = validator.validate_references(prompt, available_data)
    assert is_valid == True
    
    # 4. Clean up
    response = requests.delete(f"{BASE_URL}/api/workflow/formats/templates/{format_template['id']}")
    assert response.status_code in [200, 204]
    
    print("✓ Format system end-to-end test passed")

if __name__ == "__main__":
    # Run tests
    print("=== Format Integration Tests ===")
    
    # Create test instance and setup
    test_instance = TestFormatIntegration()
    
    # Run individual tests
    test_instance.test_format_workflow_integration()
    test_instance.test_format_reference_resolution()
    test_instance.test_format_validation_errors()
    test_instance.test_format_template_crud_integration()
    test_instance.test_format_step_configuration_integration()
    test_instance.test_format_validation_performance()
    
    # Run end-to-end test
    test_format_system_end_to_end()
    
    print("\n=== All Integration Tests Passed ===") 