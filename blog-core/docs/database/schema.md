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

## Section Synchronization System

The system uses a dual-field architecture to manage section data with automatic synchronization:

### Dual-Field Architecture

#### 1. post_development.section_headings (Master Field)
- **Purpose**: Master list of all section headings for a post
- **Usage**: LLM actions, workflow planning, and overall post structure
- **Format**: JSON array containing structured section data
- **Authority**: Primary source of truth for section structure

#### 2. post_section.section_heading (Individual Field)
- **Purpose**: Individual section heading for UI display and management
- **Usage**: Green sections module, accordion display, drag-and-drop reordering
- **Format**: Simple text string for each section
- **Authority**: Derived from master field, used for UI interactions

### Synchronization Strategy

#### Primary Direction: post_development → post_section
- **Trigger**: Any update to `post_development.section_headings`
- **Action**: Automatically sync to individual `post_section` records
- **Purpose**: Ensure UI sections reflect the master planning data

#### Secondary Direction: post_section → post_development (Optional)
- **Trigger**: When individual sections are created/updated/deleted
- **Action**: Update the master list to reflect actual section data
- **Purpose**: Keep planning data in sync with actual implementation

### Data Format Standards

#### Recommended JSON Format for section_headings
```json
[
  {
    "order": 1,
    "heading": "Introduction",
    "description": "Overview of the topic",
    "status": "draft"
  },
  {
    "order": 2,
    "heading": "Main Content",
    "description": "Core discussion points",
    "status": "in_progress"
  },
  {
    "order": 3,
    "heading": "Conclusion",
    "description": "Summary and takeaways",
    "status": "complete"
  }
]
```

#### Legacy Format Support
The system supports multiple formats during transition:
- **Simple Array**: `["Section 1", "Section 2", "Section 3"]`
- **Delimited String**: `"Section 1\nSection 2\nSection 3"`
- **Numbered Format**: `"1. Section 1\n2. Section 2"`

### Database Triggers

The synchronization is implemented using PostgreSQL triggers:

#### Primary Sync Trigger (post_development → post_section)
```sql
-- Trigger function for post_development.section_headings changes
CREATE OR REPLACE FUNCTION sync_section_headings_to_sections()
RETURNS TRIGGER AS $$
-- ... trigger implementation ...
$$ LANGUAGE plpgsql;

-- Trigger on post_development updates
CREATE TRIGGER trigger_sync_section_headings
    AFTER UPDATE OF section_headings ON post_development
    FOR EACH ROW
    EXECUTE FUNCTION sync_section_headings_to_sections();
```

#### Secondary Sync Trigger (post_section → post_development) - Optional
```sql
-- Trigger function for post_section changes
CREATE OR REPLACE FUNCTION sync_sections_to_section_headings()
RETURNS TRIGGER AS $$
-- ... trigger implementation ...
$$ LANGUAGE plpgsql;

-- Triggers for post_section changes
CREATE TRIGGER trigger_sync_sections_to_headings_insert
    AFTER INSERT ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();
```

### Manual Synchronization API

The system provides a manual sync endpoint for troubleshooting and bulk operations:

```http
POST /api/workflow/posts/{post_id}/sync-sections
```

**Parameters**:
- `direction` (string, optional): Sync direction
  - `"to_sections"`: Sync from post_development to post_section only
  - `"to_development"`: Sync from post_section to post_development only
  - `"both"`: Sync both directions (default)

For complete documentation, see [Section Synchronization System](../reference/workflow/section_synchronization.md).

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
- [Section Synchronization System](../reference/workflow/section_synchronization.md)

## Workflow Stages (Normalized)

- **workflow_stage_entity**: Canonical list of main workflow stages (planning, authoring, publishing), each with a unique order.
- **workflow_sub_stage_entity**: Ordered sub-stages for each main stage, referencing workflow_stage_entity by FK.
- **workflow_step_entity**: Individual steps within each sub-stage, with field mappings stored in the config JSON field.

### Example Structure

```sql
-- workflow_stage_entity
id          SERIAL PRIMARY KEY
name        VARCHAR(100) NOT NULL
description TEXT
stage_order INTEGER NOT NULL

-- workflow_sub_stage_entity
id             SERIAL PRIMARY KEY
stage_id       INTEGER REFERENCES workflow_stage_entity(id)
name           VARCHAR(100) NOT NULL
description    TEXT
sub_stage_order INTEGER NOT NULL

-- workflow_step_entity
id             SERIAL PRIMARY KEY
sub_stage_id   INTEGER REFERENCES workflow_sub_stage_entity(id)
name           VARCHAR(100) NOT NULL
description    TEXT
step_order     INTEGER NOT NULL
config         JSONB -- Contains input/output field mappings
```

### Field Mapping Configuration

The `config` field in `workflow_step_entity` uses this JSON structure:
```json
{
  "inputs": {
    "input1": {
      "label": "Input Field Label",
      "db_field": "database_field_name",
      "type": "text|textarea"
    }
  },
  "outputs": {
    "output1": {
      "label": "Output Field Label",
      "db_field": "database_field_name",
      "type": "text|textarea"
    }
  }
}
```

This configuration drives the workflow UI, determining which database fields are used for inputs and outputs at each step.

## Table: post_workflow_step_action

