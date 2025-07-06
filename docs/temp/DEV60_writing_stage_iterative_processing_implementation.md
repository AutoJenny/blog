# DEV60: Writing Stage Iterative Processing Implementation Plan

## Overview
Fix the Writing stage to properly process sections iteratively, respecting section selection and preventing cross-contamination between sections.

## Current Problem
- Writing stage processes ALL sections regardless of selection
- LLM output is saved to every section instead of only selected ones
- Section-specific context is not included in LLM prompts
- `process_writing_step()` incorrectly calls `process_step()` instead of section-specific processing

## Implementation Checklist

### Phase 1: Core Function Analysis & Fixes

#### 1.1 Fix `process_writing_step()` Function
**File**: `app/api/workflow/routes.py` (lines 10-71)
- [ ] **Remove incorrect call to `process_step()`**
- [ ] **Implement proper section-specific processing logic**
- [ ] **Add section_ids validation**
- [ ] **Add proper error handling for section processing**
- [ ] **Ensure function returns standardized response format**

**Current Issues to Fix**:
```python
# CURRENT (WRONG):
result = process_step(post_id, stage, substage, step, frontend_inputs)

# NEEDS TO BE:
result = process_writing_step_llm(post_id, stage, substage, step, section_ids, frontend_inputs)
```

#### 1.2 Create New `process_writing_step_llm()` Function
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Create new function signature**: `process_writing_step_llm(post_id, stage, substage, step, section_ids, frontend_inputs)`
- [ ] **Add section_ids parameter validation**
- [ ] **Implement section-by-section processing loop**
- [ ] **Build section-specific prompts for each section**
- [ ] **Call LLM for each section individually**
- [ ] **Save results to specific sections only**
- [ ] **Return standardized response with section-specific results**

**Required Logic**:
```python
def process_writing_step_llm(post_id, stage, substage, step, section_ids, frontend_inputs):
    results = []
    for section_id in section_ids:
        # Get section-specific data
        section_data = get_section_data(conn, section_id)
        # Build section-specific prompt
        prompt = build_section_prompt(section_data, frontend_inputs)
        # Call LLM
        llm_response = call_llm(prompt, llm_config)
        # Save to specific section
        save_section_output(conn, [section_id], llm_response, field)
        results.append({'section_id': section_id, 'output': llm_response})
    return standardize_llm_response(True, results, step, section_ids)
```

#### 1.3 Fix `save_section_output()` Function
**File**: `app/workflow/scripts/llm_processor.py` (lines 451-474)
- [ ] **Verify SQL query uses `WHERE id IN %s` for section_ids**
- [ ] **Add proper parameter binding for section_ids list**
- [ ] **Add error handling for invalid section_ids**
- [ ] **Add logging for debugging**
- [ ] **Ensure function only updates specified sections**

**Current SQL Issue**:
```sql
-- CURRENT (WRONG):
UPDATE post_section SET {field} = %s WHERE post_id = %s

-- NEEDS TO BE:
UPDATE post_section SET {field} = %s WHERE id = ANY(%s)
```

### Phase 2: Section Context & Prompt Building

#### 2.1 Create `get_section_data()` Function
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Create function to fetch section-specific data**
- [ ] **Include section_heading, section_description, first_draft, etc.**
- [ ] **Include section-specific elements (facts_to_include, ideas_to_include)**
- [ ] **Add post-level context (idea_scope, basic_idea)**
- [ ] **Exclude other sections' data**

**Required Fields**:
```python
def get_section_data(conn, section_id, post_id):
    # Fetch section-specific data
    # Fetch post-level context
    # Return structured data for prompt building
```

#### 2.2 Create `build_section_prompt()` Function
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Create section-specific prompt builder**
- [ ] **Include current section heading and description**
- [ ] **Include section-specific inputs**
- [ ] **Include post-level context**
- [ ] **Exclude other sections' data**
- [ ] **Use existing prompt templates with section context**

**Prompt Structure**:
```
CONTEXT to orientate you
[Post-level context: idea_scope, basic_idea]

INPUTS for your TASK below
Section Heading: [current_section_heading]
Section Description: [current_section_description]
[Section-specific inputs from frontend]

TASK to process the INPUTS above
[Task description with section-specific focus]

RESPONSE to return
[Format instructions]
```

