# Workflow Migration Implementation Plan

## Overview
This document outlines the step-by-step migration from the current 3-level workflow structure (Stage > Substage > Step) to a simplified 2-level structure (Stage > Step) while preserving all embedded knowledge and configurations.

## Current Structure Analysis

### Database Tables
- **`workflow_stage_entity`**: Main stages (planning, writing)
- **`workflow_sub_stage_entity`**: Substages (idea, research, structure, sections, post_info, images)
- **`workflow_step_entity`**: Individual steps with rich JSONB configurations
- **`post_workflow_step_action`**: Step-to-LLM action mappings
- **`workflow_field_mapping`**: Field mappings to stages/substages
- **`workflow_step_prompt`**: System and task prompt mappings

### Embedded Knowledge Inventory
- **19 steps** with rich JSONB configurations containing:
  - Input/output field definitions
  - LLM settings and parameters
  - Field mappings to database tables
  - UI settings and descriptions
  - Script configurations
- **1 step-action mapping** linking steps to LLM actions
- **31 field mappings** connecting fields to stages/substages
- **10 prompt mappings** linking steps to system/task prompts

## Migration Strategy: "Flatten and Preserve"

### Phase 1: Database Structure Migration

#### Step 1.1: Add stage_id to workflow_step_entity
```sql
-- Add stage_id column
ALTER TABLE workflow_step_entity ADD COLUMN stage_id INTEGER;

-- Populate stage_id from existing substage relationships
UPDATE workflow_step_entity 
SET stage_id = (
    SELECT wsse.stage_id 
    FROM workflow_sub_stage_entity wsse 
    WHERE wsse.id = workflow_step_entity.sub_stage_id
);

-- Add foreign key constraint
ALTER TABLE workflow_step_entity 
ADD CONSTRAINT fk_workflow_step_stage 
FOREIGN KEY (stage_id) REFERENCES workflow_stage_entity(id);
```

#### Step 1.2: Update step ordering to be global within stage
```sql
-- Create new step_order that's sequential within each stage
UPDATE workflow_step_entity 
SET step_order = reordered.new_order
FROM (
    SELECT 
        id, 
        ROW_NUMBER() OVER (
            PARTITION BY stage_id 
            ORDER BY (
                SELECT wsse.sub_stage_order 
                FROM workflow_sub_stage_entity wsse 
                WHERE wsse.id = sub_stage_id
            ), 
            step_order
        ) as new_order
    FROM workflow_step_entity
) reordered
WHERE workflow_step_entity.id = reordered.id;
```

#### Step 1.3: Verify data integrity
```sql
-- Verify all steps have stage_id
SELECT COUNT(*) as steps_without_stage_id 
FROM workflow_step_entity 
WHERE stage_id IS NULL;

-- Verify step ordering is sequential within each stage
SELECT 
    stage_id,
    COUNT(*) as step_count,
    MIN(step_order) as min_order,
    MAX(step_order) as max_order
FROM workflow_step_entity 
GROUP BY stage_id;
```

### Phase 2: URL Structure Update

#### Step 2.1: Update routing in blueprints/core.py
```python
# Old route (3-level)
@bp.route('/workflow/posts/<int:post_id>/<stage>/<substage>/<step_name>')
def workflow_step_old(post_id, stage, substage, step_name):
    # Redirect to new 2-level structure
    return redirect(f'/workflow/posts/{post_id}/{stage}/{step_name}')

# New route (2-level)
@bp.route('/workflow/posts/<int:post_id>/<stage>/<step_name>')
def workflow_step(post_id, stage, step_name):
    # Convert URL format to database format
    db_step_name = step_name.replace('_', ' ').title()
    
    # Get step directly from stage (no substage lookup needed)
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT 
                wse.id, 
                wse.name, 
                wse.step_order, 
                wse.config,
                wse.description
            FROM workflow_step_entity wse
            JOIN workflow_stage_entity wst ON wse.stage_id = wst.id
            WHERE wst.name = %s AND wse.name = %s
        """, (stage, db_step_name))
        step = cursor.fetchone()
        
        if not step:
            return redirect(f'/workflow/posts/{post_id}/planning/initial_concept')
        
        # Get next/previous steps for navigation
        cursor.execute("""
            SELECT wse.name, wse.step_order
            FROM workflow_step_entity wse
            JOIN workflow_stage_entity wst ON wse.stage_id = wst.id
            WHERE wst.name = %s
            ORDER BY wse.step_order
        """, (stage,))
        all_steps = cursor.fetchall()
        
        # Find current step position and get next/previous
        current_index = next(i for i, s in enumerate(all_steps) if s['name'] == db_step_name)
        prev_step = all_steps[current_index - 1]['name'].lower().replace(' ', '_') if current_index > 0 else None
        next_step = all_steps[current_index + 1]['name'].lower().replace(' ', '_') if current_index < len(all_steps) - 1 else None
        
        return render_template('workflow.html', 
                             post_id=post_id,
                             stage=stage,
                             step=step_name,
                             step_data=step,
                             prev_step=prev_step,
                             next_step=next_step)
```

