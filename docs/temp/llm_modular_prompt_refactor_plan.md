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

## API Refactor Progress
- [x] Refactor /api/v1/llm/prompt_parts and /prompt_parts/<id> endpoints to use direct SQL
- [x] Refactor /api/v1/llm/actions and /actions/<id> endpoints to use direct SQL (robust, tested, returns correct JSON)
- [x] Refactor /api/v1/llm/actions/<id>/prompt_parts and linking endpoints to use direct SQL (robust, tested, supports linking/unlinking)
- [x] Refactor /api/v1/llm/actions/<id>/execute endpoint to use direct SQL (robust, ORM-free, returns dummy response for now)
- [x] Test all endpoints with curl to ensure correct behavior (all endpoints robust, ORM-free, and tested end-to-end)

## UI Progress
- [ ] UI: Action Details page (display, edit, reorder prompt parts)
- [ ] UI: Prompt part CRUD and linking in Action Details
- [ ] UI: Test Action button and output display

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
- [x] Refactor /api/v1/llm/prompt_parts endpoints to use direct SQL
- [x] Refactor /api/v1/llm/actions and linking endpoints to use direct SQL
- [x] Test all LLM endpoints with curl to ensure correct behavior
- [x] Update documentation and /docs/CHANGES.log after each major step
- [ ] Continue UI wiring for modular prompt part management

## Next
- Scaffold and wire up Action Details UI to display and manage modular prompt parts, input/output fields, and test execution. 