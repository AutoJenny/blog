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

// Note: Prompt Construction accordion is managed by its own self-contained module
// to avoid ID/key mismatches and duplicate state handling.

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
    
    // Prompt Construction accordion state is restored by its own module
    
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
    
    // Panel modules self-initialize on DOMContentLoaded via their own JS files
    // No need to explicitly instantiate them here to avoid duplicate variable errors
    
    // Initialize Imaging Sections Panel with simple callbacks
    if (typeof ImagingSectionsPanel !== 'undefined') {
        const sectionsPanel = new ImagingSectionsPanel({
            postId: window.postId,
            onSectionSelect: async (data) => {
                console.log('Section selected:', data);
                window.currentSectionId = data.sectionId;
                
                // Dispatch sectionSelected event so all panels can respond
                const event = new CustomEvent('sectionSelected', {
                    detail: {
                        sectionId: data.sectionId,
                        section: data.section,
                        postId: data.postId
                    }
                });
                document.dispatchEvent(event);
                
                // Also dispatch legacy event name for compatibility
                const legacyEvent = new CustomEvent('section-selected', {
                    detail: {
                        sectionId: data.sectionId,
                        section: data.section,
                        postId: data.postId
                    }
                });
                document.dispatchEvent(legacyEvent);
                
                // Update output panel if it exists
                if (window.imagingOutputPanel) {
                    window.imagingOutputPanel.loadSectionImages(data.sectionId);
                    window.imagingOutputPanel.updateSectionTitle(data.sectionTitle || `Section ${data.sectionId}`);
                }
            }
        });
        
        // Make sections panel globally available
        window.imagingSectionsPanel = sectionsPanel;
        
        console.log('Imaging Sections Panel initialized successfully');
    } else {
        console.error('ImagingSectionsPanel class not found');
    }
    
    console.log('All imaging panels initialized successfully');
});

// Export functions for global access
window.toggleImagingInputDetailsAccordion = toggleImagingInputDetailsAccordion;
window.toggleModelSelectionAccordion = toggleModelSelectionAccordion;
// Prompt Construction toggle is exported by its own module
window.toggleDebuggingAccordion = toggleDebuggingAccordion;
