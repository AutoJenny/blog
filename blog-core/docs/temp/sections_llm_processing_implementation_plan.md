# Sections LLM Processing Implementation Plan

## Overview

This document outlines the implementation plan for fixing the Sections substage LLM processing to work with individual sections instead of post-level processing. The current system processes LLM actions at the post level, but for the Sections substage, it needs to process each selected section individually.

## Current Problem Analysis

### Current Behavior (Incorrect)
- **Purple Panel (LLM Actions)**: Processes one generic LLM action per post
- **Green Panel (Sections)**: Shows sections with checkboxes but selections are ignored
- **Data Processing**: Uses post-level context instead of section-specific context
- **Output Saving**: Saves to post-level fields instead of section-specific fields
- **Context**: No section-specific information included in LLM prompts

### Required Behavior (Correct)
- **Purple Panel**: Processes LLM actions for each selected section individually
- **Green Panel**: Checkbox selections determine which sections to process
- **Data Processing**: Uses section-specific context for each section
- **Output Saving**: Saves results to each section's specific field
- **Context**: Includes section-specific data in LLM prompts

## Architecture Analysis

### Current System Architecture
```
blog-core (port 5000) - Main workflow page
├── Purple iframe: blog-llm-actions (port 5002) - LLM processing
└── Green iframe: blog-post-sections (port 5003) - Section management
```

### Communication Flow
1. **Current**: Purple panel → LLM API → Database (post-level)
2. **Required**: Purple panel → Green panel → Section IDs → LLM API → Database (section-level)

### Existing Infrastructure
- **API Endpoints**: `/api/run-llm` already supports `section_id` parameter
- **Database**: `post_section` table has all required fields
- **Sections API**: `GET /api/sections/{section_id}` provides section context
- **Saving Logic**: Already implemented for section-specific fields

## Implementation Plan

### Phase 1: Iframe Communication Setup

#### 1.1 Green Panel (blog-post-sections) - Message Listener
**File**: `blog/blog-post-sections/static/js/sections.js`

**Add postMessage event listener**:
```javascript
// Listen for requests from purple panel
window.addEventListener('message', (event) => {
    if (event.data.type === 'GET_SELECTED_SECTIONS') {
        const selectedIds = getSelectedSectionIds();
        event.source.postMessage({
            type: 'SELECTED_SECTIONS_RESPONSE',
            sectionIds: selectedIds
        }, '*');
    }
});

// Function to get selected section IDs
function getSelectedSectionIds() {
    const checkboxes = document.querySelectorAll('.section-select-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.dataset.sectionId);
}
```

#### 1.2 Purple Panel (blog-llm-actions) - Message Sender
**File**: `blog/blog-llm-actions/templates/index.html`

**Add function to request selected sections**:
```javascript
async function getSelectedSectionIds() {
    return new Promise((resolve) => {
        const messageHandler = (event) => {
            if (event.data.type === 'SELECTED_SECTIONS_RESPONSE') {
                window.removeEventListener('message', messageHandler);
                resolve(event.data.sectionIds);
            }
        };
        
        window.addEventListener('message', messageHandler);
        window.parent.postMessage({
            type: 'GET_SELECTED_SECTIONS',
            source: 'llm-actions'
        }, '*');
        
        // Timeout fallback
        setTimeout(() => {
            window.removeEventListener('message', messageHandler);
            resolve([]);
        }, 5000);
    });
}
```

### Phase 2: Enhanced Run LLM Function

#### 2.1 Detect Sections Substage
**File**: `blog/blog-llm-actions/templates/index.html`

**Modify `runLLM()` function**:
```javascript
async function runLLM() {
    const selectedField = document.getElementById('output-field-select').value;
    const messageContent = document.getElementById('message-area').value;
    
    // Check if this is sections substage
    if (context.substage === 'sections') {
        await processSectionsWithLLM(selectedField, messageContent);
    } else {
        // Existing behavior for other substages
        await processIndividualAction(selectedField, messageContent);
    }
}
```

