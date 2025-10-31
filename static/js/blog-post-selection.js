// Blog Post Selection Manager
// Handles selection of published blog posts for Facebook syndication

class BlogPostSelectionManager {
    constructor() {
        this.selectedPost = null;
        this.allPosts = [];
        this.init();
    }

    init() {
        // Set up event listeners
        const postSelector = document.getElementById('postSelector');
        if (postSelector) {
            postSelector.addEventListener('change', (e) => this.handlePostSelection(e.target.value));
        }
        
        // Initialize state manager
        if (window.stateManager) {
            window.stateManager.set('content_type', 'blog_post');
        }
    }

    async loadPosts() {
        try {
            const response = await fetch('/launchpad/api/syndication/posts');
            const data = await response.json();
            
            if (data.success) {
                this.allPosts = data.posts;
                this.renderPostSelector();
                
                // Restore previous selection if available
                const savedPostId = localStorage.getItem('selected_blog_post_id');
                if (savedPostId) {
                    const post = this.allPosts.find(p => p.id === parseInt(savedPostId));
                    if (post) {
                        document.getElementById('postSelector').value = savedPostId;
                        this.handlePostSelection(savedPostId);
                    }
                }
            } else {
                console.error('Error loading posts:', data.error);
                const selector = document.getElementById('postSelector');
                if (selector) {
                    selector.innerHTML = '<option value="">Error loading posts</option>';
                }
            }
        } catch (error) {
            console.error('Error loading posts:', error);
            const selector = document.getElementById('postSelector');
            if (selector) {
                selector.innerHTML = '<option value="">Error loading posts</option>';
            }
        }
    }

    renderPostSelector() {
        const selector = document.getElementById('postSelector');
        if (!selector) return;
        
        selector.innerHTML = '<option value="">Select a post...</option>';
        
        this.allPosts.forEach(post => {
            const option = document.createElement('option');
            option.value = post.id;
            option.textContent = `${post.title}${post.subtitle ? ' - ' + post.subtitle : ''}`;
            selector.appendChild(option);
        });
        
        if (this.allPosts.length === 0) {
            selector.innerHTML = '<option value="">No published posts available</option>';
        }
    }

    async handlePostSelection(postId) {
        if (!postId) {
            this.selectedPost = null;
            this.clearPostDetails();
            return;
        }
        
        try {
            const response = await fetch(`/launchpad/api/syndication/posts/${postId}`);
            const data = await response.json();
            
            if (data.success && data.post) {
                this.selectedPost = data.post;
                this.displayPostDetails(data.post);
                this.updateSelectedPostDisplay();
                
                // Save selection
                localStorage.setItem('selected_blog_post_id', postId);
                
                // Notify other components
                if (window.aiContentGenerationManager) {
                    window.aiContentGenerationManager.setSelectedPost(data.post);
                }
                
                // Check for existing generated content
                this.checkExistingContent(postId);
            } else {
                console.error('Error loading post details:', data.error);
                alert('Error loading post details: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading post details:', error);
            alert('Error loading post details: ' + error.message);
        }
    }

    displayPostDetails(post) {
        // Update all display fields
        const details = document.getElementById('postDetails');
        if (details) details.classList.remove('d-none');
        
        document.getElementById('postId').textContent = post.id;
        document.getElementById('postTitle').textContent = post.title || '-';
        document.getElementById('postSubtitle').textContent = post.subtitle || '-';
        document.getElementById('postStatus').textContent = post.status || '-';
        
        if (post.clan_uploaded_url) {
            const urlLink = document.getElementById('postUrl');
            const urlText = document.getElementById('postUrlText');
            if (urlLink) urlLink.href = post.clan_uploaded_url;
            if (urlText) urlText.textContent = post.clan_uploaded_url;
        }
        
        if (post.created_at) {
            const createdDate = new Date(post.created_at);
            document.getElementById('postCreatedAt').textContent = createdDate.toLocaleDateString();
        }
        
        if (post.updated_at) {
            const updatedDate = new Date(post.updated_at);
            document.getElementById('postUpdatedAt').textContent = updatedDate.toLocaleDateString();
        }
        
        if (post.summary) {
            const summaryDiv = document.getElementById('postSummary');
            const summaryText = document.getElementById('postSummaryText');
            if (summaryDiv) summaryDiv.style.display = 'block';
            if (summaryText) summaryText.textContent = post.summary;
        }
        
        // Show selection status
        const statusDiv = document.getElementById('selectionStatus');
        if (statusDiv) statusDiv.classList.remove('d-none');
    }

    clearPostDetails() {
        const details = document.getElementById('postDetails');
        if (details) details.classList.add('d-none');
        
        const statusDiv = document.getElementById('selectionStatus');
        if (statusDiv) statusDiv.classList.add('d-none');
        
        this.updateSelectedPostDisplay();
    }

    updateSelectedPostDisplay() {
        const display = document.getElementById('selected-post-display');
        if (display) {
            if (this.selectedPost) {
                display.textContent = this.selectedPost.title;
                display.style.color = '#10b981';
            } else {
                display.textContent = 'No post selected';
                display.style.color = '#94a3b8';
            }
        }
    }

    async checkExistingContent(postId) {
        try {
            const response = await fetch(`/launchpad/api/syndication/get-blog-content/${postId}`);
            const data = await response.json();
            
            if (data.success && data.content) {
                // Notify AI content generation manager
                if (window.aiContentGenerationManager) {
                    window.aiContentGenerationManager.setExistingContent(data.content, data.queue_item_id);
                }
            }
        } catch (error) {
            console.error('Error checking existing content:', error);
        }
    }

    getSelectedPost() {
        return this.selectedPost;
    }
}

// Initialize global instance
window.blogPostSelectionManager = new BlogPostSelectionManager();

