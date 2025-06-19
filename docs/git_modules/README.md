# Modular Architecture Project

## ⚠️ CRITICAL FIREWALL RULE ⚠️

**NEVER EDIT MODULES DIRECTLY IN MAIN_HUB BRANCH**

- **Modules in MAIN_HUB are READ-ONLY** - they come from their source branches via merge script
- **Only integration code** (Flask routes, imports, etc.) can be edited in MAIN_HUB
- **Module development** happens ONLY in their source branches (workflow-navigation, etc.)
- **Any direct module edits in MAIN_HUB will be lost** on next merge

**VIOLATION = IMMEDIATE ROLLBACK**

## Core Principles and Rules

This project implements a strict modular architecture where each module exists as a self-contained directory, integrated into the main site via controlled merges. The primary goals are:

1. **Absolute Module Isolation**: Each module contains ONLY its own code, with no cross-contamination
2. **Firewall Protection**: Modules in MAIN_HUB are never edited directly
3. **Explicit Integration**: All module updates happen through the merge script from source branches
4. **Technical Enforcement**: Module separation is enforced by the merge process and file structure

## MANDATORY Rules (No Exceptions)

1. **NEVER** edit files in `modules/` directories in MAIN_HUB branch
2. **ALWAYS** develop modules in their source branches (workflow-navigation, etc.)
3. **NEVER** copy code between modules
4. **ALWAYS** use the merge script to update modules in MAIN_HUB
5. **NEVER** bypass the merge process
6. **ALWAYS** test integration code in MAIN_HUB after merges
7. **NEVER** share templates or JS between modules
8. **ALWAYS** document all merge operations
9. **NEVER** modify module internals in MAIN_HUB
10. **ALWAYS** wait for merge script completion before testing

## Current Architecture

1. **Module Source Branches** (Development)
   - `workflow-navigation`: Navigation module development
   - `workflow-llm-actions`: LLM actions module development
   - `workflow-sections`: Sections module development

2. **Integration Branch**
   - `MAIN_HUB`: Contains integrated, deployable system
   - Modules are imported via merge script
   - Only integration code is edited here

3. **Module Structure in MAIN_HUB**
   - `modules/nav/`: Navigation module (READ-ONLY)
   - `modules/llm/`: LLM actions module (READ-ONLY)
   - `modules/sections/`: Sections module (READ-ONLY)
   - `app/routes/workflow.py`: Integration code (EDITABLE)

## Getting Started

1. First, read this README completely
2. Review [ORIENTATION.md](ORIENTATION.md) for architecture overview
3. Study [code_mapping.md](code_mapping.md) for module boundaries
4. **VERIFY** you understand the firewall rule

## Workflow Process

1. **Module Development** (MANDATORY)
   - Work ONLY in source module branch
   - Follow code_mapping.md strictly
   - Remove any cross-module code
   - **DO NOT PROCEED** if other module code found

2. **Integration** (MANDATORY)
   - Use merge script to bring changes to MAIN_HUB
   - Verify module is properly integrated
   - Test all endpoints and functionality
   - **DO NOT PROCEED** without complete testing

3. **Maintenance** (MANDATORY)
   - Edit only integration code in MAIN_HUB
   - Never touch module internals
   - Use merge script for all module updates
   - **DO NOT PROCEED** without following process

## Module Independence

Each module must:
1. Contain only its own code
2. Use only the shared data/API layer
3. Have no direct dependencies on other modules
4. Maintain its own templates and assets
5. Be deployable in isolation

## Technical Safeguards

1. **Firewall Protection**
   - Modules in MAIN_HUB are READ-ONLY
   - Only integration code is editable
   - Merge script enforces separation
   - No direct module editing allowed

2. **Code Isolation**
   - No shared templates or JS
   - Only CSS/config in base framework
   - Explicit API boundaries
   - No cross-module imports

3. **Integration Control**
   - Merge script only
   - Complete testing required
   - Documented changes
   - Explicit approval needed

## Emergency Procedures

1. **Module Contamination**
   - Stop all work immediately
   - Document the contamination
   - Reset to last clean merge
   - **DO NOT ATTEMPT FIXES** without review

2. **Integration Issues**
   - Revert to last working state
   - Document the problem
   - Check merge script logs
   - **DO NOT FORCE** module edits

3. **Data Layer Problems**
   - Document the issue
   - Test in isolation
   - Wait for review
   - **DO NOT MODIFY** shared interfaces

## Important Reminders

1. **NEVER**:
   - Edit modules in MAIN_HUB
   - Skip merge process
   - Modify multiple modules at once
   - Assume module isolation
   - Bypass firewall rules
   - Share code between modules
   - Make direct module changes
   - Force module edits
   - Skip integration tests
   - Merge without review

2. **ALWAYS**:
   - Use source branches for development
   - Use merge script for updates
   - Test integration code
   - Get explicit review
   - Follow merge process
   - Document all changes
   - Check for contamination
   - Use data layer only
   - Wait for approval
   - Maintain firewall rules

## Getting Help

1. **Documentation**
   - Review ORIENTATION.md
   - Check code_mapping.md
   - Consult ARCHITECTURE.md
   - **DO NOT PROCEED** without understanding

2. **Issues**
   - Document the problem
   - Identify affected modules
   - Wait for review
   - **DO NOT ATTEMPT FIXES** without approval

3. **Questions**
   - Review all documentation first
   - Ask about specific module/branch
   - Wait for explicit guidance
   - **DO NOT MAKE ASSUMPTIONS**

Remember: The entire purpose of this architecture is to make it **technically impossible** to accidentally modify module code in MAIN_HUB. If you find yourself able to edit modules directly in MAIN_HUB, something is wrong - stop immediately and seek review.

# Modular Git Modules: Service Layer Pattern

This project uses a hybrid service layer pattern for robust modularity and integration.

- Shared services for DB access and workflow logic are defined in MAIN_HUB (`app/services/shared.py`).
- Module-specific services (e.g., `modules/nav/services.py`) import and use these shared services when available, or fallback to demo data in standalone mode.
- MAIN_HUB integration code must always call module service functions for data access and mutation.

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.

---

_Last updated: [date]_ 