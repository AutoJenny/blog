# Non-Compliant Files Analysis

## Files to Delete

### 1. Legacy Step Templates
These templates don't match our database-driven hierarchy:

```
app/templates/workflow/steps/
├── basic_idea.html                 # REMOVE: Replaced by "Idea Seed.html"
├── provisional_title.html          # REMOVE: Wrong case, replaced by "Provisional Title.html"
├── Initial.html                    # REMOVE: Legacy step name
└── research_plan.html             # REMOVE: Not in database structure
```

### 2. Legacy Configuration Files
These contain hardcoded workflow structures that should come from database:

```
app/workflow/config/
├── planning_steps.json            # REMOVE: All step data must come from database
├── workflow_structure.json        # REMOVE: Structure must come from database
└── step_config.json              # REMOVE: Configuration should be in database
```

### 3. Old Navigation Files
These implement the old navigation system:

```
modules/nav/
├── services.py                    # REMOVE: Functionality moved to app/workflow/navigation.py
├── templates/                     # REMOVE: All templates replaced
│   ├── nav.html                  # REMOVE: Replaced by _workflow_nav.html
│   └── workflow_nav.html         # REMOVE: Outdated structure
└── static/                       # REMOVE: Styles moved to app/static/css/workflow.css
```

### 4. Deprecated Route Files
Old route files that don't follow the three-level hierarchy:

```
app/routes/
├── workflow.py                    # REMOVE: Moved to app/workflow/routes.py
└── workflow_old.py               # REMOVE: Deprecated file
```

## Files Requiring Updates

### 1. Database Tables
The following tables form our core workflow structure:

```sql
-- Core Workflow Tables
workflow_stage_entity        # Main stages (planning, authoring, publishing)
workflow_sub_stage_entity   # Sub-stages for each main stage
workflow_step_entity        # Individual steps within sub-stages
workflow_field_mapping      # Maps fields to stages/substages
post_workflow_step_action   # LLM action settings for each step
```

### 2. Files to Update

#### Database Access
`app/db.py` needs:
- Update to use direct SQL queries (no SQLAlchemy)
- Add proper workflow hierarchy queries using the entity tables
- Add validation functions
- Remove any hardcoded step references
- Ensure proper error handling for invalid combinations

#### Navigation Service
`app/workflow/navigation.py` needs:
- Complete rewrite to use the workflow entity tables
- Add proper validation of stage/substage/step combinations
- Add methods for traversing hierarchy
- Remove any hardcoded paths or steps

#### Templates
Need to reorganize all step templates to match the database-driven hierarchy:

Required structure (based on workflow_step_entity):
```
app/templates/workflow/steps/
├── {stage.name}/
│   ├── {substage.name}/
│   │   ├── {step.name}.html  # Each step template
│   │   └── ...
│   └── ...
└── ...
```

Example (actual names from database):
```
app/templates/workflow/steps/
├── Planning/
│   ├── Idea/
│   │   ├── Idea Scope.html
│   │   ├── Idea Seed.html
│   │   └── Provisional Title.html
│   ├── Research/
│   │   └── Main.html
│   └── Structure/
│       └── Main.html
├── Authoring/
│   └── Content/
│       └── Main.html
└── Publishing/
    └── Preflight/
        └── Main.html
```

#### Route Files

##### Workflow Routes
`app/workflow/routes.py` needs:
- Update route patterns to use workflow entity tables
- Add validation for stage/substage/step existence
- Add proper error handling for invalid combinations
- Remove any hardcoded paths

##### Blog Routes
`app/blog/routes.py` needs:
- Update post creation to use database-driven first step
- Remove hardcoded workflow paths
- Add proper validation using workflow entity tables

#### JavaScript Files

##### Workflow JavaScript
`app/static/js/workflow.js` needs:
- Update navigation handling to use workflow entity tables
- Remove hardcoded paths
- Add proper state management
- Add support for field mapping UI

##### LLM Integration
`app/static/js/llm.js` needs:
- Update workflow step references to use workflow_step_entity
- Remove hardcoded step names
- Use database-driven paths
- Support post_workflow_step_action for button configuration

### Required New Files

#### Database Migration
```sql
migrations/
└── YYYYMMDD_workflow_hierarchy_cleanup.sql  # Clean up workflow tables
```

#### Testing
```
tests/
├── test_workflow_hierarchy.py     # Test workflow entity tables
├── test_workflow_navigation.py    # Test navigation service
└── test_workflow_templates.py     # Test template rendering
```

## Verification Steps

For each file:
1. Back up original
2. Make changes
3. Run tests
4. Test affected workflows
5. Verify no regressions
6. Verify database consistency

## Rollback Plan

For each change:
1. Create git branch
2. Commit original files
3. Make changes
4. Test thoroughly
5. If issues:
   - Reset to original commit
   - Restore database backup
   - Try alternative approach

## Success Criteria

After all updates:
1. No references to legacy step names
2. All paths follow database-driven hierarchy
3. All templates match workflow entity structure
4. All navigation database-driven
5. All tests pass
6. Field mapping working correctly
7. LLM action buttons configured properly 