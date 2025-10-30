// Header Image Details Panel JavaScript

console.log('[HeaderImageDetailsPanel] Script loading...');

class HeaderImageDetailsPanel {
    constructor() {
        this.postId = window.postId;
        this.imageData = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadImageDetails();
    }
    
    initializeElements() {
        this.captionInput = document.getElementById('image-caption-input');
        this.altTextInput = document.getElementById('image-alt-input');
        this.generateBtn = document.getElementById('generate-details-btn');
    }
    
    bindEvents() {
        if (this.generateBtn) {
            this.generateBtn.addEventListener('click', () => this.generateImageDetails());
        }
    }
    
    async loadImageDetails() {
        try {
            const response = await fetch(`/header/api/posts/${this.postId}/get-header-image`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    this.imageData = data;
                    
                    // Update form fields
                    if (this.captionInput) this.captionInput.value = data.caption || '';
                    if (this.altTextInput) this.altTextInput.value = data.alt_text || '';
                    
                    // Update image preview
                    if (this.imagePreview) {
                        this.imagePreview.src = data.file_path;
                        this.imagePreview.alt = data.alt_text || 'Header image';
                    }
                    
                    console.log('[HeaderImageDetailsPanel] Image details loaded:', data);
                }
            }
        } catch (error) {
            console.error('[HeaderImageDetailsPanel] Error loading image details:', error);
        }
    }
    
    async generateImageDetails() {
        try {
            this.generateBtn.disabled = true;
            this.generateBtn.textContent = 'Generating...';
            
            // Get the header image data to generate details from
            const response = await fetch(`/header/api/posts/${this.postId}/generate-image-details`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update the fields with generated content
                if (this.captionInput) this.captionInput.value = data.caption || '';
                if (this.altTextInput) this.altTextInput.value = data.alt_text || '';
                
                console.log('[HeaderImageDetailsPanel] Image details generated and saved');
                this.generateBtn.textContent = 'Generated!';
                setTimeout(() => {
                    this.generateBtn.textContent = 'Generate';
                }, 2000);
                // Notify opener (launchpad) that header image details are ready
                try { if (window.opener) window.opener.postMessage('header_image_details_complete', '*'); } catch(_) {}
            } else {
                console.error('[HeaderImageDetailsPanel] Error generating image details:', data.error);
                this.generateBtn.textContent = 'Error';
                setTimeout(() => {
                    this.generateBtn.textContent = 'Generate';
                }, 2000);
            }
        } catch (error) {
            console.error('[HeaderImageDetailsPanel] Error generating image details:', error);
            this.generateBtn.textContent = 'Error';
            setTimeout(() => {
                this.generateBtn.textContent = 'Generate';
            }, 2000);
        } finally {
            this.generateBtn.disabled = false;
        }
    }
}

// Global function for accordion
function toggleImageDetailsAccordion() {
    const content = document.getElementById('image-details-content');
    const icon = document.getElementById('image-details-accordion-icon');
    
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
        
        // Save accordion state
        if (window.headerAccordionManager) {
            const isOpen = !content.classList.contains('collapsed');
            window.headerAccordionManager.saveAccordionState('image-details', isOpen);
        }
    }
}

// Initialize panel when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
        window.headerAccordionManager.initializeAccordion(
            'image-details',
            'image-details-content',
            'image-details-accordion-icon'
        );
    } else {
        // Fallback: Initialize accordion as open by default
        const content = document.getElementById('image-details-content');
        const icon = document.getElementById('image-details-accordion-icon');
        if (content && icon) {
            content.classList.remove('collapsed');
            icon.classList.add('open');
        }
    }
    
    // Initialize the panel
    console.log('[HeaderImageDetailsPanel] Initializing panel...');
    window.headerImageDetailsPanel = new HeaderImageDetailsPanel();
    console.log('[HeaderImageDetailsPanel] Panel initialized:', window.headerImageDetailsPanel);
});