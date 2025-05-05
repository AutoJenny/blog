# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- LLM integration with improved interface and functionality
  - Added Test button to LLM Action modal in blog develop interface
  - Added '+ Add New Prompt' link in LLM settings panel
  - Added /api/v1/llm/prompts POST endpoint for creating new LLMPrompt records
  - Added comprehensive API documentation for workflow endpoints
  - Added docs/workflow/field_reference.md for workflow sub-stage fields
- Database management interface improvements
  - Enhanced virtual environment handling in run_server.sh
  - Added automatic venv detection and activation
  - Added new PostgreSQL-specific database management scripts
  - Added database monitoring and replication tools
- Major UI redesign of blog index page
  - Replaced table with modern, responsive card/grid layout
  - Added floating 'New Post' button
  - Added modern toggle for showing deleted posts
  - Improved accessibility and mobile responsiveness
  - Refined dark theme with improved contrast
  - Added json, edit, and delete icons/links to each post row
- Enhancement: Automatic database backup now runs after every commit (insert, update, or delete), with old backups rotated to prevent bloat. This uses a SQLAlchemy event listener and the existing backup script.
- UI: Section Generate buttons now show 'Generating...' and are disabled while the request is in progress, preventing double-clicks and giving clear feedback to the user.
- Enhancement: Added drag-and-drop reordering for prompt templates with visible gap indicator. Order is now persisted in the database and respected in all selection menus. Added /api/v1/llm/prompts/order endpoint to update order.

### Changed
- Updated all workflow documentation for asynchronous model
- Moved New Post button to main header
- Enhanced LLM interface JavaScript functionality
- Improved LLMService timeout handling and error reporting
- Increased LLM backend request timeout to 60 seconds
- Reorganized Idea Scope and Provisional Title fields with independent LLM modals
- Updated DEPENDENCIES.md with current project dependencies
- Migrated all database operations to PostgreSQL
  - Removed SQLite support completely
  - Updated database scripts to use PostgreSQL
  - Added PostgreSQL-specific backup and restore tools
  - Enhanced database monitoring capabilities

### Fixed
- Fixed incorrect route registration for /blog/develop/<post_id>
- Fixed all fetch URLs in blog development template
- Fixed Post.updated_at updates for PostDevelopment fields
- Fixed LLM Test Interface model selection and display
  - Fixed prompt handling in Test tab JavaScript
  - Improved data passing between frontend and backend
  - Removed client-side prompt formatting
  - Added proper data attributes to test options
- Fixed Idea Scope modal prompt template saving
- Fixed blueprint registration issues
- Fixed template rendering problems
- Fixed LLM input processing and prompt handling
  - Made prompt structure more explicit to ensure LLM understands input context
  - Improved prompt formatting to clearly link task and topic
  - Added clearer instruction flow in prompts
  - Fixed test endpoint response handling
- Improved error handling in LLMService
- Fixed database connection issues
  - Added proper PostgreSQL connection validation
  - Enhanced error handling for database operations
  - Improved database script reliability
- Fix: Section LLM Action dropdowns and Generate buttons are now always populated and wired up after DOM is ready, ensuring Actions are available for all section content fields in the develop page.
- Fix: LLM prompt templates and selection menus now always reflect the persisted order by ordering on the 'order' field in all UI routes.

### Removed
- Removed PromptTemplate model and table
- Removed legacy references to sequential workflow initialization
- Removed SQLite support and related code
  - Removed SQLite migration scripts
  - Removed SQLite-specific database operations
  - Removed SQLite fallback options

## [0.1.0] - 2024-03-01

### Added
- Initial project setup
- Basic blog functionality
- User authentication system
- API endpoints for core features
- Database models and migrations
- Frontend templates and styling
- Development environment configuration
- Testing framework implementation
- Documentation structure

## [Unreleased]
- Deprecated and removed all test Postgres and test database configuration, scripts, and test infrastructure. Retained backup and restore functionality only. All test-related files, configs, and scripts have been deleted for a belt-and-braces approach. Test infrastructure can be rebuilt later if needed. 