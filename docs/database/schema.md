# Database Schema Reference

> **SAFETY WARNING:**
> Always make a full backup using `pg_dump` before running `create_tables.sql`. Never run this script on production or important data without a backup and a tested restore plan. Restore data as needed after schema changes.

The Blog CMS uses PostgreSQL (or SQLite in dev) for all persistent storage. Below is an overview of the main tables and their relationships.

## Main Tables
- **post**: Stores blog post content and metadata
- **media**: Stores image and file metadata
- **llm_action**: Stores LLM prompt/action templates
- **workflow**: Tracks workflow stage and status for each post
- **user**: (if present) Stores user data (currently not used; see notes)
- **other tables**: As defined in `create_tables.sql` and SQLAlchemy models

## Relationships
- Posts reference workflow entries via `workflow.post_id` (FK to `post.id`)
- Posts may reference media (images) and LLM actions
- Foreign keys are used for referential integrity

## Workflow Table
- **workflow**: Tracks the current stage and status for each post's development
  - `id`: Primary key
  - `post_id`: Foreign key to `post.id`
  - `stage`: ENUM, one of: idea, research, structure, content, meta_information, images, preflight, publishing, syndication
  - `status`: ENUM, one of: draft, published, review, deleted
  - `created`: Timestamp (default: now)
  - `updated`: Timestamp (auto-updated)

## Management 
- Schema is managed via `create_tables.sql` and direct SQL
- No migration tool is used for this table; direct SQL is preferred

## See Also
- [Direct SQL Management](sql_management.md)
- [Database Models](README.md)

## Workflow Stages (Normalized)

- **workflow_stage_entity**: Canonical list of main workflow stages (planning, authoring, publishing), each with a unique order.
- **workflow_sub_stage_entity**: Ordered sub-stages for each main stage, referencing workflow_stage_entity by FK.

### Example Structure

| Stage      | Sub-Stages                        |
|------------|-----------------------------------|
| planning   | idea, research, structure         |
| authoring  | content, meta_info, images        |
| publishing | preflight, launch, syndication    |

All workflow logic should reference these tables for stage and sub-stage lists, not hard-coded values.

## Table: post_substage_action

Tracks LLM action button settings for each post and workflow substage. Used to store which LLM action is selected for a given substage of a post, and the button label/order for the UI.

| Column        | Type         | Description                                      |
|--------------|--------------|--------------------------------------------------|
| id           | SERIAL (PK)  | Unique row ID                                    |
| post_id      | INTEGER      | References post(id)                              |
| substage     | VARCHAR(64)  | Name of the workflow substage (e.g. 'idea')      |
| action_id    | INTEGER      | References llm_action(id)                        |
| button_label | TEXT         | Label for the action button                      |
| button_order | INTEGER      | Order for button display (default 0)             |

Example usage: Allows the UI to save and restore which LLM action is selected for a post's substage, and how it appears in the workflow editor.

## Table: workflow_field_mapping

Maps post development fields to workflow stages and substages for UI and workflow logic. Used by the Settings panel to configure which field appears in which stage/substage, and in what order.

| Column      | Type         | Description                                      |
|------------|--------------|--------------------------------------------------|
| id         | SERIAL (PK)  | Unique row ID                                    |
| field_name | TEXT         | Name of the post development field               |
| stage_id   | INTEGER      | FK to workflow_stage_entity                      |
| substage_id| INTEGER      | FK to workflow_sub_stage_entity                  |
| order_index| INTEGER      | Order for display (default 0)                    |

This table is managed via the Settings panel at `/settings` and is used to dynamically control the workflow field mapping.

**Note:** The Settings panel now displays all fields from the `post_development` table (except `id` and `post_id`), including those not yet mapped. Unmapped fields will appear as available for mapping to any workflow stage/substage.

**Update (2024-06):**
- The workflow UI input/output dropdowns are now populated from the `post_development` table fields for the current post (via `/api/v1/post/<post_id>/development`), not from the `post` table. This ensures all workflow actions operate on the correct set of development fields.

## Live Field Mapping Table

The current mapping of fields to workflow stages/substages is shown below. This table is dynamically generated from the database and can be managed in the [Settings Panel](/settings).

[View Live Mapping Table](/docs/view/database/schema.md)

### 2024-05-28: Added provider_id to llm_action
- Added `provider_id INTEGER NOT NULL REFERENCES llm_provider(id)` to `llm_action`.
- Migration performed with full backup, SQL migration script, and verification.
- Rationale: Enables explicit separation of LLM provider and model for robust multi-provider support.

- 2024-05-28: The /actions/<id>/test endpoint was updated to always use the latest prompt template from llm_prompt, not the action's stored copy. This guarantees test/preview consistency and prevents stale prompt bugs.

## Table: llm_prompt

Stores prompt templates for LLM actions. As of 2024-06, supports both legacy flat string templates and structured prompt part arrays.

| Column        | Type         | Description                                      |
|--------------|--------------|--------------------------------------------------|
| id           | SERIAL (PK)  | Unique row ID                                    |
| name         | TEXT         | Name of the prompt template                      |
| prompt_text  | TEXT         | Legacy flat string template (for display/compat) |
| prompt_json  | JSONB        | (2024-06) Structured prompt parts array for advanced LLM prompt engineering. Nullable for backward compatibility. |
| ...          | ...          | ...                                              |

- `prompt_json` stores an ordered array of objects, each with `type`, `tags`, and `content` (or `field` for data parts). See /docs/llm/llm_prompt_structuring.md for details.

### [2024-06-10] Workflow UI Field Persistence

- The workflow UI now loads and saves all input/output fields to the `post_development` table, and LLM action selections to the `post_substage_action` table, for each post and substage.
- This enables robust, permanent persistence of workflow state and makes the interface easily transferable to other stages/substages.
- See also: docs/frontend/templates.md for frontend details. 