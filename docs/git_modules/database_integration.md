# Database Integration Guide

## Overview
This document describes how the new modular system interacts with the existing database schema. The existing database is fully functional and must be preserved exactly as is.

## Existing Schema Usage

### Core Tables
1. **workflow_stage_entity**
   - Used by: Core Module
   - Purpose: Canonical list of main workflow stages
   - Access: Read-only in modular system
   - No modifications allowed without explicit permission

2. **workflow_sub_stage_entity**
   - Used by: Core Module
   - Purpose: Ordered sub-stages for each main stage
   - Access: Read-only in modular system
   - No modifications allowed without explicit permission

3. **workflow_step_entity**
   - Used by: Workflow Module
   - Purpose: Steps within each sub-stage
   - Access: Read-only in modular system
   - No modifications allowed without explicit permission

4. **workflow_field_mapping**
   - Used by: Workflow Module
   - Purpose: Maps fields to workflow stages
   - Access: Read-only in modular system
   - No modifications allowed without explicit permission

5. **llm_action**
   - Used by: LLM Module
   - Purpose: LLM prompt/action templates
   - Access: Read-only in modular system
   - No modifications allowed without explicit permission

6. **post_workflow_step_action**
   - Used by: Workflow Module
   - Purpose: Tracks LLM actions for each step
   - Access: Read-only in modular system
   - No modifications allowed without explicit permission

## Module Integration

### Core Module
- Must use existing database connection methods
- Must not create new tables
- Must not modify existing tables
- Must use documented schema relationships
- Must maintain existing data integrity

### Workflow Module
- Must use existing workflow tables
- Must not create new workflow tables
- Must maintain existing workflow relationships
- Must use documented field mappings
- Must preserve existing workflow state

### LLM Module
- Must use existing llm_action table
- Must not modify prompt templates
- Must use existing provider relationships
- Must maintain existing action mappings
- Must preserve existing LLM configurations

## Data Access Patterns

### Reading Data
```python
def get_workflow_stages():
    """Get workflow stages using existing schema."""
    return execute_query("""
        SELECT * FROM workflow_stage_entity 
        ORDER BY order_index
    """)

def get_workflow_steps(stage_id):
    """Get workflow steps using existing schema."""
    return execute_query("""
        SELECT * FROM workflow_step_entity 
        WHERE sub_stage_id IN (
            SELECT id FROM workflow_sub_stage_entity 
            WHERE stage_id = %s
        )
        ORDER BY step_order
    """, (stage_id,))
```

### Writing Data
```python
def update_workflow_status(post_id, stage_id, status):
    """Update workflow status using existing schema."""
    return execute_query("""
        UPDATE post_workflow_stage 
        SET status = %s 
        WHERE post_id = %s AND stage_id = %s
    """, (status, post_id, stage_id))
```

## Safety Rules

1. **NEVER** modify database schema
2. **NEVER** create new tables
3. **NEVER** alter existing tables
4. **ALWAYS** use existing relationships
5. **ALWAYS** verify against schema.md
6. **ALWAYS** make backups before changes
7. **ALWAYS** test in development first
8. **ALWAYS** document any changes
9. **ALWAYS** get user approval
10. **ALWAYS** maintain data integrity

## Error Handling

1. **Database Errors**
   - Log all database errors
   - Never attempt automatic fixes
   - Report to user immediately
   - Preserve error state
   - Document error details

2. **Schema Mismatches**
   - Stop execution immediately
   - Log mismatch details
   - Report to user
   - Do not attempt fixes
   - Wait for user guidance

3. **Data Integrity**
   - Verify before operations
   - Rollback on failure
   - Log all changes
   - Report issues
   - Maintain consistency

## Testing Requirements

1. **Schema Validation**
   - Verify against schema.md
   - Check all relationships
   - Validate constraints
   - Test permissions
   - Document results

2. **Data Access**
   - Test all queries
   - Verify results
   - Check performance
   - Validate integrity
   - Document tests

3. **Error Cases**
   - Test error handling
   - Verify rollbacks
   - Check logging
   - Validate reporting
   - Document scenarios

## Documentation

1. **Schema Reference**
   - Use /docs/database/schema.md
   - No local copies
   - Always check latest
   - Document usage
   - Track changes

2. **Code Documentation**
   - Document all queries
   - Explain relationships
   - Note constraints
   - Track modifications
   - Update regularly

3. **Change Tracking**
   - Log all changes
   - Document reasons
   - Track approvals
   - Note backups
   - Update docs

## Emergency Procedures

1. **Schema Issues**
   - Stop all operations
   - Log the issue
   - Report to user
   - Wait for guidance
   - Document response

2. **Data Problems**
   - Preserve state
   - Log details
   - Report to user
   - No automatic fixes
   - Wait for guidance

3. **Performance Issues**
   - Log metrics
   - Report to user
   - Document impact
   - No schema changes
   - Wait for guidance 