// SEO Meta Page JavaScript

console.log('[SEO Meta Page] Script loading...');

class SEOMetaPage {
    constructor() {
        this.postId = window.postId;
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        this.generateBtn = document.getElementById('generate-all-meta-btn');
    }
    
    bindEvents() {
        if (this.generateBtn) {
            this.generateBtn.addEventListener('click', () => this.generateMetaData());
        }
    }
    
    async generateMetaData() {
        // Check if week has a post scheduled
        if (!window.weekHasPost) {
            alert('Cannot generate SEO meta: No post is scheduled for this week. Please schedule a post first.');
            return;
        }
        
        // Validate week context
        const urlParams = new URLSearchParams(window.location.search);
        const year = urlParams.get('year') || (window.year && window.year);
        const week = urlParams.get('week') || (window.week && window.week);
        
        if (!year || !week) {
            alert('Cannot generate SEO meta: Week context (year and week) is required.');
            return;
        }
        
        try {
            this.generateBtn.disabled = true;
            this.generateBtn.textContent = 'Generating...';
            
            // Build URL with week context (required)
            const url = `/header/api/posts/${this.postId}/generate-seo-meta?year=${year}&week=${week}`;
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update HTML Meta fields
                const metaTitleInput = document.getElementById('meta-title-input');
                const metaDescriptionInput = document.getElementById('meta-description-input');
                const metaTagsInput = document.getElementById('meta-tags-input');
                
                if (metaTitleInput) metaTitleInput.value = data.meta_title || '';
                if (metaDescriptionInput) metaDescriptionInput.value = data.meta_description || '';
                if (metaTagsInput) metaTagsInput.value = data.meta_tags || '';
                
                // Update OG Meta fields
                const metaImageInput = document.getElementById('meta-image-input');
                const metaTypeInput = document.getElementById('meta-type-input');
                const metaSiteNameInput = document.getElementById('meta-site-name-input');
                
                if (metaImageInput) metaImageInput.value = data.meta_image || '';
                if (metaTypeInput) metaTypeInput.value = data.meta_type || 'article';
                if (metaSiteNameInput) metaSiteNameInput.value = data.meta_site_name || 'Clan.com Blog';
                
                console.log('[SEO Meta Page] Meta data generated successfully');
                this.generateBtn.textContent = 'Generated!';
                setTimeout(() => {
                    this.generateBtn.textContent = 'Generate Meta Data';
                }, 2000);
                // Notify opener (launchpad) that SEO Meta generation completed
                try { if (window.opener) window.opener.postMessage('header_seo_meta_complete', '*'); } catch(_) {}
            } else {
                console.error('[SEO Meta Page] Error generating meta data:', data.error);
                this.generateBtn.textContent = 'Error';
                setTimeout(() => {
                    this.generateBtn.textContent = 'Generate Meta Data';
                }, 2000);
            }
        } catch (error) {
            console.error('[SEO Meta Page] Error generating meta data:', error);
            this.generateBtn.textContent = 'Error';
            setTimeout(() => {
                this.generateBtn.textContent = 'Generate Meta Data';
            }, 2000);
        } finally {
            this.generateBtn.disabled = false;
        }
    }
}

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[SEO Meta Page] Initializing page...');
    window.seoMetaPage = new SEOMetaPage();
});

