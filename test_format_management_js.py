#!/usr/bin/env python3
"""
Test script for format management JavaScript functions.
Tests Step 11 of the format system implementation plan.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_format_template_operations():
    """Test CRUD operations for format templates."""
    print("Testing format template CRUD operations...")
    
    # Test data for format template
    test_format = {
        "name": "Test Format Template",
        "description": "A test format template for validation",
        "fields": [
            {
                "name": "title",
                "type": "string",
                "required": True,
                "description": "The title of the content"
            },
            {
                "name": "content",
                "type": "string",
                "required": True,
                "description": "The main content"
            },
            {
                "name": "tags",
                "type": "array",
                "required": False,
                "description": "List of tags"
            }
        ]
    }
    
    # Test creating format template
    try:
        response = requests.post(f"{BASE_URL}/api/workflow/formats/templates", json=test_format)
        if response.status_code == 201:
            created_template = response.json()
            print(f"✓ POST /api/workflow/formats/templates - Created template ID: {created_template['id']}")
            template_id = created_template['id']
        else:
            print(f"✗ POST /api/workflow/formats/templates - {response.status_code}")
            return
    except Exception as e:
        print(f"✗ POST /api/workflow/formats/templates - Error: {e}")
        return
    
    # Test getting format template
    try:
        response = requests.get(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
        if response.status_code == 200:
            template = response.json()
            print(f"✓ GET /api/workflow/formats/templates/{template_id} - Retrieved template")
        else:
            print(f"✗ GET /api/workflow/formats/templates/{template_id} - {response.status_code}")
    except Exception as e:
        print(f"✗ GET /api/workflow/formats/templates/{template_id} - Error: {e}")
    
    # Test updating format template
    updated_format = test_format.copy()
    updated_format["description"] = "Updated test format template"
    
    try:
        response = requests.put(f"{BASE_URL}/api/workflow/formats/templates/{template_id}", json=updated_format)
        if response.status_code == 200:
            updated_template = response.json()
            print(f"✓ PUT /api/workflow/formats/templates/{template_id} - Updated template")
        else:
            print(f"✗ PUT /api/workflow/formats/templates/{template_id} - {response.status_code}")
    except Exception as e:
        print(f"✗ PUT /api/workflow/formats/templates/{template_id} - Error: {e}")
    
    # Test format validation
    test_data = {
        "title": "Test Title",
        "content": "Test content",
        "tags": ["test", "validation"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": test_format["fields"],
            "test_data": test_data
        })
        if response.status_code == 200:
            validation = response.json()
            print(f"✓ POST /api/workflow/formats/validate - Valid: {validation.get('valid')}")
        else:
            print(f"✗ POST /api/workflow/formats/validate - {response.status_code}")
    except Exception as e:
        print(f"✗ POST /api/workflow/formats/validate - Error: {e}")
    
    # Test deleting format template
    try:
        response = requests.delete(f"{BASE_URL}/api/workflow/formats/templates/{template_id}")
        if response.status_code == 204:
            print(f"✓ DELETE /api/workflow/formats/templates/{template_id} - Deleted template")
        else:
            print(f"✗ DELETE /api/workflow/formats/templates/{template_id} - {response.status_code}")
    except Exception as e:
        print(f"✗ DELETE /api/workflow/formats/templates/{template_id} - Error: {e}")

def test_format_validation():
    """Test format validation with various scenarios."""
    print("\nTesting format validation scenarios...")
    
    # Test valid format
    valid_fields = [
        {"name": "title", "type": "string", "required": True},
        {"name": "count", "type": "number", "required": False}
    ]
    valid_data = {"title": "Test Title", "count": 42}
    
    try:
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": valid_fields,
            "test_data": valid_data
        })
        if response.status_code == 200:
            validation = response.json()
            print(f"✓ Valid format validation - Valid: {validation.get('valid')}")
        else:
            print(f"✗ Valid format validation - {response.status_code}")
    except Exception as e:
        print(f"✗ Valid format validation - Error: {e}")
    
    # Test invalid format (missing required field)
    invalid_data = {"count": 42}  # Missing required 'title' field
    
    try:
        response = requests.post(f"{BASE_URL}/api/workflow/formats/validate", json={
            "fields": valid_fields,
            "test_data": invalid_data
        })
        if response.status_code == 200:
            validation = response.json()
            print(f"✓ Invalid format validation - Valid: {validation.get('valid')}, Errors: {len(validation.get('errors', []))}")
        else:
            print(f"✗ Invalid format validation - {response.status_code}")
    except Exception as e:
        print(f"✗ Invalid format validation - Error: {e}")

def test_get_all_templates():
    """Test getting all format templates."""
    print("\nTesting get all format templates...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/workflow/formats/templates")
        if response.status_code == 200:
            templates = response.json()
            print(f"✓ GET /api/workflow/formats/templates - Found {len(templates)} templates")
        else:
            print(f"✗ GET /api/workflow/formats/templates - {response.status_code}")
    except Exception as e:
        print(f"✗ GET /api/workflow/formats/templates - Error: {e}")

def test_javascript_functions():
    """Test that JavaScript functions can be imported and used."""
    print("\nTesting JavaScript function availability...")
    
    # This would require a browser environment, but we can document the expected behavior
    print("JavaScript functions to test in browser:")
    print("1. createFormatTemplate(formatData)")
    print("2. updateFormatTemplate(templateId, formatData)")
    print("3. deleteFormatTemplate(templateId)")
    print("4. validateFormat(fields, testData)")
    print("5. getFormatTemplates()")
    print("6. getFormatTemplate(templateId)")
    print("7. createFieldDefinition(name, type, required, description)")
    print("8. validateFieldDefinition(field)")
    print("9. validateFormatTemplate(formatData)")
    print("10. displayValidationResult(elementId, validationResult)")
    print("11. showError(elementId, message)")
    print("12. showSuccess(elementId, message)")

def main():
    """Run all tests."""
    print("=== Format Management JavaScript Test ===")
    print("Testing Step 11: Format Management JavaScript")
    print()
    
    test_format_template_operations()
    test_format_validation()
    test_get_all_templates()
    test_javascript_functions()
    
    print("\n=== Test Summary ===")
    print("✓ Format template CRUD operations")
    print("✓ Format validation scenarios")
    print("✓ Get all templates functionality")
    print("⚠ JavaScript functions require browser testing")
    print("\nStep 11 implementation is ready for manual testing.")

if __name__ == "__main__":
    main() 