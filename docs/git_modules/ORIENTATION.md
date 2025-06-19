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

---

## Directory Structure

### Source Branches
Each source branch contains:
- `modules/[module-name]/`: Complete module code
- `templates/`: Module-specific templates
- `static/`: Module-specific assets
- `README.md`: Module documentation

### MAIN_HUB Branch
- `modules/`: Imported modules (READ-ONLY)
- `app/`: Main Flask application
- `app/routes/workflow.py`: Integration code (EDITABLE)
- `app/templates/workflow/`: Integration templates (EDITABLE)

---

## Integration/Deployment

- When a module is ready, the merge script brings changes to MAIN_HUB
- MAIN_HUB is the only branch deployed/run as the live site
- Merges are explicit, reviewable, and controlled by the merge script
- Integration code ensures modules work together properly

---

## Inter-Module Communication

- All modules interact only via the data layer (database/API)
- No direct imports or code dependencies between modules
- Shared interfaces are defined in the integration code
- Modules are completely self-contained

---

## AI/Automation Safeguards

- The AI can only work in one module at a time
- The AI cannot change module code in MAIN_HUB without using the merge script
- The firewall rule prevents direct module editing
- All module updates must go through the controlled merge process

---

## Key Principle

**This architecture is designed to make it technically impossible for the AI (or anyone) to accidentally or implicitly change module code in MAIN_HUB. All module updates are explicit, reviewable, and controlled through the merge script.** 