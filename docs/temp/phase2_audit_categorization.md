# Phase 2 Audit: Function Categorization

## File Structure Analysis

### Current State
- **Total lines**: 1,279
- **Routes**: 44 routes
- **Functions**: 48 functions
- **Classes**: 1 class (LLMService)

## Proposed File Structure

### 1. `blueprints/planning_views.py` (~200 lines)
**Purpose**: User-facing page routes
**Functions** (7):
- `planning_dashboard()` - @bp.route('/')
- `planning_post_overview(post_id)` - @bp.route('/posts/<int:post_id>')
- `planning_concept(post_id)` - @bp.route('/posts/<int:post_id>/concept')
- `planning_calendar(post_id)` - @bp.route('/posts/<int:post_id>/calendar')
- `categories_manage()` - @bp.route('/categories/manage')
- `planning_research(post_id)` - @bp.route('/posts/<int:post_id>/research')
- `planning_old_interface(post_id)` - @bp.route('/posts/<int:post_id>/old-interface')

### 2. `blueprints/planning_api.py` (~600 lines)
**Purpose**: All API endpoints
**Functions** (25):
- `api_calendar_categories()` - @bp.route('/api/calendar/categories')
- `api_calendar_weeks(year)` - @bp.route('/api/calendar/weeks/<int:year>')
- `api_calendar_ideas(week_number)` - @bp.route('/api/calendar/ideas/<int:week_number>')
- `api_calendar_events(year, week_number)` - @bp.route('/api/calendar/events/<int:year>/<int:week_number>')
- `api_calendar_schedule(year, week_number)` - @bp.route('/api/calendar/schedule/<int:year>/<int:week_number>')
- `api_calendar_ideas_for_week(week_number)` - @bp.route('/api/calendar/ideas/week/<int:week_number>')
- `api_get_idea_seed(post_id)` - @bp.route('/api/posts/<int:post_id>/idea-seed')
- `api_update_idea_seed(post_id)` - @bp.route('/api/posts/<int:post_id>/idea-seed')
- `api_check_topic()` - @bp.route('/api/posts/check-topic')
- `api_create_new_post()` - @bp.route('/api/posts/create-new')
- `api_redirect_after_creation()` - @bp.route('/api/posts/redirect-after-creation')
- `api_posts(post_id)` - @bp.route('/api/posts/<int:post_id>')
- `api_get_prompt(prompt_type)` - @bp.route('/api/llm/prompts/<prompt_type>')
- `api_generate_brainstorm_topics()` - @bp.route('/api/brainstorm/topics')
- `api_get_idea_scope(post_id)` - @bp.route('/api/posts/<int:post_id>/idea-scope')
- `api_update_idea_scope(post_id)` - @bp.route('/api/posts/<int:post_id>/idea-scope')
- `api_get_sections(post_id)` - @bp.route('/api/posts/<int:post_id>/sections')
- `api_get_topic_allocation(post_id)` - @bp.route('/api/posts/<int:post_id>/topic-allocation')
- `api_sections_title()` - @bp.route('/api/sections/title')
- `api_save_sections()` - @bp.route('/api/sections/save')
- `api_get_allocate_topics(post_id)` - @bp.route('/api/sections/allocate-topics/<int:post_id>')
- `api_get_expanded_idea(post_id)` - @bp.route('/api/posts/<int:post_id>/expanded-idea')
- `api_get_post_data(post_id)` - @bp.route('/api/posts/<int:post_id>')
- `api_get_section_structure(post_id)` - @bp.route('/api/sections/design-structure/<int:post_id>')
- `api_design_section_structure()` - @bp.route('/api/sections/design-structure')

### 3. `blueprints/planning_calendar.py` (~150 lines)
**Purpose**: Calendar-specific functionality
**Functions** (3):
- `planning_calendar_view(post_id)` - @bp.route('/posts/<int:post_id>/calendar/view')
- `planning_calendar_ideas_week(week_number)` - @bp.route('/calendar/ideas/week/<int:week_number>')
- `planning_calendar_ideas(post_id)` - @bp.route('/posts/<int:post_id>/calendar/ideas')

### 4. `blueprints/planning_concept.py` (~200 lines)
**Purpose**: Concept development functionality
**Functions** (9):
- `planning_concept_brainstorm(post_id)` - @bp.route('/posts/<int:post_id>/concept/brainstorm')
- `planning_concept_section_structure(post_id)` - @bp.route('/posts/<int:post_id>/concept/section-structure')
- `planning_concept_topic_allocation(post_id)` - @bp.route('/posts/<int:post_id>/concept/topic-allocation')
- `planning_concept_titling(post_id)` - @bp.route('/posts/<int:post_id>/concept/titling')
- `planning_concept_outline(post_id)` - @bp.route('/posts/<int:post_id>/concept/outline')
- `planning_research_sources(post_id)` - @bp.route('/posts/<int:post_id>/research/sources')
- `planning_research_visuals(post_id)` - @bp.route('/posts/<int:post_id>/research/visuals')
- `planning_research_prompts(post_id)` - @bp.route('/posts/<int:post_id>/research/prompts')
- `planning_research_verification(post_id)` - @bp.route('/posts/<int:post_id>/research/verification')

### 5. `blueprints/planning_llm.py` (~100 lines)
**Purpose**: LLM service and utilities
**Contents**:
- `LLMService` class (lines 16-95)
- `parse_brainstorm_topics(content)` function (line 851)

## Dependencies Analysis

### Shared Imports
All files will need:
- `from flask import Blueprint, render_template, request, jsonify`
- `from config.database import db_manager`
- `import logging`
- `from datetime import datetime`
- `import json`

### Cross-File Dependencies
- `planning_api.py` will import from `planning_sections.py` and `planning_data.py`
- `planning_concept.py` may need LLM functions from `planning_llm.py`
- All files will need the main blueprint `bp`

## Implementation Strategy

### Step 1: Create New Files
1. Create each file with appropriate imports
2. Move functions maintaining exact signatures
3. Ensure all dependencies are properly imported

### Step 2: Update Main File
1. Replace moved functions with imports
2. Maintain blueprint registration
3. Keep only essential blueprint setup

### Step 3: Test
1. Verify application starts
2. Test all routes and endpoints
3. Verify no functionality lost

## Risk Mitigation
- Test after each file creation
- Maintain rollback capability
- Consult if unexpected behavior occurs