#### 2.2 Section Processing Logic
**Add new function for section processing**:
```javascript
async function processSectionsWithLLM(outputField, messageContent) {
    try {
        // Get selected section IDs
        const selectedSectionIds = await getSelectedSectionIds();
        
        if (selectedSectionIds.length === 0) {
            alert('Please select at least one section in the green panel.');
            return;
        }
        
        // Show progress indicator
        showProgressIndicator(`Processing ${selectedSectionIds.length} sections...`);
        
        // Process each section individually
        for (let i = 0; i < selectedSectionIds.length; i++) {
            const sectionId = selectedSectionIds[i];
            updateProgressIndicator(`Processing section ${i + 1} of ${selectedSectionIds.length}...`);
            
            await processSectionWithLLM(sectionId, outputField, messageContent);
        }
        
        hideProgressIndicator();
        alert(`Successfully processed ${selectedSectionIds.length} sections!`);
        
    } catch (error) {
        hideProgressIndicator();
        console.error('Error processing sections:', error);
        alert('Error processing sections. Check console for details.');
    }
}
```

### Phase 3: Section-Specific Processing

#### 3.1 Section Context Retrieval
**Add function to get section context**:
```javascript
async function getSectionContext(sectionId) {
    try {
        const response = await fetch(`http://localhost:5003/api/sections/${sectionId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch section ${sectionId}`);
        }
        
        const section = await response.json();
        
        // Build context string from relevant fields
        const contextParts = [];
        if (section.section_heading) contextParts.push(`Section: ${section.section_heading}`);
        if (section.section_description) contextParts.push(`Description: ${section.section_description}`);
        if (section.draft) contextParts.push(`Current Draft: ${section.draft}`);
        if (section.ideas_to_include) contextParts.push(`Ideas to Include: ${section.ideas_to_include}`);
        if (section.facts_to_include) contextParts.push(`Facts to Include: ${section.facts_to_include}`);
        
        return contextParts.join('\n');
    } catch (error) {
        console.error(`Error fetching section context for ${sectionId}:`, error);
        return `Section ID: ${sectionId}`;
    }
}
```

#### 3.2 Individual Section Processing
**Add function to process single section**:
```javascript
async function processSectionWithLLM(sectionId, outputField, messageContent) {
    try {
        // Get section context
        const sectionContext = await getSectionContext(sectionId);
        
        // Build section-specific prompt
        const prompt = `${messageContent}\n\nSection Context:\n${sectionContext}`;
        
        // Call LLM with section context
        const response = await fetch('/api/run-llm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                system_prompt: '',
                persona: '',
                task: prompt,
                post_id: context.post_id,
                output_field: outputField,
                section_id: sectionId,  // Include section_id
                stage: context.stage,
                substage: context.substage
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.status === 'success' && result.output) {
            console.log(`Successfully processed section ${sectionId}`);
        } else {
            throw new Error(result.error || 'Invalid response from LLM');
        }
        
    } catch (error) {
        console.error(`Error processing section ${sectionId}:`, error);
        throw error;
    }
}
```

### Phase 4: User Experience Enhancements

#### 4.1 Progress Indicators
**Add progress indicator functions**:
```javascript
function showProgressIndicator(message) {
    // Create or update progress indicator
    let indicator = document.getElementById('progress-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'progress-indicator';
        indicator.style.cssText = `
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.8); color: white; padding: 20px; border-radius: 8px;
            z-index: 10000; text-align: center;
        `;
        document.body.appendChild(indicator);
    }
    indicator.textContent = message;
    indicator.style.display = 'block';
}

function updateProgressIndicator(message) {
    const indicator = document.getElementById('progress-indicator');
    if (indicator) {
        indicator.textContent = message;
    }
}

