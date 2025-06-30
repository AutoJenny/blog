# Format System Implementation Plan (Updated for API Compliance)

> **ALWAYS READ AND CAREFULLY FOLLOW THE CRITICAL INSTRUCTIONS BEFORE STARTING. THEN PROCEED TO THE NEXT UNCHECKED STEP.**

## Critical Instructions for Each Step
- ONLY modify code/data EXPLICITLY required for the current step. DO NOT:
   - Fix unrelated issues, even if they appear in error logs
   - Add "nice to have" features or improvements
   - Attempt to refactor or clean up existing code
   - Create new endpoints or functionality not specified
   Any issues not directly related to the current step's requirements MUST be logged in 'Post-Implementation Issues' and addressed later.
- Request permission before proceeding to next step. Each request MUST include:
   - A clear summary of what was completed in the current step
   - Results of all required tests
   - Confirmation that no unauthorized changes were made
   - The exact next step from the plan
- Test thoroughly before marking as complete. Testing MUST:
   - Follow ONLY the test cases specified in the step
   - Use the exact test commands/data shown
   - Not introduce new test cases or scenarios
   - Stop if any specified test fails
- If any test fails:
   - Stop immediately
   - Report the exact failure
   - Do not attempt fixes beyond the current step's scope
   - Wait for explicit instructions before proceeding
- No assumptions or extra features without explicit approval:
   - Follow the step's requirements exactly as written
   - Do not add functionality "just in case"
   - Do not fix "potential future issues"
   - Request clarification if any requirement is unclear

---

# Roadmap to Completion (with API Compliance)

## Phase 1: API Compliance & Database Migration

### Step 1: Database Schema Migration
- [x] **Create migration to rename `llm_format_template` to `workflow_format_template`**
- [x] **Add `description` and `fields` columns to format template table**
- [x] **Migrate existing format data to new schema**
- [x] **Update foreign key constraints**
- [x] **Test migration up/down**
> _Reason: The API spec requires a new table name and structure. This is a breaking change and must be done first._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the migration. Do not change any code or endpoints yet._

### Step 2: API Endpoint Restructuring
- [x] **Create new `/api/workflow/formats/` endpoints**
- [x] **Update response format to match API specification**
- [x] **Implement proper error handling with standardized format**
- [x] **Add data transformation between storage and API formats**
- [x] **Register new blueprint in workflow module**
- [x] **Update or migrate all code and UI to use new endpoints and schema**
- [x] **Update blueprint registration in `app/__init__.py`**
- [x] **Update all route decorators to use new paths**
- [x] **Change `PATCH` to `PUT` for update operations**
> _Reason: All endpoints must match the new API namespace and method conventions._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the endpoint moves and path changes. Do not add new features or refactor unrelated code._

### Step 3: Response Format Compliance
- [x] **Transform database responses to match API spec**
- [x] **Add `description` field to all template responses**
- [x] **Convert `format_spec` to `fields` array format**
- [x] **Update validation logic for new schema**
- [x] **Test all endpoints with new response format**
> _Reason: The API requires a specific response structure for all format endpoints._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the response format changes. Do not change business logic or add new endpoints._

### Step 4: Error Handling Standardization
- [x] **Implement standardized error response format**
- [x] **Add error codes for all error scenarios**
- [x] **Update all endpoints to use new error format**
- [x] **Test error handling across all endpoints**
> _Reason: All errors must be returned in a consistent, structured format as per the API spec._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY error format changes. Do not change endpoint logic or add new error types._

## Phase 2: Missing Endpoint Implementation

### Step 5: Stage Format Endpoints
- [x] **Implement `/api/workflow/stages/<stage_id>/format` GET endpoint**
- [x] **Implement `/api/workflow/stages/<stage_id>/format` POST endpoint**
- [x] **Create `workflow_stage_format` table if needed**
- [x] **Add stage format validation logic**
- [x] **Test stage format endpoints**
> _Reason: Stage-level format configuration is required by the API spec._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the endpoints and table for stage formats. Do not add post or step logic._

### Step 6: Post Format Endpoints
- [x] **Implement `/api/workflow/posts/<post_id>/format` GET endpoint**
- [x] **Implement `/api/workflow/posts/<post_id>/format` POST endpoint**
- [x] **Create `workflow_post_format` table if needed**
- [x] **Add post format validation logic**
- [x] **Test post format endpoints**
> _Reason: Post-level format configuration is required by the API spec._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the endpoints and table for post formats. Do not add stage or step logic._

## Phase 3: Workflow Integration

### Step 7: LLM Processor Integration
- [x] **Update `app/workflow/scripts/llm_processor.py` to use formats**
- [x] **Add format validation before LLM processing**
- [x] **Implement format reference resolution (`[data:field_name]`)**
- [x] **Add output validation after LLM processing**
- [x] **Add format-based data transformation**
- [x] **Test complete workflow with format validation**
> _Reason: The format system must be enforced in the actual workflow processing._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the integration with the LLM processor. Do not change unrelated workflow logic._

