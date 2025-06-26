# Direct SQL Management
 
> **SAFETY WARNING:**
> Always make a full backup using `pg_dump` before running `create_tables.sql`. Never run this script on production or important data without a backup and a tested restore plan. Restore data as needed after schema changes.

## Database Ownership and Permissions
- The owner of the main `blog` database is usually `nickfiddes` (see output of `psql -U postgres -c "\l"`).
- All destructive or schema-changing operations (e.g., `dropdb`, `createdb`, `psql -f ...`) **must be run as the database owner** (typically `nickfiddes`).
- If you use the wrong user (e.g., `postgres`), you will get 'must be owner' errors.
- **Checklist for DB operations:**
  1. Confirm the owner of the database:
     ```bash
     psql -U postgres -c "\l"
     # Look for the 'Owner' column for 'blog'
     ```
  2. Use the owner for all DB commands:
     ```bash
     dropdb -U nickfiddes blog
     createdb -U nickfiddes blog
     psql -U nickfiddes -d blog -f create_tables.sql
     psql -U nickfiddes -d blog -f blog_backup_YYYYMMDD_HHMMSS.sql
     ```
  3. If you get permission errors, check and fix ownership before proceeding.

This project manages the PostgreSQL database schema using direct SQL scripts instead of migration tools.

## Key Script
- `create_tables.sql`: Drops and recreates all tables, types, and triggers as needed for a clean schema.

## Safe Schema Change Process
1. **Make a Full Backup**
   - Run:
     ```bash
     pg_dump -U <user> -d blog > blog_backup_YYYYMMDD.sql
     ```
   - Replace `<user>` with your PostgreSQL username (default: `postgres`).
   - Store the backup in a safe location.
   - **If new JSONB columns (e.g., prompt_json in llm_prompt) are added, ensure all backup/restore and migration scripts are updated to preserve these fields.**
2. **Apply Schema Changes**
   - Edit `create_tables.sql` as needed.
   - Run:
     ```bash
     psql -U <user> -d blog -f create_tables.sql
     ```
   - This will drop and recreate all tables, erasing all data.
3. **Restore Data**
   - Use the backup to restore posts, images, and other critical data as needed.
   - For new tables, seed as appropriate.

> **Never run `create_tables.sql` on production or important data without a backup and a tested restore plan.**

## Usage
- To reset the database:
  ```bash
  psql -U <user> -d blog -f create_tables.sql
  ```
- Replace `<user>` with your PostgreSQL username (default: `postgres`).

## Inspecting the Database
- Use `psql` or a GUI tool (e.g., TablePlus, DBeaver) to inspect tables and data.
- Example:
  ```bash
  psql -U <user> -d blog
  \dt
  \d+ <table>
  SELECT * FROM <table>;
  ```

## Notes
- All tables should be owned by your main DB user (e.g., `nickfiddes`).
- If you encounter permission errors, check table ownership and privileges.
- No web-based DB management UI is provided; all operations are CLI-based.

## Troubleshooting
- If schema changes are not reflected, re-run `create_tables.sql`.
- For permission issues, ensure correct ownership and privileges in PostgreSQL.

## Importing Content from Eleventy (Old Blog)

To merge content from the old Eleventy-based blog (Markdown with YAML frontmatter) with your current database:

- Use `scripts/import_from_old_blog.py`.
- This script:
  - Parses all Markdown posts in `blog/__blog_old/posts/`.
  - Imports image metadata from `blog/__blog_old/_data/image_library.json`.
  - Skips posts and images that already exist in the database (by slug/filename).
  - Copies image files to `app/static/images/posts/`.
  - Prints a summary of imported and skipped items.

**Usage:**
```bash
python scripts/import_from_old_blog.py
```

This process preserves all data from previous SQL backups and only adds new content from the old site.

# Database Content Admin UI

The admin interface at `/db/` provides a modern, grouped view of your database tables and their contents.

## Features
- **Grouped Table Display:**
  - Tables are grouped by theme (e.g., Blog/Post Related, Image Related, LLM Related, User/Workflow, Other).
  - Groups are ordered alphabetically (A–Z) for clarity.
  - If a group has no tables, it is omitted.
  - If grouping fails or is empty, a flat list of all tables is shown as a fallback.
