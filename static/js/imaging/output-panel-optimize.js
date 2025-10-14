/**
 * Optimized Output Panel - Self-contained JavaScript module
 * Handles display of optimized/watermarked images for the optimize page.
 */

class OptimizedOutputPanel {
  constructor() {
    this.currentSectionId = null;
    this.init();
  }

  init() {
    console.log('[Optimized Output Panel] Initializing');
    window.optimizedOutputPanel = this; // Expose globally for other modules
    this.setupEventListeners();
  }

  setupEventListeners() {
    document.addEventListener('sectionSelected', (event) => {
      this.loadSectionImages(event.detail.sectionId);
    });
  }

  async loadSectionImages(sectionId) {
    console.log('[Optimized Output Panel] Loading optimized images for section:', sectionId);
    this.currentSectionId = sectionId;
    
    try {
      // Try to load optimized image for this section
      const response = await fetch(`/imaging/api/posts/${window.postId}/sections/${sectionId}/image`);
      const data = await response.json();
      
      if (data.success && data.path) {
        console.log('[Optimized Output Panel] Found optimized image:', data.path);
        this.displayOptimizedImage(data.path, data.type);
      } else {
        console.log('[Optimized Output Panel] No optimized image found, showing placeholder');
        this.displayNoImages();
      }
    } catch (error) {
      console.error('[Optimized Output Panel] Error loading optimized image:', error);
      this.displayNoImages();
    }
  }

  displayOptimizedImage(imagePath, imageType) {
    const displayArea = document.getElementById('image-display-area');
    if (!displayArea) return;

    displayArea.innerHTML = `
      <div class="image-grid">
        <div class="image-card">
          <img src="${imagePath}" alt="Optimized Image" style="max-width: 100%; height: auto;">
          <p class="image-caption">Optimized Image (${imageType})</p>
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

    displayArea.innerHTML = `
      <div class="image-grid">
        ${images.map(image => `
          <div class="image-card">
            <img src="${image.path}" alt="Optimized Image" style="max-width: 100%; height: auto;">
            <p class="image-caption">${image.caption || 'Optimized Image'}</p>
          </div>
        `).join('')}
      </div>
    `;
  }

  displayNoImages() {
    const displayArea = document.getElementById('image-display-area');
    if (!displayArea) return;
    displayArea.innerHTML = `
      <div class="no-selection-message">
        <i class="fas fa-image" style="font-size: 3rem; color: #64748b; margin-bottom: 1rem;"></i>
        <p style="color: #94a3b8; font-size: 1.1rem;">Select a section to view its optimized images</p>
      </div>
    `;
  }

  onImageOptimized(imagePath) {
    console.log('[Optimized Output Panel] Image optimized:', imagePath);
    this.displayOptimizedImage(imagePath, 'optimized');
  }

  updateSectionTitle(title) {
    const titleEl = document.getElementById('current-section-title');
    if (titleEl) {
      titleEl.innerHTML = `<span class="panel-name-green">Optimized Output:</span> ${title}`;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new OptimizedOutputPanel();
});
