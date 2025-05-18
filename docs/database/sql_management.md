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