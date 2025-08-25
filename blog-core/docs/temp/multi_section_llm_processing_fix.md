# Multi-Section LLM Processing Fix - Complete Implementation Guide

## Problem Summary
When multiple section checkboxes are selected in the writing stage, all sections receive the same generic content based on the first section's data instead of their own section-specific content. This is caused by the frontend assembling a single prompt with one section's data and sending it to all sections.

## Root Cause Analysis
1. **Frontend Issue**: Enhanced LLM Message Manager assembles content from the modal using the first selected section's data
2. **Backend Issue**: Receives identical prompt for all sections and tries to replace fields, but they're already populated with first section's data
3. **Data Flow Issue**: No proper separation between template prompt and section-specific data

## Required Changes

### 1. Frontend Changes - Enhanced LLM Message Manager

#### File: `app/static/js/enhanced_llm_message_manager.js`

**Function: `executeLLMRequest()` (around line 1875)**

**Current Problem:**
- Assembles prompt with section-specific data from modal
- Sends same prompt to all selected sections
- Backend receives pre-populated data

**Required Changes:**
1. **For Writing Stage**: Send template prompt without section-specific data
2. **For Planning Stage**: Keep current behavior (single section processing)
3. **Add Template Prompt Assembly**: Create function to assemble base template
4. **Remove Section Data from Prompt**: Strip section-specific content before sending

**New Functions Needed:**
```javascript
// New function to assemble template prompt without section data
getTemplatePrompt() {
    // Assemble prompt with placeholders instead of actual section data
    // Replace section-specific fields with generic placeholders
}

// New function to detect if we're in writing stage with multiple sections
isMultiSectionWritingStage() {
    // Check if writing stage and multiple sections selected
}
```

**Modified Functions:**
```javascript
executeLLMRequest(message) {
    if (this.isMultiSectionWritingStage()) {
        // Send template prompt, let backend handle section data
        const templatePrompt = this.getTemplatePrompt();
        // Send templatePrompt instead of message
    } else {
        // Current behavior for planning stage or single section
    }
}
```

### 2. Template Prompt Structure

**Required Template Format:**
```
=== SYSTEM PROMPT ===
[System prompt content]

=== BASIC IDEA ===
[Basic idea content]

=== SECTION HEADINGS ===
[Section headings JSON]

=== TASK PROMPT ===
[Task prompt content]

=== INPUT FIELDS ===
Section Heading: [SECTION_HEADING_PLACEHOLDER]
Section Description: [SECTION_DESCRIPTION_PLACEHOLDER]
Ideas to Include: [IDEAS_TO_INCLUDE_PLACEHOLDER]
Facts to Include: [FACTS_TO_INCLUDE_PLACEHOLDER]
[Other input fields as placeholders]

=== SETTINGS ===
[LLM settings]
```

**Placeholder Format:**
- `[SECTION_HEADING_PLACEHOLDER]` - Will be replaced with actual section heading
- `[SECTION_DESCRIPTION_PLACEHOLDER]` - Will be replaced with actual section description
- `[IDEAS_TO_INCLUDE_PLACEHOLDER]` - Will be replaced with section's ideas_to_include
- `[FACTS_TO_INCLUDE_PLACEHOLDER]` - Will be replaced with section's facts_to_include

### 3. Backend Changes - API Routes

#### File: `app/api/workflow/routes.py`

**Function: `process_sections_sequentially()` (around line 68)**

**Current Problem:**
- Tries to replace fields that are already populated
- Limited field replacement logic
- Doesn't handle all possible input fields

**Required Changes:**
1. **Enhanced Field Detection**: Detect all possible input fields in template
2. **Comprehensive Database Query**: Fetch all available section fields
3. **Dynamic Field Replacement**: Replace any field found in template
4. **Better Error Handling**: Handle missing fields gracefully

**Modified Database Query:**
```sql
SELECT 
    section_heading, section_description, draft, ideas_to_include, facts_to_include,
    polished, highlighting, image_concepts, image_prompts, watermarking,
    image_meta_descriptions, image_captions, image_generation_metadata,
    -- Add any other fields that might be used as inputs
FROM post_section 
WHERE id = %s AND post_id = %s
```

**Enhanced Replacement Logic:**
```python
# Replace all possible input fields dynamically
for field_name, field_value in section_data.items():
    if field_value and field_name not in ['section_heading', 'section_description']:
        display_name = field_name.replace('_', ' ').title()
        placeholder = f"[{display_name.upper().replace(' ', '_')}_PLACEHOLDER]"
        
        # Replace placeholder with actual value
        llm_prompt = llm_prompt.replace(placeholder, str(field_value))
```

### 4. Field Mapping System

