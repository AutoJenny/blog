/**
 * Header Image Photo-harvesting Display
 * Loads and displays selected header photos from title-summary stage
 */

class HeaderImagePhotoHarvesting {
    constructor(postId) {
        this.postId = postId;
        this.selectedLandscape = null;
        this.selectedPortrait = null;
        this.init();
    }
    
    init() {
        this.loadSelectedPhotos();
    }
    
    async loadSelectedPhotos() {
        try {
            const response = await fetch(`/header/api/photo-search/posts/${this.postId}/header/selected`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.selectedLandscape = data.selected_landscape?.photo || null;
                    this.selectedPortrait = data.selected_portrait?.photo || null;
                    this.displaySelectedPhotos();
                }
            }
        } catch (e) {
            console.error('[Header Image Photo] Error loading selections:', e);
        }
    }
    
    displaySelectedPhotos() {
        // Display landscape photo
        if (this.selectedLandscape) {
            const landscapeDisplay = document.getElementById('header-landscape-photo-display');
            const landscapePlaceholder = document.getElementById('header-landscape-placeholder');
            const landscapeInfo = document.getElementById('header-landscape-photo-info');
            
            if (landscapeDisplay && landscapePlaceholder) {
                landscapePlaceholder.style.display = 'none';
                landscapeDisplay.innerHTML = `
                    <img src="${this.selectedLandscape.url || this.selectedLandscape.thumbnail_url || ''}" 
                         alt="Selected landscape header image" 
                         style="max-width: 100%; max-height: 400px; border-radius: 4px;">
                `;
            }
            
            if (landscapeInfo) {
                landscapeInfo.style.display = 'block';
                document.getElementById('header-landscape-provider').textContent = 
                    this.selectedLandscape.provider === 'pexels' ? 'Pexels' : 'Unsplash';
                document.getElementById('header-landscape-photographer').textContent = 
                    this.selectedLandscape.photographer || 'Unknown';
                document.getElementById('header-landscape-photographer-link').href = 
                    this.selectedLandscape.photographer_url || '#';
                document.getElementById('header-landscape-dimensions').textContent = 
                    `${this.selectedLandscape.width || 0} × ${this.selectedLandscape.height || 0}`;
            }
        }
        
        // Display portrait photo
        if (this.selectedPortrait) {
            const portraitDisplay = document.getElementById('header-portrait-photo-display');
            const portraitPlaceholder = document.getElementById('header-portrait-placeholder');
            const portraitInfo = document.getElementById('header-portrait-photo-info');
            
            if (portraitDisplay && portraitPlaceholder) {
                portraitPlaceholder.style.display = 'none';
                portraitDisplay.innerHTML = `
                    <img src="${this.selectedPortrait.url || this.selectedPortrait.thumbnail_url || ''}" 
                         alt="Selected portrait header image" 
                         style="max-width: 100%; max-height: 400px; border-radius: 4px;">
                `;
            }
            
            if (portraitInfo) {
                portraitInfo.style.display = 'block';
                document.getElementById('header-portrait-provider').textContent = 
                    this.selectedPortrait.provider === 'pexels' ? 'Pexels' : 'Unsplash';
                document.getElementById('header-portrait-photographer').textContent = 
                    this.selectedPortrait.photographer || 'Unknown';
                document.getElementById('header-portrait-photographer-link').href = 
                    this.selectedPortrait.photographer_url || '#';
                document.getElementById('header-portrait-dimensions').textContent = 
                    `${this.selectedPortrait.width || 0} × ${this.selectedPortrait.height || 0}`;
            }
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.illustrationMethod === 'Photo-harvesting' && window.currentSubstage === 'header-image') {
        window.headerImagePhotoHarvesting = new HeaderImagePhotoHarvesting(window.postId);
    }
});

