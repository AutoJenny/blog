# Database Schema Reference

The Blog CMS uses PostgreSQL for all persistent storage. Below is an overview of the main tables and their relationships.

## Main Tables
- **post**: Stores blog post content and metadata
- **media**: Stores image and file metadata
- **llm_action**: Stores LLM prompt/action templates
- **user**: (if present) Stores user data (currently not used; see notes)
- **other tables**: As defined in `create_tables.sql` and SQLAlchemy models

## Relationships
- Posts may reference media (images) and LLM actions
- Foreign keys are used for referential integrity

## Management
- Schema is managed via `create_tables.sql` and SQLAlchemy models
- No migration tool is used; direct SQL is preferred

## See Also
- [Direct SQL Management](sql_management.md)
- [Database Models](README.md) 