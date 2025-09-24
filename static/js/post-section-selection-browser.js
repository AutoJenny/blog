/**
 * Post Section Selection Browser
 * Handles the post selection dropdown and display
 */

class PostSectionBrowser {
    constructor(dataManager) {
        this.dataManager = dataManager;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPosts();
    }

    setupEventListeners() {
        const postSelector = document.getElementById('postSelector');
        if (postSelector) {
            postSelector.addEventListener('change', (e) => {
                const postId = e.target.value;
                if (postId) {
                    this.selectPost(postId);
                } else {
                    this.clearSelection();
                }
            });
        }
    }

    async loadPosts() {
        await this.dataManager.loadPosts();
    }

    async selectPost(postId) {
        try {
            // Save selection to localStorage
            PostSectionUtils.saveToLocalStorage('selectedBlogPostId', postId);

            // Load post details
            const post = await this.dataManager.loadPostDetails(postId);
            if (post) {
                this.updatePostDetails(post);
            }

            // Load post sections
            const sections = await this.dataManager.loadPostSections(postId);
            this.updateSectionCount(sections.length);

            // Update display
            this.updateSelectedPostDisplay();

            // Dispatch event for other modules
            PostSectionUtils.dispatchEvent('postSelected', {
                post: this.dataManager.getCurrentPost(),
                sections: this.dataManager.getCurrentSections()
            });

        } catch (error) {
            console.error('Error selecting post:', error);
            alert('Error loading post details. Please try again.');
        }
    }

    updatePostDetails(post) {
        const elements = {
            'postTitle': post.title,
            'postCreatedAt': PostSectionUtils.formatDate(post.created_at),
            'postUpdatedAt': PostSectionUtils.formatDate(post.updated_at),
            'postId': post.id,
            'postStatus': post.status,
            'postSlug': post.slug || 'N/A',
            'postSectionCount': this.dataManager.getCurrentSections().length
        };

        Object.entries(elements).forEach(([id, value]) => {
            PostSectionUtils.updateElementText(id, value);
        });

        // Show post details
        PostSectionUtils.showElement('postDetails', true);
    }

    updateSectionCount(count) {
        PostSectionUtils.updateElementText('sectionCount', count);
        PostSectionUtils.setButtonState('generateAllSectionsBtn', count === 0);
    }

    updateSelectedPostDisplay() {
        const post = this.dataManager.getCurrentPost();
        const sections = this.dataManager.getCurrentSections();
        
        if (post) {
            PostSectionUtils.updateElementText('selected-post-display', 
                `${post.title} (${sections.length} sections)`);
        }
    }

    clearSelection() {
        this.dataManager.clearSelection();

        // Clear localStorage
        localStorage.removeItem('selectedBlogPostId');

        // Hide sections and details
        PostSectionUtils.showElement('sectionsList', false);
        PostSectionUtils.showElement('postDetails', false);
        PostSectionUtils.updateElementText('selected-post-display', 'No post selected');

        // Reset section count
        this.updateSectionCount(0);

        // Dispatch event
        PostSectionUtils.dispatchEvent('postSelected', {
            post: null,
            sections: []
        });
    }

    restorePreviousSelection() {
        const savedPostId = PostSectionUtils.loadFromLocalStorage('selectedBlogPostId');
        if (savedPostId) {
            const postSelector = document.getElementById('postSelector');
            if (postSelector) {
                postSelector.value = savedPostId;
                this.selectPost(savedPostId);
            }
        }
    }
}
