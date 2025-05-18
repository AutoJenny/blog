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