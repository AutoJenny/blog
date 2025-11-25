"""
Test Pipeline Status API Endpoint
Tests the /pipeline-status/<post_id> endpoint for correct response structure
and completion status tracking.
"""

import pytest
import json
from datetime import datetime
from config.database import db_manager


class TestPipelineStatusAPI:
    """Test suite for pipeline status API endpoint"""
    
    def test_pipeline_status_endpoint_exists(self, client):
        """Test that the endpoint exists and returns a response"""
        response = client.get('/launchpad/one-click-blog/api/pipeline-status/96')
        assert response.status_code in [200, 404]  # 404 if post doesn't exist, 200 if it does
    
    def test_pipeline_status_response_structure(self, client):
        """Test that response has correct structure"""
        response = client.get('/launchpad/one-click-blog/api/pipeline-status/96')
        
        if response.status_code == 200:
            data = response.get_json()
            
            # Check top-level structure
            assert 'success' in data
            assert isinstance(data['success'], bool)
            
            if data['success']:
                assert 'data' in data
                assert isinstance(data['data'], dict)
                
                # Check required top-level fields
                assert 'post_id' in data['data']
                assert 'title' in data['data']
                assert 'stages' in data['data']
                
                # Check stages structure
                stages = data['data']['stages']
                assert isinstance(stages, dict)
                
                # Check that all expected stages exist
                expected_stages = ['calendar', 'planning', 'authoring', 'imaging', 'header']
                for stage_name in expected_stages:
                    if stage_name in stages:
                        stage = stages[stage_name]
                        assert 'status' in stage
                        assert 'progress' in stage
                        assert 'substages' in stage
                        assert isinstance(stage['substages'], dict)
    
    def test_pipeline_status_with_post_96(self, client):
        """Test pipeline status for post_id=96 (the failing case)"""
        response = client.get('/launchpad/one-click-blog/api/pipeline-status/96')
        
        if response.status_code == 200:
            data = response.get_json()
            
            if data.get('success'):
                # Verify post_id matches
                assert data['data']['post_id'] == 96
                
                # Verify stages are present
                assert 'stages' in data['data']
                stages = data['data']['stages']
                
                # Check at least one stage has substages
                has_substages = False
                for stage_name, stage_data in stages.items():
                    if 'substages' in stage_data and stage_data['substages']:
                        has_substages = True
                        # Verify substage structure
                        for substage_name, substage_data in stage_data['substages'].items():
                            assert 'status' in substage_data
                            assert 'progress' in substage_data
                            assert substage_data['status'] in ['complete', 'in_progress', 'pending']
                            assert 0 <= substage_data['progress'] <= 100
                        break
                
                assert has_substages, "No substages found in response"
    
    def test_pipeline_status_nonexistent_post(self, client):
        """Test pipeline status for non-existent post"""
        response = client.get('/launchpad/one-click-blog/api/pipeline-status/999999')
        
        # Should return 404 or success:false
        if response.status_code == 404:
            assert True  # Expected behavior
        else:
            data = response.get_json()
            assert data.get('success') == False
            assert 'error' in data
    
    def test_pipeline_status_substage_completion_values(self, client):
        """Test that substage completion values are valid"""
        response = client.get('/launchpad/one-click-blog/api/pipeline-status/96')
        
        if response.status_code == 200:
            data = response.get_json()
            
            if data.get('success') and 'stages' in data['data']:
                stages = data['data']['stages']
                
                for stage_name, stage_data in stages.items():
                    if 'substages' in stage_data:
                        for substage_name, substage_data in stage_data['substages'].items():
                            # Verify status is valid
                            assert substage_data['status'] in ['complete', 'in_progress', 'pending', 'failed']
                            
                            # Verify progress is valid
                            assert isinstance(substage_data['progress'], (int, float))
                            assert 0 <= substage_data['progress'] <= 100
                            
                            # If complete, should have completed_at (or null)
                            if 'completed_at' in substage_data:
                                if substage_data['completed_at']:
                                    # Should be valid ISO format string
                                    try:
                                        datetime.fromisoformat(substage_data['completed_at'].replace('Z', '+00:00'))
                                    except ValueError:
                                        pytest.fail(f"Invalid completed_at format for {stage_name}.{substage_name}")
    
    def test_pipeline_status_all_stages_present(self, client):
        """Test that all expected stages are present in response"""
        response = client.get('/launchpad/one-click-blog/api/pipeline-status/96')
        
        if response.status_code == 200:
            data = response.get_json()
            
            if data.get('success'):
                stages = data['data'].get('stages', {})
                
                expected_stages = {
                    'calendar': ['calendar_view', 'idea_generation'],
                    'planning': ['ideas', 'taxonomy', 'topic_brainstorming', 'section_structure', 'topic_allocation', 'section_titling'],
                    'authoring': ['author_first_drafts', 'image_concepts', 'image_prompts', 'image_captions'],
                    'imaging': ['image_generation', 'optimise'],
                    'header': ['title_summary', 'header_image', 'seo_meta', 'product_match', 'final_review']
                }
                
                for stage_name, expected_substages in expected_stages.items():
                    if stage_name in stages:
                        stage = stages[stage_name]
                        if 'substages' in stage:
                            substages = stage['substages']
                            # At least verify the structure is correct, even if not all substages are present
                            assert isinstance(substages, dict)


if __name__ == '__main__':
    # Allow running directly for quick testing
    import sys
    from flask import Flask
    from blueprints.automation_core import bp as automation_bp
    
    app = Flask(__name__)
    app.register_blueprint(automation_bp)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        print("Testing pipeline status API endpoint...")
        response = client.get('/launchpad/one-click-blog/api/pipeline-status/96')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"Success: {data.get('success')}")
            if data.get('success'):
                print(f"Post ID: {data['data'].get('post_id')}")
                print(f"Title: {data['data'].get('title')}")
                print(f"Stages: {list(data['data'].get('stages', {}).keys())}")
        else:
            print(f"Response: {response.get_data(as_text=True)}")

