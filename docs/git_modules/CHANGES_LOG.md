# CHANGES_LOG.md

## [2024-12-19] - Template Integration and Service Layer Implementation
- **Hybrid Service Layer Pattern**: Implemented shared services in MAIN_HUB (`app/services/shared.py`) for DB access and workflow logic
- **Nav Module Integration**: Updated nav module to use shared services when available, fallback to demo data in standalone mode
- **Template Integration Fix**: Fixed workflow template to properly include nav module via blueprint name (`workflow_nav/nav.html`)
- **Blueprint Registration**: Registered nav blueprint in MAIN_HUB for both standalone and integrated operation
- **Fallback Content Removal**: Removed confusing placeholder text from workflow templates
- **Documentation Update**: Updated all /docs/git_modules documentation to reflect new architecture and integration patterns

## [2024-12-19] - Workflow Route Handler Synchronization
- **Route Handler Sync**: Updated workflow-navigation branch route handler to match MAIN_HUB integration code
- **Real Data Integration**: Both branches now use nav module services for real database data instead of hardcoded values
- **One-Way Merge Policy**: Maintained strict one-way merge policy (nav module only) while ensuring consistent behavior

## [2024-12-19] - Template Architecture Refinement
- **Blueprint-Based Includes**: Implemented proper Flask blueprint template includes for module integration
- **Integration Code Separation**: MAIN_HUB controls workflow layout, modules provide functionality
- **Template Path Resolution**: Fixed template include paths to use blueprint names for proper Flask resolution

## DEV12 Branch - Workflow Layout Implementation
Created: [Current Date]

### Key Changes
- Implemented stage-specific layout panels with deep backgrounds
- Full-width LLM panel for Planning stage (deep purple #2D0A50)
- Split-width panels for Writing stage (LLM panel and Sections panel)
- Renamed llm-actions module to llm_actions for consistency

### Critical Dependencies
- Base template: app/templates/base.html
  - Backup: app/templates/base.DEV12.html
- Nav module template: modules/nav/templates/nav.html
  - Pinned version: 1b7d78586eb8f770b2c767ebc3234d47c087d36e
- CSS: app/static/css/dist/main.css
  - Backup: app/static/css/dist/main.DEV12.css

### Layout Specifications
- Planning stage: Full-width LLM panel
- Writing stage: 50/50 split between LLM and Sections panels
- Panel colors: 
  - LLM Panel: #2D0A50 (deep purple)
  - Sections Panel: #013828 (deep green)
- Minimal spacing between nav and panels (-mt-20)

### Notes
- Layout is sensitive to changes in base template structure
- Panel positioning relies on current nav module implementation
- Consider pinning CSS version if making significant style changes in other branches

### Recovery Instructions
If layout breaks due to upstream changes:
1. Check out nav module at pinned commit: 
   ```
   git checkout 1b7d78586eb8f770b2c767ebc3234d47c087d36e -- modules/nav/
   ```
2. Restore base template:
   ```
   cp app/templates/base.DEV12.html app/templates/base.html
   ```
3. Restore CSS:
   ```
   cp app/static/css/dist/main.DEV12.css app/static/css/dist/main.css
   ``` 