function hideProgressIndicator() {
    const indicator = document.getElementById('progress-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}
```

#### 4.2 Error Handling
**Enhanced error handling**:
```javascript
// Add to processSectionsWithLLM function
let successCount = 0;
let errorCount = 0;

for (let i = 0; i < selectedSectionIds.length; i++) {
    try {
        await processSectionWithLLM(selectedSectionIds[i], outputField, messageContent);
        successCount++;
    } catch (error) {
        errorCount++;
        console.error(`Failed to process section ${selectedSectionIds[i]}:`, error);
    }
}

// Show final results
if (errorCount === 0) {
    alert(`Successfully processed all ${successCount} sections!`);
} else {
    alert(`Processed ${successCount} sections successfully, ${errorCount} failed. Check console for details.`);
}
```

### Phase 5: Testing and Validation

#### 5.1 Test Cases
1. **Iframe Communication Test**
   - Verify purple panel can read green panel selections
   - Test timeout handling for communication failures

2. **Section Processing Test**
   - Test with single section selected
   - Test with multiple sections selected
   - Test with no sections selected

3. **Context Integration Test**
   - Verify section context appears in LLM prompts
   - Test with sections that have different field content

4. **Saving Test**
   - Verify results save to correct section fields
   - Test persistence after page reload

5. **Error Handling Test**
   - Test with invalid section IDs
   - Test with network failures
   - Test with LLM API failures

#### 5.2 Validation Checklist
- [ ] Iframe communication works reliably
- [ ] Section context is included in LLM prompts
- [ ] Results save to correct section fields
- [ ] Progress indicators show accurate status
- [ ] Error handling works gracefully
- [ ] Other substages continue working unchanged
- [ ] Performance is acceptable for multiple sections

## Files to Modify

### Primary Files
1. **`blog/blog-llm-actions/templates/index.html`**
   - Add iframe communication functions
   - Enhance `runLLM()` function
   - Add section processing logic
   - Add progress indicators

2. **`blog/blog-post-sections/static/js/sections.js`**
   - Add postMessage event listener
   - Add `getSelectedSectionIds()` function

### Documentation Files
3. **`blog/blog-core/docs/reference/api.md`**
   - Update LLM actions API documentation
   - Add section processing details

4. **`blog/blog-core/docs/reference/microservices_overview.md`**
   - Update iframe communication documentation
   - Add sections substage specifics

## Implementation Timeline

### Day 1: Iframe Communication
- Implement postMessage listeners in green panel
- Implement message sender in purple panel
- Test basic communication

### Day 2: Section Processing Logic
- Implement section detection in `runLLM()`
- Implement `processSectionsWithLLM()` function
- Test with single section

### Day 3: Context Integration
- Implement section context retrieval
- Implement individual section processing
- Test context inclusion

### Day 4: User Experience
- Implement progress indicators
- Implement enhanced error handling
- Test user feedback

### Day 5: Testing and Documentation
- Comprehensive testing
- Update documentation
- Final validation

## Risk Mitigation

### Technical Risks
1. **Iframe Communication Failure**
   - **Mitigation**: Timeout fallback, graceful degradation
   - **Fallback**: Continue with current behavior

2. **Section API Unavailability**
   - **Mitigation**: Error handling, continue with other sections
   - **Fallback**: Use minimal context

3. **Performance Issues**
   - **Mitigation**: Progress indicators, async processing
   - **Fallback**: Process fewer sections at once

### User Experience Risks
1. **Confusion About Selection**
   - **Mitigation**: Clear error messages, visual feedback
   - **Fallback**: Default to first section

2. **Long Processing Times**
   - **Mitigation**: Progress indicators, cancel option
   - **Fallback**: Process in background

## Success Criteria

### Functional Requirements
1. **Section Selection**: Purple panel correctly reads green panel selections
2. **Individual Processing**: Each selected section is processed separately
3. **Context Inclusion**: Section-specific data appears in LLM prompts
4. **Correct Saving**: Results save to each section's specific field
5. **Persistence**: Results persist after page reload

### Performance Requirements
1. **Response Time**: Processing starts within 2 seconds of button click
2. **Progress Feedback**: User sees progress for each section
3. **Error Recovery**: System continues processing other sections if one fails

### User Experience Requirements
1. **Clear Feedback**: User understands what's happening
2. **Error Messages**: Clear, actionable error messages
3. **No Regression**: Other substages continue working unchanged

## Post-Implementation Tasks

### Documentation Updates
1. Update API documentation with section processing details
2. Update microservices overview with iframe communication
3. Create user guide for sections substage

### Monitoring and Maintenance
1. Add logging for section processing operations
2. Monitor performance metrics
3. Collect user feedback on new functionality

### Future Enhancements
1. Batch processing optimization
2. Section processing templates
3. Advanced error recovery mechanisms 