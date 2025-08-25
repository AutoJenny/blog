# Live Preview Copy Button Diagnosis

## Issue Summary
The copy button on the LLM message management modal was copying incorrect content—specifically old template/fallback content instead of the correct Scottish storytelling content visible in the live preview. The diagnostic log file was also showing this old template content.

## Root Cause Analysis

### Copy Button Issue
1. **Live preview was working correctly** - The `updatePreview()` method was reading from accordion elements and displaying the correct content
2. **Copy function was reading from wrong source** - The `copyPreview()` method was reading from textarea elements (`system_prompt`, `task_prompt`, etc.) which contained old template content from the database via `PromptSelector.loadSavedPrompts()`
3. **Content assembly mismatch** - The copy function and live preview were using different content sources, causing the discrepancy

### Diagnostic Log Issue
1. **Same root cause** - The `runLLM()` method was also reading from the same wrong sources as the copy function
2. **Endpoint receiving correct content** - The `direct_llm_call` endpoint was receiving the correct content from the frontend
3. **Log writing old content** - The diagnostic log was being written with the old template content that was passed to the endpoint

## Solution Implemented

### Copy Button Fix
- Modified `copyPreview()` method to use the same content assembly logic as `updatePreview()`
- Changed from reading textarea elements to reading accordion elements
- Ensured copy function gets content from the same source as live preview

### Diagnostic Log Fix
- Modified `runLLM()` method to use the same content assembly logic as `updatePreview()`
- Changed from reading textarea elements to reading accordion elements
- Ensured LLM run function gets content from the same source as live preview

## Testing Results

### Copy Button
- ✅ Copy button now copies the correct content matching the live preview
- ✅ Content includes proper Scottish storytelling content instead of old template content

### Diagnostic Log
- ✅ Diagnostic log now shows the correct content
- ✅ Log file `/Users/nickfiddes/Code/projects/blog/logs/workflow_diagnostic_llm_message.txt` contains the proper Scottish storytelling content
- ✅ Timestamp shows recent update (2025-07-14T16:46:45.479370)

## Code Changes Made

### Enhanced LLM Message Manager (`app/static/js/enhanced_llm_message_manager.js`)

#### Copy Preview Method (lines 998-1126)
```javascript
copyPreview() {
    console.log('[ENHANCED_LLM] Copy preview called - using same logic as updatePreview()');
    
    // Use the same content assembly logic as updatePreview() but get content from current workflow context
    const enabledElements = [];
    const container = document.getElementById('all-elements-container');
    if (!container) {
        console.error('[ENHANCED_LLM] Container not found for copy');
        return;
    }

    // Get all draggable elements in their current order
    const allElements = container.querySelectorAll('.message-accordion, .message-element[data-element-type="instruction"]');
    
    allElements.forEach(element => {
        const toggle = element.querySelector('.element-toggle');
        if (toggle && toggle.checked) {
            const elementType = element.getAttribute('data-element-type');
            
            if (elementType === 'instruction') {
                // Handle instruction elements
                const content = element.querySelector('.element-content');
                if (content && content.textContent.trim() && content.textContent !== 'Click to edit your instruction...') {
                    enabledElements.push({
                        label: 'INSTRUCTION',
                        content: content.textContent.trim()
                    });
                }
            } else {
                // Handle accordion elements - get content from current workflow context instead of textarea
                let label = elementType.replace('_', ' ').toUpperCase();
                
                switch (elementType) {
                    case 'system_prompt':
                        label = 'SYSTEM PROMPT';
                        break;
                    case 'basic_idea':
                        label = 'BASIC IDEA';
                        break;
                    case 'section_headings':
                        label = 'SECTION HEADINGS';
                        break;
                    case 'idea_scope':
                        label = 'IDEA SCOPE';
                        break;
                    case 'task_prompt':
                        label = 'TASK PROMPT';
                        break;
                    case 'inputs':
                        label = 'INPUT FIELDS';
                        break;
                    case 'settings':
                        label = 'SETTINGS';
                        break;
                }
                
                // Check if this accordion has individual field elements (like inputs/outputs)
                const fieldElements = element.querySelectorAll('.message-element');
                if (fieldElements.length > 0) {
                    // This accordion contains individual field elements
                    let sectionContent = '';
                    fieldElements.forEach(fieldElement => {
                        const fieldToggle = fieldElement.querySelector('.element-toggle');
                        if (fieldToggle && fieldToggle.checked) {
                            const fieldContent = fieldElement.querySelector('.element-content');
                            if (fieldContent && fieldContent.textContent.trim()) {
                                const fieldLabel = fieldElement.querySelector('.element-label');
                                const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                sectionContent += `${label}: ${fieldContent.textContent.trim()}\n`;
                            }
                        }
                    });
                    
                    if (sectionContent.trim()) {
                        enabledElements.push({
                            label: label,
                            content: sectionContent.trim()
                        });
                    }
                } else {
                    // This accordion has direct content - get from current workflow context
                    const content = element.querySelector('.element-content');
                    if (content && content.textContent.trim()) {
                        enabledElements.push({
                            label: label,
                            content: content.textContent.trim()
                        });
                    }
                }
            }
        }
    });

    // Assemble the message with labels and line returns (plain text version)
    let message = '';
    enabledElements.forEach((element, index) => {
        if (index > 0) {
            message += '\n\n'; // Add line returns before each part
        }
        message += `=== ${element.label} ===\n${element.content}`;
    });
    
    // If no elements enabled, show empty
    if (enabledElements.length === 0) {
        message = '';
    }
    
    console.log('[ENHANCED_LLM] Assembled content for copy:', message ? message.substring(0, 200) + '...' : 'empty');
    
    if (!message || message.trim() === '') {
        alert('Please enable some elements before copying.');
        return;
    }

    // Copy to clipboard
    navigator.clipboard.writeText(message).then(() => {
        console.log('[ENHANCED_LLM] Content copied to clipboard');
        
        // Show success message
        const copyButton = document.getElementById('copy-preview-btn');
        if (copyButton) {
            const originalText = copyButton.textContent;
            copyButton.textContent = 'Copied!';
            copyButton.classList.add('success');
            
            setTimeout(() => {
                copyButton.textContent = originalText;
                copyButton.classList.remove('success');
            }, 2000);
        }
    }).catch(err => {
        console.error('[ENHANCED_LLM] Failed to copy to clipboard:', err);
        alert('Failed to copy to clipboard. Please try again.');
    });
}
```

