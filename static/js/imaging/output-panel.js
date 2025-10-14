/**
 * Imaging Output Panel - Self-contained JavaScript module
 * Handles image display and generation results
 */

class ImagingOutputPanel {
    constructor() {
        this.currentSectionId = null;
        this.currentImages = [];
        this.init();
    }

    init() {
        console.log('[Imaging Output Panel] Initializing output panel');
        this.setupEventListeners();
        
        // Make this panel globally available
        window.imagingOutputPanel = this;
        
        // Debug: Check if elements exist
        const titleElement = document.getElementById('current-section-title');
        const displayArea = document.getElementById('image-display-area');
        console.log('[Imaging Output Panel] Title element:', titleElement);
        console.log('[Imaging Output Panel] Display area:', displayArea);
        
        // Set initial state
        this.displayNoImages();
    }

    setupEventListeners() {
        // Listen for section selection events
        document.addEventListener('sectionSelected', (event) => {
            this.loadSectionImages(event.detail.sectionId);
        });
    }

    async loadSectionImages(sectionId) {
        console.log('[Imaging Output Panel] Loading images for section:', sectionId);
        this.currentSectionId = sectionId;
        
        try {
            // Try to load persisted image for this section
            const response = await fetch(`/imaging/api/posts/${window.postId}/sections/${sectionId}/image`);
            const data = await response.json();
            
            if (data.success && data.path) {
                console.log('[Imaging Output Panel] Found persisted image:', data.path);
                this.displayPersistedImage(data.path, data.type);
            } else {
                console.log('[Imaging Output Panel] No persisted image found, showing placeholder');
                this.displayNoImages();
            }
        } catch (error) {
            console.error('[Imaging Output Panel] Error loading persisted image:', error);
            this.displayNoImages();
        }
    }

    displayPersistedImage(imagePath, imageType) {
        const displayArea = document.getElementById('image-display-area');
        if (!displayArea) return;

        displayArea.innerHTML = `
            <div class="image-grid">
                <div class="image-card">
                    <img src="${imagePath}" alt="Generated Image" style="max-width: 100%; height: auto;">
                    <p class="image-caption">Generated Image (${imageType})</p>
                </div>
            </div>
        `;
    }

    displayImages(images) {
        const displayArea = document.getElementById('image-display-area');
        if (!displayArea) return;

        if (images.length === 0) {
            this.displayNoImages();
            return;
        }

        let imagesHTML = '';
        images.forEach((image, index) => {
            imagesHTML += `
                <div class="image-item">
                    <img src="${image.url}" alt="${image.alt_text || 'Generated image'}" 
                         class="generated-image" 
                         onclick="window.imagingOutputPanel.openImageModal('${image.url}')">
                    <div class="image-info">
                        <p class="image-caption">${image.caption || 'No caption'}</p>
                        <p class="image-alt">${image.alt_text || 'No alt text'}</p>
                    </div>
                </div>
            `;
        });

        displayArea.innerHTML = imagesHTML;
    }

    displayNoImages() {
        const displayArea = document.getElementById('image-display-area');
        if (!displayArea) return;

        displayArea.innerHTML = `
            <div class="no-selection-message">
                <i class="fas fa-image" style="font-size: 3rem; color: #64748b; margin-bottom: 1rem;"></i>
                <p style="color: #94a3b8; font-size: 1.1rem;">No images generated for this section yet</p>
            </div>
        `;
    }

    openImageModal(imageUrl) {
        // Simple modal implementation
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            cursor: pointer;
        `;
        
        const img = document.createElement('img');
        img.src = imageUrl;
        img.style.cssText = `
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
        `;
        
        modal.appendChild(img);
        modal.onclick = () => document.body.removeChild(modal);
        document.body.appendChild(modal);
    }

    updateSectionTitle(sectionTitle) {
        const titleElement = document.getElementById('current-section-title');
        if (titleElement) {
            titleElement.innerHTML = `<span class="panel-name-green">Output:</span> ${sectionTitle}`;
        }
    }

    // Method to be called when image generation completes
    onImageGenerated(imageData) {
        console.log('[Imaging Output Panel] New image generated:', imageData);
        
        if (imageData && imageData.image_path) {
            // Display the new image
            const displayArea = document.getElementById('image-display-area');
            if (displayArea) {
                displayArea.innerHTML = `
                    <div class="image-grid">
                        <div class="image-card">
                            <img src="${imageData.image_path}" alt="Generated Image" style="max-width: 100%; height: auto;">
                            <p class="image-caption">Generated Image</p>
                        </div>
                    </div>
                `;
            }
        } else {
            console.error('[Imaging Output Panel] Invalid image data received:', imageData);
        }
    }
}

// Initialize the output panel when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.imagingOutputPanel = new ImagingOutputPanel();
    console.log('[Imaging Output Panel] Initialized and assigned to window.imagingOutputPanel');
});
