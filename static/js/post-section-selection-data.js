/**
 * Post Section Selection Data Management
 * Handles data loading and storage for posts and sections
 */

class PostSectionDataManager {
    constructor() {
        this.currentPost = null;
        this.currentSections = [];
        this.selectedSection = null;
    }

    async loadPosts() {
        const postSelector = document.getElementById('postSelector');
        if (!postSelector) return [];

        // Show loading state
        postSelector.innerHTML = '<option value="">Loading posts...</option>';

        try {
            const response = await fetch('/launchpad/api/syndication/posts');
            const data = await response.json();

            if (data.success && data.posts && data.posts.length > 0) {
                postSelector.innerHTML = '<option value="">Select a post...</option>';
                data.posts.forEach(post => {
                    const option = PostSectionUtils.createOption(post.id, `${post.title} (ID: ${post.id})`);
                    postSelector.appendChild(option);
                });
                return data.posts;
            } else {
                postSelector.innerHTML = '<option value="">No posts found</option>';
                return [];
            }
        } catch (error) {
            console.error('Error loading posts:', error);
            postSelector.innerHTML = '<option value="">Error loading posts</option>';
            return [];
        }
    }

    async loadPostDetails(postId) {
        try {
            const response = await fetch(`/launchpad/api/syndication/posts/${postId}`);
            const data = await response.json();

            if (data.success && data.post) {
                this.currentPost = data.post;
                return data.post;
            }
            return null;
        } catch (error) {
            console.error('Error loading post details:', error);
            return null;
        }
    }

    async loadPostSections(postId) {
        const sectionsContainer = document.getElementById('sectionsContainer');
        const sectionsList = document.getElementById('sectionsList');

        if (!sectionsContainer || !sectionsList) return [];

        try {
            const response = await fetch(`/launchpad/api/syndication/post-sections/${postId}`);
            const data = await response.json();

            sectionsContainer.innerHTML = '';

            if (data.success && data.sections && data.sections.length > 0) {
                this.currentSections = data.sections;
                
                data.sections.forEach(section => {
                    // Add post_id to section for image path construction
                    section.post_id = postId;
                    const sectionElement = PostSectionUtils.createSectionElement(section);
                    sectionsContainer.appendChild(sectionElement);
                });
                
                PostSectionUtils.showElement('sectionsList', true);
                return data.sections;
            } else {
                this.currentSections = [];
                sectionsContainer.innerHTML = '<p class="text-muted">No sections found for this post.</p>';
                PostSectionUtils.showElement('sectionsList', true);
                return [];
            }
        } catch (error) {
            console.error('Error loading sections:', error);
            this.currentSections = [];
            sectionsContainer.innerHTML = '<p class="text-danger">Error loading sections</p>';
            PostSectionUtils.showElement('sectionsList', true);
            return [];
        }
    }

    getCurrentPost() {
        return this.currentPost;
    }

    getCurrentSections() {
        return this.currentSections;
    }

    getSelectedSection() {
        return this.selectedSection;
    }

    setSelectedSection(section) {
        this.selectedSection = section;
    }

    clearSelection() {
        this.currentPost = null;
        this.currentSections = [];
        this.selectedSection = null;
    }
}
