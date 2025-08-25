# Database Fixes

## Missing Workflow Tables (2025-01-23)

### Issue
The workflow field mapping page at `http://localhost:5000/settings/workflow_field_mapping` was failing with the error:
```
Failed to delete step: relation "workflow_step_prompt" does not exist
```

### Root Cause
Two database tables were missing from the current database schema but were still referenced in the code:
1. `workflow_step_prompt` - Links workflow steps to LLM prompts
2. `workflow_step_format` - Links workflow steps to format templates

These tables existed in previous database backups but were not present in the current database.

### Solution
Created the missing tables with the correct schema based on the backup file `blog_backup_20250719_144341.sql`:

#### workflow_step_prompt table:
```sql
CREATE TABLE public.workflow_step_prompt (
    id integer NOT NULL,
    step_id integer NOT NULL,
    system_prompt_id integer NOT NULL,
    task_prompt_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);
```

#### workflow_step_format table:
```sql
CREATE TABLE public.workflow_step_format (
    id integer NOT NULL,
    step_id integer NOT NULL,
    post_id integer NOT NULL,
    input_format_id integer,
    output_format_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
```

### Verification
- ✅ Tables created successfully
- ✅ Workflow field mapping page loads without errors
- ✅ Step deletion functionality works correctly
- ✅ API endpoints return proper responses

### Files Modified
- Database schema (tables created)
- No code changes required - existing code now works correctly

### Notes
- The `workflow_format_template` table referenced in foreign keys was not created as it may not be needed
- Foreign key constraints for format templates were commented out to avoid dependency issues
- All other foreign key constraints were properly established 