- **Accordion UI:**
  - Each group and table is displayed in an accordion panel for easy browsing.
  - Up to 20 rows per table are shown for preview.
  - Columns and types are displayed for each table.
- **Live Data:**
  - Data is fetched from the `/db/tables` backend route, which returns both `groups` and a flat `tables` list for compatibility.
  - The UI prefers `groups` if present, otherwise falls back to `tables`.
- **Modern, Accessible Front-End:**
  - The front-end code for the DB display UI was completely rewritten from scratch (2025-05-XX) for robustness, clarity, and accessibility, while replicating all previous functionality.
  - Uses modern, accessible JavaScript, robust error handling, and defensive coding for missing/empty data.
  - Accordion panels are keyboard accessible and expand the first group/table by default.

## Technical Details
- **Backend:**
  - See `app/database/routes.py`, `/tables` route.
  - Returns `{ groups: [...], tables: [...] }` (both always present for compatibility).
  - Groups are defined by theme and sorted A–Z.
  - Each table includes its columns and up to 20 rows.
- **Frontend:**
  - See `app/templates/db/index.html`.
  - JavaScript fetches `/db/tables` and renders groups/tables as accordions.
  - If no groups or tables are found, a message is shown.
  - The UI is robust to errors and empty states, and is fully accessible.

## Usage
- Visit `/db/` in your browser (admin access required).
- Expand groups and tables to inspect schema and sample data.
- Use this UI for quick inspection, debugging, and schema review.

For advanced operations (backups, restores, migrations), see other sections in this document.

## LLM Prompt Assembler & Prompt Template UI/Backend Improvements (2025-06-XX)

