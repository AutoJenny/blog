// Header Image Details Panel JavaScript

class HeaderImageDetailsPanel {
    constructor() {
        this.postId = window.postId;
        this.imageId = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadExistingImageDetails();
    }
    
    initializeElements() {
        this.generateBtn = document.getElementById('generate-details-btn');
        this.saveBtn = document.getElementById('save-details-btn');
        this.captionTextarea = document.getElementById('image-caption-input');
        this.altTextTextarea = document.getElementById('image-alt-input');
        this.titleInput = document.getElementById('image-title-input');
        this.statusSpan = document.getElementById('image-details-status');
    }
    
    bindEvents() {
        if (this.generateBtn) {
            this.generateBtn.addEventListener('click', () => this.generateImageDetails());
        }
        
        if (this.saveBtn) {
            this.saveBtn.addEventListener('click', () => this.saveImageDetails());
        }
        
        // Auto-save on input changes
        if (this.captionTextarea) {
            this.captionTextarea.addEventListener('input', () => this.updateStatus('Unsaved changes'));
        }
        
        if (this.altTextTextarea) {
            this.altTextTextarea.addEventListener('input', () => this.updateStatus('Unsaved changes'));
        }
        
        if (this.titleInput) {
            this.titleInput.addEventListener('input', () => this.updateStatus('Unsaved changes'));
        }
    }
    
    async generateImageDetails() {
        try {
            this.updateStatus('Generating details...');
            this.generateBtn.disabled = true;
            
            // Get the current image prompt from the generation panel
            const promptTextarea = document.getElementById('compiled-prompt-textarea');
            const imagePrompt = promptTextarea ? promptTextarea.value.trim() : '';
            
            if (!imagePrompt) {
                throw new Error('No image prompt available. Please compile a prompt first.');
            }
            
            // Generate caption and alt text using LLM
            const response = await fetch(`/header/api/posts/${this.postId}/generate-image-details`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_prompt: imagePrompt
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.captionTextarea.value = data.caption || '';
                this.altTextTextarea.value = data.alt_text || '';
                this.titleInput.value = data.title || '';
                this.updateStatus('Details generated');
            } else {
                this.updateStatus('Generation failed');
                console.error('Generation error:', data.error);
            }
        } catch (error) {
            this.updateStatus('Generation failed');
            console.error('Error generating image details:', error);
        } finally {
            this.generateBtn.disabled = false;
        }
    }
    
    async saveImageDetails() {
        try {
            this.updateStatus('Saving...');
            this.saveBtn.disabled = true;
            
            const caption = this.captionTextarea.value.trim();
            const altText = this.altTextTextarea.value.trim();
            const title = this.titleInput.value.trim();
            
            const response = await fetch(`/header/api/posts/${this.postId}/save-image-details`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    caption: caption,
                    alt_text: altText,
                    title: title
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateStatus('Details saved');
            } else {
                this.updateStatus('Save failed');
                console.error('Save error:', data.error);
            }
        } catch (error) {
            this.updateStatus('Save failed');
            console.error('Error saving image details:', error);
        } finally {
            this.saveBtn.disabled = false;
        }
    }
    
    async loadExistingImageDetails() {
        try {
            const response = await fetch(`/header/api/posts/${this.postId}/get-header-image`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    this.imageId = data.image_id;
                    this.captionTextarea.value = data.caption || '';
                    this.altTextTextarea.value = data.alt_text || '';
                    this.titleInput.value = data.title || '';
                    this.updateStatus('Details loaded');
                }
            }
        } catch (error) {
            console.error('Error loading existing image details:', error);
        }
    }
    
    updateStatus(message) {
        if (this.statusSpan) {
            this.statusSpan.textContent = message;
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
    window.headerImageDetailsPanel = new HeaderImageDetailsPanel();
});
