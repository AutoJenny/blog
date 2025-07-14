// Test script to verify enhanced LLM message manager content population
console.log('Testing enhanced LLM message manager content population...');

// Wait for page to load
setTimeout(() => {
    // Check if the enhanced LLM message manager exists
    const manager = window.enhancedLLMMessageManager;
    if (!manager) {
        console.error('Enhanced LLM Message Manager not found');
        return;
    }
    
    console.log('Enhanced LLM Message Manager found:', manager);
    
    // Check if modal exists
    const modal = document.getElementById('enhanced-llm-message-modal');
    if (!modal) {
        console.error('Enhanced LLM message modal not found');
        return;
    }
    
    console.log('Modal found:', modal);
    
    // Check if accordion elements exist
    const accordions = modal.querySelectorAll('.message-accordion');
    console.log('Found accordions:', accordions.length);
    
    accordions.forEach((accordion, index) => {
        const elementType = accordion.getAttribute('data-element-type');
        const content = accordion.querySelector('.element-content');
        const toggle = accordion.querySelector('.element-toggle');
        
        console.log(`Accordion ${index}:`, {
            elementType: elementType,
            hasContent: !!content,
            contentText: content ? content.textContent.substring(0, 100) + '...' : 'no content',
            isEnabled: toggle ? toggle.checked : false
        });
    });
    
    // Check if preview element exists
    const preview = document.getElementById('enhanced-prompt-preview');
    if (preview) {
        console.log('Preview element found:', {
            hasContent: !!preview.textContent,
            content: preview.textContent.substring(0, 200) + '...'
        });
    } else {
        console.error('Preview element not found');
    }
    
}, 2000); 