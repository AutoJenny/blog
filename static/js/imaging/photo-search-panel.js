/**
 * Photo Search Panel
 * Handles search functionality for Pexels/Unsplash photo APIs
 */

class PhotoSearchPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentSectionId = null;
        this.init();
    }
    
    init() {
        const searchBtn = document.getElementById('photo-search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.performSearch());
        }
        
        // Allow Enter key to trigger search
        const searchInput = document.getElementById('photo-search-term');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
        
        // Listen for section selection changes (imaging core dispatches 'sectionSelected')
        document.addEventListener('sectionSelected', (e) => {
            this.currentSectionId = e.detail.sectionId;
            this.loadExistingSearchTerm();
        });
    }
    
    async loadExistingSearchTerm() {
        if (!this.currentSectionId) return;
        
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${this.currentSectionId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.section) {
                    // Prefer image_prompts.image_prompt from the section record
                    const ip = data.section.image_prompts;
                    let promptText = '';
                    if (ip) {
                        if (typeof ip === 'string') {
                            try { const parsed = JSON.parse(ip); promptText = parsed.image_prompt || ''; } catch { promptText = ip; }
                        } else if (typeof ip === 'object') {
                            promptText = ip.image_prompt || '';
                        }
                    }
                    if (promptText) {
                        document.getElementById('photo-search-term').value = promptText;
                    }
                }
            }
        } catch (e) {
            console.error('[Photo Search] Error loading existing search term:', e);
        }
    }
    
    async performSearch() {
        if (!this.currentSectionId) {
            alert('Please select a section first');
            return;
        }
        
        const searchTerm = document.getElementById('photo-search-term').value.trim();
        if (!searchTerm) {
            alert('Please enter a search term');
            return;
        }
        
        const provider = document.getElementById('photo-search-provider').value;
        const perPage = parseInt(document.getElementById('photo-search-per-page').value);
        
        const searchBtn = document.getElementById('photo-search-btn');
        const statusDiv = document.getElementById('photo-search-status');
        
        // Update UI
        searchBtn.disabled = true;
        searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = '<span class="text-info">Searching for photos...</span>';
        
        try {
            const response = await fetch(`/imaging/api/photo-search/posts/${this.postId}/sections/${this.currentSectionId}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    search_term: searchTerm,
                    provider: provider,
                    per_page: perPage
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                statusDiv.innerHTML = `<span class="text-success">Found ${data.count} photos</span>`;
                
                // Trigger results panel update
                document.dispatchEvent(new CustomEvent('photo-search-complete', {
                    detail: {
                        results: data.results,
                        count: data.count
                    }
                }));
            } else {
                statusDiv.innerHTML = `<span class="text-danger">Error: ${data.error}</span>`;
            }
        } catch (e) {
            console.error('[Photo Search] Error:', e);
            statusDiv.innerHTML = `<span class="text-danger">Search failed: ${e.message}</span>`;
        } finally {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-search"></i> Search Photos';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.currentSubstage === 'photo-selection') {
        window.photoSearchPanel = new PhotoSearchPanel(window.postId);
    }
});