#### Run LLM Method (lines 1203-1355)
```javascript
runLLM() {
    console.log('[ENHANCED_LLM] Run LLM called - using same logic as updatePreview()');
    
    // Use the same content assembly logic as updatePreview() but get content from current workflow context
    const enabledElements = [];
    const container = document.getElementById('all-elements-container');
    if (!container) {
        console.error('[ENHANCED_LLM] Container not found for LLM run');
        return;
    }

    // Get all draggable elements in their current order
    const allElements = container.querySelectorAll('.message-accordion, .message-element[data-element-type="instruction"]');
    
    allElements.forEach(element => {
        const toggle = element.querySelector('.element-toggle');
        if (toggle && toggle.checked) {
            const elementType = element.getAttribute('data-element-type');
            
            if (elementType === 'instruction') {
                // Handle instruction elements
                const content = element.querySelector('.element-content');
                if (content && content.textContent.trim() && content.textContent !== 'Click to edit your instruction...') {
                    enabledElements.push({
                        label: 'INSTRUCTION',
                        content: content.textContent.trim()
                    });
                }
            } else {
                // Handle accordion elements - get content from current workflow context instead of textarea
                let label = elementType.replace('_', ' ').toUpperCase();
                
                switch (elementType) {
                    case 'system_prompt':
                        label = 'SYSTEM PROMPT';
                        break;
                    case 'basic_idea':
                        label = 'BASIC IDEA';
                        break;
                    case 'section_headings':
                        label = 'SECTION HEADINGS';
                        break;
                    case 'idea_scope':
                        label = 'IDEA SCOPE';
                        break;
                    case 'task_prompt':
                        label = 'TASK PROMPT';
                        break;
                    case 'inputs':
                        label = 'INPUT FIELDS';
                        break;
                    case 'settings':
                        label = 'SETTINGS';
                        break;
                }
                
                // Check if this accordion has individual field elements (like inputs/outputs)
                const fieldElements = element.querySelectorAll('.message-element');
                if (fieldElements.length > 0) {
                    // This accordion contains individual field elements
                    let sectionContent = '';
                    fieldElements.forEach(fieldElement => {
                        const fieldToggle = fieldElement.querySelector('.element-toggle');
                        if (fieldToggle && fieldToggle.checked) {
                            const fieldContent = fieldElement.querySelector('.element-content');
                            if (fieldContent && fieldContent.textContent.trim()) {
                                const fieldLabel = fieldElement.querySelector('.element-label');
                                const label = fieldLabel ? fieldLabel.textContent : 'Field';
                                sectionContent += `${label}: ${fieldContent.textContent.trim()}\n`;
                            }
                        }
                    });
                    
                    if (sectionContent.trim()) {
                        enabledElements.push({
                            label: label,
                            content: sectionContent.trim()
                        });
                    }
                } else {
                    // This accordion has direct content - get from current workflow context
                    const content = element.querySelector('.element-content');
                    if (content && content.textContent.trim()) {
                        enabledElements.push({
                            label: label,
                            content: content.textContent.trim()
                        });
                    }
                }
            }
        }
    });

    // Assemble the message with labels and line returns (plain text version)
    let message = '';
    enabledElements.forEach((element, index) => {
        if (index > 0) {
            message += '\n\n'; // Add line returns before each part
        }
        message += `=== ${element.label} ===\n${element.content}`;
    });
    
    // If no elements enabled, show empty
    if (enabledElements.length === 0) {
        message = '';
    }
    
    console.log('[ENHANCED_LLM] Assembled content for LLM:', message ? message.substring(0, 200) + '...' : 'empty');
    
    if (!message || message.trim() === '') {
        alert('Please enable some elements before running the LLM.');
        return;
    }

    // Get current workflow context
    const pathParts = window.location.pathname.split('/');
    const postId = pathParts[3];
    const stage = pathParts[4];
    const substage = pathParts[5];
    
    // Get current step from panel data
    const panel = document.querySelector('[data-current-stage]');
    const step = panel ? panel.dataset.currentStep : 'section_headings';
    
    console.log('[ENHANCED_LLM] Running LLM with context:', { postId, stage, substage, step });
    
    // Use the existing LLM direct endpoint
    fetch('/api/workflow/llm/direct', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            prompt: message,
            post_id: postId,
            step: step
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('[ENHANCED_LLM] LLM response:', data);
        if (data.success) {
            alert('LLM run completed successfully!');
        } else {
            alert('LLM run failed: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('[ENHANCED_LLM] LLM run error:', error);
        alert('LLM run failed: ' + error.message);
    });
}
```

## Status: RESOLVED ✅

Both the copy button and diagnostic log issues have been successfully fixed. The copy button now copies the correct content matching the live preview, and the diagnostic log shows the proper Scottish storytelling content instead of the old template content. 