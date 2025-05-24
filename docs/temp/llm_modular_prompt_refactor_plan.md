# LLM Modular Prompt Refactor Plan

## Purpose
Track the plan and rationale for refactoring LLM prompt handling to support modular prompt parts (system, style, instructions, etc.) in LLM Actions and Prompts.

## Current State
- LLMAction links to a single LLMPrompt (prompt_template_id), which has a main prompt_text and an optional system_prompt.
- The UI and future workflow require modular prompt parts: system, style, instructions, and possibly more.
- Only one field (field_name) is used for both input and output, which is ambiguous.
- **[COMPLETED]** Models, services, and API endpoints now use direct SQL (psycopg2) only. All ORM usage has been removed.

## Problems
- Cannot select or assemble multiple prompt parts for an action.
- Cannot clearly specify both input and output fields for an action.
- No support for prompt part ordering or types beyond 'system'.
- **[RESOLVED]** ORM code was present, causing technical debt and inconsistency with project rules. Now fully removed.

## Goals
- Add support for modular prompt parts (system, style, instructions, etc.)
- Allow LLMAction to reference multiple prompt parts, with order and type.
- Add explicit input_field and output_field to LLMAction for clarity.
- Update all code, UI, and docs to match.
- **[COMPLETED]** Remove all SQLAlchemy/ORM usage and use direct SQL (psycopg2) for all LLM features.

## Proposed Model Changes
- New table: llm_prompt_part (id, type, content, description, tags, order, created_at, updated_at)
- Table: llm_action_prompt_part (action_id, prompt_part_id, order)
- LLMAction: add input_field, output_field
- LLMPrompt: may be deprecated or used for legacy/simple prompts

## Migration & Refactor Steps (Direct SQL)
1. **[COMPLETED]** Add new tables and fields via direct SQL in create_tables.sql
2. **[COMPLETED]** Update schema and migrate existing data as needed
3. **[COMPLETED]** Remove all SQLAlchemy and Flask-SQLAlchemy imports from the codebase
4. **[COMPLETED]** Rewrite all model classes as plain Python data classes or dicts (no ORM)
5. **[COMPLETED]** Refactor all service layer logic (app/llm/services.py) to use direct SQL (psycopg2) for all DB access:
    - Prompt part CRUD
    - Action CRUD
    - Prompt assembly and execution
    - History logging
6. **[COMPLETED]** Refactor all API endpoints (app/llm/routes.py, app/api/llm.py) to use direct SQL for all DB operations
7. **[IN PROGRESS]** Update all Jinja2 templates and JS to use the new API endpoints and data structures
8. **[COMPLETED]** Remove all ORM-based relationships, queries, and session management
9. **[IN PROGRESS]** Test all endpoints and UI flows with curl and browser to ensure no regressions
10. **[IN PROGRESS]** Update documentation and diagrams to reflect direct SQL usage and new patterns

## Risks/Questions
- How to handle legacy actions/prompts? (Plan: support both for a transition period)
- Should prompt parts be global (reusable) or per-action? (Plan: global, reusable)
- How to handle prompt part ordering? (Use 'order' field in join table)
- **[ONGOING]** Ensure all transactional logic and error handling is robust in direct SQL

## References
- docs/llm/llm_framework_hybrid_refactor.md
- create_tables.sql
- app/models.py (to be deprecated)
- app/llm/services.py
- app/llm/routes.py
- app/api/llm.py

## Progress
- [x] Backend: Models and schema for modular prompt parts
- [x] Backend: Service layer (assemble, execute, input/output fields)
- [x] Backend: API endpoints for CRUD and linking
- [ ] UI: Action Details page (display, edit, reorder prompt parts)
- [ ] UI: Prompt part CRUD and linking in Action Details
- [ ] UI: Test Action button and output display
- [x] Backend: Remove all ORM usage and switch to direct SQL for all LLM features

## Restore Progress (2025-05-23)
- Successfully performed a lossless restore of all post and action data from the most recent backup (blog_backup_20250523_082634.sql).
- All fields, including `idea_seed` and `substage_id`, are present and restored in the `post` table.
- Foreign key issues were resolved by restoring `workflow_stage_entity` and `workflow_sub_stage_entity` tables before restoring `post`.
- The `llm_action` table is restored and matches the backup.
- The `llm_prompt_part` table was empty in the backup, so no prompt part data was lost or skipped.
- The backend is now in a known-good state and ready for further modular prompt refactor work.

## Next Steps (Immediate)
- [x] Remove all SQLAlchemy/ORM imports and model definitions from app/models.py, app/__init__.py, and related files
- [x] Refactor app/llm/services.py to use direct SQL for all LLMAction, LLMPromptPart, and LLMActionPromptPart logic
- [x] Refactor app/llm/routes.py and app/api/llm.py to use direct SQL for all endpoints
- [ ] Test all LLM endpoints with curl to ensure correct behavior
- [ ] Update documentation and /docs/CHANGES.log after each major step
- [ ] Continue UI wiring for modular prompt part management

## Next
- Scaffold and wire up Action Details UI to display and manage modular prompt parts, input/output fields, and test execution. 