#### 2.3 Update `construct_prompt()` Function
**File**: `app/workflow/scripts/llm_processor.py` (lines 270-373)
- [ ] **Add section_context parameter**
- [ ] **Modify prompt construction to include section data**
- [ ] **Ensure section-specific data is properly formatted**
- [ ] **Maintain backward compatibility for Planning stage**

### Phase 3: Frontend Integration

#### 3.1 Verify Section Selection Logic
**File**: `app/static/js/llm_utils.js` (lines 130-160)
- [ ] **Verify `getSelectedSectionIds()` function works correctly**
- [ ] **Test with single section selection**
- [ ] **Test with multiple section selection**
- [ ] **Test with no section selection (should default to first)**
- [ ] **Add logging for debugging section selection**

**Test Cases**:
- [ ] Single checkbox checked → returns [section_id]
- [ ] Multiple checkboxes checked → returns [section_id1, section_id2, ...]
- [ ] No checkboxes checked → returns [first_section_id]

#### 3.2 Update Response Handling
**File**: `app/static/js/llm_utils.js` (lines 60-90)
- [ ] **Verify handling of multiple section results**
- [ ] **Update only selected sections in UI**
- [ ] **Handle section-specific output updates**
- [ ] **Add error handling for section-specific errors**

**Response Handling Logic**:
```javascript
if (data.success && data.results) {
    data.results.forEach(result => {
        const sectionId = result.section_id;
        const output = result.output;
        
        if (sectionId) {
            // Update specific section output
            const sectionOutput = document.querySelector(`[data-section-id="${sectionId}"] textarea[data-field="output"]`);
            if (sectionOutput) {
                sectionOutput.value = output;
                sectionOutput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    });
}
```

#### 3.3 Test Section Selection UI
**File**: `app/templates/workflow/writing/content.html`
- [ ] **Verify section checkboxes are present**
- [ ] **Test checkbox functionality**
- [ ] **Verify data-section-id attributes are set**
- [ ] **Test section selection persistence**

### Phase 4: API Endpoint Verification

#### 4.1 Verify Writing Stage Endpoint
**File**: `app/api/workflow/routes.py` (lines 1040-1077)
- [ ] **Verify `/writing_llm` endpoint accepts section_ids**
- [ ] **Test endpoint with single section**
- [ ] **Test endpoint with multiple sections**
- [ ] **Test endpoint with no sections (error handling)**
- [ ] **Verify response format matches documentation**

**Endpoint Test Cases**:
```bash
# Single section
curl -X POST "http://localhost:5000/api/workflow/posts/22/writing/content/writing_llm" \
  -H "Content-Type: application/json" \
  -d '{"step": "author_first_drafts", "section_ids": [1], "inputs": {}}'

# Multiple sections
curl -X POST "http://localhost:5000/api/workflow/posts/22/writing/content/writing_llm" \
  -H "Content-Type: application/json" \
  -d '{"step": "author_first_drafts", "section_ids": [1, 2], "inputs": {}}'
```

#### 4.2 Verify Section Data Endpoint
**File**: `app/api/workflow/routes.py` (lines 185-346)
- [ ] **Verify `/sections` endpoint returns correct data**
- [ ] **Test section data structure**
- [ ] **Verify section-specific fields are included**

### Phase 5: Database Schema Verification

#### 5.1 Verify post_section Table Structure
**File**: `docs/database/schema.md`
- [ ] **Verify all required fields exist**
- [ ] **Check field data types**
- [ ] **Verify indexes for performance**

**Required Fields**:
- [ ] `id` (Primary Key)
- [ ] `post_id` (Foreign Key)
- [ ] `section_order` (Integer)
- [ ] `section_heading` (Text)
- [ ] `section_description` (Text)
- [ ] `first_draft` (Text)
- [ ] `status` (Text)
- [ ] `ideas_to_include` (Text)
- [ ] `facts_to_include` (Text)
- [ ] `highlighting` (Text)
- [ ] `uk_british` (Boolean)
- [ ] `image_concepts` (Text)

#### 5.2 Verify Database Triggers
**File**: Database triggers (if any)
- [ ] **Check for any triggers that might interfere**
- [ ] **Verify trigger functions work correctly**
- [ ] **Test trigger behavior with section updates**

### Phase 6: Configuration Verification

#### 6.1 Verify Step Configuration
**Database**: `workflow_step_entity` table
- [ ] **Check Writing stage step configurations**
- [ ] **Verify output_mapping points to post_section table**
- [ ] **Verify field mappings are correct**
- [ ] **Test step configuration loading**

