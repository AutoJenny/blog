/**
 * Pipeline Manager
 * Manages the pipeline progress tracker for any post
 */

class PipelineManager {
    constructor(postId = null) {
        this.currentPostId = postId;
        this.stages = ['planning', 'authoring', 'imaging'];
        this.init();
    }

    init() {
        console.log('[Pipeline Manager] Initializing with post ID:', this.currentPostId);
        
        // Load posts list for selector
        this.loadPostsList();
        
        // Set up post selector change handler
        this.setupPostSelector();
        
        // Load pipeline data if we have a post ID
        if (this.currentPostId) {
            this.loadPipelineData(this.currentPostId);
        }
    }

    /**
     * Set the current post ID and reload pipeline data
     */
    async setPostId(postId) {
        console.log('[Pipeline Manager] Setting post ID to:', postId);
        this.currentPostId = postId;
        
        // Update the selector if it's different
        const selector = document.getElementById('pipeline-post-selector');
        if (selector && selector.value != postId) {
            selector.value = postId;
        }
        
        // Load pipeline data for this post
        await this.loadPipelineData(postId);
    }

    /**
     * Load list of posts in development for the selector
     */
    async loadPostsList() {
        try {
            const response = await fetch('/launchpad/one-click-blog/api/posts-in-development');
            const data = await response.json();
            
            if (data.success) {
                this.populatePostSelector(data.posts);
            } else {
                console.error('[Pipeline Manager] Failed to load posts:', data.error);
            }
        } catch (error) {
            console.error('[Pipeline Manager] Error loading posts list:', error);
        }
    }

    /**
     * Populate the post selector dropdown
     */
    populatePostSelector(posts) {
        const selector = document.getElementById('pipeline-post-selector');
        if (!selector) return;
        
        selector.innerHTML = '<option value="">Select a post...</option>';
        
        posts.forEach(post => {
            const option = document.createElement('option');
            option.value = post.id;
            option.textContent = `#${post.id} - ${post.title}`;
            if (post.id === this.currentPostId) {
                option.selected = true;
            }
            selector.appendChild(option);
        });
        
        console.log('[Pipeline Manager] Populated selector with', posts.length, 'posts');
    }

    /**
     * Set up post selector change event
     */
    setupPostSelector() {
        const selector = document.getElementById('pipeline-post-selector');
        if (!selector) return;
        
        selector.addEventListener('change', async (e) => {
            const postId = parseInt(e.target.value);
            if (postId) {
                await this.setPostId(postId);
            }
        });
    }

    /**
     * Load pipeline data for a specific post
     */
    async loadPipelineData(postId) {
        if (!postId) {
            console.log('[Pipeline Manager] No post ID provided');
            return;
        }
        
        console.log('[Pipeline Manager] Loading pipeline data for post:', postId);
        
        try {
            // Show loading state
            this.showLoadingState();
            
            const response = await fetch(`/launchpad/one-click-blog/api/pipeline-status/${postId}`);
            const data = await response.json();
            
            if (data.success) {
                this.updatePipelineDisplay(data);
            } else {
                console.error('[Pipeline Manager] Failed to load pipeline data:', data.error);
                this.showError('Failed to load pipeline data');
            }
        } catch (error) {
            console.error('[Pipeline Manager] Error loading pipeline data:', error);
            this.showError('Error loading pipeline data');
        }
    }

    /**
     * Update the pipeline display with data
     */
    updatePipelineDisplay(data) {
        console.log('[Pipeline Manager] Updating pipeline display:', data);
        
        // Update overall progress
        const progressBar = document.querySelector('.overall-progress .progress-fill');
        const progressText = document.querySelector('.overall-progress .progress-text');
        if (progressBar && progressText) {
            progressBar.style.width = `${data.overall_progress}%`;
            progressText.textContent = `${data.overall_progress}%`;
        }
        
        // Update each stage
        this.stages.forEach(stage => {
            if (data.stages[stage]) {
                this.updateStageDisplay(stage, data.stages[stage]);
            }
        });
        
        console.log('[Pipeline Manager] Pipeline display updated');
    }

