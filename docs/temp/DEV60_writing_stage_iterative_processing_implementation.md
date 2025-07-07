# DEV60: Writing Stage Iterative Processing Implementation Plan

## Overview
Fix the Writing stage to properly process sections iteratively, respecting section selection and preventing cross-contamination between sections.

## Current Problem (CORRECTED ANALYSIS)
- **REAL ISSUE**: Writing stage includes ALL section headings in LLM prompts, not just selected sections
- **REAL ISSUE**: LLM receives data from all sections, causing potential cross-contamination
- **REAL ISSUE**: System processes sections sequentially but uses the same prompt for all
- **NOT AN ISSUE**: `process_writing_step()` function structure (it's actually correct)
- **NOT AN ISSUE**: `save_section_output()` SQL query (it's actually correct)

## Root Cause Analysis
The issue is in **section-specific prompt building**. The current system:
1. ✅ Correctly calls `process_step()` to get LLM response
2. ✅ Correctly saves responses to specific sections using `save_section_output()`
3. ❌ **INCORRECTLY** includes ALL section headings in the prompt instead of just selected sections
4. ❌ **INCORRECTLY** uses the same prompt for all sections instead of section-specific prompts

## Implementation Plan

### Phase 1: Section-Specific Prompt Building (CRITICAL FIX)

#### 1.1 Modify Prompt Construction Logic
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Create `build_section_specific_prompt()` function**
- [ ] **Filter section headings to only include selected sections**
- [ ] **Add section context to prompt (current section heading + description)**
- [ ] **Maintain existing prompt structure and format**

**Required Function**:
```python
def build_section_specific_prompt(conn, post_id, step_id, selected_section_ids, current_section_id):
    """
    Build section-specific prompt for Writing stage.
    
    Args:
        conn: Database connection
        post_id: Post ID
        step_id: Workflow step ID
        selected_section_ids: List of selected section IDs
        current_section_id: ID of section being processed
    
    Returns:
        Dict with system_prompt, task_prompt, and context_data
    """
    # Get base prompts from workflow_step_prompt table
    # Filter section_headings to only selected sections
    # Add current section context
    # Return section-specific prompt structure
```

#### 1.2 Update Section Data Retrieval
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Create `get_selected_sections_data()` function**
- [ ] **Filter sections by selected IDs**
- [ ] **Include only relevant section data in prompt**
- [ ] **Add current section context for processing**

**Required Function**:
```python
def get_selected_sections_data(conn, post_id, selected_section_ids, current_section_id):
    """
    Get data for selected sections and current section context.
    
    Args:
        conn: Database connection
        post_id: Post ID
        selected_section_ids: List of selected section IDs
        current_section_id: ID of section being processed
    
    Returns:
        Dict with filtered section data and current section context
    """
    # Query post_section table for selected sections only
    # Get current section heading and description
    # Return filtered data structure
```

### Phase 1.5: Prompt System Integration (CRITICAL)

#### 1.5.1 Maintain Existing Prompt System
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Keep existing `workflow_step_prompt` table usage**
- [ ] **Maintain `system_prompt_id` and `task_prompt_id` structure**
- [ ] **Use existing `get_step_prompt_templates()` function**
- [ ] **Add section-specific context to existing prompts**

**Required Integration**:
```python
def get_section_specific_prompts(conn, step_id, post_id, selected_section_ids, current_section_id):
    """
    Get section-specific prompts while maintaining existing prompt system.
    
    Args:
        conn: Database connection
        step_id: Workflow step ID
        post_id: Post ID
        selected_section_ids: List of selected section IDs
        current_section_id: ID of section being processed
    
    Returns:
        Dict with system_prompt, task_prompt, and section_context
    """
    # Get existing prompts from workflow_step_prompt table
    # Add section-specific context to task_prompt
    # Maintain existing prompt structure
    # Return enhanced prompt with section context
```

#### 1.5.2 Section Context Integration
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Add section context to existing prompt templates**
- [ ] **Use `[data:section_heading]` and `[data:section_description]` references**
- [ ] **Maintain backward compatibility with existing prompts**
- [ ] **Test with existing prompt templates**

### Phase 2: Iterative Processing Implementation

#### 2.1 Modify Writing Stage Processing
**File**: `app/api/workflow/routes.py` (lines 10-71)
- [ ] **Add section iteration logic to `process_writing_step()`**
- [ ] **Process each selected section individually**
- [ ] **Use section-specific prompts for each iteration**
- [ ] **Maintain existing error handling and response structure**

**Required Changes**:
```python
def process_writing_step(post_id, step_id, selected_section_ids):
    """
    Process Writing stage with section-specific prompts.
    
    Args:
        post_id: Post ID
        step_id: Workflow step ID
        selected_section_ids: List of selected section IDs
    
    Returns:
        Dict with success status and results for each section
    """
    results = {}
    
    for section_id in selected_section_ids:
        try:
            # Build section-specific prompt
            prompt_data = build_section_specific_prompt(
                conn, post_id, step_id, selected_section_ids, section_id
            )
            
            # Process LLM with section-specific prompt
            llm_response = process_step_with_prompt(prompt_data)
            
            # Save to specific section
            save_section_output(conn, post_id, section_id, llm_response)
            
            results[section_id] = {"success": True, "response": llm_response}
            
        except Exception as e:
            results[section_id] = {"success": False, "error": str(e)}
    
    return results
```

#### 2.2 Sequential Processing with Per-Section Timeouts
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Implement sequential processing (not parallel)**
- [ ] **Apply timeout per section, not per group of requests**
- [ ] **Continue processing other sections if one fails**
- [ ] **Provide detailed status for each section**

**Required Implementation**:
```python
def process_sections_sequentially(conn, post_id, step_id, selected_section_ids, timeout_per_section=300):
    """
    Process sections sequentially with per-section timeout.
    
    Args:
        conn: Database connection
        post_id: Post ID
        step_id: Workflow step ID
        selected_section_ids: List of selected section IDs
        timeout_per_section: Timeout in seconds per section (default: 300)
    
    Returns:
        Dict with results for each section
    """
    results = {}
    
    for section_id in selected_section_ids:
        try:
            # Set timeout for this section only
            with timeout_context(timeout_per_section):
                # Process section with section-specific prompt
                result = process_single_section(conn, post_id, step_id, section_id, selected_section_ids)
                results[section_id] = {"success": True, "result": result}
                
        except TimeoutError:
            results[section_id] = {"success": False, "error": f"Timeout after {timeout_per_section}s"}
        except Exception as e:
            results[section_id] = {"success": False, "error": str(e)}
            # Continue with next section
    
    return results
```

### Phase 2.5: Field Selection Compliance (CRITICAL)

#### 2.5.1 Verify Field Selection Policy
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Ensure compliance with "per-step only, never per-post" policy**
- [ ] **Use `workflow_step_entity.config.settings.llm.user_output_mapping`**
- [ ] **Verify Writing stage steps have correct field mappings**
- [ ] **Test global field selection across multiple posts**

**Required Compliance**:
```python
def get_user_output_mapping(conn, step_id, post_id):
    """
    Get field mapping following canonical policy: per-step only, never per-post.
    
    Args:
        conn: Database connection
        step_id: Workflow step ID
        post_id: Post ID (for verification only)
    
    Returns:
        Dict with field and table mapping for the step
    """
    # Get mapping from workflow_step_entity.config.settings.llm.user_output_mapping
    # Verify this is global for all posts using this step
    # Return consistent mapping regardless of post_id
```

#### 2.5.2 Handle Writing Stage Field Mapping
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Verify Writing stage steps point to `post_section` table**
- [ ] **Test field mapping with section-specific processing**
- [ ] **Ensure field selection works with section IDs**
- [ ] **Handle field mapping errors gracefully**

### Phase 3: Frontend Integration

#### 3.1 Section Selection UI Integration (CRITICAL)
**File**: `app/static/js/workflow/template_view.js` (lines 110-209)
- [ ] **Verify existing section selection checkboxes work correctly**
- [ ] **Integrate with LLM Panel field selection system**
- [ ] **Update context variables for section-specific processing**
- [ ] **Add visual feedback for selected sections**

**Required Integration**:
```javascript
// Update section selection to communicate with LLM Panel
function updateLLMPanelForSections(selectedSectionIds) {
    // Update LLM Panel context variables
    const panel = document.querySelector('[data-current-stage="writing"]');
    if (panel) {
        panel.setAttribute('data-selected-sections', JSON.stringify(selectedSectionIds));
        panel.setAttribute('data-section-count', selectedSectionIds.length);
    }
    
    // Update field mapping for section-specific processing
    updateFieldMappingForSections(selectedSectionIds);
}
```

#### 3.2 LLM Panel Context Variable Updates
**File**: `app/templates/workflow/_modular_llm_panels.html`
- [ ] **Add section-specific context variables to LLM Panel**
- [ ] **Include `selected_section_ids` in panel data attributes**
- [ ] **Update field mapping to handle section-specific fields**
- [ ] **Maintain existing LLM Panel functionality**

**Required Context Variables**:
```html
<div class="space-y-4 p-4 rounded-lg shadow-md" 
     style="background-color: #2D0A50;"
     data-current-stage="{{ current_stage }}" 
     data-current-substage="{{ current_substage }}"
     data-current-step="{{ current_step }}" 
     data-step-id="{{ step_id }}" 
     data-post-id="{{ current_post_id }}"
     data-selected-sections="{{ selected_section_ids|tojson }}"
     data-section-count="{{ selected_section_ids|length }}">
```

#### 3.3 Verify Section Selection Logic
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

#### 3.4 Update Response Handling
**File**: `app/static/js/workflow/template_view.js`
- [ ] **Handle section-specific response updates**
- [ ] **Update UI for each processed section**
- [ ] **Show progress for multi-section processing**
- [ ] **Handle partial failures gracefully**

### Phase 3.5: Trigger and Sync Management (CRITICAL)

#### 3.5.1 Prevent Database Trigger Conflicts
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Temporarily disable section sync triggers during processing**
- [ ] **Re-enable triggers after all sections processed**
- [ ] **Handle trigger conflicts gracefully**
- [ ] **Maintain data consistency**

**Required Implementation**:
```python
def process_sections_with_trigger_management(conn, post_id, step_id, selected_section_ids):
    """
    Process sections while managing database triggers.
    
    Args:
        conn: Database connection
        post_id: Post ID
        step_id: Workflow step ID
        selected_section_ids: List of selected section IDs
    
    Returns:
        Dict with results for each section
    """
    try:
        # Temporarily disable section sync triggers
        disable_section_sync_triggers(conn, post_id)
        
        # Process sections
        results = process_sections_sequentially(conn, post_id, step_id, selected_section_ids)
        
        # Re-enable triggers
        enable_section_sync_triggers(conn, post_id)
        
        return results
        
    except Exception as e:
        # Ensure triggers are re-enabled even on error
        enable_section_sync_triggers(conn, post_id)
        raise e
```

### Phase 4: API Endpoint Structure

#### 4.1 Update LLM Processing Endpoint
**File**: `app/api/workflow/routes.py`
- [ ] **Modify existing LLM endpoint to handle section selection**
- [ ] **Add section_ids parameter to request**
- [ ] **Maintain backward compatibility**
- [ ] **Update response format for section-specific results**

**Required Endpoint Changes**:
```python
@workflow_bp.route('/posts/<int:post_id>/<stage>/<substage>/llm', methods=['POST'])
def run_llm_processing(post_id, stage, substage):
    """
    Run LLM processing with section selection support.
    
    Request:
    {
        "step": "Author First Drafts",
        "selected_section_ids": [1, 2, 3],  # NEW: Section selection
        "timeout_per_section": 300  # NEW: Per-section timeout
    }
    
    Response:
    {
        "success": true,
        "results": {
            "1": {"success": true, "result": "Generated content..."},
            "2": {"success": true, "result": "Generated content..."},
            "3": {"success": false, "error": "Timeout after 300s"}
        }
    }
    """
```

#### 4.2 Section-Specific Field Mapping Endpoint
**File**: `app/api/workflow/routes.py`
- [ ] **Add endpoint for section-specific field mapping**
- [ ] **Support section field selection in LLM Panel**
- [ ] **Maintain existing field mapping functionality**
- [ ] **Add validation for section-specific fields**

### Phase 4.5: LLM Settings Integration (CRITICAL)

#### 4.5.1 Apply Settings Per Section
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Get LLM settings from 'Section Creator JSON' Action**
- [ ] **Apply settings to each section individually**
- [ ] **Use local LLM provider (Ollama) configuration**
- [ ] **Maintain settings consistency across sections**

**Required Implementation**:
```python
def get_section_llm_settings(conn, post_id, step_id):
    """
    Get LLM settings from database configuration.
    
    Args:
        conn: Database connection
        post_id: Post ID
        step_id: Workflow step ID
    
    Returns:
        Dict with LLM provider, model, and parameters
    """
    # Query 'Section Creator JSON' Action for LLM settings
    # Return local LLM provider configuration (Ollama)
    # Include model, temperature, max_tokens, etc.
```

### Phase 5: Database Schema Verification

#### 5.1 Verify Section Table Structure
**File**: `docs/database/schema.md`
- [ ] **Confirm `post_section` table has required fields**
- [ ] **Verify `first_draft` field exists and is TEXT**
- [ ] **Check section selection tracking fields**
- [ ] **Validate foreign key relationships**

**Required Fields**:
- `id` (PRIMARY KEY)
- `post_id` (FOREIGN KEY)
- `section_heading` (TEXT)
- `section_description` (TEXT)
- `first_draft` (TEXT) - **CRITICAL for Writing stage**
- `section_order` (INTEGER)
- `status` (TEXT)

#### 5.2 Check Workflow Step Configuration
**File**: Database verification
- [ ] **Verify Writing stage steps exist**
- [ ] **Check step configuration for field mappings**
- [ ] **Confirm prompt templates are configured**
- [ ] **Validate format assignments**

### Phase 6: Configuration Verification

#### 6.1 LLM Provider Configuration
**File**: Database verification
- [ ] **Confirm Ollama is configured as LLM provider**
- [ ] **Verify API endpoint is accessible**
- [ ] **Check model availability**
- [ ] **Test connection to local LLM service**

#### 6.2 Prompt Template Verification
**File**: Database verification
- [ ] **Confirm Writing stage prompts exist**
- [ ] **Check prompt template structure**
- [ ] **Verify section-specific prompt support**
- [ ] **Test prompt template loading**

### Phase 6.5: Format System Integration (CRITICAL)

#### 6.5.1 Section-Specific Format Handling
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Apply format validation per section**
- [ ] **Handle section-specific format requirements**
- [ ] **Use `[data:field_name]` references for section data**
- [ ] **Validate format compliance before saving**

**Required Implementation**:
```python
def validate_section_format(conn, section_id, output_data, format_id):
    """
    Validate section output against format specification.
    
    Args:
        conn: Database connection
        section_id: Section ID
        output_data: LLM output data
        format_id: Format template ID
    
    Returns:
        Tuple of (is_valid, errors)
    """
    # Get format template
    # Validate output against format specification
    # Handle section-specific field references
    # Return validation results
```

#### 6.5.2 Format Reference Resolution
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Resolve `[data:section_heading]` references**
- [ ] **Handle `[data:section_description]` references**
- [ ] **Validate all references exist in section data**
- [ ] **Provide clear error messages for missing references**

### Phase 7: Testing Strategy

#### 7.1 Section Selection Testing
**File**: `tests/workflow/test_section_processing.py`
- [ ] **Test single section selection**
- [ ] **Test multiple section selection**
- [ ] **Test no section selection (default behavior)**
- [ ] **Test section selection UI integration**

**Required Test Cases**:
```python
def test_section_selection_scenarios():
    """Test various section selection scenarios."""
    
    # Test single section
    selected_ids = [1]
    result = process_writing_step(post_id=22, step_id=41, selected_section_ids=selected_ids)
    assert len(result) == 1
    assert result[1]["success"] == True
    
    # Test multiple sections
    selected_ids = [1, 2, 3]
    result = process_writing_step(post_id=22, step_id=41, selected_section_ids=selected_ids)
    assert len(result) == 3
    
    # Test no selection (should default to first section)
    selected_ids = []
    result = process_writing_step(post_id=22, step_id=41, selected_section_ids=selected_ids)
    assert len(result) == 1
```

#### 7.2 Sequential Processing Testing
**File**: `tests/workflow/test_section_processing.py`
- [ ] **Test sequential processing order**
- [ ] **Test per-section timeout handling**
- [ ] **Test partial failure scenarios**
- [ ] **Test transaction rollback on errors**

#### 7.3 Prompt Building Testing
**File**: `tests/workflow/test_section_processing.py`
- [ ] **Test section-specific prompt building**
- [ ] **Test prompt filtering for selected sections**
- [ ] **Test section context inclusion**
- [ ] **Test prompt template integration**

#### 7.4 Format Integration Testing
**File**: `tests/workflow/test_section_processing.py`
- [ ] **Test section-specific format validation**
- [ ] **Test format reference resolution**
- [ ] **Test format error handling**
- [ ] **Test format compliance checking**

### Phase 8: Response Standardization

#### 8.1 Standardize API Response Format
**File**: `app/api/workflow/routes.py`
- [ ] **Match documented API response format**
- [ ] **Include section-specific results**
- [ ] **Provide detailed error information**
- [ ] **Maintain backward compatibility**

**Required Response Format**:
```json
{
    "success": true,
    "message": "Processing completed",
    "results": {
        "1": {
            "success": true,
            "section_id": 1,
            "section_heading": "Ancient Roots",
            "result": "Generated content...",
            "processing_time": 45.2
        },
        "2": {
            "success": false,
            "section_id": 2,
            "section_heading": "Evolution of Storytelling",
            "error": "Timeout after 300s",
            "processing_time": 300.0
        }
    },
    "summary": {
        "total_sections": 2,
        "successful": 1,
        "failed": 1,
        "total_time": 345.2
    }
}
```

#### 8.2 Error Handling Standardization
**File**: `app/api/workflow/routes.py`
- [ ] **Standardize error response format**
- [ ] **Include section-specific error details**
- [ ] **Provide actionable error messages**
- [ ] **Maintain consistent error codes**

### Phase 9: Performance Optimization

#### 9.1 Sequential Processing Optimization
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Optimize database queries for section processing**
- [ ] **Implement efficient prompt building**
- [ ] **Minimize memory usage during processing**
- [ ] **Add progress tracking for long operations**

#### 9.2 Caching Strategy
**File**: `app/workflow/scripts/llm_processor.py`
- [ ] **Cache section data during processing**
- [ ] **Cache prompt templates**
- [ ] **Implement efficient field mapping cache**
- [ ] **Add cache invalidation for updates**

### Phase 10: Documentation Updates

#### 10.1 Update API Documentation
**File**: `docs/reference/api/current/llm.md`
- [ ] **Document section-specific endpoint changes**
- [ ] **Update request/response examples**
- [ ] **Add section selection parameters**
- [ ] **Include error handling examples**

#### 10.2 Update Workflow Documentation
**File**: `docs/reference/workflow/sections.md`
- [ ] **Document section selection functionality**
- [ ] **Update Writing stage processing details**
- [ ] **Add section-specific prompt building**
- [ ] **Include troubleshooting guide**

#### 10.3 Update Testing Documentation
**File**: `docs/reference/workflow/testing.md`
- [ ] **Add section processing test cases**
- [ ] **Include curl commands for testing**
- [ ] **Document expected responses**
- [ ] **Add debugging instructions**

## Implementation Order

1. **Phase 1**: Section-specific prompt building (CRITICAL FIX)
2. **Phase 1.5**: Prompt system integration
3. **Phase 2**: Iterative processing implementation
4. **Phase 2.5**: Field selection compliance
5. **Phase 3**: Frontend integration
6. **Phase 3.5**: Trigger and sync management
7. **Phase 4**: API endpoint structure
8. **Phase 4.5**: LLM settings integration
9. **Phase 5**: Database schema verification
10. **Phase 6**: Configuration verification
11. **Phase 6.5**: Format system integration
12. **Phase 7**: Testing strategy
13. **Phase 8**: Response standardization
14. **Phase 9**: Performance optimization
15. **Phase 10**: Documentation updates

## Rollback Plan

### Emergency Rollback
If critical issues arise during implementation:

1. **Git Stash Current Changes**:
   ```bash
   git stash push -m "DEV60_emergency_rollback_$(date +%Y%m%d_%H%M%S)"
   ```

2. **Revert to Last Known Good State**:
   ```bash
   git checkout HEAD~1
   ```

3. **Restart Flask Server**:
   ```bash
   ./scripts/dev/restart_flask_dev.sh
   ```

4. **Verify System Functionality**:
   ```bash
   curl -s "http://localhost:5000/api/v1/post/22/development" | python3 -m json.tool
   ```

### Partial Rollback
If specific phases have issues:

1. **Identify Problematic Phase**
2. **Revert Only That Phase's Changes**
3. **Continue with Remaining Phases**
4. **Re-implement Problematic Phase Later**

## Success Criteria

### Functional Requirements
- [ ] Writing stage processes only selected sections
- [ ] Each section gets section-specific prompt
- [ ] No cross-contamination between sections
- [ ] Sequential processing with per-section timeouts
- [ ] Proper error handling and recovery
- [ ] Backward compatibility maintained

### Performance Requirements
- [ ] Processing time scales linearly with section count
- [ ] Memory usage remains reasonable
- [ ] Database queries are optimized
- [ ] UI remains responsive during processing

### Quality Requirements
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Error messages are clear and actionable
- [ ] Code follows project standards

## Risk Mitigation

### High-Risk Areas
1. **Database Trigger Conflicts**: Implement trigger management
2. **Prompt System Integration**: Maintain existing structure
3. **Format System Compatibility**: Test thoroughly
4. **Performance Degradation**: Monitor and optimize

### Mitigation Strategies
1. **Comprehensive Testing**: Test each phase thoroughly
2. **Incremental Implementation**: Implement phases sequentially
3. **Rollback Preparation**: Maintain ability to rollback quickly
4. **Monitoring**: Add logging and monitoring throughout

## Timeline Estimate

- **Phase 1-2**: 2-3 days (Core functionality)
- **Phase 3-4**: 1-2 days (Integration)
- **Phase 5-6**: 1 day (Verification)
- **Phase 7**: 1-2 days (Testing)
- **Phase 8-10**: 1 day (Polish and documentation)

**Total Estimated Time**: 6-9 days

## Notes

- **CRITICAL**: Maintain existing prompt system structure
- **CRITICAL**: Ensure per-section timeout, not per-group timeout
- **CRITICAL**: Preserve backward compatibility
- **IMPORTANT**: Test thoroughly at each phase
- **IMPORTANT**: Document all changes
- **REMINDER**: This project does not use logins or registration 