"""
Test Calendar Schedule Builder

Tests for utils/calendar_schedule_builder.py to ensure:
- Builder outputs exactly 52 entries
- Week numbers increment correctly
- Cyclic logic works correctly
- Overrides are applied
"""

import pytest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from utils.calendar_schedule_builder import (
    build_category_year_schedule,
    write_category_year_json,
    _build_weeks_from_base_list,
    _load_base_list,
)


class TestCalendarBuilder:
    """Test suite for calendar schedule builder"""
    
    @pytest.fixture
    def temp_schedule_dir(self):
        """Create temporary schedule directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_base_list(self):
        """Mock base list with 3 items"""
        return [
            {"id": 101, "position": 1, "title": "Item 1"},
            {"id": 102, "position": 2, "title": "Item 2"},
            {"id": 103, "position": 3, "title": "Item 3"},
        ]
    
    @pytest.fixture
    def mock_db_cursor(self):
        """Mock database cursor"""
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = None
        return cursor
    
    def test_builds_exactly_52_weeks(self, mock_base_list):
        """Test that builder outputs exactly 52 week entries"""
        with patch('utils.calendar_schedule_builder._load_base_list', return_value=mock_base_list):
            with patch('utils.calendar_schedule_builder.get_cycle_start_week', return_value=1):
                with patch('utils.calendar_schedule_builder._load_overrides_for_category_year', return_value={}):
                    result = build_category_year_schedule('theme', 2025)
        
        assert 'weeks' in result
        weeks = result['weeks']
        assert len(weeks) == 52
        
        # Check all week numbers 1-52 are present
        week_numbers = [int(k) for k in weeks.keys()]
        assert sorted(week_numbers) == list(range(1, 53))
    
    def test_week_numbers_increment_correctly(self, mock_base_list):
        """Test that week numbers are sequential 1-52"""
        with patch('utils.calendar_schedule_builder._load_base_list', return_value=mock_base_list):
            with patch('utils.calendar_schedule_builder.get_cycle_start_week', return_value=1):
                with patch('utils.calendar_schedule_builder._load_overrides_for_category_year', return_value={}):
                    result = build_category_year_schedule('theme', 2025)
        
        weeks = result['weeks']
        for week_num in range(1, 53):
            assert str(week_num) in weeks
    
    def test_cyclic_logic_applies_correctly(self, mock_base_list):
        """Test that cyclic formula correctly maps positions to weeks"""
        with patch('utils.calendar_schedule_builder._load_base_list', return_value=mock_base_list):
            with patch('utils.calendar_schedule_builder.get_cycle_start_week', return_value=1):
                with patch('utils.calendar_schedule_builder._load_overrides_for_category_year', return_value={}):
                    result = build_category_year_schedule('theme', 2025)
        
        weeks = result['weeks']
        
        # Week 1 should have position 1 (cycle_start_week = 1, week 1 -> position 1)
        assert weeks['1']['position'] == 1
        assert weeks['1']['id'] == 101
        
        # Week 2 should have position 2
        assert weeks['2']['position'] == 2
        assert weeks['2']['id'] == 102
        
        # Week 3 should have position 3
        assert weeks['3']['position'] == 3
        assert weeks['3']['id'] == 103
        
        # Week 4 should cycle back to position 1 (3 items, so week 4 = position 1)
        assert weeks['4']['position'] == 1
        assert weeks['4']['id'] == 101
    
    def test_handles_empty_base_list(self):
        """Test that empty base list produces empty weeks dict"""
        with patch('utils.calendar_schedule_builder._load_base_list', return_value=[]):
            with patch('utils.calendar_schedule_builder.get_cycle_start_week', return_value=1):
                with patch('utils.calendar_schedule_builder._load_overrides_for_category_year', return_value={}):
                    result = build_category_year_schedule('theme', 2025)
        
        assert 'weeks' in result
        assert len(result['weeks']) == 0
    
    def test_includes_metadata(self, mock_base_list):
        """Test that result includes category, year, generated_at"""
        with patch('utils.calendar_schedule_builder._load_base_list', return_value=mock_base_list):
            with patch('utils.calendar_schedule_builder.get_cycle_start_week', return_value=1):
                with patch('utils.calendar_schedule_builder._load_overrides_for_category_year', return_value={}):
                    result = build_category_year_schedule('theme', 2025)
        
        assert result['category'] == 'theme'
        assert result['year'] == 2025
        assert 'generated_at' in result
        assert isinstance(result['generated_at'], str)
    
    def test_applies_overrides(self, mock_base_list):
        """Test that overrides replace cyclic items"""
        # Override week 2 to use item_id 999
        overrides = {2: 999}
        
        def mock_get_item_by_id(category, item_id):
            if item_id == 999:
                return {"id": 999, "position": 99, "title": "Override Item"}
            return None
        
        with patch('utils.calendar_schedule_builder._load_base_list', return_value=mock_base_list):
            with patch('utils.calendar_schedule_builder.get_cycle_start_week', return_value=1):
                with patch('utils.calendar_schedule_builder._load_overrides_for_category_year', return_value=overrides):
                    with patch('utils.calendar_schedule_builder._get_item_by_id', side_effect=mock_get_item_by_id):
                        result = build_category_year_schedule('theme', 2025)
        
        weeks = result['weeks']
        # Week 2 should have override item
        assert weeks['2']['id'] == 999
        assert weeks['2']['title'] == "Override Item"
        
        # Week 1 should still have cyclic item
        assert weeks['1']['id'] == 101
    
    def test_writes_valid_json_file(self, temp_schedule_dir, mock_base_list):
        """Test that write_category_year_json creates valid JSON file"""
        with patch('utils.calendar_schedule_builder._get_schedule_base_dir', return_value=temp_schedule_dir):
            with patch('utils.calendar_schedule_builder._load_base_list', return_value=mock_base_list):
                with patch('utils.calendar_schedule_builder.get_cycle_start_week', return_value=1):
                    with patch('utils.calendar_schedule_builder._load_overrides_for_category_year', return_value={}):
                        file_path = write_category_year_json('theme', 2025)
        
        assert os.path.exists(file_path)
        assert file_path.endswith('theme_2025.json')
        
        # Verify JSON is valid
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['category'] == 'theme'
        assert data['year'] == 2025
        assert 'weeks' in data
        assert len(data['weeks']) == 52
    
    def test_handles_invalid_override_gracefully(self, mock_base_list):
        """Test that invalid override item_id is skipped"""
        # Override week 2 to use non-existent item_id 9999
        overrides = {2: 9999}
        
        def mock_get_item_by_id(category, item_id):
            return None  # Item doesn't exist
        
        with patch('utils.calendar_schedule_builder._load_base_list', return_value=mock_base_list):
            with patch('utils.calendar_schedule_builder.get_cycle_start_week', return_value=1):
                with patch('utils.calendar_schedule_builder._load_overrides_for_category_year', return_value=overrides):
                    with patch('utils.calendar_schedule_builder._get_item_by_id', side_effect=mock_get_item_by_id):
                        result = build_category_year_schedule('theme', 2025)
        
        weeks = result['weeks']
        # Week 2 should have cyclic item (override skipped)
        assert weeks['2']['id'] == 102  # Cyclic item, not override


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

