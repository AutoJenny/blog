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
- **JSON Files**: `data/calendar/schedule/{category}_{year}.json`
- **Display API**: `blueprints/planning_api_calendar_scheduling_cache.py`
- **Builder Module**: `utils/calendar_schedule_builder.py`
- **Builder Script**: `scripts/build_calendar_schedules.py`
- **List Management**: `blueprints/planning_api_calendar_cyclic.py`
- **Override API**: `blueprints/planning_api_calendar_overrides.py`
- **Frontend**: `templates/planning/calendar/scheduling.html`

### Key Concepts
- **5 Layers**: Database → Logic → JSON Storage → API → Frontend
- **JSON-Centric**: All display data comes from pre-computed JSON files
- **Range-Based**: API returns flexible week ranges, not fixed years
- **12-Month Window**: UI shows rolling 12 months from today

### Implementation Status
- **Phase 1 (Current)**: Display layer - fast page loads with JSON files
- **Phase 2 (Future)**: Modification layer - reassignments, overrides, drag-and-drop

---

*Document created: 2025-01-XX*
*Status: Documentation index*

