/* Imaging JavaScript Bundle - Standalone imaging workflow */

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

// Restore accordion state on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedState = localStorage.getItem('imaging-input-details-accordion-state');
    if (savedState === 'open') {
        const content = document.getElementById('imaging-input-details-accordion-content');
        const icon = document.getElementById('imaging-input-details-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
});

// Initialize imaging workspace on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    window.ImagingUtils.init();
});
