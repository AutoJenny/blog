# Blog Post Workflow Stages

The blog post workflow is fully asynchronous, allowing authors to work on any stage or sub-stage at any time. Each stage has three possible statuses:

- `NOT_STARTED`
- `IN_PROGRESS`
- `COMPLETED`

The development interface (`app/templates/blog/development.html`) provides a rich editing environment for managing all stages and sub-stages, including LLM-assisted content generation for various fields. See the Development Documentation for details on the interface functionality.

> **Note:** As of the latest update, the workflow system is fully asynchronous. All stages and sub-stages are initialized for every post at creation, enabling editing in any order. The seeding script (`scripts/update_workflow.py`) ensures that all workflow stages and sub-stages are present in the database. There is no longer any sequential or partial initialization—authors can work on any stage or sub-stage at any time. Validation and required fields are enforced only at key transitions (e.g., publishing).

## Overview
The blog post workflow is divided into multiple stages, each with its own sub-stages. All stages are initialized at post creation and can be worked on in any order. While there is a recommended progression through stages, the workflow is asynchronous to allow for flexible content development.

Each stage and sub-stage can have one of three statuses:
- `NOT_STARTED`: Default state when initialized
- `IN_PROGRESS`: Work has begun but is not complete
- `COMPLETED`: All validation rules are satisfied

## Stage Progression
While stages can be worked on in any order, the recommended progression is:

1. Idea Stage
2. Research Stage
3. Outlining Stage
4. Authoring Stage
5. Images Stage
6. Metadata Stage
7. Review Stage
8. Publishing Stage
9. Updates Stage
10. Syndication Stage

This progression ensures a logical flow of content development but is not enforced. Authors can work on any stage at any time based on their needs and workflow preferences.

## Detailed Stage Descriptions

### 1. Idea Stage
**Description**: Initial concept and basic idea formation

**Sub-stages**:
- **Basic Idea**
  - Required: Yes
  - Validation: Content must not be empty
  - Dependencies: None

- **Audience Definition**
  - Required: Yes
  - Validation: Must define target audience
  - Dependencies: Basic Idea

- **Value Proposition**
  - Required: Yes
  - Validation: Must define value proposition
  - Dependencies: Audience Definition

### 2. Research Stage
**Description**: Research and information gathering

**Sub-stages**:
- **Initial Research**
  - Required: Yes
  - Validation: Must have research notes
  - Dependencies: None

- **Expert Consultation**
  - Required: No
  - Validation: Must have expert notes
  - Dependencies: Initial Research

- **Fact Verification**
  - Required: Yes
  - Validation: Facts must be verified
  - Dependencies: Initial Research

### 3. Outlining Stage
**Description**: Post structure and outline creation

**Sub-stages**:
- **Section Planning**
  - Required: Yes
  - Validation: Sections must be defined
  - Dependencies: None

- **Flow Optimization**
  - Required: Yes
  - Validation: Flow must be reviewed
  - Dependencies: Section Planning

- **Resource Planning**
  - Required: Yes
  - Validation: Resources must be listed
  - Dependencies: Section Planning

### 4. Authoring Stage
**Description**: Content writing and development

**Sub-stages**:
- **First Draft**
  - Required: Yes
  - Validation: Content must not be empty
  - Dependencies: None

- **Technical Review**
  - Required: Yes
  - Validation: Must be technically reviewed
  - Dependencies: First Draft

- **Readability Pass**
  - Required: Yes
  - Validation: Must check readability
  - Dependencies: First Draft

### 5. Images Stage
**Description**: Image creation and optimization

**Sub-stages**:
- **Image Planning**
  - Required: Yes
  - Validation: Image plan must be complete
  - Dependencies: None

- **Generation**
  - Required: Yes
  - Validation: Images must be generated
  - Dependencies: Image Planning

- **Optimization**
  - Required: Yes
  - Validation: Images must be optimized
  - Dependencies: Generation

- **Watermarking**
  - Required: Yes
  - Validation: Images must be watermarked
  - Dependencies: Optimization

### 6. Metadata Stage
**Description**: SEO and metadata optimization

**Sub-stages**:
- **Basic Metadata**
  - Required: Yes
  - Validation: Basic meta must be complete
  - Dependencies: None

- **SEO Optimization**
  - Required: Yes
  - Validation: Must be SEO optimized
  - Dependencies: Basic Metadata

- **Social Preview**
  - Required: Yes
  - Validation: Social preview must be complete
  - Dependencies: Basic Metadata

### 7. Review Stage
**Description**: Content review and quality assurance

**Sub-stages**:
- **Self Review**
  - Required: Yes
  - Validation: Must be self-reviewed
  - Dependencies: None

- **Peer Review**
  - Required: No
  - Validation: Must be peer-reviewed
  - Dependencies: Self Review

- **Final Check**
  - Required: Yes
  - Validation: Must have final check
  - Dependencies: Self Review

### 8. Publishing Stage
**Description**: Content publishing and deployment

