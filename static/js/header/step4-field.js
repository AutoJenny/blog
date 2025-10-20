/**
 * Step 4 Field - Completely new script
 */

console.log('[Step4Field] New script loaded');

class Step4Field {
    constructor(postId) {
        this.postId = postId;
        this.init();
    }

    init() {
        console.log('[Step4Field] Initializing for post:', this.postId);
        this.loadContent();
    }

    async loadContent() {
        try {
            console.log('[Step4Field] Loading content...');
            
            const url = `/header/api/posts/${this.postId}/test-field`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('[Step4Field] Data loaded:', data);
            
            const field = document.getElementById('simple-blank-field');
            if (field) {
                field.innerHTML = data.content;
                console.log('[Step4Field] Content set with same formatting as Step 3');
            } else {
                console.error('[Step4Field] Field not found');
            }
            
        } catch (error) {
            console.error('[Step4Field] Error:', error);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Step4Field] DOM loaded');
    
    if (window.postId && window.currentSubstage === 'header-image') {
        console.log('[Step4Field] Initializing...');
        window.step4Field = new Step4Field(window.postId);
    }
});

console.log('[Step4Field] Script execution complete');
