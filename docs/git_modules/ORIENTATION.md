# Modular Architecture Orientation

## Purpose
This document defines the strict modular architecture for BlogForge workflow development. Its primary goal is to ensure robust, reviewable, and technically enforced separation between major UI modules, preventing accidental or unauthorized code changes across module boundaries—especially by AI automation. This orientation is the canonical reference for all contributors and AI agents to stay on track and avoid cross-contamination.

---

## ⚠️ CRITICAL FIREWALL RULE ⚠️

**NEVER EDIT MODULES DIRECTLY IN MAIN_HUB BRANCH**

- Modules in MAIN_HUB are READ-ONLY and come from source branches via merge script
- Only integration code (Flask routes, imports) can be edited in MAIN_HUB
- Module development happens ONLY in source branches
- Any direct module edits in MAIN_HUB will be lost on next merge

---

## What We Are Trying to Accomplish

- **Absolute separation** of UI modules (Navigation, LLM-Actions, Sections) into distinct, self-contained directories
- **No code for other modules** present in any module—only the code for that module exists
- **Firewall protection**: Modules in MAIN_HUB are never edited directly
- **Explicit integration**: All module updates happen through the merge script from source branches
- **Impossible for AI or developers to change modules** in MAIN_HUB without using the merge script
- **All inter-module communication** must be via the data layer (database/API) or explicit shared interfaces
- **Service layer consistency**: Shared services in MAIN_HUB provide consistent data access
- **Template integration**: Flask blueprint-based template includes for proper module integration

---

## Current Architecture

### Source Branches (Development)
- `workflow-navigation`: Contains only the navigation module code
- `workflow-llm-actions`: Contains only the LLM-Actions module code  
- `workflow-sections`: Contains only the Sections module code

### Integration Branch
- `MAIN_HUB`: The integration branch containing the live site
- Modules are imported via merge script from source branches
- Only integration code is edited here

### Module Structure in MAIN_HUB
- `modules/nav/`: Navigation module (READ-ONLY)
- `modules/llm/`: LLM actions module (READ-ONLY)
- `modules/sections/`: Sections module (READ-ONLY)
- `app/routes/workflow.py`: Integration code (EDITABLE)
- `app/services/shared.py`: Shared services (EDITABLE)
- `app/templates/workflow/`: Integration templates (EDITABLE)

---

## Service Layer Pattern

### Shared Services (MAIN_HUB)
- **Location**: `app/services/shared.py`
- **Purpose**: Centralized database access and workflow logic
- **Functions**: `get_all_posts_from_db()`, `get_workflow_stages_from_db()`
- **Usage**: All modules import and use these services when available

### Module Services
- **Pattern**: Import shared services when available, fallback to local logic
- **Fallback**: Demo data for standalone development
- **Integration**: MAIN_HUB integration code calls module service functions

### Benefits
- **Consistency**: Same data access logic across all modules
- **Fallback Safety**: Modules work in both standalone and integrated modes
- **Single Source of Truth**: Shared services prevent data inconsistencies

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

---

## Directory Structure

### Source Branches
Each source branch contains:
- `modules/[module-name]/`: Complete module code
- `templates/`: Module-specific templates
- `static/`: Module-specific assets
- `README.md`: Module documentation
- `app/routes/workflow.py`: Integration code (matches MAIN_HUB)

### MAIN_HUB Branch
- `modules/`: Imported modules (READ-ONLY)
- `app/`: Main Flask application
- `app/routes/workflow.py`: Integration code (EDITABLE)
- `app/services/shared.py`: Shared services (EDITABLE)
- `app/templates/workflow/`: Integration templates (EDITABLE)

---

## Integration/Deployment

- When a module is ready, the merge script brings changes to MAIN_HUB
- MAIN_HUB is the only branch deployed/run as the live site
- Merges are explicit, reviewable, and controlled by the merge script
- Integration code ensures modules work together properly
- Service layer provides consistent data access across all modules
- Template integration uses Flask blueprint includes

---

## Inter-Module Communication

- All modules interact only via the data layer (database/API)
- No direct imports or code dependencies between modules
- Shared interfaces are defined in the integration code
- Modules are completely self-contained
- Service layer provides consistent data access
- Template integration uses blueprint names

---

## AI/Automation Safeguards

- The AI can only work in one module at a time
- The AI cannot change module code in MAIN_HUB without using the merge script
- The firewall rule prevents direct module editing
- All module updates must go through the controlled merge process
- Service layer ensures consistent data access
- Template integration prevents cross-module template dependencies

---

## Key Principle

**This architecture is designed to make it technically impossible for the AI (or anyone) to accidentally or implicitly change module code in MAIN_HUB. All module updates are explicit, reviewable, and controlled through the merge script. The service layer and template integration patterns ensure consistency and proper separation of concerns.**

---

_Last updated: 2024-12-19_ 