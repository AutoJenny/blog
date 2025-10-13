/**
 * Imaging Workspace - Main Coordination Script
 * Handles initialization and coordination between all imaging panels
 */

// Imaging-specific utility functions
window.ImagingUtils = {
    // Initialize imaging workspace
    init: function() {
        console.log('Imaging workspace initialized');
        this.setupEventListeners();
    },
    
    // Setup global event listeners
    setupEventListeners: function() {
        // Add any global imaging event listeners here
    },
    
    // Imaging-specific state management
    state: {
        currentPost: null,
        currentSection: null,
        selectedModel: 'sdxl-lora'
    },
    
    // Update imaging state
    updateState: function(key, value) {
        this.state[key] = value;
        localStorage.setItem(`imaging-${key}`, JSON.stringify(value));
    },
    
    // Get imaging state
    getState: function(key) {
        const stored = localStorage.getItem(`imaging-${key}`);
        return stored ? JSON.parse(stored) : this.state[key];
    }
};

// Imaging-specific accordion functions
function toggleImagingInputDetailsAccordion() {
    const content = document.getElementById('imaging-input-details-accordion-content');
    const icon = document.getElementById('imaging-input-details-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('imaging-input-details-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('imaging-input-details-accordion-state', 'closed');
    }
}

function toggleModelSelectionAccordion() {
    const content = document.getElementById('model-selection-accordion-content');
    const icon = document.getElementById('model-selection-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('model-selection-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('model-selection-accordion-state', 'closed');
    }
}

function togglePromptConstructionAccordion() {
    const content = document.getElementById('prompt-construction-accordion-content');
    const icon = document.getElementById('prompt-construction-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('prompt-construction-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('prompt-construction-accordion-state', 'closed');
    }
}

function toggleDebuggingAccordion() {
    const content = document.getElementById('debugging-accordion-content');
    const icon = document.getElementById('debugging-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('debugging-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('debugging-accordion-state', 'closed');
    }
}

// Restore accordion states on page load
function restoreImagingAccordionStates() {
    // Restore Input Details accordion state
    const inputDetailsState = localStorage.getItem('imaging-input-details-accordion-state');
    if (inputDetailsState === 'open') {
        const content = document.getElementById('imaging-input-details-accordion-content');
        const icon = document.getElementById('imaging-input-details-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
    
    // Restore Model Selection accordion state
    const modelState = localStorage.getItem('model-selection-accordion-state');
    if (modelState === 'open') {
        const content = document.getElementById('model-selection-accordion-content');
        const icon = document.getElementById('model-selection-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
    
    // Restore Prompt Construction accordion state
    const promptState = localStorage.getItem('prompt-construction-accordion-state');
    if (promptState === 'open') {
        const content = document.getElementById('prompt-construction-accordion-content');
        const icon = document.getElementById('prompt-construction-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
    
    // Restore Debugging accordion state
    const debuggingState = localStorage.getItem('debugging-accordion-state');
    if (debuggingState === 'open') {
        const content = document.getElementById('debugging-accordion-content');
        const icon = document.getElementById('debugging-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Imaging workspace loaded, initializing panels');
    
    // Restore accordion states
    restoreImagingAccordionStates();
    
    // Initialize imaging workspace
    window.ImagingUtils.init();
    
    // Initialize Sections Panel with callbacks
    if (typeof SectionsPanel !== 'undefined') {
        const sectionsPanel = new SectionsPanel({
            postId: window.postId,
            onSectionSelect: async (data) => {
                console.log('Section selected:', data);
                
                // Set global current section ID for other modules
                window.currentSectionId = data.sectionId;
                window.currentSelectedSectionId = data.sectionId;
                
                // Update imaging state
                window.ImagingUtils.updateState('currentSection', data.sectionId);
                
                // Trigger any imaging-specific logic
                if (typeof window.imageGenerationModule !== 'undefined' && window.imageGenerationModule.onSectionSelect) {
                    window.imageGenerationModule.onSectionSelect(data);
                }
            },
            onBatchStart: (selectedIds) => {
                console.log('Batch generation started:', selectedIds);
                
                // Trigger any imaging-specific batch logic
                if (typeof window.imageGenerationModule !== 'undefined' && window.imageGenerationModule.onBatchStart) {
                    window.imageGenerationModule.onBatchStart(selectedIds);
                }
            },
            onBatchComplete: (result) => {
                console.log('Batch generation completed:', result);
                
                // Trigger any imaging-specific completion logic
                if (typeof window.imageGenerationModule !== 'undefined' && window.imageGenerationModule.onBatchComplete) {
                    window.imageGenerationModule.onBatchComplete(result);
                }
            }
        });
        
        console.log('Sections Panel initialized successfully');
    }
    
    console.log('All imaging panels initialized successfully');
});

// Export functions for global access
window.toggleImagingInputDetailsAccordion = toggleImagingInputDetailsAccordion;
window.toggleModelSelectionAccordion = toggleModelSelectionAccordion;
window.togglePromptConstructionAccordion = togglePromptConstructionAccordion;
window.toggleDebuggingAccordion = toggleDebuggingAccordion;
