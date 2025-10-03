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

// Initialize imaging workspace on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    window.ImagingUtils.init();
});
