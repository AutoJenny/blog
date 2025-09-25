# Workflow Navigation System Documentation

## Overview
The Workflow Navigation System provides a flexible, database-driven approach to managing blog creation workflows. It supports dynamic step ordering, easy addition/removal of steps, and preserves all embedded knowledge and configurations.

## Core Principles

### 1. Database-Driven Architecture
- All workflow structure defined in database tables
- No hard-coded step definitions in application code
- Easy to add, remove, or reorder steps without code changes

### 2. Preserve Embedded Knowledge
- All step configurations, mappings, and prompts preserved
- Rich JSONB configurations for flexible step definitions
- Maintain all existing functionality during transitions

### 3. Flexible URL Structure
- Human-readable URLs using step names
- Easy to understand and bookmark
- SEO-friendly structure

### 4. Modular Design
- Clear separation between stages and steps
- Independent step configurations
- Reusable components and templates

## Database Schema

### Core Tables

#### `workflow_stage_entity`
Main workflow stages (e.g., planning, writing).

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `name` | VARCHAR | Stage name (e.g., 'planning', 'writing') |
| `stage_order` | INTEGER | Display order |
| `description` | TEXT | Stage description |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

#### `workflow_step_entity`
Individual workflow steps with rich configurations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `name` | VARCHAR | Step name (e.g., 'Initial Concept') |
| `stage_id` | INTEGER | Foreign key to workflow_stage_entity |
| `step_order` | INTEGER | Order within stage |
| `config` | JSONB | Rich step configuration |
| `description` | TEXT | Step description |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

### Configuration Tables

#### `workflow_step_prompt`
Links steps to system and task prompts.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `step_id` | INTEGER | Foreign key to workflow_step_entity |
| `system_prompt_id` | INTEGER | Foreign key to llm_prompt |
| `task_prompt_id` | INTEGER | Foreign key to llm_prompt |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

#### `post_workflow_step_action`
Maps steps to LLM actions.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `step_id` | INTEGER | Foreign key to workflow_step_entity |
| `action_id` | INTEGER | Foreign key to llm_action |
| `button_label` | VARCHAR | Display label for action button |
| `input_field` | VARCHAR | Input field name |
| `output_field` | VARCHAR | Output field name |
| `button_order` | INTEGER | Button display order |

#### `workflow_field_mapping`
Maps fields to workflow stages.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `field_name` | VARCHAR | Field name |
| `stage_id` | INTEGER | Foreign key to workflow_stage_entity |
| `order_index` | INTEGER | Display order |

## URL Structure

### Format
```
/workflow/posts/<post_id>/<stage>/<step_name>
```

### Examples
```
/workflow/posts/53/planning/initial_concept
/workflow/posts/53/planning/interesting_facts
/workflow/posts/53/writing/ideas_to_include
```

### URL to Database Mapping
- `<stage>` maps to `workflow_stage_entity.name`
- `<step_name>` maps to `workflow_step_entity.name` (converted from URL format)
- URL format: `step_name` (lowercase with underscores)
- Database format: `Step Name` (title case with spaces)

## Step Configuration (JSONB)

Each step's `config` field contains rich configuration data:

```json
{
  "title": "Step Display Title",
  "description": "Step description",
  "inputs": {
    "input1": {
      "type": "textarea",
      "label": "Input Field Label",
      "db_field": "field_name",
      "db_table": "table_name",
      "required": true
    }
  },
  "outputs": {
    "output1": {
      "type": "textarea",
      "label": "Output Field Label",
      "db_field": "field_name",
      "db_table": "table_name"
    }
  },
  "settings": {
    "auto_save": true,
    "validation_rules": ["required", "min_length"]
  },
  "llm_settings": {
    "model": "llama3.2:latest",
    "temperature": 0.7,
    "max_tokens": 1000
  },
  "field_mapping": {
    "source_field": "target_field"
  },
  "script_config": {
    "enabled": true,
    "script_name": "custom_script.js"
  }
}
```

## Navigation Implementation

### Backend Routing (Flask)
```python
@bp.route('/workflow/posts/<int:post_id>/<stage>/<step_name>')
def workflow_step(post_id, stage, step_name):
    # Convert URL format to database format
    db_step_name = step_name.replace('_', ' ').title()
    
    # Get step from database
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
        
        # Get navigation context
        cursor.execute("""
            SELECT wse.name, wse.step_order
            FROM workflow_step_entity wse
            JOIN workflow_stage_entity wst ON wse.stage_id = wst.id
            WHERE wst.name = %s
            ORDER BY wse.step_order
        """, (stage,))
        all_steps = cursor.fetchall()
        
        # Calculate previous/next steps
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

### Frontend Navigation (Jinja2)
```html
<!-- Stage Navigation -->
<nav class="workflow-stages">
  {% for stage in stages %}
    <a href="/workflow/posts/{{ post_id }}/{{ stage.name }}" 
       class="{% if stage.name == current_stage %}active{% endif %}">
      {{ stage.name|title }}
    </a>
  {% endfor %}
