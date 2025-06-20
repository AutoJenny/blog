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
| id           | SERIAL       | Primary key                                      |
| post_id      | INTEGER      | References post(id)                              |
| substage     | VARCHAR(64)  | Substage name                                    |
| action_id    | INTEGER      | References llm_action(id)                        |
| input_field  | VARCHAR(128) | **NEW**: Selected input field for this action    |
| output_field | VARCHAR(128) | **NEW**: Selected output field for this action   |
| button_label | TEXT         | Button label (optional)                          |
| button_order | INTEGER      | Button order (default 0)                         |

**2025-05-30:** Added `input_field` and `output_field` columns to `post_substage_action` for LLM workflow field persistence.

Example usage: Allows the UI to save and restore which LLM action is selected for a post's substage, and how it appears in the workflow editor.

### post_substage_action

- **PUT /api/v1/llm/post_substage_actions/<int:psa_id>**
  - Now supports updating `input_field` and `output_field` in addition to `button_label` and `button_order`.
  - Enables field persistence for workflow UI.

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

## Table: post_workflow_stage

Tracks the status and timing of each workflow stage for a post. As of 2025-06-10, supports LLM workflow field persistence at the stage level.

| Column        | Type         | Description                                      |
|--------------|--------------|--------------------------------------------------|
| id           | SERIAL       | Primary key                                      |
| post_id      | INTEGER      | References post(id)                              |
| stage_id     | INTEGER      | References workflow_stage_entity(id)             |
| started_at   | TIMESTAMP    | When this stage started                          |
| completed_at | TIMESTAMP    | When this stage completed                        |
| status       | VARCHAR(32)  | Status of the stage                              |
| input_field  | VARCHAR(128) | **NEW**: Selected input field for this stage     |
| output_field | VARCHAR(128) | **NEW**: Selected output field for this stage    |

**2025-06-10:** Added `input_field` and `output_field` columns to `post_workflow_stage` for robust LLM workflow field persistence at the stage level. See migration and restore notes below.

### Migration & Restore Notes
- Always make a full backup and save the current create_tables.sql before running this migration.
- If restoring a backup made before this change, use the matching create_tables.sql from the backup directory.
- If you need to bring restored data up to the new schema, run the migration SQL to add the new columns after restore. 

### 2025-06-01: Added `timeout` to llm_action
- Added `timeout INTEGER DEFAULT 60` to `llm_action` for per-action LLM request timeout. Update all schema, backup, and restore scripts accordingly.

## Table: llm_action

Stores LLM prompt/action templates. As of 2025-06, supports both legacy flat string templates and structured prompt part arrays.

| Column        | Type         | Description                                      |
|--------------|--------------|--------------------------------------------------|
| id           | SERIAL (PK)  | Unique row ID                                    |
| field_name   | VARCHAR(128) | Name of the action (UI/display)                  |
| prompt_template | TEXT      | Canonical prompt template (flat string)           |
| prompt_template_id | INTEGER | FK to llm_prompt(id)                             |
| llm_model    | VARCHAR(128) | Model name (e.g., 'llama3:latest')               |
| provider_id  | INTEGER      | FK to llm_provider(id)                           |
| temperature  | FLOAT        | Sampling temperature (default 0.7)                |
| max_tokens   | INTEGER      | Max tokens to generate (default 1000)             |
| order        | INTEGER      | Display order (default 0)                        |
| input_field  | VARCHAR(128) | Input field for this action (optional)           |
| output_field | VARCHAR(128) | Output field for this action (optional)          |
| timeout      | INTEGER      | **NEW**: Max seconds to wait for LLM response (default 60) |
| created_at   | TIMESTAMP    | Created timestamp                                |
| updated_at   | TIMESTAMP    | Updated timestamp                                |

- `prompt_json` stores an ordered array of objects, each with `type`, `tags`, and `content` (or `field` for data parts). See /docs/llm/llm_prompt_structuring.md for details.

### [2024-06-10] Workflow UI Field Persistence

- The workflow UI now loads and saves all input/output fields to the `post_development` table, and LLM action selections to the `post_substage_action` table, for each post and substage.
- This enables robust, permanent persistence of workflow state and makes the interface easily transferable to other stages/substages.
- See also: docs/frontend/templates.md for frontend details.

## Table: post_workflow_stage

Tracks the status and timing of each workflow stage for a post. As of 2025-06-10, supports LLM workflow field persistence at the stage level.

| Column        | Type         | Description                                      |
|--------------|--------------|--------------------------------------------------|
| id           | SERIAL       | Primary key                                      |
| post_id      | INTEGER      | References post(id)                              |
| stage_id     | INTEGER      | References workflow_stage_entity(id)             |
| started_at   | TIMESTAMP    | When this stage started                          |
| completed_at | TIMESTAMP    | When this stage completed                        |
| status       | VARCHAR(32)  | Status of the stage                              |
| input_field  | VARCHAR(128) | **NEW**: Selected input field for this stage     |
| output_field | VARCHAR(128) | **NEW**: Selected output field for this stage    |

**2025-06-10:** Added `input_field` and `output_field` columns to `post_workflow_stage` for robust LLM workflow field persistence at the stage level. See migration and restore notes below.

### Migration & Restore Notes
- Always make a full backup and save the current create_tables.sql before running this migration.
- If restoring a backup made before this change, use the matching create_tables.sql from the backup directory.
- If you need to bring restored data up to the new schema, run the migration SQL to add the new columns after restore. 