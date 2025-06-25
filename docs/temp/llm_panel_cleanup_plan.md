# LLM Panel Template Structure Cleanup Plan

## MANDATORY DIAGNOSTIC PROTOCOL

### Phase 0.1: Target Identification
- [ ] Locate and document each template component:
  ```
  1. Panel Base Template:
     - Current location: app/templates/modules/llm_panel/templates/panel.html
     - HTML structure: [document exact structure]
     - Unique identifiers: [list all IDs and classes]
     - Visual location: [describe where it appears in UI]
     
  2. Inputs Component:
     - Current location: app/templates/modules/llm_panel/templates/components/inputs.html
     - HTML structure: [document exact structure]
     - Unique identifiers: [list all IDs and classes]
     - Visual location: [describe where it appears in UI]
     
  3. Outputs Component:
     - Current location: app/templates/modules/llm_panel/templates/components/outputs.html
     - HTML structure: [document exact structure]
     - Unique identifiers: [list all IDs and classes]
     - Visual location: [describe where it appears in UI]
  ```

### Phase 0.2: Dependency Mapping
- [ ] For each template component, document ALL files that reference it:
  ```
  1. Panel Base Template Dependencies:
     a) Direct Control:
        - [file path]: [exact lines that control the panel]
        - [code example showing control mechanism]
     
     b) Supporting Functionality:
        - [file path]: [exact lines providing support]
        - [code example showing support mechanism]
     
     c) Incidental References:
        - [file path]: [exact lines with references]
        - [explanation of why reference exists]

  2. Inputs Component Dependencies:
     [same structure as above]

  3. Outputs Component Dependencies:
     [same structure as above]
  ```

### Phase 0.3: Change Impact Analysis
- [ ] For each proposed template move:
  ```
  1. Panel Base Template Move:
     - Current path: [exact current path]
     - Target path: [exact new path]
     - Files requiring update:
       a) [file path]:
          - Current code: [exact lines]
          - Proposed change: [exact new lines]
          - Impact proof: [explanation of why change is isolated]
          - Test cases: [specific tests to verify isolation]

  2. Inputs Component Move:
     [same structure as above]

  3. Outputs Component Move:
     [same structure as above]
  ```

### Phase 0.4: Isolation Verification
- [ ] For each component:
  ```
  1. Panel Base Template:
     - Interacting components:
       a) [component name]:
          - Interaction type: [how they interact]
          - Proof of isolation: [why move won't affect it]
          - Test case: [specific test to verify]
     
  2. Inputs Component:
     [same structure as above]
     
  3. Outputs Component:
     [same structure as above]
  ```

### Phase 0.5: Documentation Review
- [ ] Review all documentation files for references to template paths:
  ```
  1. [doc file path]:
     - Current references: [exact lines]
     - Required updates: [proposed changes]
     - Impact assessment: [why change is safe]
  ```

## VERIFICATION CHECKLIST
Before proceeding with ANY changes:
- [ ] All template components fully documented with exact structures
- [ ] All dependencies mapped and categorized
- [ ] All proposed changes documented with exact before/after code
- [ ] All isolation proofs documented with test cases
- [ ] All documentation impacts identified
- [ ] Review completed by another team member

## Current State Overview

### Active Template Locations
1. `app/templates/modules/llm_panel/templates/components/outputs.html` (currently active)
2. `app/templates/llm_panel_FUCKUP/` (deprecated)
3. `modules/llm_panel/templatesYETANOTHERFUCKUP/` (deprecated)

### Key Files and Dependencies
- **JavaScript**: `app/static/modules/llm_panel/js/panels.js`
- **Templates**: 
  - `app/templates/modules/llm_panel/templates/components/outputs.html`
  - `app/templates/modules/llm_panel/templates/components/inputs.html`
  - `app/templates/modules/llm_panel/templates/panel.html`
- **Endpoints**:
  - `/workflow/api/field_mappings/` (GET)
  - `/workflow/api/update_field_mapping/` (POST)
  - `/blog/api/v1/post/{post_id}/development` (GET/POST)

## Cleanup Steps

### Phase 1: Documentation and Backup
- [ ] Create git branch `cleanup/llm-panel-templates`
- [ ] Document current working state with comprehensive endpoint testing:
  ```bash
  # Test field mappings endpoint
  curl -s "http://localhost:5000/workflow/api/field_mappings/" | python3 -m json.tool

  # Test field mapping update
  curl -s -X POST "http://localhost:5000/workflow/api/update_field_mapping/" \
    -H "Content-Type: application/json" \
    -d '{"target_id":"input1", "field_name":"idea_seed", "section":"inputs"}' \
    | python3 -m json.tool

  # Test post development fields (using post ID 22 as example)
  curl -s "http://localhost:5000/blog/api/v1/post/22/development" | python3 -m json.tool

  # Test post development update
  curl -s -X POST "http://localhost:5000/blog/api/v1/post/22/development" \
    -H "Content-Type: application/json" \
    -d '{"idea_seed": "test value"}' \
    | python3 -m json.tool
  ```
