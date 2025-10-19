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
        this.captionInput = document.getElementById('image-caption');
        this.altTextInput = document.getElementById('image-alt-text');
        this.titleInput = document.getElementById('image-title');
        this.saveBtn = document.getElementById('save-image-details-btn');
        this.imagePreview = document.getElementById('image-details-preview');
    }
    
    bindEvents() {
        if (this.saveBtn) {
            this.saveBtn.addEventListener('click', () => this.saveImageDetails());
        }
        
        // Auto-save on input change
        [this.captionInput, this.altTextInput, this.titleInput].forEach(input => {
            if (input) {
                input.addEventListener('input', () => this.markAsChanged());
            }
        });
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
                    if (this.titleInput) this.titleInput.value = data.title || '';
                    
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
    
    async saveImageDetails() {
        if (!this.imageData) {
            console.warn('[HeaderImageDetailsPanel] No image data to save');
            return;
        }
        
        try {
            this.saveBtn.disabled = true;
            this.saveBtn.textContent = 'Saving...';
            
            const updateData = {
                caption: this.captionInput ? this.captionInput.value : '',
                alt_text: this.altTextInput ? this.altTextInput.value : '',
                title: this.titleInput ? this.titleInput.value : ''
            };
            
            const response = await fetch(`/header/api/posts/${this.postId}/update-image-details`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('[HeaderImageDetailsPanel] Image details saved successfully');
                this.saveBtn.textContent = 'Saved!';
                setTimeout(() => {
                    this.saveBtn.textContent = 'Save Details';
                }, 2000);
            } else {
                console.error('[HeaderImageDetailsPanel] Error saving image details:', data.error);
                this.saveBtn.textContent = 'Error';
                setTimeout(() => {
                    this.saveBtn.textContent = 'Save Details';
                }, 2000);
            }
        } catch (error) {
            console.error('[HeaderImageDetailsPanel] Error saving image details:', error);
            this.saveBtn.textContent = 'Error';
            setTimeout(() => {
                this.saveBtn.textContent = 'Save Details';
            }, 2000);
        } finally {
            this.saveBtn.disabled = false;
        }
    }
    
    markAsChanged() {
        if (this.saveBtn) {
            this.saveBtn.textContent = 'Save Details';
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