</nav>

<!-- Step Navigation -->
<nav class="workflow-steps">
  {% for step in stage_steps %}
    <a href="/workflow/posts/{{ post_id }}/{{ stage }}/{{ step.name|lower|replace(' ', '_') }}" 
       class="{% if step.name|lower|replace(' ', '_') == current_step %}active{% endif %}">
      {{ step.name }}
    </a>
  {% endfor %}
</nav>
```

## Step Management

### Adding a New Step
1. Insert new row in `workflow_step_entity`:
```sql
INSERT INTO workflow_step_entity (name, stage_id, step_order, config, description)
VALUES ('New Step Name', 1, 5, '{"title": "New Step"}', 'Step description');
```

2. Update step ordering if needed:
```sql
UPDATE workflow_step_entity 
SET step_order = step_order + 1 
WHERE stage_id = 1 AND step_order >= 5;
```

3. Add step-specific configurations:
```sql
-- Add prompt mappings
INSERT INTO workflow_step_prompt (step_id, system_prompt_id, task_prompt_id)
VALUES (new_step_id, system_prompt_id, task_prompt_id);

-- Add action mappings
INSERT INTO post_workflow_step_action (step_id, action_id, button_label, input_field, output_field)
VALUES (new_step_id, action_id, 'Button Label', 'input_field', 'output_field');
```

### Removing a Step
1. Remove dependent data:
```sql
DELETE FROM workflow_step_prompt WHERE step_id = step_id_to_remove;
DELETE FROM post_workflow_step_action WHERE step_id = step_id_to_remove;
```

2. Remove the step:
```sql
DELETE FROM workflow_step_entity WHERE id = step_id_to_remove;
```

3. Update step ordering:
```sql
UPDATE workflow_step_entity 
SET step_order = step_order - 1 
WHERE stage_id = (SELECT stage_id FROM workflow_step_entity WHERE id = step_id_to_remove) 
AND step_order > (SELECT step_order FROM workflow_step_entity WHERE id = step_id_to_remove);
```

### Reordering Steps
```sql
-- Move step to new position
UPDATE workflow_step_entity 
SET step_order = new_position 
WHERE id = step_id;

-- Adjust other steps
UPDATE workflow_step_entity 
SET step_order = step_order + 1 
WHERE stage_id = (SELECT stage_id FROM workflow_step_entity WHERE id = step_id)
AND step_order >= new_position 
AND id != step_id;
```

## Integration Points

### LLM Actions Microservice
- Receives step configuration via iframe parameters
- Uses step-specific prompts and settings
- Returns results to parent workflow

### Field Mapping System
- Maps step inputs/outputs to database fields
- Handles data validation and transformation
- Manages field dependencies and relationships

### Prompt Management
- Links steps to system and task prompts
- Manages prompt templates and parameters
- Handles prompt versioning and updates

## Best Practices

### Step Configuration
- Use descriptive step names
- Include comprehensive descriptions
- Define clear input/output field mappings
- Set appropriate validation rules

### URL Design
- Use lowercase with underscores for step names
- Keep URLs short and meaningful
- Avoid special characters in step names
- Maintain consistent naming conventions

### Database Design
- Use JSONB for flexible configurations
- Maintain referential integrity
- Index frequently queried fields
- Regular cleanup of orphaned records

### Performance
- Cache frequently accessed step configurations
- Use efficient queries with proper joins
- Monitor query performance
- Optimize for common navigation patterns

## Troubleshooting

### Common Issues
1. **Step not found**: Check step name conversion between URL and database formats
2. **Navigation broken**: Verify step ordering and stage relationships
3. **Configuration missing**: Check JSONB config field for required keys
4. **Prompts not loading**: Verify prompt mappings in workflow_step_prompt table

### Debugging Queries
```sql
-- Check step configuration
SELECT name, config FROM workflow_step_entity WHERE id = step_id;

-- Verify step ordering
SELECT name, step_order FROM workflow_step_entity 
WHERE stage_id = stage_id ORDER BY step_order;

-- Check prompt mappings
SELECT wse.name, sp.name as system_prompt, tp.name as task_prompt
FROM workflow_step_entity wse
LEFT JOIN workflow_step_prompt wsp ON wse.id = wsp.step_id
LEFT JOIN llm_prompt sp ON wsp.system_prompt_id = sp.id
LEFT JOIN llm_prompt tp ON wsp.task_prompt_id = tp.id
WHERE wse.id = step_id;
```

## Future Enhancements

### Planned Features
- Step dependencies and prerequisites
- Conditional step visibility
- Step templates and cloning
- Advanced step validation rules
- Step analytics and metrics

### Extensibility
- Plugin system for custom step types
- API for external step integrations
- Webhook support for step events
- Custom step configuration UI
