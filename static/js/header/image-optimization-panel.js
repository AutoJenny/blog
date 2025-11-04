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
        // These elements may not exist in the simplified layout
        this.optimizedImagePreview = document.getElementById('optimized-image-preview');
        this.optimizedImageSection = document.getElementById('optimized-image-section');
        this.optimizeBtn = document.getElementById('optimize-image-btn');
        
        // Check if we're in simplified layout (optimized images panel exists)
        this.isSimplifiedLayout = document.getElementById('optimized-images-panel') !== null;
    }
    
    bindEvents() {
        if (this.optimizeBtn) {
            this.optimizeBtn.addEventListener('click', () => this.optimizeImage());
        }
    }
    
    async loadRawImage() {
        // Skip loading in simplified layout - it's handled by HeaderImageSimplified
        if (this.isSimplifiedLayout) {
            return;
        }
        
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
            if (this.optimizedImagePreview) {
                this.optimizedImagePreview.src = optimizedPath;
            }
            if (this.optimizedImageSection) {
                this.optimizedImageSection.style.display = 'block';
            }
        };
        img.onerror = () => {
            // Optimized image doesn't exist yet
            if (this.optimizedImageSection) {
                this.optimizedImageSection.style.display = 'none';
            }
        };
        img.src = optimizedPath;
    }
    
    async optimizeImage() {
        try {
            if (!this.optimizeBtn) return;
            
            this.optimizeBtn.disabled = true;
            this.optimizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Optimizing...';
            
            const response = await fetch(`/header/api/posts/${this.postId}/optimize-header-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (data.success) {
                // In simplified layout, the HeaderImageSimplified class handles the display
                if (this.isSimplifiedLayout && window.headerImageSimplified) {
                    // Trigger the simplified layout's optimization handler
                    if (typeof window.headerImageSimplified.optimizeImages === 'function') {
                        // Call it to update the display
                        await window.headerImageSimplified.optimizeImages();
                    }
                    console.log('[ImageOptimizationPanel] Image optimized successfully (simplified layout)');
                } else {
                    // Legacy layout - update the optimized image preview
                    if (this.optimizedImagePreview) {
                        this.optimizedImagePreview.src = data.optimized_path;
                    }
                    if (this.optimizedImageSection) {
                        this.optimizedImageSection.style.display = 'block';
                    }
                }
                
                console.log('[ImageOptimizationPanel] Image optimized successfully');
                if (this.optimizeBtn) {
                    this.optimizeBtn.innerHTML = '<i class="fas fa-check"></i> Optimized!';
                    setTimeout(() => {
                        this.optimizeBtn.innerHTML = '<i class="fas fa-magic"></i> Optimize and Watermark';
                    }, 2000);
                }
                // Notify opener (launchpad) that header image has been optimized
                try { if (window.opener) window.opener.postMessage('header_image_optimized', '*'); } catch(_) {}
            } else {
                console.error('[ImageOptimizationPanel] Error optimizing image:', data.error);
                if (this.optimizeBtn) {
                    this.optimizeBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                    setTimeout(() => {
                        this.optimizeBtn.innerHTML = '<i class="fas fa-magic"></i> Optimize and Watermark';
                    }, 2000);
                }
            }
        } catch (error) {
            console.error('[ImageOptimizationPanel] Error optimizing image:', error);
            if (this.optimizeBtn) {
                this.optimizeBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                setTimeout(() => {
                    this.optimizeBtn.innerHTML = '<i class="fas fa-magic"></i> Optimize and Watermark';
                }, 2000);
            }
        } finally {
            if (this.optimizeBtn) {
                this.optimizeBtn.disabled = false;
            }
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
    
    // Don't auto-initialize on optimise page (which is for sections, not headers)
    if (window.optimisePage || window.currentSubstage === 'optimise') {
        console.log('[ImageOptimizationPanel] Skipping auto-initialization on optimise page');
        return;
    }
    
    // Only initialize if the panel container exists on the page
    if (!document.getElementById('image-optimization-panel')) {
        console.log('[ImageOptimizationPanel] Panel container not found, skipping initialization');
        return;
    }
    
    // Initialize the panel
    console.log('[ImageOptimizationPanel] Initializing panel...');
    window.imageOptimizationPanel = new ImageOptimizationPanel();
    console.log('[ImageOptimizationPanel] Panel initialized:', window.imageOptimizationPanel);
});

