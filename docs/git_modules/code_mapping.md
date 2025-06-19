# Code Mapping: Hybrid Service Layer

- **Shared DB connection**: `app/database/routes.py:get_db_conn()`
- **Shared services**: `app/services/shared.py` (MAIN_HUB)
- **Nav module services**: `modules/nav/services.py`
- **Workflow integration**: `app/routes/workflow.py`
- **Nav blueprint registration**: `app/__init__.py`

## Data Flow
- MAIN_HUB integration code calls nav module service functions for all workflow/nav data.
- Nav module service functions use shared services for DB access when available, fallback to demo data otherwise.

---

_Last updated: [date]_

# Code Mapping - Module Boundaries

## ⚠️ CRITICAL FIREWALL RULE ⚠️

**NEVER EDIT MODULES DIRECTLY IN MAIN_HUB BRANCH**

- Modules in MAIN_HUB are READ-ONLY and come from source branches via merge script
- Only integration code can be edited in MAIN_HUB
- Module development happens ONLY in source branches

---

## Module Architecture Overview

This document maps the strict boundaries between modules in the BlogForge workflow system. Each module is completely self-contained and communicates only through the data layer.

### Current Module Structure

1. **Navigation Module** (`modules/nav/` in MAIN_HUB)
   - Source: `workflow-navigation` branch
   - Purpose: Workflow stage navigation and UI
   - Status: ✅ Implemented and integrated

2. **LLM Actions Module** (`modules/llm/` in MAIN_HUB)
   - Source: `workflow-llm-actions` branch
   - Purpose: LLM action management and execution
   - Status: 🔄 In development

3. **Sections Module** (`modules/sections/` in MAIN_HUB)
   - Source: `workflow-sections` branch
   - Purpose: Article section management
   - Status: 📋 Planned

---

## Module Boundaries

### Navigation Module (`modules/nav/`)

**Allowed Code:**
- Navigation templates and UI components
- Navigation-specific JavaScript
- Navigation route handlers
- Navigation CSS (module-specific only)

**Forbidden Code:**
- LLM action logic
- Section management code
- Any code not related to navigation
- Cross-module imports or dependencies

**Integration Points:**
- Uses workflow data from database
- Displays workflow stages and substages
- Integrates with main workflow route

### LLM Actions Module (`modules/llm/`)

**Allowed Code:**
- LLM action management
- LLM provider integration
- Action execution logic
- LLM-specific templates and UI

**Forbidden Code:**
- Navigation logic
- Section management code
- Any code not related to LLM actions
- Cross-module imports or dependencies

**Integration Points:**
- Uses LLM action data from database
- Executes actions via API
- Integrates with workflow system

### Sections Module (`modules/sections/`)

**Allowed Code:**
- Section creation and management
- Section templates and UI
- Section-specific logic
- Section CSS (module-specific only)

**Forbidden Code:**
- Navigation logic
- LLM action code
- Any code not related to sections
- Cross-module imports or dependencies

**Integration Points:**
- Uses section data from database
- Manages article sections
- Integrates with workflow system

---

## Integration Code (EDITABLE in MAIN_HUB)

### `app/routes/workflow.py`
- Main workflow route handler
- Module integration logic
- Data layer coordination
- Template rendering coordination

**Responsibilities:**
- Import and initialize modules
- Coordinate module interactions
- Handle workflow state management
- Provide data to modules

**Forbidden:**
- Direct module code implementation
- Module-specific business logic
- Cross-module code sharing

---

## Data Layer (Shared)

### Database Tables
- `workflow_stages`: Workflow stage definitions
- `workflow_sub_stages`: Workflow substage definitions
- `workflow_step_entity`: Workflow step data
- `llm_actions`: LLM action definitions
- `posts`: Post data
- `post_sections`: Section data

### API Endpoints
- `/workflow/`: Main workflow endpoint
- `/api/llm/`: LLM API endpoints
- `/api/posts/`: Post management endpoints

---

## Module Development Rules

### Source Branch Development
1. **Work ONLY in source branch** (workflow-navigation, etc.)
2. **Follow module boundaries strictly**
3. **Remove any cross-module code**
4. **Test module in isolation**
5. **Use merge script to update MAIN_HUB**

### MAIN_HUB Integration
1. **NEVER edit modules directly**
2. **Edit only integration code**
3. **Test integration after merges**
4. **Document all changes**

---

## Firewall Enforcement

### Technical Safeguards
- Modules in MAIN_HUB are READ-ONLY
- Only integration code is editable
- Merge script enforces separation
- No direct module editing allowed

### Process Safeguards
- Source branch development only
- Merge script for all updates
- Complete testing required
- Explicit review process

---

## Emergency Procedures

### Module Contamination
1. **Stop immediately**
2. **Document contamination**
3. **Reset to last clean merge**
4. **Seek review before proceeding**

### Integration Issues
1. **Revert to working state**
2. **Check merge script logs**
3. **Document the problem**
4. **Wait for review**

---

## Key Principles

1. **Absolute Module Isolation**: Each module contains only its own code
2. **Firewall Protection**: Modules in MAIN_HUB are never edited directly
3. **Explicit Integration**: All updates go through merge script
4. **Data Layer Communication**: Modules interact only via database/API
5. **Technical Enforcement**: Architecture prevents cross-contamination

**Remember: The entire purpose is to make it technically impossible to accidentally modify module code in MAIN_HUB. If you can edit modules directly in MAIN_HUB, something is wrong - stop immediately.** 