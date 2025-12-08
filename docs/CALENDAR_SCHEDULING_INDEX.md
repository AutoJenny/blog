# Calendar Scheduling System - Documentation Index

Quick reference guide to all calendar scheduling documentation.

## Start Here

**New to the system?** Read these in order:

1. **`CALENDAR_SCHEDULING_NEW_PARADIGM.md`** - High-level architectural overview
   - Explains the 5-layer architecture
   - Objectives and principles
   - Implementation phases

2. **`CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md`** - Complete component reference
   - All files and their responsibilities
   - Quick summary list
   - Component dependencies

3. **`CALENDAR_SCHEDULING_JSON_FORMAT.md`** - JSON file specification
   - Exact structure and format
   - Examples for each category
   - Validation rules

4. **`CALENDAR_SCHEDULING_BUILDER.md`** - Builder usage guide
   - How to generate JSON files
   - When to run the builder
   - Troubleshooting

## Documentation by Topic

### Architecture & Design
- `CALENDAR_SCHEDULING_NEW_PARADIGM.md` - Overall architecture and design principles
- `CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md` - Component structure and file organization

### Data Format
- `CALENDAR_SCHEDULING_JSON_FORMAT.md` - JSON file structure and format specification
- `data/schedule/README.md` - On-disk layout, invariants, and generation notes for schedule JSON files

### Operations & Maintenance
- `CALENDAR_SCHEDULING_BUILDER.md` - How to build and regenerate schedule files
- `CALENDAR_SCHEDULING_OPERATIONS.md` - Operational guide for production environments

### Testing
- `tests/README_CALENDAR_SCHEDULING.md` - Test suite documentation
- `tests/test_calendar_json_loader.py` - JSON loader tests
- `tests/test_calendar_builder.py` - Builder tests
- `tests/test_calendar_display_api.py` - Display API tests

### Problem Context
- `PERFORMANCE_ISSUE_SCHEDULING_ENDPOINT.md` - Performance problems this system solves

### Legacy Documentation (May Be Superseded)
- `CALENDAR_REASSIGNMENT_SYSTEM_REPORT.md` - Previous system documentation
- `CALENDAR_SCHEDULING_ENDPOINTS.md` - Current endpoint documentation (may change)

## Quick Reference

### Key Files
- **Configuration**: `config/calendar_settings.py` - Centralized configuration
- **JSON Files**: `data/calendar/schedule/{category}/{year}.json` (directory layout)
- **Display API**: `blueprints/planning_api_calendar_scheduling_cache.py`
- **Week View API**: `blueprints/planning_api_calendar_schedule.py` - Uses cyclic resolver
- **Builder Module**: `utils/calendar_schedule_builder.py`
- **Builder Script**: `scripts/build_calendar_schedules.py`
- **List Management**: `blueprints/planning_api_calendar_cyclic.py`
- **Override API**: `blueprints/planning_api_calendar_overrides.py` (Permanent Sequence Model - no overrides)
- **Resolver**: `utils/calendar_resolver.py` - Cyclic item resolution
- **Frontend Scheduling**: `templates/planning/calendar/scheduling.html`
- **Frontend Week View**: `templates/planning/calendar/week_view.html`

### Key Concepts
- **5 Layers**: Database → Logic → JSON Storage → API → Frontend
- **JSON-Centric**: All display data comes from pre-computed JSON files
- **Range-Based**: API returns flexible week ranges, not fixed years
- **12-Month Window**: UI shows rolling 12 months from today

### Implementation Status
- **Phase 1 (Complete)**: Display layer - fast page loads with JSON files
- **Phase 2 (Complete)**: Modification layer - drag-and-drop, modals, list management
- **Week View Integration (Complete)**: Week-view page aligned with scheduling calendar
- **Modal Functionality (Complete)**: Themes, recipes, profiles all open in modals
- **Categories (Complete)**: All 7 categories implemented (theme, recipe, profile_product, profile_surname, weekly_word, weekly_phrase, weekly_insult)

### Recent Updates
- **Weekly Insult**: Added as 7th category alongside weekly_word and weekly_phrase
- **Week View**: Integrated with new cyclic calendar system, deprecating old week-specific assignments
- **Modals**: Fixed modal functionality for all blog entry types (themes, recipes, surnames, products)
- **Product Selection**: Refined algorithm for balanced category diversity

---

*Document created: 2025-01-XX*
*Status: Documentation index*