#### Step 2.2: Update navigation templates
Update `templates/nav/nav.html` to use new 2-level structure:

```html
<!-- Old: 3-level navigation -->
<li><a href="/workflow/posts/{{ post_id }}/planning/idea/initial_concept">Initial Concept</a></li>
<li><a href="/workflow/posts/{{ post_id }}/planning/research/interesting_facts">Interesting Facts</a></li>

<!-- New: 2-level navigation -->
<li><a href="/workflow/posts/{{ post_id }}/planning/initial_concept">Initial Concept</a></li>
<li><a href="/workflow/posts/{{ post_id }}/planning/interesting_facts">Interesting Facts</a></li>
```

### Phase 3: Update Supporting Systems

#### Step 3.1: Update LLM Actions microservice
Update `blog-llm-actions` to use new URL structure:
- Change iframe URLs from 3-level to 2-level
- Update step configuration API endpoints
- Update navigation parameters

#### Step 3.2: Update field mapping queries
Update any queries that reference substages to use the new structure:
```sql
-- Old query
SELECT * FROM workflow_field_mapping wfm
JOIN workflow_sub_stage_entity wsse ON wfm.substage_id = wsse.id
WHERE wsse.name = 'idea'

-- New query (if needed)
SELECT * FROM workflow_field_mapping wfm
JOIN workflow_step_entity wse ON wfm.step_id = wse.id
WHERE wse.name = 'Initial Concept'
```

### Phase 4: Testing and Validation

#### Step 4.1: Test all workflow steps
- Verify all 19 steps load correctly with new URLs
- Test navigation between steps
- Verify all configurations are preserved
- Test LLM actions and prompts

#### Step 4.2: Test data integrity
- Verify all step configurations are intact
- Test step-action mappings
- Verify field mappings work correctly
- Test prompt mappings

#### Step 4.3: Performance testing
- Compare query performance before/after
- Test with large datasets
- Verify no regression in response times

### Phase 5: Cleanup (Optional)

#### Step 5.1: Remove old substage references
```sql
-- Remove substage_id column (after migration is complete and tested)
ALTER TABLE workflow_step_entity DROP COLUMN sub_stage_id;

-- Drop substage table (after all references are updated)
DROP TABLE workflow_sub_stage_entity;
```

#### Step 5.2: Update documentation
- Update API documentation
- Update user guides
- Update developer documentation

## Implementation Timeline

### Week 1: Database Migration
- [ ] Add stage_id column
- [ ] Update step ordering
- [ ] Verify data integrity
- [ ] Create backup

### Week 2: URL Structure Update
- [ ] Update routing in core.py
- [ ] Update navigation templates
- [ ] Test basic navigation

### Week 3: Supporting Systems
- [ ] Update LLM Actions microservice
- [ ] Update field mapping queries
- [ ] Test all integrations

### Week 4: Testing and Cleanup
- [ ] Comprehensive testing
- [ ] Performance validation
- [ ] Optional cleanup
- [ ] Documentation updates

## Risk Mitigation

### Data Backup
- Create full database backup before migration
- Test migration on copy of production data
- Keep rollback plan ready

### Gradual Rollout
- Implement redirects from old URLs to new URLs
- Monitor for broken links or missing functionality
- Have rollback plan ready

### Testing Strategy
- Test each phase thoroughly before proceeding
- Use staging environment for full testing
- Monitor production metrics during rollout

## Success Criteria

- [ ] All 19 workflow steps accessible via new 2-level URLs
- [ ] All embedded configurations preserved
- [ ] Navigation works correctly
- [ ] LLM actions function properly
- [ ] No data loss or corruption
- [ ] Performance maintained or improved
- [ ] All existing functionality preserved

## Rollback Plan

If issues arise during migration:
1. Restore database from backup
2. Revert code changes
3. Restore old URL structure
4. Investigate and fix issues
5. Retry migration with fixes

## Post-Migration Benefits

- **Simplified URLs**: Cleaner, more intuitive structure
- **Easier Step Management**: Add/remove steps by updating single table
- **Better Performance**: Fewer joins, simpler queries
- **Maintained Flexibility**: All existing configurability preserved
- **Future-Proof**: Easy to add new stages or reorganize steps
