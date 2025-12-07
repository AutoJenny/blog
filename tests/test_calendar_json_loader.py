"""
Test Calendar JSON Loader

Tests for utils/calendar_json_loader.py to ensure robust handling of:
- Valid JSON files
- Missing files
- Corrupt JSON
- Invalid formats
"""

import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch
from utils.calendar_json_loader import (
    load_category_year_schedule,
    get_schedule_json_path,
    get_schedule_base_dir,
)


class TestCalendarJsonLoader:
    """Test suite for calendar JSON loader"""
    
    @pytest.fixture
    def temp_schedule_dir(self):
        """Create temporary schedule directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def valid_theme_json(self, temp_schedule_dir):
        """Create a valid theme JSON file"""
        json_data = {
            "category": "theme",
            "year": 2025,
            "generated_at": "2025-01-01T00:00:00Z",
            "weeks": {
                "1": {"id": 101, "position": 1, "title": "Theme 1"},
                "2": {"id": 102, "position": 2, "title": "Theme 2"},
                "52": {"id": 103, "position": 3, "title": "Theme 3"}
            }
        }
        file_path = os.path.join(temp_schedule_dir, "theme_2025.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)
        return file_path, json_data
    
    def test_loads_valid_json_correctly(self, temp_schedule_dir, valid_theme_json):
        """Test that valid JSON is loaded and converted to week mapping"""
        file_path, json_data = valid_theme_json
        
        with patch('utils.calendar_json_loader.get_schedule_json_path', return_value=file_path):
            result = load_category_year_schedule('theme', 2025)
        
        assert isinstance(result, dict)
        assert len(result) == 3  # 3 weeks in fixture
        assert 1 in result
        assert 2 in result
        assert 52 in result
        
        # Check week 1 entry
        week1 = result[1]
        assert week1['item_id'] == 101
        assert week1['position'] == 1
        assert week1['title'] == "Theme 1"
    
    def test_returns_week_number_mapping(self, temp_schedule_dir, valid_theme_json):
        """Test that result maps week numbers (int) to entry dicts"""
        file_path, json_data = valid_theme_json
        
        with patch('utils.calendar_json_loader.get_schedule_json_path', return_value=file_path):
            result = load_category_year_schedule('theme', 2025)
        
        # All keys should be integers
        assert all(isinstance(k, int) for k in result.keys())
        
        # All values should be dicts
        assert all(isinstance(v, dict) for v in result.values())
    
    def test_handles_missing_file_gracefully(self):
        """Test that missing JSON file returns empty dict, not exception"""
        fake_path = "/nonexistent/path/theme_2025.json"
        
        with patch('utils.calendar_json_loader.get_schedule_json_path', return_value=fake_path):
            result = load_category_year_schedule('theme', 2025)
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_handles_corrupt_json_gracefully(self, temp_schedule_dir):
        """Test that corrupt JSON returns empty dict, not exception"""
        corrupt_file = os.path.join(temp_schedule_dir, "theme_2025.json")
        with open(corrupt_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json syntax !!!")
        
        with patch('utils.calendar_json_loader.get_schedule_json_path', return_value=corrupt_file):
            result = load_category_year_schedule('theme', 2025)
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_handles_invalid_json_format(self, temp_schedule_dir):
        """Test that non-dict JSON returns empty dict"""
        invalid_file = os.path.join(temp_schedule_dir, "theme_2025.json")
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump(["not", "a", "dict"], f)
        
        with patch('utils.calendar_json_loader.get_schedule_json_path', return_value=invalid_file):
            result = load_category_year_schedule('theme', 2025)
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_handles_missing_weeks_key(self, temp_schedule_dir):
        """Test that JSON without 'weeks' key returns empty dict"""
        invalid_file = os.path.join(temp_schedule_dir, "theme_2025.json")
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump({"category": "theme", "year": 2025}, f)
        
        with patch('utils.calendar_json_loader.get_schedule_json_path', return_value=invalid_file):
            result = load_category_year_schedule('theme', 2025)
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_handles_legacy_list_format(self, temp_schedule_dir):
        """Test backward compatibility with legacy flat list format"""
        legacy_file = os.path.join(temp_schedule_dir, "theme_2025.json")
        legacy_data = [
            {"week": 1, "item_id": 101, "position": 1, "title": "Theme 1"},
            {"week": 2, "item_id": 102, "position": 2, "title": "Theme 2"}
        ]
        with open(legacy_file, 'w', encoding='utf-8') as f:
            json.dump(legacy_data, f)
        
        with patch('utils.calendar_json_loader.get_schedule_json_path', return_value=legacy_file):
            result = load_category_year_schedule('theme', 2025)
        
        assert isinstance(result, dict)
        assert len(result) == 2
        assert 1 in result
        assert 2 in result
    
    def test_converts_id_to_item_id(self, temp_schedule_dir, valid_theme_json):
        """Test that 'id' field is converted to 'item_id' in result"""
        file_path, json_data = valid_theme_json
        
        with patch('utils.calendar_json_loader.get_schedule_json_path', return_value=file_path):
            result = load_category_year_schedule('theme', 2025)
        
        week1 = result[1]
        assert 'item_id' in week1
        assert week1['item_id'] == 101
        # Original 'id' should not be present
        assert 'id' not in week1 or week1.get('id') != 101


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

