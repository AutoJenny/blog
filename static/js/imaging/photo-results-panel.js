/**
 * Photo Results Panel
 * Displays search results separated by landscape and portrait orientations
 * Shows images in their actual dimensions
 */

class PhotoResultsPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentSectionId = null;
        this.results = [];
        this.selectedLandscape = null;
        this.selectedPortrait = null;
        this.init();
    }
    
    init() {
        // Listen for search completion
        document.addEventListener('photo-search-complete', (e) => {
            this.displayResults(e.detail.results);
        });
        
        // Listen for section selection (note: event name may vary)
        document.addEventListener('sectionSelected', (e) => {
            this.currentSectionId = e.detail.sectionId || e.detail.section?.id;
            this.loadExistingResults();
            this.loadSelectedPhotos();
        });
        
        // Fallback for legacy event name
        document.addEventListener('section-selected', (e) => {
            this.currentSectionId = e.detail.sectionId || e.detail.section?.id;
            this.loadExistingResults();
            this.loadSelectedPhotos();
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
    
    async loadSelectedPhotos() {
        if (!this.currentSectionId) return;
        
        try {
            const response = await fetch(`/imaging/api/photo-search/posts/${this.postId}/sections/${this.currentSectionId}/selected`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.selectedLandscape = data.selected_landscape?.photo || null;
                    this.selectedPortrait = data.selected_portrait?.photo || null;
                }
            }
        } catch (e) {
            console.error('[Photo Results] Error loading selected photos:', e);
        }
    }
    
    displayResults(results) {
        this.results = results;
        
        // Hide empty message
        const emptyMsg = document.getElementById('photo-results-empty-message');
        if (emptyMsg) {
            emptyMsg.style.display = 'none';
        }
        
        // Separate by orientation
        const landscapePhotos = [];
        const portraitPhotos = [];
        
        results.forEach(photo => {
            const width = photo.width || 0;
            const height = photo.height || 0;
            // Determine orientation: landscape if width > height, portrait if height > width
            // Square photos go to landscape section
            if (width >= height) {
                landscapePhotos.push(photo);
            } else {
                portraitPhotos.push(photo);
            }
        });
        
        // Display landscape section
        this.displayOrientationSection('landscape', landscapePhotos);
        
        // Display portrait section
        this.displayOrientationSection('portrait', portraitPhotos);
        
        // Update count badge
        const countBadge = document.getElementById('photo-results-count');
        if (countBadge) {
            countBadge.textContent = `${results.length} results (${landscapePhotos.length} landscape, ${portraitPhotos.length} portrait)`;
        }
    }
    
    displayOrientationSection(orientation, photos) {
        const containerId = `photo-results-${orientation}`;
        const resultsPanel = document.getElementById('photo-results-panel');
        if (!resultsPanel) return;
        
        const gridContainer = resultsPanel.querySelector('.photo-results-grid-container');
        if (!gridContainer) return;
        
        let container = document.getElementById(containerId);
        
        if (!container) {
            // Create container if it doesn't exist
            container = document.createElement('div');
            container.id = containerId;
            container.className = 'orientation-section';
            gridContainer.appendChild(container);
        }
        
        // Update header and grid
        container.innerHTML = `
            <h4 class="orientation-header">
                <i class="fas fa-${orientation === 'landscape' ? 'image' : 'mobile-alt'}"></i>
                ${orientation.charAt(0).toUpperCase() + orientation.slice(1)} Images
                <span class="count-badge">${photos.length}</span>
            </h4>
            <div class="photo-grid ${orientation}-grid"></div>
        `;
        
        const grid = container.querySelector('.photo-grid');
        if (!grid) return;
        
        if (photos.length === 0) {
            grid.innerHTML = `<p class="text-muted text-center">No ${orientation} images found.</p>`;
            return;
        }
        
        // Display each photo
        photos.forEach((photo, index) => {
            const photoCard = this.createPhotoCard(photo, index, orientation);
            grid.appendChild(photoCard);
        });
    }
    
    createPhotoCard(photo, index, orientation) {
        const width = photo.width || 0;
        const height = photo.height || 0;
        
        // Calculate display dimensions (scale down if too large, maintain exact aspect ratio)
        // Scale based on orientation: constrain width for landscape, height for portrait
        const maxDisplayWidth = 600; // Max width for landscape images
        const maxDisplayHeight = 600; // Max height for portrait images
        
        let displayWidth = width;
        let displayHeight = height;
        
        if (width > 0 && height > 0) {
            if (orientation === 'landscape') {
                // For landscape, constrain width and calculate height proportionally
                if (width > maxDisplayWidth) {
                    const scale = maxDisplayWidth / width;
                    displayWidth = maxDisplayWidth;
                    displayHeight = Math.round(height * scale);
                }
            } else {
                // For portrait, constrain height and calculate width proportionally
                if (height > maxDisplayHeight) {
                    const scale = maxDisplayHeight / height;
                    displayWidth = Math.round(width * scale);
                    displayHeight = maxDisplayHeight;
                }
            }
        } else {
            // Fallback if dimensions are missing
            if (orientation === 'landscape') {
                displayWidth = 400;
                displayHeight = 267; // 3:2 ratio
            } else {
                displayWidth = 300;
                displayHeight = 400; // 3:4 ratio
            }
        }
        
        // Determine if this photo is selected for this orientation
        const isSelected = orientation === 'landscape' 
            ? (this.selectedLandscape && this.selectedLandscape.image_id === photo.image_id && this.selectedLandscape.provider === photo.provider)
            : (this.selectedPortrait && this.selectedPortrait.image_id === photo.image_id && this.selectedPortrait.provider === photo.provider);
        
        const card = document.createElement('div');
        card.className = `photo-card ${orientation}-card ${isSelected ? 'selected' : ''}`;
        
        const providerBadge = photo.provider === 'pexels' ? 'Pexels' : 'Unsplash';
        const providerClass = photo.provider === 'pexels' ? 'badge-pexels' : 'badge-unsplash';
        
        // Only set one dimension and let the browser calculate the other to preserve aspect ratio
        // Set width for landscape, height for portrait to maintain natural proportions
        const styleAttr = orientation === 'landscape' 
            ? `width: ${displayWidth}px; height: auto;`
            : `width: auto; height: ${displayHeight}px;`;
        
        card.innerHTML = `
            <div class="photo-image-container">
                <img src="${photo.thumbnail_url || photo.url}" 
                     alt="Photo ${index + 1}" 
                     class="photo-image"
                     loading="lazy"
                     width="${displayWidth}"
                     height="${displayHeight}"
                     style="${styleAttr}">
                ${isSelected ? '<div class="selected-overlay"><i class="fas fa-check-circle"></i><span>Selected</span></div>' : ''}
            </div>
            <div class="photo-info">
                <div class="photo-provider">
                    <span class="badge ${providerClass}">${providerBadge}</span>
                </div>
                <div class="photo-dimensions">
                    <small>${width} × ${height}</small>
                </div>
                <div class="photo-photographer">
                    <small>${photo.photographer || 'Unknown'}</small>
                </div>
            </div>
            <button class="btn btn-sm btn-primary select-photo-btn ${isSelected ? 'selected' : ''}" 
                    data-provider="${photo.provider}" 
                    data-image-id="${photo.image_id}"
                    data-orientation="${orientation}"
                    ${isSelected ? 'disabled' : ''}>
                ${isSelected ? '<i class="fas fa-check"></i> Selected' : '<i class="fas fa-check-circle"></i> Select'}
            </button>
        `;
        
        // Add click handler
        const selectBtn = card.querySelector('.select-photo-btn');
        if (selectBtn && !isSelected) {
            selectBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectPhoto(photo, orientation);
            });
        }
        
        // Also allow clicking the card to select (if not already selected)
        if (!isSelected) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', (e) => {
                if (e.target !== selectBtn && !selectBtn.contains(e.target)) {
                    this.selectPhoto(photo, orientation);
                }
            });
        }
        
        return card;
    }
    
    async selectPhoto(photo, orientation) {
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
                    image_id: photo.image_id,
                    orientation: orientation
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update selected photo for this orientation
                if (orientation === 'landscape') {
                    this.selectedLandscape = photo;
                } else {
                    this.selectedPortrait = photo;
                }
                
                // Redisplay results to show selection
                this.displayResults(this.results);
                
                // Trigger selection panel update
                document.dispatchEvent(new CustomEvent('photo-selected', {
                    detail: {
                        photo: data.selected_photo,
                        orientation: orientation
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
