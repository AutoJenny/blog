# Blog Post Development Workflow

## Overview
The blog uses a comprehensive workflow system to track post development from initial idea through to syndication. Each stage has specific requirements and validation rules to ensure quality and completeness. **The workflow is asynchronous: all stages and sub-stages are initialized at post creation, and authors can work on any stage or sub-stage at any time.** Validation occurs at key points like publishing, not during editing.

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
While stages can be worked on in any order, there are recommended dependencies for optimal content development:
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
These dependencies are suggestions for optimal workflow but are not enforced. **All stages and sub-stages are available for editing at any time.**

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

## API Reference

For a complete reference of all workflow-related API endpoints, including:
- Workflow status management
- Stage transitions
- Sub-stage updates and validation
- Progress tracking
- Workflow history

Please refer to the [Workflow API Documentation](../api/workflow.md).

## API Endpoints (Normalized SQL)

### Get Workflow Status
```http
GET /api/v1/workflow/<slug>/status
```

### Update Stage
```http
POST /api/v1/workflow/<slug>/transition
{
  "target_stage": "string",
  "notes": "string"
}
```

### Update Sub-stage
```http
POST /api/v1/workflow/<slug>/sub-stage
{
  "post_workflow_stage_id": <int>,
  "sub_stage_id": <int>,
  "status": "string",
  "note": "string",
  "content": "string"
}
```

### Get History
```http
GET /api/v1/workflow/<slug>/history
```

**Note:** All stages and sub-stages are initialized during post creation, enabling asynchronous editing of any stage or sub-stage at any time. The workflow tables must be seeded before use. See `scripts/update_workflow.py` for the seeding script and example data.

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

- All stages and sub-stages are now initialized at post creation
- Asynchronous editing is enabled for all stages and sub-stages
- Validation occurs at key points (e.g., publishing) rather than during editing
- Legacy JSON-based workflow fields will be removed after migration is complete

## Sub-Stage Updates

Sub-stage content is now saved using element lookup by subStageId (e.g., `document.getElementById('sub-stage-' + subStageId)`) and dataset attributes for correct data binding. This replaces the previous approach that relied on `this.closest`, which caused errors in some contexts.

## Frontend Workflow UI: Sub-Stage Data Binding

- All sub-stage fields in the workflow UI must be dynamically bound to backend values from the `stage_data` JSON in the `workflow_status` table.
- Sub-stage updates are performed by looking up the relevant element by its `subStageId` and using dataset attributes for data binding.
- Do not use static field definitions or rely on `this.closest` for DOM traversal; always use explicit element lookup and backend-driven data.
- See API documentation for correct sub-stage update endpoints and payload structure.

### Seeding and Initialization

Workflow tables must be seeded before use. The script `scripts/update_workflow.py` seeds all workflow stages and sub-stages into the database, ensuring the normalized SQL tables are fully populated. As of the latest update, when a new post is created, **all** stages and sub-stages are initialized for that post, enabling asynchronous editing—authors can work on any stage or sub-stage at any time. There is no longer any sequential or partial initialization. Legacy JSON-based workflow fields are deprecated and will be removed after migration is complete. 