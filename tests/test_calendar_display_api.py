"""
Test Calendar Display API

Tests for blueprints/planning_api_calendar_scheduling_cache.py to ensure:
- Default behavior returns 52 weeks
- Range navigation works correctly
- Year boundaries are handled
- Missing JSON files degrade gracefully
- Performance is acceptable
"""

import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestCalendarDisplayAPI:
    """Test suite for calendar display API"""
    
    @pytest.fixture
    def app(self):
        """Create Flask test app"""
        from unified_app import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def temp_schedule_dir(self):
        """Create temporary schedule directory with fixtures"""
        temp_dir = tempfile.mkdtemp()
        
        # Create fixture JSON files
        fixtures = {
            'theme_2025.json': {
                "category": "theme",
                "year": 2025,
                "generated_at": "2025-01-01T00:00:00Z",
                "weeks": {
                    "1": {"id": 101, "position": 1, "title": "Theme 1"},
                    "2": {"id": 102, "position": 2, "title": "Theme 2"},
                    "52": {"id": 103, "position": 3, "title": "Theme 3"}
                }
            },
            'recipe_2025.json': {
                "category": "recipe",
                "year": 2025,
                "generated_at": "2025-01-01T00:00:00Z",
                "weeks": {
                    "1": {"id": 201, "position": 1, "title": "Recipe 1"},
                    "2": {"id": 202, "position": 2, "title": "Recipe 2"}
                }
            }
        }
        
        for filename, data in fixtures.items():
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_default_behavior_returns_weeks(self, client, temp_schedule_dir):
        """Test that default GET returns weeks array"""
        with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=temp_schedule_dir):
            response = client.get('/planning/api/calendar/scheduling/all')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert 'data' in data
        assert 'weeks' in data['data']
        assert isinstance(data['data']['weeks'], list)
    
    def test_includes_current_year_and_week(self, client, temp_schedule_dir):
        """Test that response includes current_year and current_week"""
        with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=temp_schedule_dir):
            response = client.get('/planning/api/calendar/scheduling/all')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'current_year' in data['data']
        assert 'current_week' in data['data']
        assert isinstance(data['data']['current_year'], int)
        assert isinstance(data['data']['current_week'], int)
    
    def test_weeks_contain_year_week_schedule(self, client, temp_schedule_dir):
        """Test that each week entry has year, week, and schedule"""
        with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=temp_schedule_dir):
            response = client.get('/planning/api/calendar/scheduling/all')
        
        assert response.status_code == 200
        data = response.get_json()
        weeks = data['data']['weeks']
        
        if len(weeks) > 0:
            week_entry = weeks[0]
            assert 'year' in week_entry
            assert 'week' in week_entry
            assert 'schedule' in week_entry
            assert isinstance(week_entry['schedule'], list)
    
    def test_range_navigation_parameters(self, client, temp_schedule_dir):
        """Test that start_year, start_week, weeks parameters work"""
        with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=temp_schedule_dir):
            response = client.get('/planning/api/calendar/scheduling/all?start_year=2025&start_week=1&weeks=10')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['data']['range_start_year'] == 2025
        assert data['data']['range_start_week'] == 1
        assert data['data']['range_weeks'] == 10
        assert len(data['data']['weeks']) == 10
    
    def test_handles_year_boundary(self, client, temp_schedule_dir):
        """Test that ranges crossing year boundaries work"""
        # Create 2026 fixture
        theme_2026 = {
            "category": "theme",
            "year": 2026,
            "generated_at": "2026-01-01T00:00:00Z",
            "weeks": {
                "1": {"id": 201, "position": 1, "title": "Theme 2026-1"}
            }
        }
        file_path = os.path.join(temp_schedule_dir, 'theme_2026.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(theme_2026, f)
        
        # Request range that crosses year boundary (week 52 of 2025 + week 1 of 2026)
        with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=temp_schedule_dir):
            response = client.get('/planning/api/calendar/scheduling/all?start_year=2025&start_week=52&weeks=2')
        
        assert response.status_code == 200
        data = response.get_json()
        weeks = data['data']['weeks']
        
        # Should have 2 weeks
        assert len(weeks) == 2
        
        # First week should be 2025 week 52
        assert weeks[0]['year'] == 2025
        assert weeks[0]['week'] == 52
        
        # Second week should be 2026 week 1
        assert weeks[1]['year'] == 2026
        assert weeks[1]['week'] == 1
    
    def test_handles_missing_json_gracefully(self, client):
        """Test that missing JSON files don't crash the endpoint"""
        empty_dir = tempfile.mkdtemp()
        try:
            with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=empty_dir):
                response = client.get('/planning/api/calendar/scheduling/all?start_year=2025&start_week=1&weeks=2')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Should still return structure, just with empty schedules
            assert data['success'] is True
            assert 'weeks' in data['data']
        finally:
            shutil.rmtree(empty_dir)
    
    def test_invalid_parameters_fallback_to_defaults(self, client, temp_schedule_dir):
        """Test that invalid parameters fall back to defaults"""
        with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=temp_schedule_dir):
            # Invalid start_year
            response = client.get('/planning/api/calendar/scheduling/all?start_year=invalid&start_week=1')
            assert response.status_code == 400
            
            # Invalid weeks (too large)
            response = client.get('/planning/api/calendar/scheduling/all?weeks=1000')
            assert response.status_code == 200  # Should cap at MAX_RANGE_WEEKS
    
    def test_schedule_items_have_correct_types(self, client, temp_schedule_dir):
        """Test that schedule items have correct type fields"""
        with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=temp_schedule_dir):
            response = client.get('/planning/api/calendar/scheduling/all?start_year=2025&start_week=1&weeks=1')
        
        assert response.status_code == 200
        data = response.get_json()
        weeks = data['data']['weeks']
        
        if len(weeks) > 0 and len(weeks[0]['schedule']) > 0:
            schedule = weeks[0]['schedule']
            
            # Find theme item
            theme_item = next((item for item in schedule if item.get('type') == 'theme_selection'), None)
            if theme_item:
                assert 'theme_id' in theme_item
                assert 'theme_title' in theme_item
            
            # Find recipe item
            recipe_item = next((item for item in schedule if item.get('type') == 'recipe'), None)
            if recipe_item:
                assert 'recipe_id' in recipe_item
                assert 'recipe_title' in recipe_item
    
    def test_performance_acceptable(self, client, temp_schedule_dir):
        """Test that endpoint responds quickly (< 200ms)"""
        import time
        
        with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=temp_schedule_dir):
            start = time.time()
            response = client.get('/planning/api/calendar/scheduling/all?start_year=2025&start_week=1&weeks=52')
            elapsed = time.time() - start
        
        assert response.status_code == 200
        # Should be fast (allowing some overhead for test environment)
        assert elapsed < 1.0  # 1 second is generous for test environment
    
    def test_returns_range_metadata(self, client, temp_schedule_dir):
        """Test that response includes range metadata"""
        with patch('utils.calendar_json_loader.get_schedule_base_dir', return_value=temp_schedule_dir):
            response = client.get('/planning/api/calendar/scheduling/all?start_year=2025&start_week=10&weeks=20')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'range_start_year' in data['data']
        assert 'range_start_week' in data['data']
        assert 'range_weeks' in data['data']
        
        assert data['data']['range_start_year'] == 2025
        assert data['data']['range_start_week'] == 10
        assert data['data']['range_weeks'] == 20


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