**Required Field Mappings:**
- Database field → Display name → Placeholder
- `section_heading` → `Section Heading` → `[SECTION_HEADING_PLACEHOLDER]`
- `section_description` → `Section Description` → `[SECTION_DESCRIPTION_PLACEHOLDER]`
- `ideas_to_include` → `Ideas to Include` → `[IDEAS_TO_INCLUDE_PLACEHOLDER]`
- `facts_to_include` → `Facts to Include` → `[FACTS_TO_INCLUDE_PLACEHOLDER]`
- `draft` → `Draft` → `[DRAFT_PLACEHOLDER]`
- `polished` → `Polished` → `[POLISHED_PLACEHOLDER]`
- `highlighting` → `Highlighting` → `[HIGHLIGHTING_PLACEHOLDER]`
- `image_concepts` → `Image Concepts` → `[IMAGE_CONCEPTS_PLACEHOLDER]`
- `image_prompts` → `Image Prompts` → `[IMAGE_PROMPTS_PLACEHOLDER]`
- `watermarking` → `Watermarking` → `[WATERMARKING_PLACEHOLDER]`
- `image_meta_descriptions` → `Image Meta Descriptions` → `[IMAGE_META_DESCRIPTIONS_PLACEHOLDER]`
- `image_captions` → `Image Captions` → `[IMAGE_CAPTIONS_PLACEHOLDER]`

### 5. Frontend Template Assembly Logic

**Function: `getTemplatePrompt()` Implementation:**

1. **Get Base Content**: Assemble system prompt, basic idea, section headings, task prompt
2. **Create Input Fields Section**: Generate input fields with placeholders
3. **Add Settings**: Include LLM settings
4. **Return Template**: Return complete template with placeholders

**Input Fields Assembly:**
```javascript
// For each enabled input field in the modal
const inputFields = [];
enabledInputFields.forEach(field => {
    const displayName = field.label.replace(/\s+/g, ' ').trim();
    const placeholder = `[${displayName.toUpperCase().replace(/\s+/g, '_')}_PLACEHOLDER]`;
    inputFields.push(`${displayName}: ${placeholder}`);
});
```

### 6. API Endpoint Changes

#### File: `app/api/workflow/routes.py`

**Function: `run_writing_llm()` (around line 1577)**

**Required Changes:**
1. **Template Validation**: Ensure template contains placeholders
2. **Section Data Validation**: Verify all required section data exists
3. **Enhanced Logging**: Log template and replacement process
4. **Error Handling**: Better error messages for missing data

### 7. Testing Strategy

**Test Cases Required:**
1. **Single Section**: Verify current behavior still works
2. **Multiple Sections**: Verify each section gets unique content
3. **Different Input Fields**: Test with various input field combinations
4. **Missing Data**: Test handling of empty/null section data
5. **Template Validation**: Ensure template format is correct

**Test Data Setup:**
- Create test post with multiple sections
- Ensure each section has different data in key fields
- Test with various input field selections

### 8. Implementation Order

**Phase 1: Backend Template Support**
1. Modify `process_sections_sequentially()` to handle template prompts
2. Implement comprehensive field replacement logic
3. Add template validation and error handling
4. Test backend with manual template input

**Phase 2: Frontend Template Assembly**
1. Implement `getTemplatePrompt()` function
2. Modify `executeLLMRequest()` for writing stage
3. Add template assembly logic
4. Test frontend template generation

**Phase 3: Integration Testing**
1. Test complete flow with multiple sections
2. Verify section-specific content generation
3. Test error scenarios
4. Performance testing with many sections

**Phase 4: Edge Cases**
1. Handle missing section data
2. Test with unusual field names
3. Verify output field mapping still works
4. Test with different LLM settings

### 9. Files to Modify

**Primary Files:**
1. `app/static/js/enhanced_llm_message_manager.js`
2. `app/api/workflow/routes.py`

**Supporting Files:**
1. `docs/temp/` - Add implementation documentation
2. `tests/` - Add test cases
3. `logs/` - Enhanced logging for debugging

### 10. Rollback Plan

**If Issues Arise:**
1. Keep current single-section processing intact
2. Add feature flag for new multi-section processing
3. Maintain backward compatibility
4. Provide fallback to current behavior

## Success Criteria

1. **Multiple sections selected** → Each section gets unique content based on its own data
2. **Single section selected** → Current behavior maintained
3. **Different input fields** → All selected input fields are properly replaced
4. **Error handling** → Graceful handling of missing or invalid data
5. **Performance** → No significant performance degradation with multiple sections

## Risk Assessment

**Low Risk:**
- Single section processing (existing functionality)
- Template assembly (new isolated function)

**Medium Risk:**
- Field replacement logic (complex regex operations)
- Database query changes (additional fields)

**High Risk:**
- Integration between frontend and backend
- Template format consistency

## Estimated Effort

**Backend Changes**: 4-6 hours
**Frontend Changes**: 6-8 hours  
**Testing**: 4-6 hours
**Documentation**: 2-3 hours
**Total**: 16-23 hours

## Dependencies

1. **LLM Server**: Must be running and accessible
2. **Database**: All required fields must exist in post_section table
3. **Frontend**: Enhanced LLM Message Manager must be loaded
4. **Sections**: Must have valid section data for replacement 