/**
 * Photo Results Panel
 * Displays search results in a grid format
 */

class PhotoResultsPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentSectionId = null;
        this.results = [];
        this.init();
    }
    
    init() {
        // Listen for search completion
        document.addEventListener('photo-search-complete', (e) => {
            this.displayResults(e.detail.results);
        });
        
        // Listen for section selection
        document.addEventListener('section-selected', (e) => {
            this.currentSectionId = e.detail.sectionId;
            this.loadExistingResults();
        });
    }
    
    async loadExistingResults() {
        if (!this.currentSectionId) return;
        
        try {
            const response = await fetch(`/imaging/api/photo-search/posts/${this.postId}/sections/${this.currentSectionId}/results`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.results.length > 0) {
                    this.displayResults(data.results);
                }
            }
        } catch (e) {
            console.error('[Photo Results] Error loading existing results:', e);
        }
    }
    
    displayResults(results) {
        this.results = results;
        const grid = document.getElementById('photo-results-grid');
        const countBadge = document.getElementById('photo-results-count');
        
        if (!results || results.length === 0) {
            grid.innerHTML = '<p class="text-muted text-center">No results found. Try different search terms.</p>';
            if (countBadge) countBadge.textContent = '0 results';
            return;
        }
        
        if (countBadge) countBadge.textContent = `${results.length} results`;
        
        // Clear and rebuild grid
        grid.innerHTML = '';
        grid.className = 'photo-results-grid';
        
        results.forEach((photo, index) => {
            const photoCard = this.createPhotoCard(photo, index);
            grid.appendChild(photoCard);
        });
    }
    
    createPhotoCard(photo, index) {
        const card = document.createElement('div');
        card.className = 'photo-card';
        if (photo.selected) {
            card.classList.add('selected');
        }
        
        const providerBadge = photo.provider === 'pexels' ? 'Pexels' : 'Unsplash';
        const providerClass = photo.provider === 'pexels' ? 'badge-pexels' : 'badge-unsplash';
        
        card.innerHTML = `
            <div class="photo-thumbnail-container">
                <img src="${photo.thumbnail_url || photo.url}" 
                     alt="Photo ${index + 1}" 
                     class="photo-thumbnail"
                     loading="lazy">
                ${photo.selected ? '<div class="selected-overlay"><i class="fas fa-check-circle"></i></div>' : ''}
            </div>
            <div class="photo-info">
                <div class="photo-provider">
                    <span class="badge ${providerClass}">${providerBadge}</span>
                </div>
                <div class="photo-photographer">
                    <small>${photo.photographer || 'Unknown'}</small>
                </div>
            </div>
            <button class="btn btn-sm btn-primary select-photo-btn" 
                    data-provider="${photo.provider}" 
                    data-image-id="${photo.image_id}"
                    ${photo.selected ? 'disabled' : ''}>
                ${photo.selected ? '<i class="fas fa-check"></i> Selected' : '<i class="fas fa-check-circle"></i> Select'}
            </button>
        `;
        
        // Add click handler
        const selectBtn = card.querySelector('.select-photo-btn');
        if (selectBtn && !photo.selected) {
            selectBtn.addEventListener('click', () => this.selectPhoto(photo));
        }
        
        // Also allow clicking the card to select (if not already selected)
        if (!photo.selected) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', (e) => {
                if (e.target !== selectBtn && !selectBtn.contains(e.target)) {
                    this.selectPhoto(photo);
                }
            });
        }
        
        return card;
    }
    
    async selectPhoto(photo) {
        if (!this.currentSectionId) {
            alert('Please select a section first');
            return;
        }
        
        try {
            const response = await fetch(`/imaging/api/photo-search/posts/${this.postId}/sections/${this.currentSectionId}/select`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    provider: photo.provider,
                    image_id: photo.image_id
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update the photo in our results array
                this.results.forEach(p => {
                    p.selected = false;
                    if (p.provider === photo.provider && p.image_id === photo.image_id) {
                        p.selected = true;
                        p.selected_at = data.selected_photo.selected_at;
                    }
                });
                
                // Redisplay results to show selection
                this.displayResults(this.results);
                
                // Trigger selection panel update
                document.dispatchEvent(new CustomEvent('photo-selected', {
                    detail: {
                        photo: data.selected_photo
                    }
                }));
            } else {
                alert(`Error selecting photo: ${data.error}`);
            }
        } catch (e) {
            console.error('[Photo Results] Error selecting photo:', e);
            alert('Failed to select photo');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.currentSubstage === 'photo-selection') {
        window.photoResultsPanel = new PhotoResultsPanel(window.postId);
    }
});

