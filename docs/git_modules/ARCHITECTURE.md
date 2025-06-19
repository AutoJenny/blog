# Modular Architecture - Technical Implementation

## ⚠️ CRITICAL FIREWALL RULE ⚠️

**NEVER EDIT MODULES DIRECTLY IN MAIN_HUB BRANCH**

- Modules in MAIN_HUB are READ-ONLY and come from source branches via merge script
- Only integration code (Flask routes, imports) can be edited in MAIN_HUB
- Module development happens ONLY in source branches
- Any direct module edits in MAIN_HUB will be lost on next merge

---

## Architecture Overview

This document describes the technical implementation of the modular architecture for BlogForge. The system uses a source branch → merge script → integration branch pattern to ensure absolute module isolation, with a hybrid service layer for data access and template integration via Flask blueprints.

### Core Architecture

```
Source Branches (Development)
├── workflow-navigation    → Navigation module development
├── workflow-llm-actions   → LLM actions module development
└── workflow-sections      → Sections module development
                                    ↓
                              Merge Script
                                    ↓
Integration Branch (Deployment)
└── MAIN_HUB              → Live site with integrated modules
    ├── modules/nav/      (READ-ONLY)
    ├── modules/llm/      (READ-ONLY)
    ├── modules/sections/ (READ-ONLY)
    ├── app/routes/workflow.py (EDITABLE - Integration code)
    ├── app/services/shared.py (EDITABLE - Shared services)
    └── app/templates/workflow/ (EDITABLE - Integration templates)
```

---

## Technical Implementation

### Source Branch Structure

Each source branch contains a complete, self-contained module:

```
workflow-navigation/
├── modules/nav/
│   ├── __init__.py
│   ├── routes.py
│   ├── services.py
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       └── nav.html
├── app/routes/workflow.py (matches MAIN_HUB integration)
├── README.md
└── requirements.txt
```

### MAIN_HUB Integration Structure

The integration branch contains imported modules and integration code:

```
MAIN_HUB/
├── modules/              (READ-ONLY - Imported from source branches)
│   ├── nav/
│   ├── llm/
│   └── sections/
├── app/
│   ├── routes/
│   │   └── workflow.py   (EDITABLE - Integration code)
│   ├── services/
│   │   └── shared.py     (EDITABLE - Shared services)
│   ├── templates/
│   │   └── workflow/     (EDITABLE - Integration templates)
│   └── static/
├── merge_NAV_module.sh   (Merge script)
└── requirements.txt
```

---

## Hybrid Service Layer Pattern

### Shared Services (MAIN_HUB)
- **Location**: `app/services/shared.py`
- **Purpose**: Centralized database access and workflow logic
- **Functions**: `get_all_posts_from_db()`, `get_workflow_stages_from_db()`
- **Usage**: Used by all modules for consistent data access

### Module Services
- **Location**: `modules/[module]/services.py`
- **Pattern**: Import shared services when available, fallback to local logic
- **Fallback**: Demo data for standalone development
- **Integration**: MAIN_HUB integration code calls module service functions

### Service Layer Benefits
- **Consistency**: Same data access logic across all modules
- **Fallback Safety**: Modules work in both standalone and integrated modes
- **Single Source of Truth**: Shared services prevent data inconsistencies
- **Maintainability**: Centralized database logic

---

## Template Integration Pattern

### Flask Blueprint Integration
- **Module Blueprints**: Each module registers as a Flask blueprint
- **Template Includes**: MAIN_HUB templates include module templates via blueprint names
- **Example**: `{% include 'workflow_nav/nav.html' %}` includes nav module template
- **Separation**: MAIN_HUB controls layout, modules provide functionality

### Template Structure
```
MAIN_HUB Integration Template:
app/templates/workflow/index.html
├── Extends base.html
├── Includes workflow_nav/nav.html (nav module)
├── Includes llm_actions/llm_actions.html (LLM module)
└── Controls overall workflow layout

Module Template:
modules/nav/templates/nav.html
├── Self-contained navigation UI
├── Uses context from integration code
└── No knowledge of other modules
```

### Template Integration Benefits
- **Blueprint Resolution**: Flask properly resolves template paths
- **Context Sharing**: Integration code provides data to module templates
- **Layout Control**: MAIN_HUB controls overall page structure
- **Module Independence**: Modules don't know about each other

---

## Module Isolation Mechanisms

### 1. Physical Separation
- Modules exist in separate directories
- No shared code between modules
- Each module is self-contained

### 2. Import Control
- Modules are imported via merge script only
- No direct module editing in MAIN_HUB
- Integration code coordinates modules

### 3. Data Layer Communication
- Modules communicate only via database/API
- No direct code dependencies
- Shared interfaces defined in integration code

### 4. Service Layer Isolation
- Shared services in MAIN_HUB
- Module services import shared services when available
- Fallback to local logic in standalone mode

---

## Merge Script Process

### Automated Merge Process
1. **Source Branch Checkout**: Switch to source module branch
2. **Module Export**: Copy module to temporary location
3. **MAIN_HUB Integration**: Merge module into MAIN_HUB
4. **Cleanup**: Remove temporary files
5. **Return to MAIN_HUB**: Ensure proper branch state

### Safety Features
- Automatic conflict detection
- Rollback on failure
- Logging of all operations
- Verification of module boundaries

---

## Integration Code Responsibilities

