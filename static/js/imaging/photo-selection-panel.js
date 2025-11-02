/**
 * Photo Selection Panel
 * Displays currently selected photo with credits and details
 */

class PhotoSelectionPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentSectionId = null;
        this.init();
    }
    
    init() {
        // Listen for photo selection
        document.addEventListener('photo-selected', (e) => {
            this.displaySelectedPhoto(e.detail.photo);
        });
        
        // Listen for section selection
        document.addEventListener('section-selected', (e) => {
            this.currentSectionId = e.detail.sectionId;
            this.loadSelectedPhoto();
        });
        
        // Deselect button
        const deselectBtn = document.getElementById('deselect-photo-btn');
        if (deselectBtn) {
            deselectBtn.addEventListener('click', () => this.deselectPhoto());
        }
    }
    
    async loadSelectedPhoto() {
        if (!this.currentSectionId) {
            this.showNoSelection();
            return;
        }
        
        try {
            const response = await fetch(`/imaging/api/photo-search/posts/${this.postId}/sections/${this.currentSectionId}/selected`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.selected_photo) {
                    this.displaySelectedPhoto(data.selected_photo);
                } else {
                    this.showNoSelection();
                }
            }
        } catch (e) {
            console.error('[Photo Selection] Error loading selected photo:', e);
            this.showNoSelection();
        }
    }
    
    displaySelectedPhoto(photo) {
        const displayDiv = document.getElementById('selected-photo-display');
        const noSelectionDiv = document.getElementById('no-selection-message');
        
        if (!displayDiv || !noSelectionDiv) return;
        
        // Update image
        const img = document.getElementById('selected-photo-image');
        if (img) img.src = photo.url;
        
        // Update info
        document.getElementById('selected-photo-provider').textContent = photo.provider === 'pexels' ? 'Pexels' : 'Unsplash';
        
        const photographerLink = document.getElementById('selected-photo-photographer-link');
        const photographerSpan = document.getElementById('selected-photo-photographer');
        if (photographerLink && photographerSpan) {
            photographerSpan.textContent = photo.photographer || 'Unknown';
            if (photo.photographer_url) {
                photographerLink.href = photo.photographer_url;
                photographerLink.target = '_blank';
            } else {
                photographerLink.href = '#';
                photographerLink.onclick = (e) => e.preventDefault();
            }
        }
        
        document.getElementById('selected-photo-credits').textContent = photo.credits || 'Photo credit not available';
        document.getElementById('selected-photo-dimensions').textContent = `${photo.width || '?'} × ${photo.height || '?'}`;
        
        // Show display, hide no-selection message
        displayDiv.style.display = 'block';
        noSelectionDiv.style.display = 'none';
        
        // Trigger output panel update
        document.dispatchEvent(new CustomEvent('photo-selection-updated', {
            detail: { photo }
        }));
    }
    
    showNoSelection() {
        const displayDiv = document.getElementById('selected-photo-display');
        const noSelectionDiv = document.getElementById('no-selection-message');
        
        if (displayDiv) displayDiv.style.display = 'none';
        if (noSelectionDiv) noSelectionDiv.style.display = 'block';
    }
    
    async deselectPhoto() {
        if (!this.currentSectionId) return;
        
        // Reload results and clear selection
        try {
            const response = await fetch(`/imaging/api/photo-search/posts/${this.postId}/sections/${this.currentSectionId}/results`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.results) {
                    // Find and unselect any selected photo
                    let updated = false;
                    data.results.forEach(photo => {
                        if (photo.selected) {
                            photo.selected = false;
                            delete photo.selected_at;
                            updated = true;
                        }
                    });
                    
                    if (updated) {
                        // Save updated results (we'll need an endpoint for this, or just reload)
                        // For now, just clear the selection display
                        this.showNoSelection();
                        
                        // Trigger results panel refresh
                        document.dispatchEvent(new CustomEvent('photo-deselected'));
                    }
                }
            }
        } catch (e) {
            console.error('[Photo Selection] Error deselecting photo:', e);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.currentSubstage === 'photo-selection') {
        window.photoSelectionPanel = new PhotoSelectionPanel(window.postId);
    }
});

