// HTML Meta Tags Panel JavaScript

console.log('[MetaTitlePanel] Script loading...');

class MetaTitlePanel {
    constructor() {
        this.postId = window.postId;
        
        this.initializeElements();
        this.loadMetaData();
    }
    
    initializeElements() {
        this.metaTitleInput = document.getElementById('meta-title-input');
        this.metaDescriptionInput = document.getElementById('meta-description-input');
        this.metaTagsInput = document.getElementById('meta-tags-input');
    }
    
    async loadMetaData() {
        try {
            const response = await fetch(`/header/api/posts/${this.postId}/get-meta-data`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    if (this.metaTitleInput) this.metaTitleInput.value = data.meta_title || '';
                    if (this.metaDescriptionInput) this.metaDescriptionInput.value = data.meta_description || '';
                    if (this.metaTagsInput) this.metaTagsInput.value = data.meta_tags || '';
                }
            }
        } catch (error) {
            console.error('[MetaTitlePanel] Error loading meta data:', error);
        }
    }
}

// Global function for accordion
function toggleMetaTitleAccordion() {
    const content = document.getElementById('meta-title-content');
    const icon = document.getElementById('meta-title-accordion-icon');
    
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
        
        // Save accordion state
        if (window.headerAccordionManager) {
            const isOpen = !content.classList.contains('collapsed');
            window.headerAccordionManager.saveAccordionState('meta-title', isOpen);
        }
    }
}

// Initialize panel when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
        window.headerAccordionManager.initializeAccordion(
            'meta-title',
            'meta-title-content',
            'meta-title-accordion-icon'
        );
    } else {
        // Fallback: Initialize accordion as open by default
        const content = document.getElementById('meta-title-content');
        const icon = document.getElementById('meta-title-accordion-icon');
        if (content && icon) {
            content.classList.remove('collapsed');
            icon.classList.add('open');
        }
    }
    
    // Initialize the panel
    console.log('[MetaTitlePanel] Initializing panel...');
    window.metaTitlePanel = new MetaTitlePanel();
});

