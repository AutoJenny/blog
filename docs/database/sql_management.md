# Direct SQL Management

This project manages the PostgreSQL database schema using direct SQL scripts instead of migration tools.

## Key Script
- `create_tables.sql`: Drops and recreates all tables, types, and triggers as needed for a clean schema.

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

## Usage
- Visit `/db/` in your browser (admin access required).
- Expand groups and tables to inspect schema and sample data.
- Use this UI for quick inspection, debugging, and schema review.

For advanced operations (backups, restores, migrations), see other sections in this document. 