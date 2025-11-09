/**
 * Header Photo-harvesting Panel Integration
 * Manages header image search, results display, and selection for Photo-harvesting route
 */

class HeaderPhotoHarvesting {
    constructor(postId) {
        this.postId = postId;
        this.results = [];
        this.selectedLandscape = null;
        this.selectedPortrait = null;
        this.init();
    }
    
    init() {
        // Initialize Uber Generate & Search button (main action)
        this.initUberButton();
        
        // Initialize search panel (optional manual controls)
        this.initSearchPanel();
        
        // Initialize results panel
        this.initResultsPanel();
        
        // Initialize selection panel
        this.initSelectionPanel();
        
        // Load existing results and selections
        this.loadExistingResults();
        this.loadSelectedPhotos();
    }
    
    initUberButton() {
        const uberBtn = document.getElementById('header-generate-and-search-btn');
        if (uberBtn) {
            uberBtn.addEventListener('click', () => this.runEndToEnd());
        }
    }
    
    async runEndToEnd() {
        const uberBtn = document.getElementById('header-generate-and-search-btn');
        const statusDiv = document.getElementById('header-generate-and-search-status');
        
        // Disable button and show status
        if (uberBtn) {
            uberBtn.disabled = true;
            uberBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
        if (statusDiv) {
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '<span class="text-info">Step 1/4: Generating search term...</span>';
        }
        
        try {
            // Step 1: Generate search term
            const urlParams = new URLSearchParams(window.location.search);
            const year = urlParams.get('year') || (window.weekYear && window.weekYear.year);
            const week = urlParams.get('week') || (window.weekYear && window.weekYear.week);
            
            let generateUrl = `/header/api/photo-search/posts/${this.postId}/header/generate-search-term`;
            if (year && week) {
                generateUrl += `?year=${year}&week=${week}`;
            }
            
            const generateResponse = await fetch(generateUrl, { method: 'POST' });
            const generateData = await generateResponse.json();
            
            if (!generateData.success || !generateData.search_term) {
                throw new Error(generateData.error || 'Failed to generate search term');
            }
            
            const searchTerm = generateData.search_term.trim();
            if (statusDiv) {
                statusDiv.innerHTML = `<span class="text-success">✓ Search term: "${searchTerm}"</span><br><span class="text-info">Step 2/4: Searching photos...</span>`;
            }
            
            // Step 2: Search photos
            const provider = document.getElementById('header-photo-search-provider')?.value || 'both';
            const perPage = parseInt(document.getElementById('header-photo-search-per-page')?.value || '20');
            
            const searchResponse = await fetch(`/header/api/photo-search/posts/${this.postId}/header/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    search_term: searchTerm,
                    provider: provider,
                    per_page: perPage
                })
            });
            
            const searchData = await searchResponse.json();
            
            if (!searchData.success || !searchData.results || searchData.results.length === 0) {
                throw new Error(searchData.error || 'No photos found');
            }
            
            this.results = searchData.results || [];
            this.displayResults(this.results);
            
            if (statusDiv) {
                statusDiv.innerHTML = `<span class="text-success">✓ Found ${this.results.length} photos</span><br><span class="text-info">Step 3/4: Auto-selecting best images...</span>`;
            }
            
            // Step 3: Auto-select first landscape and portrait
            const landscapePhotos = [];
            const portraitPhotos = [];
            
            this.results.forEach(photo => {
                const width = photo.width || 0;
                const height = photo.height || 0;
                if (width >= height) {
                    landscapePhotos.push(photo);
                } else {
                    portraitPhotos.push(photo);
                }
            });
            
            const selectedLandscape = landscapePhotos.length > 0 ? landscapePhotos[0] : null;
            const selectedPortrait = portraitPhotos.length > 0 ? portraitPhotos[0] : null;
            
            if (!selectedLandscape && !selectedPortrait) {
                throw new Error('No suitable photos found (need at least one landscape or portrait)');
            }
            
            // Step 4: Persist selections
            const selections = [];
            
            if (selectedLandscape) {
                if (statusDiv) {
                    statusDiv.innerHTML = `<span class="text-success">✓ Found ${this.results.length} photos</span><br><span class="text-info">Selecting landscape image...</span>`;
                }
                
                const landscapeSelectResponse = await fetch(`/header/api/photo-search/posts/${this.postId}/header/select`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider: selectedLandscape.provider,
                        image_id: selectedLandscape.image_id,
                        orientation: 'landscape'
                    })
                });
                
                const landscapeSelectData = await landscapeSelectResponse.json();
                if (landscapeSelectData.success) {
                    this.selectedLandscape = selectedLandscape;
                    selections.push('landscape');
                } else {
                    console.warn('[Header Photo] Failed to select landscape:', landscapeSelectData.error);
                }
            }
            
            if (selectedPortrait) {
                if (statusDiv) {
                    const currentText = statusDiv.innerHTML;
                    statusDiv.innerHTML = currentText.replace(/Selecting.*?\.\.\./, 'Selecting portrait image...');
                }
                
                const portraitSelectResponse = await fetch(`/header/api/photo-search/posts/${this.postId}/header/select`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider: selectedPortrait.provider,
                        image_id: selectedPortrait.image_id,
                        orientation: 'portrait'
                    })
                });
                
                const portraitSelectData = await portraitSelectResponse.json();
                if (portraitSelectData.success) {
                    this.selectedPortrait = selectedPortrait;
                    selections.push('portrait');
                } else {
                    console.warn('[Header Photo] Failed to select portrait:', portraitSelectData.error);
                }
            }
            
            // Refresh display
            this.displayResults(this.results);
            this.updateSelectionDisplay();
            
            // Update status with success
            if (statusDiv) {
                const selectionText = selections.length > 0 
                    ? `✓ Selected ${selections.join(' and ')} image${selections.length > 1 ? 's' : ''}`
                    : '⚠ Selection partially failed';
                statusDiv.innerHTML = `<span class="text-success">✓ Complete! Search term: "${searchTerm}", Found ${this.results.length} photos. ${selectionText}.</span>`;
                // Clear status after 5 seconds
                setTimeout(() => {
                    if (statusDiv) statusDiv.style.display = 'none';
                }, 5000);
            }
            
        } catch (error) {
            console.error('[Header Photo] End-to-end error:', error);
            if (statusDiv) {
                statusDiv.innerHTML = `<span class="text-danger">✗ Error: ${error.message}</span>`;
            }
            alert(`Header image generation failed: ${error.message}`);
        } finally {
            if (uberBtn) {
                uberBtn.disabled = false;
                uberBtn.innerHTML = '<i class="fas fa-magic"></i> Generate & Search Header Image';
            }
        }
    }
    
    initSearchPanel() {
        // Manual search controls are hidden by default
        // Only initialize if panel is visible (for debugging)
        const searchBtn = document.getElementById('header-photo-search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.performSearch());
        }
    }
    
    initResultsPanel() {
        // Results panel is display-only, no initialization needed
        // Results are populated by displayResults() method
    }
    
    initSelectionPanel() {
        // Selection panel is display-only, no initialization needed
        // Selections are managed by updateSelectionDisplay() method
    }
    
    async generateSearchTerm() {
        const btn = document.getElementById('header-generate-search-term-btn');
        const status = document.getElementById('header-photo-search-status');
        const input = document.getElementById('header-photo-search-term');
        
        if (btn) btn.disabled = true;
        if (status) {
            status.style.display = 'block';
            status.innerHTML = '<span class="text-info">Generating search term...</span>';
        }
        
        try {
            // Get year/week from URL or window context
            const urlParams = new URLSearchParams(window.location.search);
            const year = urlParams.get('year') || (window.weekYear && window.weekYear.year);
            const week = urlParams.get('week') || (window.weekYear && window.weekYear.week);
            
            let url = `/header/api/photo-search/posts/${this.postId}/header/generate-search-term`;
            if (year && week) {
                url += `?year=${year}&week=${week}`;
            }
            
            const response = await fetch(url, { method: 'POST' });
            const data = await response.json();
            
            if (data.success && data.search_term) {
                if (input) input.value = data.search_term;
                if (status) status.innerHTML = '<span class="text-success">Search term generated</span>';
            } else {
                if (status) status.innerHTML = `<span class="text-danger">Error: ${data.error || 'Failed to generate'}</span>`;
            }
        } catch (e) {
            console.error('[Header Photo] Error generating search term:', e);
            if (status) status.innerHTML = `<span class="text-danger">Error: ${e.message}</span>`;
        } finally {
            if (btn) btn.disabled = false;
        }
    }
    
    async performSearch() {
        const searchTerm = document.getElementById('header-photo-search-term')?.value.trim();
        if (!searchTerm) {
            alert('Please enter a search term');
            return;
        }
        
        const provider = document.getElementById('header-photo-search-provider')?.value || 'both';
        const perPage = parseInt(document.getElementById('header-photo-search-per-page')?.value || '20');
        const orientationEl = document.getElementById('header-photo-search-orientation');
        const orientation = orientationEl ? orientationEl.value.trim() : '';
        
        const searchBtn = document.getElementById('header-photo-search-btn');
        const statusDiv = document.getElementById('header-photo-search-status');
        
        if (searchBtn) {
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        }
        if (statusDiv) {
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '<span class="text-info">Searching for photos...</span>';
        }
        
        const requestBody = { search_term: searchTerm, provider, per_page: perPage };
        if (orientation) requestBody.orientation = orientation;
        
        try {
            const response = await fetch(`/header/api/photo-search/posts/${this.postId}/header/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (statusDiv) statusDiv.innerHTML = `<span class="text-success">Found ${data.count} photos</span>`;
                this.results = data.results || [];
                this.displayResults(this.results);
            } else {
                if (statusDiv) statusDiv.innerHTML = `<span class="text-danger">Error: ${data.error}</span>`;
            }
        } catch (e) {
            console.error('[Header Photo] Search error:', e);
            if (statusDiv) statusDiv.innerHTML = `<span class="text-danger">Search failed: ${e.message}</span>`;
        } finally {
            if (searchBtn) {
                searchBtn.disabled = false;
                searchBtn.innerHTML = '<i class="fas fa-search"></i> Search Photos';
            }
        }
    }
    
    async loadExistingResults() {
        try {
            const response = await fetch(`/header/api/photo-search/posts/${this.postId}/header/results`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.results && data.results.length > 0) {
                    this.results = data.results;
                    this.displayResults(this.results);
                }
            }
        } catch (e) {
            console.error('[Header Photo] Error loading results:', e);
        }
    }
    
