/**
 * Input Image Panel - Self-contained JavaScript module
 * Handles display of raw images that will be optimized.
 */

class InputImagePanel {
  constructor(options = {}) {
    this.postId = options.postId || window.postId;
    this.containerId = options.containerId || 'input-image-panel';
    this.currentSectionId = null;
    this.init();
  }

  init() {
    console.log('[Input Image Panel] Initializing');
    this.setupEventListeners();
    this.restoreAccordionState();
  }

  setupEventListeners() {
    // Listen for section selection events
    document.addEventListener('sectionSelected', (event) => {
      this.loadSectionImages(event.detail.sectionId);
    });
  }

  async loadSectionImages(sectionId) {
    console.log('[Input Image Panel] Loading raw images for section:', sectionId);
    this.currentSectionId = sectionId;
    
    try {
      // Try to load raw image for this section
      const response = await fetch(`/imaging/api/posts/${window.postId}/sections/${sectionId}/raw-image`);
      const data = await response.json();
      
      if (data.success && data.path) {
        console.log('[Input Image Panel] Found raw image:', data.path);
        this.displayRawImage(data.path);
        this.updateStatus(`Raw image loaded for section ${sectionId}`);
      } else {
        console.log('[Input Image Panel] No raw image found');
        this.displayNoImages();
        this.updateStatus(`No raw image found for section ${sectionId}`);
      }
    } catch (error) {
      console.error('[Input Image Panel] Error loading raw image:', error);
      this.displayNoImages();
      this.updateStatus(`Error loading raw image for section ${sectionId}`);
    }
  }

  displayRawImage(imagePath) {
    const displayArea = document.getElementById('input-image-area');
    if (!displayArea) return;

    displayArea.innerHTML = `
      <div class="image-grid">
        <div class="image-card">
          <img src="${imagePath}" alt="Raw Image" style="max-width: 100%; height: auto;">
          <p class="image-caption">Raw Image (PNG)</p>
        </div>
      </div>
    `;
  }

  displayNoImages() {
    const displayArea = document.getElementById('input-image-area');
    if (!displayArea) return;
    displayArea.innerHTML = `
      <div class="no-selection-message">
        <i class="fas fa-image" style="font-size: 3rem; color: #64748b; margin-bottom: 1rem;"></i>
        <p style="color: #94a3b8; font-size: 1.1rem;">Select a section to view its raw images</p>
      </div>
    `;
  }

  updateStatus(text) {
    const statusEl = document.getElementById('input-image-status');
    if (statusEl) {
      statusEl.textContent = text;
    }
  }

  restoreAccordionState() {
    try {
      const state = localStorage.getItem('imaging-input-image-accordion-state');
      const content = document.getElementById('input-image-accordion-content');
      const icon = document.getElementById('input-image-accordion-icon');
      
      if (content && icon) {
        if (state === 'open') {
          content.style.display = 'block';
          icon.className = 'fas fa-chevron-down';
        } else {
          content.style.display = 'none';
          icon.className = 'fas fa-chevron-up';
        }
      }
    } catch (error) {
      console.error('[Input Image Panel] Error restoring accordion state:', error);
    }
  }
}

// Global accordion toggle function
window.toggleInputImageAccordion = function() {
  const content = document.getElementById('input-image-accordion-content');
  const icon = document.getElementById('input-image-accordion-icon');
  
  if (!content || !icon) return;
  
  const isOpen = content.style.display === 'block';
  const nextState = !isOpen;
  
  content.style.display = nextState ? 'block' : 'none';
  icon.className = nextState ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
  
  try {
    localStorage.setItem('imaging-input-image-accordion-state', nextState ? 'open' : 'closed');
  } catch (error) {
    console.error('[Input Image Panel] Error saving accordion state:', error);
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new InputImagePanel();
});