### `app/routes/workflow.py`
- **Module Coordination**: Import and initialize modules
- **Data Provision**: Provide data to modules from database via service layer
- **Template Rendering**: Coordinate template rendering
- **State Management**: Handle workflow state transitions

### `app/services/shared.py`
- **Database Access**: Centralized database connection and queries
- **Data Consistency**: Ensure consistent data across all modules
- **Error Handling**: Robust error handling and fallback logic

### `app/templates/workflow/index.html`
- **Layout Control**: Define overall workflow page structure
- **Module Integration**: Include module templates via blueprint names
- **Context Provision**: Provide data context to module templates

### Forbidden in Integration Code
- Direct module code implementation
- Module-specific business logic
- Cross-module code sharing
- Module internals modification

---

## Data Layer Architecture

### Database Tables (Shared)
- `workflow_stages`: Stage definitions
- `workflow_sub_stages`: Substage definitions
- `workflow_step_entity`: Step data
- `llm_actions`: Action definitions
- `posts`: Post data
- `post_sections`: Section data

### API Endpoints (Shared)
- `/workflow/`: Main workflow endpoint
- `/api/llm/`: LLM API endpoints
- `/api/posts/`: Post management endpoints

---

## Development Workflow

### Module Development (Source Branches)
1. **Checkout source branch**: `git checkout workflow-navigation`
2. **Develop module**: Work only on module code
3. **Test isolation**: Ensure no cross-module code
4. **Commit changes**: Save module updates
5. **Use merge script**: Update MAIN_HUB

### Integration Development (MAIN_HUB)
1. **Edit integration code**: Only `app/routes/workflow.py`, `app/services/shared.py`
2. **Edit integration templates**: Only `app/templates/workflow/`
3. **Test integration**: Verify modules work together
4. **Document changes**: Update integration docs
5. **Never touch modules**: Modules are READ-ONLY

---

## Firewall Enforcement

### Technical Safeguards
- **File Permissions**: Modules in MAIN_HUB are READ-ONLY
- **Merge Script**: Only way to update modules
- **Branch Protection**: Source branches protected
- **Code Review**: All changes reviewed

### Process Safeguards
- **Source Development**: Modules developed in source branches only
- **Merge Process**: All updates go through merge script
- **Testing**: Complete testing after each merge
- **Documentation**: All changes documented

---

## Emergency Procedures

### Module Contamination
1. **Stop immediately**: Cease all work
2. **Document issue**: Record what happened
3. **Reset to clean state**: Use git reset
4. **Seek review**: Get approval before proceeding

### Integration Issues
1. **Revert changes**: Go back to working state
2. **Check logs**: Review merge script output
3. **Document problem**: Record the issue
4. **Wait for review**: Get guidance before fixing

---

## Key Technical Principles

1. **Absolute Isolation**: Modules contain only their own code
2. **Firewall Protection**: Modules in MAIN_HUB are never edited directly
3. **Explicit Integration**: All updates go through controlled process
4. **Data Layer Communication**: Modules interact only via database/API
5. **Service Layer Consistency**: Shared services ensure data consistency
6. **Template Integration**: Blueprint-based template includes
7. **Technical Enforcement**: Architecture prevents cross-contamination

---

## Implementation Checklist

### For Each Module
- [ ] Module is self-contained
- [ ] No cross-module dependencies
- [ ] Uses service layer for data access
- [ ] Has clear integration points
- [ ] Follows module boundaries
- [ ] Template uses blueprint registration

### For Integration
- [ ] Integration code coordinates modules
- [ ] No direct module editing
- [ ] Complete testing after merges
- [ ] Documentation updated
- [ ] Firewall rules followed
- [ ] Service layer properly implemented
- [ ] Template includes use blueprint names

---

## Success Metrics

- **Zero Cross-Contamination**: No module code in other modules
- [ ] Firewall Integrity: No direct module editing in MAIN_HUB
- [ ] Clean Merges: All merges complete successfully
- [ ] Working Integration: All modules work together properly
- [ ] Clear Boundaries: Module responsibilities are well-defined
- [ ] Service Layer Consistency: All modules use shared services
- [ ] Template Integration: Module templates properly included

**Remember: The entire purpose is to make it technically impossible to accidentally modify module code in MAIN_HUB. If you can edit modules directly in MAIN_HUB, something is wrong - stop immediately.**

# Modular Service Layer Architecture

## Hybrid Service Layer Pattern

- Shared services for DB access and workflow logic are defined in MAIN_HUB (`app/services/shared.py`).
- Module-specific services (e.g., `modules/nav/services.py`) import and use these shared services when available.
- If MAIN_HUB is not present, modules fall back to local demo data for standalone development.

## Integration
- MAIN_HUB integration code (e.g., `app/routes/workflow.py`) must always call module service functions for data access and mutation.
- This ensures a single source of truth and consistent behavior in both standalone and integrated modes.

## Fallback Logic
- If shared services are not importable, modules use fallback demo data for posts and workflow stages.

## Testing
- Test `/workflow/` for MAIN_HUB integration (should show real DB posts).
- Test `/modules/nav/` for standalone mode (should show demo data if MAIN_HUB is not present, or real data if integrated).

## Rationale
- This approach balances modularity, maintainability, and robust integration.
- It avoids circular imports and ensures modules can be developed and tested independently.

---

_Last updated: [date]_ 