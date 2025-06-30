# Documentation Index

Welcome to the documentation for the Blog Content Management System (CMS). This index provides an overview and links to all major documentation sections for users, developers, and administrators.

---

## Documentation Structure & Outline Plan

1. **Project Overview**
   - [Project Introduction](project/overview.md)
   - [Key Features](project/features.md)
   - [System Architecture](project/architecture.md)
   - [Development Roadmap](project/roadmap.md)

2. **Getting Started**
   - [Quick Start Guide](guides/quick_start.md)
   - [Technical Setup](guides/technical_setup.md)
   - [Environment Configuration](guides/environment.md)
   - **Assistant Config:** The assistant and automated tools use `assistant_config.env` at the project root for database connection info.
   - **Robust DB Connection:** All database connection functions (e.g., get_db_conn) now use `dotenv_values` to reload `assistant_config.env` on every call for reliability. Do not rely on a single os.getenv or load_dotenv at import time.
   - [FAQ & Troubleshooting](guides/faq.md)

3. **Content Creation & Management**
   - [User Guide](guides/user_guide.md)
   - [Media Management](api/media.md)
   - [Content Export & Publishing](guides/export.md)

4. **AI & LLM Integration**
   - [LLM Features Overview](api/llm.md)
   - [LLM Service Architecture](llm/architecture.md)
   - [Prompt Templates & Actions](llm/prompts.md)
   - [LLM API Reference](api/llm_api.md)
   - **Format Template System:** Step-level format configuration with complete schema and LLM instruction integration. All format configuration is now unified and post-specific overrides have been removed.
   - **If a workflow LLM action fails because Ollama is not running, a Start Ollama button will appear in the error panel, allowing you to start Ollama directly from the workflow UI. This is now handled by a shared utility and works for all workflow LLM actions, regardless of which button or script is used.**

5. **API Documentation**
   - [API Overview](api/README.md)
   - [Blog API Endpoints](api/blog.md)
   - [LLM API Endpoints](api/llm.md)
   - [Database API](api/database.md)
   - [Monitoring & Health](api/monitoring.md)

6. **Database**
   - [Database Models](database/README.md)
   - [Schema Reference](database/schema.md)
   - [Direct SQL Management](database/sql_management.md)
   - **Assistant Config:** See `assistant_config.env` for the database connection string used by the assistant/tools.
   - **Robust DB Connection:** All get_db_conn functions reload `assistant_config.env` using dotenv_values for every call, ensuring the correct database is always used. See CHANGES.log and sql_management.md for details.
   - [Migration Guide](guides/migration.md)
   - **Deprecation Notice:** SQLAlchemy ORM and Flask-SQLAlchemy have been fully removed. All database operations now use direct SQL via psycopg2.
   - **Workflow Field Mapping**: Post development fields can now be mapped to workflow stages and substages via the [Settings Panel](/settings). The current mapping is always visible in the [Live Field Mapping Table](/docs/view/database/schema.md).

**IMPORTANT:**
- This project uses PostgreSQL only. All database changes are made via direct SQL. No ORM or migration tools (Alembic, Flask-Migrate, SQLAlchemy, SQLite) are used or supported.

7. **Frontend & Styling**
   - [Template Structure](frontend/templates.md)
   - [Tailwind CSS Integration](frontend/tailwind.md)
   - [Custom Components](frontend/components.md)
   - [Static Assets](frontend/static.md)

8. **System Administration**
   - [Deployment Guide](project/deployment.md)
   - [Backup & Restore](project/backup.md)
   - [Monitoring & Logging](api/monitoring.md)
   - [Security Notes](project/security.md)

9. **Scripts & Utilities**
   - [Utility Scripts](project/scripts.md)
   - [Image Management](project/images.md)
   - [Workflow Automation](project/workflow.md)

10. **Changelog & History**
    - [Changelog](../CHANGES.log)
    - [Release Notes](project/releases.md)

---

## How to Use This Documentation

- **Start with the Quick Start Guide** if you are new to the project.
- **Developers** should review the Technical Setup, API, Database, and LLM sections.
- **Content creators** should see the User Guide and Media Management docs.
- **Admins** should check Deployment, Backup, and Monitoring docs.

## Contribution & Support

- For issues, use GitHub Issues.
- For feature requests, use GitHub Discussions.
- For technical support, contact the project maintainers.

---

*This documentation is a living document and will be updated as the project evolves.*

## Database Access

- As of 2025-05-23, all database access is performed using direct SQL via psycopg2. SQLAlchemy and ORM models are no longer used anywhere in the codebase. All data access, migrations, and queries are handled with raw SQL and psycopg2 connections.

## Recent Changes (2025-06-30)

### Format Template System Cleanup & Unification
- **Step-level format configuration only:** All format configuration is now stored in `workflow_step_entity.default_input_format_id` and `default_output_format_id`
- **Removed post-specific overrides:** All post-specific `workflow_step_format` rows have been deleted
- **Unified diagnostic logs:** Format templates appear once at top level with complete schema and LLM instruction data
- **Clean integration:** Format template data is properly integrated into LLM prompts with no duplication
- **Updated backend:** `llm_processor.py` now fetches format configuration from step-level only
- **Next steps:** Externalizing prompt construction to dedicated script for better maintainability

### Previous Changes (2025-05-25)
- The LLM Actions dropdown on `/workflow/idea` now dynamically fetches and displays all available actions from the backend (`/api/v1/llm/actions`).
- The green JSON debug text has been removed from the `/llm/actions` admin page for a cleaner UI.
- Modal CSS and Action creation bugs have been fixed for a better user experience.
- The `/api/v1/llm/prompts` endpoint now uses direct SQL (psycopg2), restoring prompt template selection and ensuring ORM is not used.
- All changes follow the project engineering rules: no ORM, no destructive migration, direct SQL only, and robust backup-first, additive schema management.

## Main Navigation

The main header now features:
- **Workflow** dropdown: Planning, Authoring, Publishing
- **Modules** dropdown: Database, AI (LLM), Images
- **Docs** link: Direct access to project documentation

All links are accessible from the top navigation bar for quick access to major features.

## 2025-05-29 Update
- LLM actions now use `parse_tagged_prompt_to_messages` to build canonical prompts, ensuring all prompt elements (system, user, operation, data) are included as per [llm/llm_prompt_structuring.md](llm/llm_prompt_structuring.md). See the changelog for details.

## 2024-06-07
- Fixed: Correct substage is now always sent and saved for post_substage_action (e.g., 'research' as well as 'idea').
- If a substage row is missing, verify the frontend is sending the correct substage in the payload. You can debug by POSTing directly to `/api/v1/llm/post_substage_actions` with the desired substage.

## 2024-06-14: Universal Modular LLM Workflow Panel
- All workflow substages (Planning, Authoring, Publishing) now use a single modular LLM panel include and JS for input, output, and action selection.
- Dropdowns show all post_development fields, but default to the first field mapped to the current substage for robust cross-stage workflows.
- The modular panel is fully plug-and-play for new substages and fields; no manual DB or template changes are needed.
- All documentation is up to date as of 2024-06-14 and reflects the new universal modular framework and persistence logic. 