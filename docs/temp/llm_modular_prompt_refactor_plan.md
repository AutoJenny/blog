# LLM Modular Prompt Refactor Plan

## Purpose
Track the plan and rationale for refactoring LLM prompt handling to support modular prompt parts (system, style, instructions, etc.) in LLM Actions and Prompts.

## Current State
- LLMAction links to a single LLMPrompt (prompt_template_id), which has a main prompt_text and an optional system_prompt.
- The UI and future workflow require modular prompt parts: system, style, instructions, and possibly more.
- Only one field (field_name) is used for both input and output, which is ambiguous.

## Problems
- Cannot select or assemble multiple prompt parts for an action.
- Cannot clearly specify both input and output fields for an action.
- No support for prompt part ordering or types beyond 'system'.

## Goals
- Add support for modular prompt parts (system, style, instructions, etc.)
- Allow LLMAction to reference multiple prompt parts, with order and type.
- Add explicit input_field and output_field to LLMAction for clarity.
- Update all code, UI, and docs to match.

## Proposed Model Changes
- New table: llm_prompt_part (id, type, content, description, tags, order, created_at, updated_at)
- Table: llm_action_prompt_part (action_id, prompt_part_id, order)
- LLMAction: add input_field, output_field
- LLMPrompt: may be deprecated or used for legacy/simple prompts

## Migration Steps
- Add new tables and fields via direct SQL in create_tables.sql
- Update models.py to match
- Update service layer to assemble prompts from parts
- Update API and UI to support modular prompt selection and preview
- Migrate existing prompt data to new structure (manual or script)

## Risks/Questions
- How to handle legacy actions/prompts? (Plan: support both for a transition period)
- Should prompt parts be global (reusable) or per-action? (Plan: global, reusable)
- How to handle prompt part ordering? (Use 'order' field in join table)

## References
- docs/llm/llm_framework_hybrid_refactor.md
- create_tables.sql
- app/models.py

## Progress
- [x] Backend: Models and schema for modular prompt parts
- [x] Backend: Service layer (assemble, execute, input/output fields)
- [x] Backend: API endpoints for CRUD and linking
- [ ] UI: Action Details page (display, edit, reorder prompt parts)
- [ ] UI: Prompt part CRUD and linking in Action Details
- [ ] UI: Test Action button and output display

## Next
- Scaffold and wire up Action Details UI to display and manage modular prompt parts, input/output fields, and test execution. 