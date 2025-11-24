// SEO Meta Page JavaScript

console.log('[SEO Meta Page] Script loading...');

class SEOMetaPage {
    constructor() {
        this.postId = window.postId;
        
        // Debug: Log postType when class is instantiated
        console.log('[SEO Meta Page] Constructor - window.postType:', window.postType, 'type:', typeof window.postType);
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        this.generateBtn = document.getElementById('generate-all-meta-btn');
    }
    
    bindEvents() {
        if (this.generateBtn) {
            console.log('[SEO Meta Page] Binding click handler to button');
            this.generateBtn.addEventListener('click', () => {
                console.log('[SEO Meta Page] Button clicked! window.postType:', window.postType);
                this.generateMetaData();
            });
        } else {
            console.error('[SEO Meta Page] Button not found!');
        }
    }
    
    async generateMetaData() {
        console.log('[SEO Meta] generateMetaData CALLED');
        console.log('[SEO Meta] window.postType:', window.postType, 'typeof:', typeof window.postType);
        
        // Get post type - it's set in the template as window.postType
        const postType = String(window.postType || '').toLowerCase().trim();
        console.log('[SEO Meta] postType after normalization:', postType);
        
        // Non-themed post types (recipe, profile, generated) NEVER require week context
        const NON_THEMED_TYPES = ['recipe', 'profile', 'generated'];
        const isNonThemedPost = NON_THEMED_TYPES.includes(postType);
        console.log('[SEO Meta] isNonThemedPost:', isNonThemedPost, 'NON_THEMED_TYPES:', NON_THEMED_TYPES);
        
        // For non-themed posts, skip ALL week context checks and proceed directly
        if (isNonThemedPost) {
            console.log('[SEO Meta] Non-themed post (' + postType + ') - proceeding without week context');
            // Continue to generation - no checks needed
        } else {
            console.log('[SEO Meta] Themed post - checking week context');
            // Only themed posts require week context validation
            const weekHasPost = window.weekHasPost === true || window.weekHasPost === 'true' || window.weekHasPost === 1;
            console.log('[SEO Meta] weekHasPost:', weekHasPost, 'window.weekHasPost:', window.weekHasPost);
            if (!weekHasPost) {
                console.error('[SEO Meta] ERROR: weekHasPost is false for themed post');
                alert('Cannot generate SEO meta: No post is scheduled for this week. Please schedule a post first.');
                return;
            }
            
            const urlParams = new URLSearchParams(window.location.search);
            const year = urlParams.get('year') || (window.year && window.year !== 'null' ? window.year : null);
            const week = urlParams.get('week') || (window.week && window.week !== 'null' ? window.week : null);
            
            if (!year || !week) {
                console.error('[SEO Meta] ERROR: Missing year/week for themed post');
                alert('Cannot generate SEO meta: Week context (year and week) is required for themed posts.');
                return;
            }
        }
        
        try {
            this.generateBtn.disabled = true;
            this.generateBtn.textContent = 'Generating...';
            
            // Build URL - only include year/week for themed posts
            let url = `/header/api/posts/${this.postId}/generate-seo-meta`;
            if (!isNonThemedPost) {
                // Only themed posts need year/week in URL
                const urlParams = new URLSearchParams(window.location.search);
                const year = urlParams.get('year') || (window.year && window.year !== 'null' ? window.year : null);
                const week = urlParams.get('week') || (window.week && window.week !== 'null' ? window.week : null);
                if (year && week) {
                    url += `?year=${year}&week=${week}`;
                }
            }
            
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
                
                // Generate embeddings as well
                if (window.generatePostEmbeddings) {
                    try {
                        await window.generatePostEmbeddings();
                    } catch (embedError) {
                        console.error('[SEO Meta Page] Error generating embeddings:', embedError);
                    }
                }
                
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

