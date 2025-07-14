// Comprehensive test script for enhanced LLM message manager debugging
console.log('=== ENHANCED LLM MESSAGE MANAGER DEBUG TEST ===');

// Test 1: Check if manager exists
const manager = window.enhancedLLMMessageManager;
if (!manager) {
    console.error('❌ Enhanced LLM Message Manager not found');
} else {
    console.log('✅ Enhanced LLM Message Manager found');
}

// Test 2: Check if modal exists
const modal = document.getElementById('enhanced-llm-message-modal');
if (!modal) {
    console.error('❌ Enhanced LLM message modal not found');
} else {
    console.log('✅ Modal found');
}

// Test 3: Check if accordion elements exist
const accordions = modal ? modal.querySelectorAll('.message-accordion') : [];
console.log(`Found ${accordions.length} accordion elements`);

accordions.forEach((accordion, index) => {
    const elementType = accordion.getAttribute('data-element-type');
    const content = accordion.querySelector('.element-content');
    const toggle = accordion.querySelector('.element-toggle');
    
    console.log(`Accordion ${index} (${elementType}):`, {
        hasContent: !!content,
        contentText: content ? content.textContent.substring(0, 100) + '...' : 'no content',
        isEnabled: toggle ? toggle.checked : false
    });
});

// Test 4: Check if preview element exists
const preview = document.getElementById('enhanced-prompt-preview');
if (preview) {
    console.log('Preview element found:', {
        hasContent: !!preview.textContent,
        content: preview.textContent.substring(0, 200) + '...'
    });
} else {
    console.error('❌ Preview element not found');
}

// Test 5: Check if source elements exist
const sourceElements = {
    system_prompt: document.getElementById('system_prompt'),
    task_prompt: document.getElementById('task_prompt'),
    context_basic_idea: document.getElementById('context_basic_idea'),
    context_section_headings: document.getElementById('context_section_headings'),
    context_idea_scope: document.getElementById('context_idea_scope')
};

console.log('Source elements check:');
Object.entries(sourceElements).forEach(([name, element]) => {
    if (element) {
        console.log(`✅ ${name}:`, {
            hasValue: !!element.value,
            valueLength: element.value ? element.value.length : 0,
            valuePreview: element.value ? element.value.substring(0, 50) + '...' : 'empty'
        });
    } else {
        console.log(`❌ ${name}: not found`);
    }
});

// Test 6: Test content population manually
if (manager) {
    console.log('Testing manual content population...');
    
    // Test system prompt
    const systemPromptElement = document.getElementById('system_prompt');
    if (systemPromptElement && systemPromptElement.value) {
        console.log('Testing system prompt population...');
        manager.updateAccordionContent('system_prompt', systemPromptElement.value);
    }
    
    // Test task prompt
    const taskPromptElement = document.getElementById('task_prompt');
    if (taskPromptElement && taskPromptElement.value) {
        console.log('Testing task prompt population...');
        manager.updateAccordionContent('task_prompt', taskPromptElement.value);
    }
    
    // Test basic idea
    const basicIdeaElement = document.getElementById('context_basic_idea');
    if (basicIdeaElement && basicIdeaElement.value) {
        console.log('Testing basic idea population...');
        manager.updateAccordionContent('basic_idea', basicIdeaElement.value);
    }
    
    // Test section headings
    const sectionHeadingsElement = document.getElementById('context_section_headings');
    if (sectionHeadingsElement && sectionHeadingsElement.value) {
        console.log('Testing section headings population...');
        manager.updateAccordionContent('section_headings', sectionHeadingsElement.value);
    }
    
    // Test idea scope
    const ideaScopeElement = document.getElementById('context_idea_scope');
    if (ideaScopeElement && ideaScopeElement.value) {
        console.log('Testing idea scope population...');
        manager.updateAccordionContent('idea_scope', ideaScopeElement.value);
    }
    
    // Update preview
    console.log('Updating preview...');
    manager.updatePreview();
    
    // Check preview content after update
    const updatedPreview = document.getElementById('enhanced-prompt-preview');
    if (updatedPreview) {
        console.log('Updated preview content:', {
            hasContent: !!updatedPreview.textContent,
            content: updatedPreview.textContent.substring(0, 200) + '...'
        });
    }
}

console.log('=== DEBUG TEST COMPLETE ==='); 