import pytest
from flask import Flask
from app import create_app
from app.db import get_db_conn
import json

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_workflow_step():
    """Create a sample workflow step for testing"""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO workflow_step_entity (name, description)
                VALUES ('test_step', 'Test Step')
                RETURNING id
            """)
            step_id = cur.fetchone()[0]
            conn.commit()
            return step_id

def test_complete_format_workflow(client, sample_workflow_step):
    """Test complete format system workflow from creation to use in workflow"""
    
    # 1. Create input format template
    input_format = {
        "name": "Article Input Format",
        "format_type": "input",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "themes": {"type": "array", "items": {"type": "string"}},
                "facts": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "themes", "facts"]
        })
    }
    response = client.post("/api/formats/templates", json=input_format)
    assert response.status_code == 201
    input_format_data = response.get_json()
    
    # 2. Create output format template
    output_format = {
        "name": "Article Structure Format",
        "format_type": "output",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "theme": {"type": "string"},
                            "facts": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["title", "theme", "facts"]
                    }
                }
            },
            "required": ["sections"]
        })
    }
    response = client.post("/api/formats/templates", json=output_format)
    assert response.status_code == 201
    output_format_data = response.get_json()
    
    # 3. Configure workflow step with formats
    response = client.put(f"/api/workflow/steps/{sample_workflow_step}/formats", json={
        "input_format_id": input_format_data["id"],
        "output_format_id": output_format_data["id"]
    })
    assert response.status_code == 200
    step_format_config = response.get_json()
    assert step_format_config["input_format_id"] == input_format_data["id"]
    assert step_format_config["output_format_id"] == output_format_data["id"]
    
    # 4. Test input validation
    valid_input = {
        "title": "Scottish Traditions",
        "themes": ["history", "culture"],
        "facts": [
            "The kilt has been worn since the 16th century",
            "Highland games originated from military exercises"
        ]
    }
    response = client.post("/api/formats/validate", json={
        "format_spec": input_format["format_spec"],
        "test_data": valid_input
    })
    assert response.status_code == 200
    validation_result = response.get_json()
    assert validation_result["valid"] is True
    
    # 5. Test output validation
    valid_output = {
        "sections": [
            {
                "title": "History of the Kilt",
                "theme": "history",
                "facts": ["The kilt has been worn since the 16th century"]
            },
            {
                "title": "Highland Games",
                "theme": "culture",
                "facts": ["Highland games originated from military exercises"]
            }
        ]
    }
    response = client.post("/api/formats/validate", json={
        "format_spec": output_format["format_spec"],
        "test_data": valid_output
    })
    assert response.status_code == 200
    validation_result = response.get_json()
    assert validation_result["valid"] is True
    
    # 6. Test invalid input handling
    invalid_input = {
        "title": "Scottish Traditions",
        # Missing required fields
    }
    response = client.post("/api/formats/validate", json={
        "format_spec": input_format["format_spec"],
        "test_data": invalid_input
    })
    assert response.status_code == 200
    validation_result = response.get_json()
    assert validation_result["valid"] is False
    assert len(validation_result["errors"]) > 0

def test_format_template_versioning(client):
    """Test format template versioning and compatibility"""
    
    # 1. Create initial format template
    initial_format = {
        "name": "Article Format v1",
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
    response = client.post("/api/formats/templates", json=initial_format)
    assert response.status_code == 201
    initial_data = response.get_json()
    
    # 2. Create updated version with backward compatibility
    updated_format = {
        "name": "Article Format v2",
        "format_type": "input",
        "format_spec": json.dumps({
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "content"]  # tags optional for backward compatibility
        })
    }
    response = client.post("/api/formats/templates", json=updated_format)
    assert response.status_code == 201
    updated_data = response.get_json()
    
    # 3. Test data valid for both versions
    test_data = {
        "title": "Test Article",
        "content": "Test content"
    }
    
    # Should be valid for v1
    response = client.post("/api/formats/validate", json={
        "format_spec": initial_format["format_spec"],
        "test_data": test_data
    })
    assert response.status_code == 200
    assert response.get_json()["valid"] is True
    
    # Should also be valid for v2
    response = client.post("/api/formats/validate", json={
        "format_spec": updated_format["format_spec"],
        "test_data": test_data
    })
    assert response.status_code == 200
    assert response.get_json()["valid"] is True
    
    # 4. Test data with new field
    test_data_v2 = {
        "title": "Test Article",
        "content": "Test content",
        "tags": ["test", "article"]
    }
    
    # Should be valid for v2
    response = client.post("/api/formats/validate", json={
        "format_spec": updated_format["format_spec"],
        "test_data": test_data_v2
    })
    assert response.status_code == 200
    assert response.get_json()["valid"] is True

def test_workflow_format_chain(client, sample_workflow_step):
    """Test format chaining in workflow context"""
    
    # 1. Create format templates for a chain of workflow steps
    formats = []
    for i, format_data in enumerate([
        {
            "name": "Facts Collection Format",
            "format_type": "input",
            "format_spec": json.dumps({
                "type": "object",
                "properties": {
                    "facts": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["facts"]
            })
        },
        {
            "name": "Theme Extraction Format",
            "format_type": "output",
            "format_spec": json.dumps({
                "type": "object",
                "properties": {
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "facts": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["themes", "facts"]
            })
        },
        {
            "name": "Section Planning Format",
            "format_type": "output",
            "format_spec": json.dumps({
                "type": "object",
                "properties": {
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "theme": {"type": "string"},
                                "facts": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["title", "theme", "facts"]
                        }
                    }
                },
                "required": ["sections"]
            })
        }
    ]):
        response = client.post("/api/formats/templates", json=format_data)
        assert response.status_code == 201
        formats.append(response.get_json())
    
    # 2. Test format chain compatibility
    # Facts -> Themes -> Sections
    test_data = {
        "facts": [
            "The kilt has been worn since the 16th century",
            "Highland games originated from military exercises",
            "The sporran was used to carry personal items"
        ]
    }
    
    # Validate against first format
    response = client.post("/api/formats/validate", json={
        "format_spec": formats[0]["format_spec"],
        "test_data": test_data
    })
    assert response.status_code == 200
    assert response.get_json()["valid"] is True
    
    # Transform and validate against second format
    themes_data = {
        "themes": ["history", "culture", "tradition"],
        "facts": test_data["facts"]
    }
    response = client.post("/api/formats/validate", json={
        "format_spec": formats[1]["format_spec"],
        "test_data": themes_data
    })
    assert response.status_code == 200
    assert response.get_json()["valid"] is True
    
    # Transform and validate against final format
    sections_data = {
        "sections": [
            {
                "title": "History of the Kilt",
                "theme": "history",
                "facts": [test_data["facts"][0]]
            },
            {
                "title": "Highland Games Tradition",
                "theme": "culture",
                "facts": [test_data["facts"][1]]
            },
            {
                "title": "Traditional Accessories",
                "theme": "tradition",
                "facts": [test_data["facts"][2]]
            }
        ]
    }
    response = client.post("/api/formats/validate", json={
        "format_spec": formats[2]["format_spec"],
        "test_data": sections_data
    })
    assert response.status_code == 200
    assert response.get_json()["valid"] is True 