    async loadSelectedPhotos() {
        try {
            const response = await fetch(`/header/api/photo-search/posts/${this.postId}/header/selected`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.selectedLandscape = data.selected_landscape?.photo || null;
                    this.selectedPortrait = data.selected_portrait?.photo || null;
                    this.updateSelectionDisplay();
                }
            }
        } catch (e) {
            console.error('[Header Photo] Error loading selections:', e);
        }
    }
    
    displayResults(results) {
        this.results = results;
        const emptyMsg = document.getElementById('header-photo-results-empty-message');
        if (emptyMsg) emptyMsg.style.display = 'none';
        
        // Separate by orientation
        const landscapePhotos = [];
        const portraitPhotos = [];
        
        results.forEach(photo => {
            const width = photo.width || 0;
            const height = photo.height || 0;
            if (width >= height) {
                landscapePhotos.push(photo);
            } else {
                portraitPhotos.push(photo);
            }
        });
        
        const gridContainer = document.querySelector('#header-photo-results-panel .photo-results-grid-container');
        if (!gridContainer) return;
        
        gridContainer.innerHTML = '';
        
        // Display landscape section
        if (landscapePhotos.length > 0) {
            this.displayOrientationSection(gridContainer, 'landscape', landscapePhotos);
        }
        
        // Display portrait section
        if (portraitPhotos.length > 0) {
            this.displayOrientationSection(gridContainer, 'portrait', portraitPhotos);
        }
        
        const countBadge = document.getElementById('header-photo-results-count');
        if (countBadge) {
            countBadge.textContent = `${results.length} results (${landscapePhotos.length} landscape, ${portraitPhotos.length} portrait)`;
        }
    }
    
    displayOrientationSection(container, orientation, photos) {
        const section = document.createElement('div');
        section.className = 'orientation-section';
        section.id = `header-photo-results-${orientation}`;
        
        section.innerHTML = `
            <h4 class="orientation-header">
                <i class="fas fa-${orientation === 'landscape' ? 'image' : 'mobile-alt'}"></i>
                ${orientation.charAt(0).toUpperCase() + orientation.slice(1)} Images
                <span class="count-badge">${photos.length}</span>
            </h4>
            <div class="photo-grid ${orientation}-grid"></div>
        `;
        
        container.appendChild(section);
        
        const grid = section.querySelector('.photo-grid');
        photos.forEach((photo, index) => {
            const card = this.createPhotoCard(photo, index, orientation);
            grid.appendChild(card);
        });
    }
    
    createPhotoCard(photo, index, orientation) {
        const width = photo.width || 0;
        const height = photo.height || 0;
        
        const maxDisplayDimension = 500;
        let displayWidth = width;
        let displayHeight = height;
        
        if (width > 0 && height > 0) {
            const longerSide = Math.max(width, height);
            if (longerSide > maxDisplayDimension) {
                const scale = maxDisplayDimension / longerSide;
                displayWidth = Math.round(width * scale);
                displayHeight = Math.round(height * scale);
            }
        }
        
        const isSelected = orientation === 'landscape' 
            ? (this.selectedLandscape && this.selectedLandscape.image_id === photo.image_id && this.selectedLandscape.provider === photo.provider)
            : (this.selectedPortrait && this.selectedPortrait.image_id === photo.image_id && this.selectedPortrait.provider === photo.provider);
        
        const card = document.createElement('div');
        card.className = `photo-card ${orientation}-card ${isSelected ? 'selected' : ''}`;
        
        const providerBadge = photo.provider === 'pexels' ? 'Pexels' : 'Unsplash';
        const providerClass = photo.provider === 'pexels' ? 'badge-pexels' : 'badge-unsplash';
        
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
+            <div class="photo-info">
+                <div class="photo-provider">
+                    <span class="badge ${providerClass}">${providerBadge}</span>
+                </div>
+                <div class="photo-dimensions">
+                    <small>${width} × ${height}</small>
+                </div>
+                <div class="photo-photographer">
+                    <small>${photo.photographer || 'Unknown'}</small>
+                </div>
+            </div>
+            <button class="btn btn-sm btn-primary select-photo-btn ${isSelected ? 'selected' : ''}" 
+                    data-provider="${photo.provider}" 
+                    data-image-id="${photo.image_id}"
+                    data-orientation="${orientation}"
+                    ${isSelected ? 'disabled' : ''}>
+                ${isSelected ? '<i class="fas fa-check"></i> Selected' : '<i class="fas fa-check-circle"></i> Select'}
+            </button>
+        `;
        
        const selectBtn = card.querySelector('.select-photo-btn');
        if (selectBtn && !isSelected) {
            selectBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectPhoto(photo, orientation);
            });
        }
        
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
        try {
            const response = await fetch(`/header/api/photo-search/posts/${this.postId}/header/select`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: photo.provider,
                    image_id: photo.image_id,
                    orientation: orientation
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (orientation === 'landscape') {
                    this.selectedLandscape = photo;
                } else {
                    this.selectedPortrait = photo;
                }
                this.displayResults(this.results);
                this.updateSelectionDisplay();
            } else {
                alert(`Error selecting photo: ${data.error}`);
            }
        } catch (e) {
            console.error('[Header Photo] Error selecting photo:', e);
            alert('Failed to select photo');
        }
    }
    
    updateSelectionDisplay() {
        // Update selection panel display (show landscape selection if available)
        const selected = this.selectedLandscape || this.selectedPortrait;
        const displayDiv = document.getElementById('header-selected-photo-display');
        const noSelectionDiv = document.getElementById('header-no-selection-message');
        
        if (selected) {
            if (displayDiv) displayDiv.style.display = 'block';
            if (noSelectionDiv) noSelectionDiv.style.display = 'none';
            
            document.getElementById('header-selected-photo-image').src = selected.url || selected.thumbnail_url || '';
            document.getElementById('header-selected-photo-provider').textContent = selected.provider === 'pexels' ? 'Pexels' : 'Unsplash';
            document.getElementById('header-selected-photo-photographer').textContent = selected.photographer || 'Unknown';
            document.getElementById('header-selected-photo-photographer-link').href = selected.photographer_url || '#';
            document.getElementById('header-selected-photo-credits').textContent = selected.credits || '';
            document.getElementById('header-selected-photo-dimensions').textContent = `${selected.width || 0} × ${selected.height || 0}`;
            document.getElementById('header-selected-photo-orientation').textContent = this.selectedLandscape ? 'Landscape' : 'Portrait';
        } else {
            if (displayDiv) displayDiv.style.display = 'none';
            if (noSelectionDiv) noSelectionDiv.style.display = 'block';
        }
        
        // Deselect button
        const deselectBtn = document.getElementById('header-deselect-photo-btn');
        if (deselectBtn) {
            deselectBtn.addEventListener('click', () => {
                // TODO: Implement deselection (delete JSON files)
                this.selectedLandscape = null;
                this.selectedPortrait = null;
                this.updateSelectionDisplay();
                this.displayResults(this.results);
            });
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.illustrationMethod === 'Photo-harvesting' && window.currentSubstage === 'title-summary') {
        window.headerPhotoHarvesting = new HeaderPhotoHarvesting(window.postId);
    }
});

