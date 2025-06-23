# Required Navigation System Files

## Core Database Access Layer

### Database Models (`app/workflow/models.py`)
Must define the three-level hierarchy:
```python
class WorkflowStageEntity:
    id: Integer
    name: String  # e.g., "planning"
    description: String
    stage_order: Integer

class WorkflowSubStageEntity:
    id: Integer
    stage_id: ForeignKey(WorkflowStageEntity)
    name: String  # e.g., "idea"
    description: String
    sub_stage_order: Integer

class WorkflowStepEntity:
    id: Integer
    sub_stage_id: ForeignKey(WorkflowSubStageEntity)
    name: String  # e.g., "Idea Seed"
    description: String
    step_order: Integer
```

### Navigation Service (`app/workflow/navigation.py`)
Must provide methods to:
1. Get complete workflow hierarchy
2. Get specific stage/substage/step by name
3. Get next/previous step respecting hierarchy
4. Validate stage/substage/step combinations

Example methods:
```python
def get_workflow_structure():
    """Return complete three-level hierarchy from database."""

def get_step(stage_name, substage_name, step_name):
    """Get specific step, validating full path exists."""

def get_next_step(current_stage, current_substage, current_step):
    """Get next step, handling transitions between substages/stages."""
```

## Templates

### Base Layout (`app/templates/workflow/base.html`)
- Must include navigation component
- Must provide blocks for step-specific content
- Must handle all three hierarchy levels in breadcrumbs

### Navigation Component (`app/templates/workflow/_workflow_nav.html`)
Must reflect the three-level hierarchy:
```html
<nav class="workflow-nav">
    {% for stage in stages %}
        <div class="stage">
            <h2>{{ stage.name }}</h2>
            {% for substage in stage.substages %}
                <div class="substage">
                    <h3>{{ substage.name }}</h3>
                    {% for step in substage.steps %}
                        <a href="{{ url_for('workflow.step',
                                          post_id=post.id,
                                          stage_name=stage.name,
                                          substage_name=substage.name,
                                          step_name=step.name) }}"
                           class="step {% if step.is_current %}active{% endif %}">
                            {{ step.name }}
                        </a>
                    {% endfor %}
                </div>
            {% endfor %}
        </div>
    {% endfor %}
</nav>
```

### Step Templates (`app/templates/workflow/steps/`)
- One template per step
- Names MUST match database exactly
- Example structure:
  ```
  steps/
  ├── Planning Stage/
  │   ├── Idea/
  │   │   ├── Idea Scope.html
  │   │   ├── Idea Seed.html
  │   │   ├── Initial.html
  │   │   └── Provisional Title.html
  │   ├── Research/
  │   │   ├── Interesting Facts.html
  │   │   ├── Research Notes.html
  │   │   └── Topics To Cover.html
  │   └── Structure/
  │       ├── Allocate Facts.html
  │       ├── Main.html
  │       ├── Section Headings.html
  │       ├── Section Order.html
  │       └── Structure.html
  ├── Writing Stage/
  │   ├── Content/
  │   │   └── Sections.html
  │   ├── Meta/
  │   │   └── Main.html
  │   └── Images/
  │       └── Main.html
  └── Publishing Stage/
      ├── Preflight/
      │   ├── Final Check.html
      │   ├── Peer Review.html
      │   ├── SEO Optimization.html
      │   ├── Self Review.html
      │   └── Tartans Products.html
      ├── Launch/
      │   ├── Deployment.html
      │   ├── Scheduling.html
      │   └── Verification.html
      └── Syndication/
          ├── Content Adaptation.html
          ├── Content Distribution.html
          ├── Content Updates.html
          ├── Engagement Tracking.html
          ├── Feedback Collection.html
          ├── Platform Selection.html
          └── Version Control.html
  ```

## Routes

### Workflow Routes (`app/workflow/routes.py`)
Must handle the three-level hierarchy:
```python
@bp.route('/<int:post_id>/<stage_name>/<substage_name>/<step_name>/')
def step(post_id, stage_name, substage_name, step_name):
    """
    1. Validate stage exists
    2. Validate substage exists in stage
    3. Validate step exists in substage
    4. Load appropriate template
    5. Pass complete hierarchy to template
    """
```

## Integration Points

### Post Creation (`app/blog/routes.py`)
Must redirect to first step using database hierarchy:
```python
@bp.route('/create_post', methods=['POST'])
def create_post():
    post = create_new_post()
    first_step = get_first_workflow_step()  # From database
    return redirect(url_for('workflow.step',
                          post_id=post.id,
                          stage_name=first_step.stage_name,
                          substage_name=first_step.substage_name,
                          step_name=first_step.step_name))
```

### Templates Using Workflow Links
Must use complete hierarchy in URLs:
```html
<a href="{{ url_for('workflow.step',
                    post_id=post.id,
                    stage_name='planning',
                    substage_name='idea',
                    step_name='Idea Seed') }}">
    Start Workflow
</a>
```

## Required Database Functions

### Structure Queries
```python
def get_workflow_structure():
    """Return complete stage/substage/step hierarchy."""
    return db.session.query(WorkflowStageEntity)\\
                    .options(joinedload(WorkflowStageEntity.substages)\\
                            .joinedload(WorkflowSubStageEntity.steps))\\
                    .order_by(WorkflowStageEntity.stage_order)\\
                    .all()

def get_step(stage_name, substage_name, step_name):
    """Validate and return specific step."""
    return db.session.query(WorkflowStepEntity)\\
                    .join(WorkflowSubStageEntity)\\
                    .join(WorkflowStageEntity)\\
                    .filter(WorkflowStageEntity.name == stage_name,
                           WorkflowSubStageEntity.name == substage_name,
                           WorkflowStepEntity.name == step_name)\\
                    .first()
```

## Testing Requirements

### Unit Tests
1. Test database models enforce hierarchy
2. Test navigation functions respect order
3. Test step validation
4. Test template rendering
5. Test URL generation

### Integration Tests
1. Test complete workflow navigation
2. Test invalid combinations return 404
3. Test step transitions
4. Test breadcrumb generation

### URL Structure Tests
Must verify URLs follow pattern:
```
/workflow/<post_id>/<stage_name>/<substage_name>/<step_name>/
```

## Success Criteria
1. All navigation driven by database
2. Complete hierarchy respected
3. No hardcoded paths
4. All templates match database names
5. All tests pass 