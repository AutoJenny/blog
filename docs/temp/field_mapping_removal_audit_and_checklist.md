# Field Mapping Removal Audit & Implementation Checklist

IMPORTANT: you MUST NOT change any other code or data beyond the specific task we are working on. NO extra refactoring, no assumptions, no “helpful” changes outside the agreed scope. Seek permission for any coding beyond the strict scope of this task.


**Purpose:**
Strictly guide the process of removing the field mapping system and switching to direct use of step names for all workflow/LLM actions. No changes are to be made outside the items listed here. This document must be reviewed and approved by the user before any implementation begins.

---

## 1. Audit: Where Field Mapping Is Used

### A. Templates/UI
- `app/templates/settings/workflow_field_mapping.html` (current field mapping UI)
- `backups/settings_json_viewer/settings/workflow_field_mapping.html` (previous step management UI)
- Any other settings or workflow-related templates referencing field mapping, field_name, or display_name

### B. Backend Python Code
- `app/routes/settings.py` (routes for workflow_field_mapping, step loading, etc.)
- `app/api/workflow/routes.py` (API endpoints for field mapping management)
- `app/workflow/scripts/llm_processor.py` (functions: load_field_mappings, process_writing_step, etc.)
- `app/workflow/scripts/prompt_constructor.py` (input/output mapping logic)
- `app/workflow/routes.py` (step config, field_mapping in step_config, etc.)
- Any other scripts or modules referencing field mapping, field_name, or display_name

### C. Database & Migrations
- Table: `workflow_field_mapping`
- Migrations: 
  - `migrations/20250104_add_workflow_field_mapping.sql`
  - `migrations/20250104_update_workflow_field_mapping.sql`
  - `migrations/20240624_create_workflow_field_mapping.sql`
  - `migrations/20250607_remove_workflow_field_mapping.sql`
  - Any other related migration files
- Data: Any references to field_name/display_name in `workflow_step_entity.config` or related tables

### D. JavaScript
- `app/static/js/llm.js` (fetchFieldMappings, etc.)
- Any other JS files handling field mapping or step/field selection

### E. Documentation
- `docs/temp/llm_response_standardization_and_universal_mapping.md`
- `docs/temp/field_selection_analysis.md`
- Any other docs referencing field mapping or field_name/display_name

---

## 2. Implementation Checklist (To Be Approved Before Work)

### A. Remove Field Mapping UI & Logic
- [ ] Remove or archive `app/templates/settings/workflow_field_mapping.html` (replace with step-centric UI)
- [ ] Restore previous step management UI (grouped listing, DND, renaming) from backup if available
- [ ] Remove all field mapping controls, dropdowns, and references from settings UI

### B. Backend Refactor
- [ ] Remove all field mapping API endpoints and logic from `app/api/workflow/routes.py`
- [ ] Remove field mapping loading and processing from `app/workflow/scripts/llm_processor.py` and related scripts
- [ ] Refactor prompt construction and LLM input/output handling to use step names directly
- [ ] Update `app/routes/settings.py` to load and display steps by name/order only

### C. Database Cleanup
- [ ] Drop or archive the `workflow_field_mapping` table (after backup)
- [ ] Remove all field_name/display_name references from `workflow_step_entity.config` and related data
- [ ] Remove or archive all related migration files

### D. JavaScript Cleanup
- [ ] Remove all JS code for field mapping UI, AJAX, and API calls
- [ ] Restore or update JS for step-centric management (DND, renaming, etc.)

### E. Documentation
- [ ] Update or archive all docs referencing field mapping
- [ ] Add a summary of the new, simplified step-centric approach

### F. Testing
- [ ] Test all settings and workflow management UIs for correct step listing, renaming, and ordering
- [ ] Test LLM prompt construction and response handling for all steps (using step names only)
- [ ] Test database for absence of field mapping data and correct step data usage

---

**No changes will be made until this checklist is reviewed and approved by the user.** 