Tracks LLM action button settings for each post and workflow step. Used to store which LLM action is selected for a given step of a post, and the button label/order for the UI.

| Column        | Type         | Description                                      |
|--------------|--------------|--------------------------------------------------|
| id           | SERIAL       | Primary key                                      |
| post_id      | INTEGER      | References post(id)                              |
| step_id      | INTEGER      | References workflow_step_entity(id)              |
| action_id    | INTEGER      | References llm_action(id)                        |
| input_field  | VARCHAR(128) | Selected input field for this action             |
| output_field | VARCHAR(128) | Selected output field for this action            |
| button_label | TEXT         | Button label (optional)                          |
| button_order | INTEGER      | Button order (default 0)                         |

**2024-06-11:** Table renamed from post_substage_action to post_workflow_step_action. Now references workflow_step_entity (step_id) instead of substage. All LLM workflow actions are now step-based for maximum granularity and future extensibility.

Example usage: Allows the UI to save and restore which LLM action is selected for a post's step, and how it appears in the workflow editor.

### post_workflow_step_action

- **PUT /api/v1/llm/post_workflow_step_actions/<int:pws_id>**
  - Supports updating `input_field`, `output_field`, `button_label`, and `button_order`.
  - Enables field persistence for workflow UI at the step level.

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

- The workflow UI now loads and saves all input/output fields to the `post_development` table, and LLM action selections to the `post_workflow_step_action` table, for each post and step.
- This enables robust, permanent persistence of workflow state and makes the interface easily transferable to other steps/stages.
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

- The workflow UI now loads and saves all input/output fields to the `post_development` table, and LLM action selections to the `post_workflow_step_action` table, for each post and step.
- This enables robust, permanent persistence of workflow state and makes the interface easily transferable to other steps/stages.
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

## Table: workflow_step_entity

Canonical list of steps for each workflow sub-stage. Each step belongs to a sub-stage and is ordered. Used for fine-grained workflow navigation and UI logic.

| Column                    | Type         | Description                                      |
|--------------------------|--------------|--------------------------------------------------|
| id                       | SERIAL (PK)  | Unique row ID                                    |
| sub_stage_id             | INTEGER      | FK to workflow_sub_stage_entity(id)              |
| name                     | VARCHAR(100) | Step name (e.g., 'Main')                         |
| description              | TEXT         | Step description                                 |
| step_order               | INTEGER      | Order for display (default 1)                    |
| config                   | JSONB        | Contains input/output field mappings             |
| field_name               | TEXT         | Legacy field mapping (deprecated)                |
| order_index              | INTEGER      | Legacy order mapping (deprecated)                |
| default_input_format_id  | INTEGER      | **NEW**: FK to workflow_format_template(id) for default input format |
| default_output_format_id | INTEGER      | **NEW**: FK to workflow_format_template(id) for default output format |

- **UNIQUE(sub_stage_id, name)**: Ensures no duplicate step names within a sub-stage.
- Used by the workflow navigation system to allow multiple steps per sub-stage (future extensibility).
- All workflow navigation and seeding scripts must reference this table for step data.
- **2025-06-28**: Added `default_input_format_id` and `default_output_format_id` columns to support default format template assignment at the step level.

### Example Usage
- Each sub-stage is seeded with a default 'Main' step.
- Additional steps can be added for more granular workflow processes.
- Default format templates can be assigned to steps for consistent input/output structure.

## Table: workflow_step_prompt

Stores system and task prompts for each workflow step. This table enables separate management of system and task prompts, allowing for more flexible and maintainable prompt engineering.

| Column           | Type         | Description                                           |
|-----------------|--------------|-------------------------------------------------------|
| id              | SERIAL       | Primary key                                           |
| step_id         | INTEGER      | References workflow_step_entity(id)                   |
| system_prompt_id| INTEGER      | References llm_prompt(id) for the system prompt       |
| task_prompt_id  | INTEGER      | References llm_prompt(id) for the task prompt         |
| created_at      | TIMESTAMP    | Creation timestamp                                    |
| updated_at      | TIMESTAMP    | Last update timestamp                                 |

**2024-06-07:** Added workflow_step_prompt table with separate system_prompt_id and task_prompt_id fields to support independent management of system and task prompts in the workflow UI. This change enables:
- Independent selection and persistence of system and task prompts
- Better prompt reusability across different workflow steps
- Clearer separation of prompt components in the UI
- More flexible prompt engineering capabilities

The table includes appropriate indexes on foreign keys and an updated_at trigger for change tracking. Both system_prompt_id and task_prompt_id reference the llm_prompt table, which supports both legacy flat string templates and structured prompt parts via its prompt_json field.

### Example Usage
```sql
-- Get prompts for a specific post's workflow step
SELECT 
    wse.name as step_name,
    sp.name as system_prompt,
    tp.name as task_prompt
FROM workflow_step_prompt wsp
JOIN workflow_step_entity wse ON wse.id = wsp.step_id
LEFT JOIN llm_prompt sp ON sp.id = wsp.system_prompt_id
LEFT JOIN llm_prompt tp ON tp.id = wsp.task_prompt_id
WHERE wsp.step_id = 123;
``` 

## Deprecated Tables

- The table `llm_format_template` has been dropped as of 2025-06-29. All format template operations now use `workflow_format_template` exclusively. Update all scripts, endpoints, and documentation to reference only `workflow_format_template`. 