- [ ] Save curl output to `docs/temp/llm_panel_pre_cleanup_state.md`

### Phase 2: Template Consolidation
- [ ] Create canonical template directory at `app/templates/modules/llm_panel/`:
  ```
  app/templates/modules/llm_panel/
  ├── components/
  │   ├── inputs.html
  │   └── outputs.html
  └── panel.html
  ```
- [ ] Test after directory creation using all documented endpoints

### Phase 3: Template Migration (One File at a Time)
- [ ] Migrate `panel.html`:
  1. Copy from working version to canonical location
  2. Update import paths
  3. Test all endpoints
  4. Verify field mapping functionality
  5. If working, delete old file

- [ ] Migrate `inputs.html`:
  1. Copy from working version to canonical location
  2. Update import paths
  3. Test field mappings endpoint
  4. Test field selection persistence
  5. If working, delete old file

- [ ] Migrate `outputs.html`:
  1. Copy from working version to canonical location
  2. Update import paths
  3. Test field mappings endpoint
  4. Test field value persistence
  5. If working, delete old file

### Phase 4: Clean Up Deprecated Directories
- [ ] Archive `app/templates/llm_panel_FUCKUP/`:
  1. Move to `backups/llm_panel_templates_backup_YYYY_MM_DD/`
  2. Test all endpoints
  3. If working, delete directory

- [ ] Archive `modules/llm_panel/templatesYETANOTHERFUCKUP/`:
  1. Move to `backups/llm_panel_templates_backup_YYYY_MM_DD/`
  2. Test all endpoints
  3. If working, delete directory

### Phase 5: Path Updates
- [ ] Update Flask route handlers:
  ```

## Execution Phases

### Phase 1: Documentation and Backup
- [ ] Create git branch `cleanup/llm-panel-templates`
- [ ] Document current working state with comprehensive endpoint testing:
  ```bash
  # Test field mappings endpoint
  curl -s "http://localhost:5000/workflow/api/field_mappings/" | python3 -m json.tool

  # Test field mapping update
  curl -s -X POST "http://localhost:5000/workflow/api/update_field_mapping/" \
    -H "Content-Type: application/json" \
    -d '{"target_id":"input1", "field_name":"idea_seed", "section":"inputs"}' \
    | python3 -m json.tool

  # Test post development fields (using post ID 22 as example)
  curl -s "http://localhost:5000/blog/api/v1/post/22/development" | python3 -m json.tool

  # Test post development update
  curl -s -X POST "http://localhost:5000/blog/api/v1/post/22/development" \
    -H "Content-Type: application/json" \
    -d '{"idea_seed": "test value"}' \
    | python3 -m json.tool
  ```
- [ ] Save curl output to `docs/temp/llm_panel_pre_cleanup_state.md`

### Phase 2: Template Consolidation
- [ ] Create canonical template directory at `app/templates/modules/llm_panel/`:
  ```
  app/templates/modules/llm_panel/
  ├── components/
  │   ├── inputs.html
  │   └── outputs.html
  └── panel.html
  ```
- [ ] Test after directory creation using all documented endpoints

### Phase 3: Template Migration (One File at a Time)
- [ ] Migrate `panel.html`:
  1. Copy from working version to canonical location
  2. Update import paths
  3. Test all endpoints
  4. Verify field mapping functionality
  5. If working, delete old file

- [ ] Migrate `inputs.html`:
  1. Copy from working version to canonical location
  2. Update import paths
  3. Test field mappings endpoint
  4. Test field selection persistence
  5. If working, delete old file

- [ ] Migrate `outputs.html`:
  1. Copy from working version to canonical location
  2. Update import paths
  3. Test field mappings endpoint
  4. Test field value persistence
  5. If working, delete old file

### Phase 4: Clean Up Deprecated Directories
- [ ] Archive `app/templates/llm_panel_FUCKUP/`:
  1. Move to `backups/llm_panel_templates_backup_YYYY_MM_DD/`
  2. Test all endpoints
  3. If working, delete directory

- [ ] Archive `modules/llm_panel/templatesYETANOTHERFUCKUP/`:
  1. Move to `backups/llm_panel_templates_backup_YYYY_MM_DD/`
  2. Test all endpoints
  3. If working, delete directory

### Phase 5: Path Updates
- [ ] Update Flask route handlers:
  ```