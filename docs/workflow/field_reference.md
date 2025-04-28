# Workflow Field Reference and Data Binding

## 1. Field Names and Values

### Stages and Sub-Stages
Defined in `app/workflow/constants.py` and documented in `docs/workflow/stages.md`:

- **Idea**
  - `basic_idea`
  - `audience_definition`
  - `value_proposition`
- **Research**
  - `initial_research`
  - `expert_consultation`
  - `fact_verification`
- **Outlining**
  - `section_planning`
  - `flow_optimization`
  - `resource_planning`
- **Authoring**
  - `first_draft`
  - `technical_review`
  - `readability_pass`
- **Images**
  - `image_planning`
  - `generation`
  - `optimization`
  - `watermarking`
- **Metadata**
  - `basic_meta`
  - `seo_optimization`
  - `social_preview`
- **Review**
  - `self_review`
  - `peer_review`
  - `final_check`
- **Publishing**
  - `scheduling`
  - `deployment`
  - `verification`
- **Updates**
  - `feedback_collection`
  - `content_updates`
  - `version_control`
- **Syndication**
  - `platform_selection`
  - `content_adaptation`
  - `distribution`
  - `engagement_tracking`

---

## 2. API Endpoints and Data Formats

### Sub-Stage Content Update
- **Endpoint:** `POST /api/v1/workflow/<slug>/sub-stage`
- **Request Body:**
  ```json
  {
    "post_workflow_stage_id": <int>,
    "sub_stage_id": <int>,
    "content": <string>
  }
  ```
  - `post_workflow_stage_id`: Integer, the ID of the parent stage instance for the post.
  - `sub_stage_id`: Integer, the ID of the sub-stage (not the string name).
  - `content`: String, the content to save.

- **Response:**
  ```json
  {
    "status": "success",
    "message": "Sub-stage updated successfully"
  }
  ```

---

## 3. Frontend Data Binding and Field Mapping

### HTML Structure
- Each sub-stage is rendered as:
  ```html
  <div class="sub-stage" id="sub-stage-{{ sub_stage_id }}"
       data-post-workflow-stage-id="{{ post_workflow_stage_id }}"
       data-sub-stage-id="{{ sub_stage_id }}">
    ...
    <textarea class="content-editor-field" id="content-{{ sub_stage_id }}"
              data-substage="{{ sub_stage_id }}"></textarea>
    ...
    <button class="save-content-btn" id="save-{{ sub_stage_id }}"
            onclick="saveSubStageContent('{{ sub_stage_id }}')" disabled>
      Save Changes
    </button>
  </div>
  ```
- The `data-post-workflow-stage-id` and `data-sub-stage-id` attributes must be set to the correct integer IDs.

### JavaScript Save Logic
- The save function collects these attributes and sends them to the backend:
  ```js
  const subStageEl = document.getElementById(`sub-stage-${subStageId}`);
  fetch(`/api/v1/workflow/${postSlug}/sub-stage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      post_workflow_stage_id: subStageEl.dataset.postWorkflowStageId,
      sub_stage_id: subStageEl.dataset.subStageId,
      content: content
    })
  });
  ```
- **If `data-sub-stage-id` is not an integer, the backend will fail.**

---

## 4. Backend Data Model

- **WorkflowStageEntity**: Table of stages (`id`, `name`, ...)
- **WorkflowSubStageEntity**: Table of sub-stages (`id`, `stage_id`, `name`, ...)
- **PostWorkflowStage**: Instance of a stage for a post (`id`, `post_id`, `stage_id`, ...)
- **PostWorkflowSubStage**: Instance of a sub-stage for a post (`id`, `post_workflow_stage_id`, `sub_stage_id`, `content`, ...)

---

## 5. Validation and Consistency Checklist

- **Every sub-stage field in the UI** must have:
  - `data-post-workflow-stage-id` set to the correct integer (from `post_workflow_stage_id_map[stage]`)
  - `data-sub-stage-id` set to the correct integer (from the normalized DB, not the string name)
- **The save function** must send these as integers in the JSON payload.
- **The backend** expects integer IDs for both `post_workflow_stage_id` and `sub_stage_id`.

---

## 6. Debugging Steps for Sub-Stage Save Issues

- If a sub-stage (e.g., "basic idea") is not saving but others are:
  - Check if `data-sub-stage-id` for that field is a string (e.g., "basic_idea") instead of the integer sub-stage ID.
  - Check if the mapping from sub-stage name to sub-stage ID is missing or broken for that sub-stage.
  - Check if the backend is receiving the correct integer for `sub_stage_id` in the POST payload.
  - Check backend logs for errors and payloads.

---

## 7. Implementation Notes

- All stages and sub-stages are initialized during post creation.
- Each stage can be edited independently.
- Validation occurs at key points rather than during editing.
- Progress tracking is maintained for all stages.
- The UI indicates recommended next stages while allowing access to all stages.

---

**This document should be kept up to date with any changes to the workflow system, field names, or data binding logic.**

> **Note:** All workflow stages and sub-stages are initialized for every post at creation, enabling asynchronous editing. The seeding script (`scripts/update_workflow.py`) ensures all stages and sub-stages are present in the database. There is no longer any sequential or partial initialization—authors can work on any stage or sub-stage at any time. 