# Blog Post Development Workflow

## Overview
The blog uses a comprehensive workflow system to track post development from initial idea through to syndication. Each stage has specific requirements and validation rules to ensure quality and completeness.

## Workflow Stages

### 1. Idea
Initial concept formation and validation
- Basic idea definition
- Audience definition
- Value proposition

### 2. Research
Information gathering and verification
- Initial research
- Expert consultation (optional)
- Fact verification

### 3. Outlining
Content structure planning
- Section planning
- Flow optimization
- Resource planning

### 4. Authoring
Content development
- First draft
- Technical review
- Readability pass

### 5. Images
Visual content creation and optimization
- Image planning
- Generation
- Optimization
- Watermarking

### 6. Metadata
SEO and metadata optimization
- Basic metadata
- SEO optimization
- Social preview

### 7. Review
Quality assurance
- Self review
- Peer review (optional)
- Final check

### 8. Publishing
Content deployment
- Scheduling
- Deployment
- Verification

### 9. Updates
Post-publication maintenance
- Feedback collection
- Content updates (optional)
- Version control

### 10. Syndication
Platform distribution
- Platform selection
- Content adaptation
- Distribution
- Engagement tracking

## Stage Dependencies
Each stage has specific dependencies and validation requirements:
```json
{
  "idea": ["research"],
  "research": ["outlining", "idea"],
  "outlining": ["authoring", "research"],
  "authoring": ["images", "outlining"],
  "images": ["metadata", "authoring"],
  "metadata": ["review", "images"],
  "review": ["publishing", "metadata", "authoring"],
  "publishing": ["updates", "review"],
  "updates": ["syndication", "publishing"],
  "syndication": ["updates"]
}
```

## Validation Rules
Each stage has specific validation rules that must be satisfied before proceeding:

### Idea Stage
- Basic idea must be defined
- Target audience must be specified
- Value proposition must be clear

### Research Stage
- Research notes must be documented
- Key facts must be verified
- Expert consultation notes (if applicable)

### Outlining Stage
- Sections must be defined
- Content flow must be reviewed
- Required resources must be listed

### Authoring Stage
- Content must not be empty
- Technical accuracy must be verified
- Readability must be checked

### Images Stage
- Image plan must be complete
- All required images must be generated
- Images must be optimized
- Images must be watermarked

### Metadata Stage
- Basic metadata must be complete
- SEO optimization must be complete
- Social preview must be configured

### Review Stage
- Self-review must be completed
- Peer review must be documented (if required)
- Final check must be completed

### Publishing Stage
- Publication date must be set
- Content must be deployed
- Live verification must be completed

### Updates Stage
- Feedback must be collected
- Updates must be tracked
- Version history must be maintained

### Syndication Stage
- Platforms must be selected
- Content must be adapted
- Distribution must be completed
- Engagement tracking must be set up

## API Endpoints

### Get Workflow Status
```http
GET /api/v1/posts/<slug>/workflow/status
```

### Update Stage
```http
POST /api/v1/posts/<slug>/workflow/transition
{
  "target_stage": "string",
  "notes": "string"
}
```

### Update Sub-stage
```http
POST /api/v1/posts/<slug>/workflow/sub-stage
{
  "sub_stage": "string",
  "status": "string",
  "note": "string"
}
```

### Get History
```http
GET /api/v1/posts/<slug>/workflow/history
```

## Stage Data Structure
Each stage maintains its data in the following format:
```json
{
  "started_at": "ISO datetime",
  "sub_stages": {
    "sub_stage_name": {
      "status": "not_started|in_progress|completed|blocked|skipped",
      "started_at": "ISO datetime",
      "completed_at": "ISO datetime",
      "notes": [
        {
          "text": "string",
          "timestamp": "ISO datetime"
        }
      ]
    }
  }
}
```

# Workflow Data Model (Normalized SQL)

## Overview

The workflow system is now fully normalized in SQL, providing robust, queryable, and future-proof tracking of post development stages and sub-stages.

## Tables

- **WorkflowStageEntity**: Defines each workflow stage (e.g., Idea, Research, Authoring).
- **WorkflowSubStageEntity**: Defines sub-stages for each stage (e.g., Basic Idea, Audience Definition).
- **PostWorkflowStage**: Tracks a post's progress in a given stage (status, timestamps, etc.).
- **PostWorkflowSubStage**: Tracks a post's progress/content in a sub-stage (content, status, notes, timestamps).

## Relationships

- Each `WorkflowStageEntity` can have multiple `WorkflowSubStageEntity` children.
- Each `Post` can have multiple `PostWorkflowStage` records (one per stage).
- Each `PostWorkflowStage` can have multiple `PostWorkflowSubStage` records (one per sub-stage).

## Rationale

- **Data Integrity**: SQL constraints ensure valid relationships and prevent orphaned data.
- **Queryability**: Easily filter, sort, and aggregate workflow progress across posts.
- **Robustness**: Schema changes (adding/removing stages/sub-stages) are explicit and safe.
- **Migration-Friendly**: Future changes to the workflow structure are handled via SQL migrations, not ad-hoc JSON updates.

## Migration

Existing workflow data in JSON will be migrated to the new structure. See `scripts/update_workflow.py` for details.

## Example Usage

- To get all posts in the 'Authoring' stage: join `PostWorkflowStage` with `WorkflowStageEntity`.
- To get all sub-stages for a post: join `PostWorkflowSubStage` with `WorkflowSubStageEntity`.

## Next Steps

- Update all backend logic and templates to use the new models.
- Remove the old JSON-based workflow fields after migration is complete. 