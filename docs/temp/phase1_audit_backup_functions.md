# Phase 1 Audit: Backup Functions Analysis

## Functions Currently Imported from Backup File

### 1. `api_sections_title()` 
- **Location**: Lines 4064-4594 (530 lines)
- **Purpose**: Create titles and descriptions for sections with allocated topics
- **Dependencies**: 
  - `request` (Flask)
  - `jsonify` (Flask)
  - `db_manager` (config.database)
  - `logger` (logging)
  - Database table: `llm_prompt` (name='Section Titling')
- **Contamination Status**: ✅ CLEAN (no hardcoded content)
- **API Endpoint**: `/api/sections/title` (POST)

### 2. `api_save_sections(post_id)`
- **Location**: Lines 4595-5094 (499 lines)  
- **Purpose**: Save generated sections to post_development table
- **Dependencies**:
  - `request` (Flask)
  - `jsonify` (Flask)
  - `db_manager` (config.database)
  - `logger` (logging)
  - `json` (standard library)
  - `sanitize_sections_text` function
- **Contamination Status**: ✅ CLEAN (no prompts, just data saving)
- **API Endpoint**: `/api/sections/save` (POST)

### 3. `get_post_data(post_id)`
- **Location**: Lines 371-1093 (722 lines)
- **Purpose**: Get detailed post data for data tab
- **Dependencies**:
  - `db_manager` (config.database)
  - `jsonify` (Flask)
  - Database tables: `post`, `post_development`, `calendar_schedule`
- **Contamination Status**: ✅ CLEAN (no prompts, just data retrieval)
- **API Endpoint**: `/api/posts/<int:post_id>` (GET)

### 4. `api_design_section_structure()`
- **Location**: Lines 2320-4063 (1,744 lines)
- **Purpose**: Design 7-section blog structure
- **Dependencies**:
  - `request` (Flask)
  - `jsonify` (Flask)
  - `db_manager` (config.database)
  - `logger` (logging)
  - `json` (standard library)
  - Database table: `llm_prompt` (name='Section Structure Design')
- **Contamination Status**: ❌ CONTAMINATED (uses hardcoded "Scottish autumn folklore")
- **API Endpoint**: `/api/sections/design-structure` (POST)

## Current Import Usage in planning.py

```python
# Line 1062: Used in api_sections_title()
from blueprints.planning_original_backup import api_sections_title as original_api_sections_title

# Line 1083: Used in api_save_sections()  
from blueprints.planning_original_backup import api_save_sections as original_api_save_sections

# Line 1199: Used in api_get_post_data()
from blueprints.planning_original_backup import get_post_data as original_get_post_data

# Line 1247: Used in api_design_section_structure()
from blueprints.planning_original_backup import api_design_section_structure as original_api_design_section_structure
```

## Extraction Plan

### File 1: `blueprints/planning_sections.py`
- `api_sections_title()` (530 lines)
- `api_save_sections()` (499 lines)
- `api_design_section_structure()` (1,744 lines)
- **Total**: ~2,773 lines

### File 2: `blueprints/planning_data.py`
- `get_post_data()` (722 lines)
- **Total**: ~722 lines

## Dependencies to Include
- Flask imports: `request`, `jsonify`
- Database: `db_manager`
- Logging: `logger`
- Standard library: `json`
- Custom functions: `sanitize_sections_text` (if exists)

## Testing Strategy
1. Create new files with exact function copies
2. Test imports work
3. Rename backup file to `_deprecated`
4. Update imports in main file
5. Test all endpoints work identically
6. Verify no functionality lost