**Sub-stages**:
- **Scheduling**
  - Required: Yes
  - Validation: Must set schedule
  - Dependencies: None

- **Deployment**
  - Required: Yes
  - Validation: Must be deployed
  - Dependencies: Scheduling

- **Verification**
  - Required: Yes
  - Validation: Must verify live content
  - Dependencies: Deployment

### 9. Updates Stage
**Description**: Post-publication updates and maintenance

**Sub-stages**:
- **Feedback Collection**
  - Required: Yes
  - Validation: Must collect feedback
  - Dependencies: None

- **Content Updates**
  - Required: No
  - Validation: Must apply updates
  - Dependencies: Feedback Collection

- **Version Control**
  - Required: Yes
  - Validation: Must track versions
  - Dependencies: Content Updates

### 10. Syndication Stage
**Description**: Content syndication across platforms

**Sub-stages**:
- **Platform Selection**
  - Required: Yes
  - Validation: Must select platforms
  - Dependencies: None

- **Content Adaptation**
  - Required: Yes
  - Validation: Must adapt content
  - Dependencies: Platform Selection

- **Distribution**
  - Required: Yes
  - Validation: Must distribute content
  - Dependencies: Content Adaptation

- **Engagement Tracking**
  - Required: Yes
  - Validation: Must setup tracking
  - Dependencies: Distribution

## Stage Transitions
Stage transitions are flexible and allow moving to any stage at any time. However, certain actions (like publishing) require all mandatory sub-stages to be completed and validated. The recommended transitions are:

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

These transitions are suggestions for optimal workflow but are not enforced during editing.

## Validation Rules
While editing is asynchronous, validation rules are enforced at key points (e.g., publishing):

Each validation rule ensures specific criteria are met before marking a sub-stage as complete:

1. `basic_idea_not_empty`: Ensures the basic idea content is provided
2. `audience_defined`: Verifies audience definition is complete
3. `value_prop_defined`: Checks value proposition is defined
4. `research_notes_added`: Verifies research notes exist
5. `expert_notes_added`: Checks for expert consultation notes
6. `facts_verified`: Ensures facts have been verified
7. `sections_defined`: Verifies section structure is defined
8. `flow_reviewed`: Checks content flow has been reviewed
9. `resources_listed`: Ensures required resources are listed
10. `content_not_empty`: Verifies content exists
11. `tech_reviewed`: Ensures technical review is complete
12. `readability_checked`: Verifies readability check is done
13. `image_plan_complete`: Checks image plan exists
14. `images_generated`: Verifies images are generated
15. `images_optimized`: Ensures images are optimized
16. `images_watermarked`: Checks images are watermarked
17. `basic_meta_complete`: Verifies basic metadata exists
18. `seo_optimized`: Ensures SEO optimization is complete
19. `social_preview_complete`: Checks social preview is ready
20. `self_reviewed`: Verifies self-review is complete
21. `peer_reviewed`: Checks peer review is done
22. `final_checked`: Ensures final check is complete
23. `schedule_set`: Verifies publication schedule exists
24. `deployed`: Checks content is deployed
25. `verified_live`: Ensures content is live and verified
26. `feedback_collected`: Verifies feedback collection
27. `updates_applied`: Checks updates are applied
28. `version_tracked`: Ensures version tracking is in place
29. `platforms_selected`: Verifies platforms are selected
30. `content_adapted`: Checks content is adapted
31. `distributed`: Ensures content is distributed
32. `tracking_setup`: Verifies tracking is configured

**Frontend Note:**

Sub-stage updates in the workflow UI now use element lookup by subStageId and dataset attributes for accurate data binding. The previous use of `this.closest` has been replaced to avoid errors and ensure correct updates.

## Sub-Stage Field Mapping and Data Binding

- Each sub-stage field in the workflow UI must be mapped to a corresponding backend value in the `stage_data` JSON of the `workflow_status` table.
- Frontend updates to sub-stage fields should use the `subStageId` and dataset attributes for precise data binding and saving.
- Avoid static field definitions; always ensure the UI reflects the current backend state for each sub-stage.
- Refer to the API documentation for the correct structure of update requests and expected responses.

## Implementation Notes
- All stages and sub-stages are initialized during post creation
- Each stage can be edited independently
- Validation occurs at key points rather than during editing
- Progress tracking is maintained for all stages
- The UI indicates recommended next stages while allowing access to all stages

### Development Stage

The Development Stage is where the main content of the blog post is written and refined. This stage includes:

#### Sub-stages:
1. **Initial Draft**: Create the first draft of the post content. The development interface provides LLM-assisted content generation using customizable templates for different sections and fields.
2. **Technical Review**: Review and validate technical accuracy
3. **Editorial Review**: Review for style, clarity, and consistency
4. **Final Draft**: Incorporate feedback and finalize content

#### Required:
- Post content must be complete
- All sections must be reviewed
- Technical accuracy must be verified
- Editorial standards must be met

#### Dependencies:
- Research Stage must be `COMPLETED` 