    /**
     * Update a specific stage's display
     */
    updateStageDisplay(stage, stageData) {
        // Update stage status
        const statusElement = document.querySelector(`#${stage}-content`)?.closest('.stage-accordion')?.querySelector('.stage-status');
        if (statusElement) {
            statusElement.className = `stage-status ${stageData.status}`;
            statusElement.textContent = stageData.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        }
        
        // Update stage progress
        const progressBar = document.querySelector(`#${stage}-content`)?.closest('.stage-accordion')?.querySelector('.stage-progress .progress-fill');
        const progressText = document.querySelector(`#${stage}-content`)?.closest('.stage-accordion')?.querySelector('.stage-progress .progress-text');
        if (progressBar && progressText) {
            progressBar.style.width = `${stageData.progress}%`;
            progressText.textContent = `${stageData.progress}%`;
        }
        
        // Update substages if available
        if (stageData.substages && stageData.substages.length > 0) {
            this.updateSubstagesDisplay(stage, stageData.substages);
        }
    }

    /**
     * Update substages display
     */
    updateSubstagesDisplay(stage, substages) {
        const substagesContainer = document.querySelector(`#${stage}-content .substages`);
        if (!substagesContainer) return;
        
        substagesContainer.innerHTML = '';
        
        substages.forEach(substage => {
            const substageElement = document.createElement('div');
            substageElement.className = `substage ${substage.status}`;
            
            let icon = '<i class="fas fa-clock"></i>';
            if (substage.status === 'complete') {
                icon = '<i class="fas fa-check-circle"></i>';
            } else if (substage.status === 'in-progress') {
                icon = '<i class="fas fa-spinner fa-spin"></i>';
            }
            
            let timeInfo = '';
            if (substage.completed_at) {
                timeInfo = `<span class="completed-at">${substage.completed_at}</span>`;
            } else if (substage.estimated_time) {
                timeInfo = `<span class="estimated-time">${substage.estimated_time}</span>`;
            }
            
            substageElement.innerHTML = `
                ${icon}
                <span>${substage.name}</span>
                ${timeInfo}
            `;
            
            substagesContainer.appendChild(substageElement);
        });
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        const selector = document.getElementById('pipeline-post-selector');
        if (selector) {
            selector.disabled = true;
        }
        
        // Could add a loading spinner here
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error('[Pipeline Manager]', message);
        
        const selector = document.getElementById('pipeline-post-selector');
        if (selector) {
            selector.disabled = false;
        }
        
        // Could show a notification here
    }

    /**
     * Toggle stage accordion
     */
    toggleStage(stage) {
        console.log('[Pipeline Manager] Toggling stage:', stage);
        
        const content = document.getElementById(`${stage}-content`);
        const chevron = document.getElementById(`${stage}-chevron`);
        
        if (!content) {
            console.error('[Pipeline Manager] Stage content not found:', stage);
            return;
        }
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            if (chevron) chevron.style.transform = 'rotate(180deg)';
        } else {
            content.style.display = 'none';
            if (chevron) chevron.style.transform = 'rotate(0deg)';
        }
    }

    /**
     * Toggle mode (manual/auto) for a stage
     */
    toggleMode(stage, mode) {
        console.log('[Pipeline Manager] Toggling mode for', stage, 'to', mode);
        
        // Update button states
        const stageAccordion = document.querySelector(`#${stage}-content`)?.closest('.stage-accordion');
        if (!stageAccordion) return;
        
        const buttons = stageAccordion.querySelectorAll('.mode-toggle');
        buttons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.toLowerCase().includes(mode)) {
                btn.classList.add('active');
            }
        });
        
        // TODO: Save mode preference to backend
        console.log('[Pipeline Manager] Mode changed to', mode, 'for', stage);
    }

    /**
     * Review a stage - navigate to the stage page
     */
    reviewStage(stage) {
        if (!this.currentPostId) {
            console.error('[Pipeline Manager] No post ID set');
            return;
        }
        
        console.log('[Pipeline Manager] Reviewing stage:', stage, 'for post:', this.currentPostId);
        
        // Map stage names to URL paths
        const stageUrls = {
            'planning': `/planning/posts/${this.currentPostId}/concept/titling`,
            'concept': `/planning/posts/${this.currentPostId}/concept/titling`,
            'authoring': `/authoring/posts/${this.currentPostId}/sections/author-first-drafts`,
            'imaging': `/imaging/posts/${this.currentPostId}/sections`
        };
        
        const url = stageUrls[stage];
        if (url) {
            window.location.href = url;
        } else {
            console.error('[Pipeline Manager] Unknown stage:', stage);
        }
    }

    /**
     * Skip a stage
     */
    skipStage(stage) {
        console.log('[Pipeline Manager] Skipping stage:', stage);
        
        // TODO: Implement skip logic
        // This would mark the stage as skipped in the backend
        // and move to the next stage
        
        alert(`Skip functionality for ${stage} stage will be implemented soon`);
    }
}