**Required Configurations**:
```sql
-- Check Writing stage steps
SELECT wse.name, wse.config 
FROM workflow_step_entity wse 
JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id 
JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id 
WHERE wst.name = 'writing' AND wsse.name = 'content';
```

#### 6.2 Verify LLM Configuration
**Database**: `llm_action` table
- [ ] **Check Writing stage LLM actions**
- [ ] **Verify prompt templates are correct**
- [ ] **Test LLM parameter configurations**

### Phase 7: Testing & Validation

#### 7.1 Unit Tests
- [ ] **Test `process_writing_step_llm()` with single section**
- [ ] **Test `process_writing_step_llm()` with multiple sections**
- [ ] **Test `save_section_output()` with valid section_ids**
- [ ] **Test `get_section_data()` returns correct data**
- [ ] **Test `build_section_prompt()` creates correct prompts**

#### 7.2 Integration Tests
- [ ] **Test complete workflow: UI → API → Processing → Database**
- [ ] **Test section selection → LLM processing → UI update**
- [ ] **Test multiple sections processed sequentially**
- [ ] **Test error handling for invalid section_ids**

#### 7.3 Cross-Contamination Tests
- [ ] **Test that unselected sections are NOT updated**
- [ ] **Test that section-specific data is isolated**
- [ ] **Test that post-level data remains unchanged**
- [ ] **Test that other sections' data is not included in prompts**

### Phase 8: Documentation Updates

#### 8.1 Update Implementation Documentation
**File**: `docs/reference/workflow/sections.md`
- [ ] **Update implementation status**
- [ ] **Add new function documentation**
- [ ] **Update troubleshooting section**
- [ ] **Add testing examples**

#### 8.2 Update API Documentation
**File**: `docs/reference/workflow/endpoints.md`
- [ ] **Verify endpoint documentation is accurate**
- [ ] **Add section-specific examples**
- [ ] **Update response format documentation**

### Phase 9: Rollback Plan

#### 9.1 Backup Strategy
- [ ] **Create database backup before changes**
- [ ] **Document current working state**
- [ ] **Prepare rollback scripts**

#### 9.2 Rollback Procedures
- [ ] **Revert code changes if needed**
- [ ] **Restore database from backup if needed**
- [ ] **Test rollback procedures**

## Implementation Order

1. **Phase 1**: Core function fixes (highest priority)
2. **Phase 2**: Section context & prompt building
3. **Phase 3**: Frontend integration
4. **Phase 4**: API endpoint verification
5. **Phase 5**: Database schema verification
6. **Phase 6**: Configuration verification
7. **Phase 7**: Testing & validation
8. **Phase 8**: Documentation updates
9. **Phase 9**: Rollback plan (ongoing)

## Success Criteria

- [ ] **Single section selection**: Only selected section is processed and updated
- [ ] **Multiple section selection**: Each selected section is processed individually
- [ ] **No cross-contamination**: Unselected sections remain unchanged
- [ ] **Section-specific context**: LLM prompts include only relevant section data
- [ ] **Proper error handling**: Errors are handled gracefully
- [ ] **UI updates correctly**: Only selected sections show updates
- [ ] **Performance**: Processing time scales linearly with number of selected sections

## Risk Assessment

### High Risk
- **Breaking existing functionality**: Mitigation - thorough testing
- **Database corruption**: Mitigation - backups and careful SQL
- **Performance degradation**: Mitigation - optimize queries

### Medium Risk
- **UI inconsistencies**: Mitigation - comprehensive frontend testing
- **Configuration issues**: Mitigation - verify all configurations

### Low Risk
- **Documentation gaps**: Mitigation - update docs as we go

## Timeline Estimate

- **Phase 1-2**: 2-3 hours (core functionality)
- **Phase 3-4**: 1-2 hours (integration)
- **Phase 5-6**: 30 minutes (verification)
- **Phase 7**: 1-2 hours (testing)
- **Phase 8-9**: 30 minutes (documentation)

**Total**: 5-8 hours for complete implementation

## Notes

- **Backward Compatibility**: Planning stage must remain unchanged
- **Error Handling**: All functions must handle errors gracefully
- **Logging**: Add comprehensive logging for debugging
- **Testing**: Test each phase before proceeding to next
- **Documentation**: Update docs as implementation progresses 