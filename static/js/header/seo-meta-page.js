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
        try {
            this.generateBtn.disabled = true;
            this.generateBtn.textContent = 'Generating...';
            
            const response = await fetch(`/header/api/posts/${this.postId}/generate-seo-meta`, {
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

