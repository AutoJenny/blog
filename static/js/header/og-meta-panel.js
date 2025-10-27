// Open Graph Meta Panel JavaScript

console.log('[OgMetaPanel] Script loading...');

class OgMetaPanel {
    constructor() {
        this.postId = window.postId;
        
        this.initializeElements();
        this.loadOgMetaData();
    }
    
    initializeElements() {
        this.metaImageInput = document.getElementById('meta-image-input');
        this.metaTypeInput = document.getElementById('meta-type-input');
        this.metaSiteNameInput = document.getElementById('meta-site-name-input');
    }
    
    async loadOgMetaData() {
        try {
            const response = await fetch(`/header/api/posts/${this.postId}/get-meta-data`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    if (this.metaImageInput) this.metaImageInput.value = data.meta_image || '';
                    if (this.metaTypeInput) this.metaTypeInput.value = data.meta_type || 'article';
                    if (this.metaSiteNameInput) this.metaSiteNameInput.value = data.meta_site_name || 'Clan.com Blog';
                }
            }
        } catch (error) {
            console.error('[OgMetaPanel] Error loading OG meta data:', error);
        }
    }
}

// Global function for accordion
function toggleOgMetaAccordion() {
    const content = document.getElementById('og-meta-content');
    const icon = document.getElementById('og-meta-accordion-icon');
    
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
        
        // Save accordion state
        if (window.headerAccordionManager) {
            const isOpen = !content.classList.contains('collapsed');
            window.headerAccordionManager.saveAccordionState('og-meta', isOpen);
        }
    }
}

// Initialize panel when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
        window.headerAccordionManager.initializeAccordion(
            'og-meta',
            'og-meta-content',
            'og-meta-accordion-icon'
        );
    } else {
        // Fallback: Initialize accordion as open by default
        const content = document.getElementById('og-meta-content');
        const icon = document.getElementById('og-meta-accordion-icon');
        if (content && icon) {
            content.classList.remove('collapsed');
            icon.classList.add('open');
        }
    }
    
    // Initialize the panel
    console.log('[OgMetaPanel] Initializing panel...');
    window.ogMetaPanel = new OgMetaPanel();
});

