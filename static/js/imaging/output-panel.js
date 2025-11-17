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
            // Determine which endpoint to use based on current substage
            let apiEndpoint;
            if (window.currentSubstage === 'image-generation') {
                apiEndpoint = `/imaging/api/posts/${window.postId}/sections/${sectionId}/raw-image`;
                console.log('[Imaging Output Panel] Using raw-image endpoint for image-generation stage');
            } else {
                apiEndpoint = `/imaging/api/posts/${window.postId}/sections/${sectionId}/image`;
                console.log('[Imaging Output Panel] Using persisted image endpoint for', window.currentSubstage, 'stage');
            }
            
            // Try to load image for this section
            const response = await fetch(apiEndpoint);
            const data = await response.json();
            
            if (data.success) {
                // Check for both landscape and portrait images
                if (data.landscape_path || data.portrait_path) {
                    console.log('[Imaging Output Panel] Found images - landscape:', data.landscape_path, 'portrait:', data.portrait_path);
                    this.displayImagesWithTabs(data.landscape_path, data.portrait_path, data.type);
                } else if (data.path) {
                    // Fallback to old format
                    console.log('[Imaging Output Panel] Found image (old format):', data.path);
                    this.displayPersistedImage(data.path, data.type);
                } else {
                    console.log('[Imaging Output Panel] No image found, showing placeholder');
                    this.displayNoImages();
                }
            } else {
                console.log('[Imaging Output Panel] No image found, showing placeholder');
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

    displayImagesWithTabs(landscapePath, portraitPath, imageType) {
        const displayArea = document.getElementById('image-display-area');
        if (!displayArea) return;

        // Determine which images are available
        const hasLandscape = !!landscapePath;
        const hasPortrait = !!portraitPath;
        
        if (!hasLandscape && !hasPortrait) {
            this.displayNoImages();
            return;
        }

        // If only one image, display it directly without tabs
        if (hasLandscape && !hasPortrait) {
            this.displayPersistedImage(landscapePath, imageType);
            return;
        }
        if (hasPortrait && !hasLandscape) {
            this.displayPersistedImage(portraitPath, imageType);
            return;
        }

        // Both images available - show tabs
        displayArea.innerHTML = `
            <div class="image-tabs-container" style="margin-bottom: 1rem;">
                <div class="image-tabs" style="display: flex; gap: 0.5rem; border-bottom: 2px solid #334155; margin-bottom: 1rem;">
                    <button class="image-tab active" data-tab="landscape" style="
                        background: none;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        color: #e2e8f0;
                        cursor: pointer;
                        border-bottom: 2px solid #10b981;
                        margin-bottom: -2px;
                        font-size: 0.9rem;
                        font-weight: 500;
                    ">Landscape</button>
                    <button class="image-tab" data-tab="portrait" style="
                        background: none;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        color: #94a3b8;
                        cursor: pointer;
                        border-bottom: 2px solid transparent;
                        margin-bottom: -2px;
                        font-size: 0.9rem;
                        font-weight: 500;
                    ">Portrait</button>
                </div>
                <div class="image-tab-content" id="landscape-tab-content" style="display: block;">
                    <div class="image-grid">
                        <div class="image-card">
                            <img src="${landscapePath}" alt="Landscape Image" style="max-width: 100%; height: auto;">
                            <p class="image-caption">Landscape Image (${imageType})</p>
                        </div>
                    </div>
                </div>
                <div class="image-tab-content" id="portrait-tab-content" style="display: none;">
                    <div class="image-grid">
                        <div class="image-card">
                            <img src="${portraitPath}" alt="Portrait Image" style="max-width: 100%; height: auto;">
                            <p class="image-caption">Portrait Image (${imageType})</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add tab switching functionality
        const tabs = displayArea.querySelectorAll('.image-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                
                // Update tab styles
                tabs.forEach(t => {
                    t.style.color = '#94a3b8';
                    t.style.borderBottomColor = 'transparent';
                });
                tab.style.color = '#e2e8f0';
                tab.style.borderBottomColor = '#10b981';
                
                // Show/hide content
                const landscapeContent = displayArea.querySelector('#landscape-tab-content');
                const portraitContent = displayArea.querySelector('#portrait-tab-content');
                
                if (tabName === 'landscape') {
                    landscapeContent.style.display = 'block';
                    portraitContent.style.display = 'none';
                } else {
                    landscapeContent.style.display = 'none';
                    portraitContent.style.display = 'block';
                }
            });
        });
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
        
        if (imageData) {
            // Use the new tabbed display if both landscape and portrait are available
            if (imageData.landscape_path || imageData.portrait_path) {
                this.displayImagesWithTabs(imageData.landscape_path, imageData.portrait_path, 'raw');
            } else if (imageData.image_path) {
                // Fallback to single image display
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
        } else {
            console.error('[Imaging Output Panel] No image data received');
        }
    }
}

// Initialize the output panel when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.imagingOutputPanel = new ImagingOutputPanel();
    console.log('[Imaging Output Panel] Initialized and assigned to window.imagingOutputPanel');
});
