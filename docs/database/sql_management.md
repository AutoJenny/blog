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

## LLM Prompt Assembler UI Improvements (2025-06-XX)

- The Prompt Assembler on `/llm/prompts` now uses [SortableJS](https://sortablejs.github.io/Sortable/) for robust drag-and-drop of prompt parts.
- Draggable items are styled with a deep green background and a drag handle for clarity.
- The UI prevents accidental duplication and provides a smoother, more accessible experience.
- See `app/templates/main/llm_prompts.html` for implementation details. 