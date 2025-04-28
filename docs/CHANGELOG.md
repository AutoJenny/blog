# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- LLM integration for content generation
- Database management interface
- Workflow management system
- Fully normalized SQL workflow system for post development stages and sub-stages
- Seeding script for workflow tables (`scripts/update_workflow.py`)
- Major UI redesign of blog index page (2024-07-10):
  - Replaced table with a modern, responsive card/grid layout for posts
  - Each post is now a card showing title, status, date, and clear action buttons (Develop, JSON, Delete)
  - Added a floating 'New Post' button
  - Modern toggle for showing deleted posts
  - Improved accessibility, mobile responsiveness, and visual hierarchy
  - Updated scripts and styles for new structure

### Fixed
- Blueprint registration for LLM and DB modules
- Port configuration standardization (now using port 5000)
- Template rendering issues in base template
- Fixed frontend bug where sub-stage content save failed due to incorrect use of `this.closest` in `saveSubStageContent` (now uses element lookup by subStageId).
- All sub-stage update requests now use correct data binding via element dataset attributes.
- Rendered 'Basic Idea' as a normal sub-stage in the workflow accordion, removed static block, and ensured all sub-stages are editable and save correctly.

### Changed
- Improved development documentation
- Standardized server startup process
- Migrated workflow logic, transitions, and sub-stage updates to normalized SQL tables
- Deprecated legacy JSON-based workflow fields (to be removed after migration)
- Frontend workflow UI: sub-stage updates now use element lookup by subStageId and dataset attributes for data binding, replacing 'this.closest'.
- Updated documentation to clarify that all workflow UI fields must be bound to backend stage_data, not static definitions.

## [0.1.0] - 2025-04-24

### Added
- Initial project setup
- Basic blog functionality
- Post creation and management
- User authentication
- Admin interface
- Celery task queue integration
- Basic API endpoints 