- The Prompt Assembler on `/llm/prompts` uses [SortableJS](https://sortablejs.github.io/Sortable/) for robust drag-and-drop of prompt parts.
- Available prompt parts are blue; assembled sequence parts are blue (prompt parts) or green (data fields).
- The green data field entity can be dragged and dropped into any position in the sequence, with visible drop space.
- All tab logic (Prompt Parts, Assembler, Templates) is robust and accessible.
- Prompt template deletion is now robust: the backend uses direct SQL, and the frontend checks for `{ success: true }` in the response, providing clear UI feedback.
- All changes are committed and tested with curl and browser.
- See `app/templates/main/llm_prompts.html` for implementation details.
- **2024-06: The llm_prompt table now includes a prompt_json JSONB column for structured prompt templates. All backup, restore, and migration scripts must preserve this field.**

## Changes from 2025-05-26
- As of 2025-05-26, the `llm_action_prompt_part` table has been dropped from the schema and is no longer present in the LLM group in the /db UI. The LLM group now includes: `llm_action`, `llm_action_history`, `llm_provider`, `llm_model`, `llm_interaction`, `llm_prompt`, `llm_prompt_part`, and `post_substage_action`.
- The Restore dropdown in `/db` is now dynamic and always lists all available backup files (most recent first) from both the `backups/` directory and the project root.
- The schema migration script (`create_tables.sql`) is fully aligned with the current live database schema and should be used for all future migrations.

psql $DATABASE_URL -U nickfiddes -c "REASSIGN OWNED BY nickfiddes TO postgres;" 

## 2025-06-XX: Sequence Ownership and Permission Recovery

- Resolved a persistent permission error on the llm_prompt_id_seq sequence by granting superuser to the postgres user and recreating the sequence as postgres.
- If you encounter sequence permission errors, ensure the user performing the operation is a superuser. Use \du to check roles.
- Steps taken:
  1. Grant superuser to postgres (as nickfiddes):
     ALTER USER postgres WITH SUPERUSER;
  2. Drop and recreate the sequence as postgres:
     DROP SEQUENCE IF EXISTS llm_prompt_id_seq CASCADE;
     CREATE SEQUENCE llm_prompt_id_seq OWNED BY llm_prompt.id;
     ALTER TABLE llm_prompt ALTER COLUMN id SET DEFAULT nextval('llm_prompt_id_seq');
     SELECT setval('llm_prompt_id_seq', (SELECT COALESCE(MAX(id), 1) FROM llm_prompt), true);
  3. Create a new backup after the fix:
     pg_dump -U postgres -d blog > blog_backup_YYYYMMDD_HHMMSS_after_seqfix.sql
- See CHANGES.log for details.

## 2025-06-XX: Non-modal Action Builder Panel (Updated)

- The /llm/actions page now features a fully functional non-modal Action Builder panel below the action list.
- All four stages (Basic Info, Model Settings, Prompt Template, Test & Save) are always visible, stacked vertically.
- The builder supports dropdowns, prompt preview, test run, and save, matching the modal wizard's logic and UI.
- The panel is fully accessible, robust, and provides clear error and success feedback.
- See CHANGES.log for details.

## 2025-06-XX: LLM Actions Builder Test & Save Button Fixes

- The Test button in the Action Builder is only enabled for existing actions (edit mode) and calls the correct endpoint.
- Test is disabled for new actions, with a tooltip explaining why.
- Save button always sends all required fields; clear error messages for missing fields or backend errors.
- The UI and logic are robust and user-friendly.

## 2025-06-XX: LLM Action Test Data Variable Support

- The Action Builder Test field now maps to [data:variable] placeholders in prompt templates.
- The frontend extracts [data:var] and sends test input as { var: value }.
- The backend replaces [data:var] with {{ var }} and flattens input mapping for Jinja2 rendering.
- This enables robust, real-world testing of actions with data variables directly from the UI.
- See CHANGES.log for details.

## Environment Variable Loading for Database Connections

- All database connection functions (e.g., get_db_conn in app/blog/routes.py and app/database/routes.py) now use `dotenv_values` to reload `assistant_config.env` on every call.
- This ensures the correct `DATABASE_URL` is always used, regardless of the shell or environment state.
- Do **not** rely on a single os.getenv or load_dotenv at import time; always reload the config file for robust, predictable behavior.
- See CHANGES.log for details of the 2025-05-28 fix.

## 2025-05-30: Added `input_field` and `output_field` columns to `post_substage_action` for LLM workflow field persistence. All backup, restore, and migration scripts must be updated to match this schema. Test restores after migration.

## Post-Restore Validation Checklist (2024-06)

- After restoring a backup, always:
  - Visit `/db/` or use curl to confirm all expected tables are present.
  - Check that critical tables (e.g., post, post_section, post_development, llm_action, etc.) contain data if expected.
  - If a table is empty, determine if this is expected (e.g., new feature, not yet used) or a sign of a backup/restore issue.
  - Validate with curl or browser before proceeding with further destructive or schema-changing operations.
  - For new tables/features, check if they are present in the backup and document if they are not yet in use.

## Canonical Workflow Tables

- The canonical workflow tables are: workflow_stage_entity, workflow_sub_stage_entity, workflow_step_entity, and workflow_field_mapping.
- When seeding workflow tables, always ensure workflow_step_entity is included and seeded with at least a 'Main' step for each sub-stage.
- All schema changes to workflow_step_entity must be documented in /docs/database/schema.md and backed up before applying.

## 2025-06-XX: Workflow Table Ownership Alignment

- All workflow-related tables must be owned by the same database user (typically `nickfiddes`) to avoid permission errors
- Critical workflow tables that must share ownership:
  * `workflow_step_prompt`
  * `workflow_step_entity`
  * `llm_prompt`
- To verify table ownership:
  ```sql
  SELECT tablename, tableowner 
  FROM pg_tables 
  WHERE tablename IN ('workflow_step_prompt', 'workflow_step_entity', 'llm_prompt');
  ```
- To fix ownership mismatches:
  ```sql
  ALTER TABLE workflow_step_entity OWNER TO nickfiddes;
  ```
- After ownership changes, verify functionality with:
  ```bash
  curl -X POST "http://localhost:5000/workflow/api/step_prompts/22/41" \
    -H "Content-Type: application/json" \
    -d '{"system_prompt_id": 71, "task_prompt_id": 86}'
  ```
- Always make a backup before changing table ownership:
  ```bash
  pg_dump -U nickfiddes -d blog > blog_backup_YYYYMMDD_HHMMSS_pre_ownership_fix.sql
  ``` 