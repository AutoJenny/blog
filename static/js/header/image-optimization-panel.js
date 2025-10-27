// Image Optimization Panel JavaScript

console.log('[ImageOptimizationPanel] Script loading...');

class ImageOptimizationPanel {
    constructor() {
        this.postId = window.postId;
        this.imageData = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadRawImage();
    }
    
    initializeElements() {
        this.optimizedImagePreview = document.getElementById('optimized-image-preview');
        this.optimizedImageSection = document.getElementById('optimized-image-section');
        this.optimizeBtn = document.getElementById('optimize-image-btn');
    }
    
    bindEvents() {
        if (this.optimizeBtn) {
            this.optimizeBtn.addEventListener('click', () => this.optimizeImage());
        }
    }
    
    async loadRawImage() {
        try {
            // Get the raw image path from the image generation panel
            const response = await fetch(`/header/api/posts/${this.postId}/get-header-image`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.file_path) {
                    // Check if optimized image exists
                    const optimizedPath = data.file_path.replace('/raw/', '/optimized/').replace('.png', '.jpg');
                    this.loadOptimizedImage(optimizedPath);
                }
            }
        } catch (error) {
            console.error('[ImageOptimizationPanel] Error loading raw image:', error);
        }
    }
    
    async loadOptimizedImage(optimizedPath) {
        // Try to load the optimized image
        const img = new Image();
        img.onload = () => {
            this.optimizedImagePreview.src = optimizedPath;
            this.optimizedImageSection.style.display = 'block';
        };
        img.onerror = () => {
            // Optimized image doesn't exist yet
            this.optimizedImageSection.style.display = 'none';
        };
        img.src = optimizedPath;
    }
    
    async optimizeImage() {
        try {
            this.optimizeBtn.disabled = true;
            this.optimizeBtn.textContent = 'Optimizing...';
            
            const response = await fetch(`/header/api/posts/${this.postId}/optimize-header-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update the optimized image preview
                this.optimizedImagePreview.src = data.optimized_path;
                this.optimizedImageSection.style.display = 'block';
                
                console.log('[ImageOptimizationPanel] Image optimized successfully');
                this.optimizeBtn.textContent = 'Optimized!';
                setTimeout(() => {
                    this.optimizeBtn.textContent = 'Optimize and Watermark';
                }, 2000);
            } else {
                console.error('[ImageOptimizationPanel] Error optimizing image:', data.error);
                this.optimizeBtn.textContent = 'Error';
                setTimeout(() => {
                    this.optimizeBtn.textContent = 'Optimize and Watermark';
                }, 2000);
            }
        } catch (error) {
            console.error('[ImageOptimizationPanel] Error optimizing image:', error);
            this.optimizeBtn.textContent = 'Error';
            setTimeout(() => {
                this.optimizeBtn.textContent = 'Optimize and Watermark';
            }, 2000);
        } finally {
            this.optimizeBtn.disabled = false;
        }
    }
}

// Global function for accordion
function toggleImageOptimizationAccordion() {
    const content = document.getElementById('image-optimization-content');
    const icon = document.getElementById('image-optimization-accordion-icon');
    
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
        
        // Save accordion state
        if (window.headerAccordionManager) {
            const isOpen = !content.classList.contains('collapsed');
            window.headerAccordionManager.saveAccordionState('image-optimization', isOpen);
        }
    }
}

// Initialize panel when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
        window.headerAccordionManager.initializeAccordion(
            'image-optimization',
            'image-optimization-content',
            'image-optimization-accordion-icon'
        );
    } else {
        // Fallback: Initialize accordion as open by default
        const content = document.getElementById('image-optimization-content');
        const icon = document.getElementById('image-optimization-accordion-icon');
        if (content && icon) {
            content.classList.remove('collapsed');
            icon.classList.add('open');
        }
    }
    
    // Initialize the panel
    console.log('[ImageOptimizationPanel] Initializing panel...');
    window.imageOptimizationPanel = new ImageOptimizationPanel();
    console.log('[ImageOptimizationPanel] Panel initialized:', window.imageOptimizationPanel);
});