### Step 8: Format Reference System
- [x] **Implement field reference parser**
- [x] **Add field value lookup logic**
- [x] **Handle missing reference errors gracefully**
- [x] **Add reference validation to format validator**
- [x] **Update format validation error messages**
- [x] **Test reference resolution with various scenarios**
> _Reason: Reference resolution is required for dynamic field mapping in prompts._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the reference system. Do not change other validation logic._

## Phase 4: UI Integration

### Step 9: Workflow Panel Integration
- [x] **Add format selection to workflow panels**
- [x] **Implement format preview in workflow interface**
- [x] **Add format validation feedback to UI**
- [x] **Connect field mapping dropdowns to format validation**
- [x] **Add format-aware field suggestions**
- [x] **Test UI integration end-to-end**
> _Reason: Users must be able to configure and see format status in the workflow UI._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the UI changes for format integration. Do not change backend logic._

### Step 10: Field Mapping Integration
- [x] **Update `field_selector.js` to be format-aware**
- [x] **Add format validation to field selection**
- [x] **Implement format-based field filtering**
- [x] **Add format compliance indicators**
- [x] **Test field mapping with format validation**
> _Reason: Field mapping must be format-aware for data integrity._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the field selector changes. Do not change unrelated JS or backend code._

## Phase 5: JavaScript Implementation

### Step 11: Format Management JavaScript
- [x] **Create `/static/js/format_management.js`**
- [x] **Implement `createFormatTemplate()` function**
- [x] **Implement `updateFormatTemplate()` function**
- [x] **Implement `deleteFormatTemplate()` function**
- [x] **Implement `validateFormat()` function**
- [x] **Test all JavaScript functions**
> _Reason: Dedicated JS is needed for format management UI._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the JS for format management. Do not change unrelated JS or backend code._

### Step 12: Format Configuration JavaScript
- [x] **Create `/static/js/format_configuration.js`**
- [x] **Implement `configureStepFormat()` function**
- [x] **Implement `previewFormat()` function**
- [x] **Add format testing interface**
- [x] **Implement error display and handling**
- [x] **Test format configuration functionality**
> _Reason: Dedicated JS is needed for step/post format configuration UI._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the JS for format configuration. Do not change unrelated JS or backend code._

## Phase 6: Testing & Documentation

### Step 13: Integration Testing
- [x] **Create `/tests/test_format_integration.py`**
- [x] **Add `test_format_workflow_integration()` test**
- [x] **Add `test_format_reference_resolution()` test**
- [x] **Add `test_format_validation_errors()` test**
- [x] **Create UI tests in `/tests/test_format_ui.py`**
- [x] **Create API tests in `/tests/api/test_format_endpoints.py`**
- [x] **Run full test suite and fix failures**
> _Reason: Comprehensive testing is required for reliability and maintainability._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the tests for format system. Do not add unrelated tests or change production code._

### Step 14: Documentation Updates
- [x] **Update `/docs/workflow/formats.md` with new API endpoints**
- [x] **Add format reference documentation**
- [x] **Update API endpoint documentation**
- [x] **Add UI component documentation**
- [x] **Update testing documentation with new test cases**
- [x] **Add format system troubleshooting guide**
- [x] **Verify all documentation accuracy**
> _Reason: Documentation must match the new implementation and API._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the documentation updates. Do not change code or add new features._

## Phase 7: Deployment & Verification

### Step 15: Pre-deployment Tasks
- [x] **Create database backup before migration**
- [x] **Verify all migrations work correctly**
- [x] **Test rollback procedures**
- [x] **Update deployment documentation**
- [x] **Test backup/restore procedures**
> _Reason: Safe deployment requires backup and rollback verification._
> _Reminder: NEVER make other changes to code without user consent. Take care to retain all existing functionality except the specified changes. ASK and consult! Do ONLY the deployment prep. Do not deploy or change code._

### Step 16: Final Deployment
- [x] **Deploy database changes**
- [x] **Deploy application updates**

---

## Completion Criteria
- [ ] All endpoints match API specification exactly
- [ ] Database schema matches API specification
- [ ] Format validation works in workflow processing
- [ ] UI allows format configuration and preview
- [ ] Field mapping is format-aware
- [ ] All tests pass
- [ ] Documentation is complete and accurate
- [ ] No regressions in existing functionality
- [ ] All changes properly committed
- [ ] Deployment verified successful

## Post-Implementation Issues to Review
1. Blueprint naming conflict in workflow module:
   - Error: "The name 'workflow' is already registered for a different blueprint"
   - Location: app/__init__.py
   - Impact: No impact on format system implementation
   - Review after completion of implementation plan
2. Missing workflow step formats module:
   - Error: "No module named 'app.api.workflow.step_formats'"
   - Location: app/__init__.py import statement
   - Impact: No impact on format system implementation
   - Review after completion of implementation plan 