# Calendar Scheduling Test Suite

This directory contains automated tests for the JSON-backed calendar scheduling system.

## Test Files

- `test_calendar_json_loader.py` - Tests for JSON file loading and error handling
- `test_calendar_builder.py` - Tests for JSON schedule generation
- `test_calendar_display_api.py` - Tests for the display API endpoint

## Test Fixtures

Fixtures are located in `fixtures/schedule/` and provide small, deterministic JSON files for testing:

- `theme_2025.json`
- `recipe_2025.json`
- `profile_product_2025.json`
- `profile_surname_2025.json`
- `weekly_word_2025.json`
- `weekly_phrase_2025.json`

## Running Tests

### Using pytest (Recommended)

```bash
# Run all calendar scheduling tests
pytest tests/test_calendar_*.py -v

# Run specific test file
pytest tests/test_calendar_json_loader.py -v

# Run with coverage
pytest tests/test_calendar_*.py --cov=utils.calendar_json_loader --cov=utils.calendar_schedule_builder --cov=blueprints.planning_api_calendar_scheduling_cache

# Run with max 1 failure (stop on first error)
pytest tests/test_calendar_*.py --maxfail=1
```

### Using unittest (Alternative)

```bash
python -m unittest tests.test_calendar_json_loader
python -m unittest tests.test_calendar_builder
python -m unittest tests.test_calendar_display_api
```

## Test Coverage

### JSON Loader Tests
- ✅ Loads valid JSON correctly
- ✅ Returns week number mapping
- ✅ Handles missing files gracefully
- ✅ Handles corrupt JSON gracefully
- ✅ Handles invalid formats
- ✅ Backward compatibility with legacy format

### Builder Tests
- ✅ Outputs exactly 52 weeks
- ✅ Week numbers increment correctly
- ✅ Cyclic logic applies correctly
- ✅ Handles empty base lists
- ✅ Includes metadata
- ✅ Applies overrides
- ✅ Writes valid JSON files
- ✅ Handles invalid overrides gracefully

### Display API Tests
- ✅ Default behavior returns weeks
- ✅ Includes current year/week
- ✅ Weeks contain correct structure
- ✅ Range navigation parameters work
- ✅ Handles year boundaries
- ✅ Handles missing JSON gracefully
- ✅ Invalid parameters fallback
- ✅ Schedule items have correct types
- ✅ Performance is acceptable
- ✅ Returns range metadata

## Dependencies

Tests require:
- `pytest` (or `unittest` for basic tests)
- Flask test client
- Mock support (unittest.mock)

Install pytest:
```bash
pip install pytest pytest-cov
```

## Notes

- Tests use temporary directories and mock database connections
- No real database or file system changes are made
- Fixtures are small and deterministic for predictable results
- Tests are designed to run quickly (< 5 seconds total)

