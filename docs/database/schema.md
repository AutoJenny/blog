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