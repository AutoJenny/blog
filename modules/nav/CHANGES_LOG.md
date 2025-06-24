# Navigation Module Changes Log

## [2024-06-24]
### Changed
- Refactored navigation services to use shared database services exclusively
- Removed redundant database query functions from nav module
- Simplified workflow context building to focus on navigation concerns
- Improved separation of concerns between database and navigation logic

### Removed
- Removed `get_workflow_stages()` and `get_workflow_substages()` from nav services
- Removed duplicate database querying logic
- Removed redundant `get_workflow_stages_fallback()` function
- Removed local `get_all_posts()` function in favor of direct shared service usage

## [2024-03-19]
### Changed
- Implemented hybrid service layer pattern
- Removed direct database access in favor of shared services
- Added proper URL generation for all navigation links
- Added post selector JavaScript handling
- Improved error messages and status indicators
- Added context validation with fallbacks
- Standardized template structure with proper loops
- Added blueprint-aware static file loading

## [Previous Changes]
- Initial implementation of navigation module
- Basic workflow stage navigation
- Dark theme styling 