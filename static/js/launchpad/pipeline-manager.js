/**
 * Pipeline Manager
 * Manages the pipeline progress tracker for any post
 */

class PipelineManager {
    constructor(postId = null) {
        this.currentPostId = postId;
        this.stages = ['calendar', 'planning', 'authoring', 'imaging', 'header'];
        // Map API stage names to template IDs
        this.stageIdMap = {
            'calendar': 'calendar',
            'planning': 'concept',
            'authoring': 'authoring', 
            'imaging': 'imaging',
            'header': 'header'
        };
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
                this.populatePostSelector(data.data);
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
        
        if (posts && Array.isArray(posts)) {
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
        } else {
            console.log('[Pipeline Manager] No posts data available');
        }
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
        console.log('[Pipeline Manager] Updating pipeline display with data:', data);
        
        if (!data || !data.data) {
            console.error('[Pipeline Manager] Invalid data structure:', data);
            return;
        }
        
        const pipelineData = data.data;
        
        // Debug: Log completed substages
        if (pipelineData.stages) {
            console.log('[Pipeline Manager] Checking for completed substages...');
            Object.entries(pipelineData.stages).forEach(([stageName, stageData]) => {
                if (stageData.substages) {
                    Object.entries(stageData.substages).forEach(([substageName, substageData]) => {
                        if (substageData.status === 'complete') {
                            console.log(`[Pipeline Manager] Found completed: ${stageName}.${substageName}`);
                        }
                    });
                }
            });
        }
        
        // Update overall progress
        const progressBar = document.querySelector('.overall-progress .progress-fill');
        const progressText = document.querySelector('.overall-progress .progress-text');
        if (progressBar && progressText && pipelineData.overall_progress !== undefined) {
            progressBar.style.width = `${pipelineData.overall_progress}%`;
            progressText.textContent = `${pipelineData.overall_progress}%`;
        }
        
        // Update each stage
        if (pipelineData.stages) {
            this.stages.forEach(stage => {
                if (pipelineData.stages[stage]) {
                    this.updateStageDisplay(stage, pipelineData.stages[stage]);
                }
            });
        }
        
        console.log('[Pipeline Manager] Pipeline display updated');
    }

    /**
     * Update a specific stage's display
     */
    updateStageDisplay(stage, stageData) {
        const templateStageId = this.stageIdMap[stage];
        
        // Update stage status
        const statusElement = document.querySelector(`#${templateStageId}-content`)?.closest('.stage-accordion')?.querySelector('.stage-status');
        if (statusElement) {
            statusElement.className = `stage-status ${stageData.status}`;
            statusElement.textContent = stageData.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        }
        
        // Update stage progress
        const progressBar = document.querySelector(`#${templateStageId}-content`)?.closest('.stage-accordion')?.querySelector('.stage-progress .progress-fill');
        const progressText = document.querySelector(`#${templateStageId}-content`)?.closest('.stage-accordion')?.querySelector('.stage-progress .progress-text');
        if (progressBar && progressText) {
            progressBar.style.width = `${stageData.progress}%`;
            progressText.textContent = `${stageData.progress}%`;
        }
        
        // Update substages if available
        if (stageData.substages && Object.keys(stageData.substages).length > 0) {
            this.updateSubstagesDisplay(templateStageId, stageData.substages, stage);
        }
    }

    /**
     * Update substages display
     */
    updateSubstagesDisplay(stage, substages, apiStageName = null) {
        console.log('[Pipeline Manager] Updating substages display for stage:', stage, 'substages:', substages);
        
        // Handle both object and array formats
        const substagesList = Array.isArray(substages) ? substages : Object.entries(substages).map(([key, data]) => ({
            name: key.replace(/_/g, '-'), // Use dashes for data attributes
            key: key,
            ...data
        }));
        
        console.log('[Pipeline Manager] Processed substages list:', substagesList);
        
        // Map API substage names to template data-substage values
        const substageNameMap = {
            'ideas': 'ideas',
            'taxonomy': 'taxonomy',
            'topic_brainstorming': 'topic_brainstorming',
            'section_structure': 'section_structure',
            'topic_allocation': 'topic_allocation',
            'section_titling': 'section_titling',
            'author_first_drafts': 'author_first_drafts',
            'image_concepts': 'image_concepts',
            'image_prompts': 'image_prompts',
            'image_captions': 'image_captions',
            'image_generation': 'image_generation',
            'optimise': 'optimise',
            'title_summary': 'title_summary',
            'header_image': 'header_image',
            'seo_meta': 'seo_meta',
            'product_match': 'product_match',
            'final_review': 'final_review',
            'calendar_view': 'view',
            'idea_generation': 'ideas_week'
        };
        
        // Update existing substages with timestamps
        substagesList.forEach(substage => {
            // Try both the API key and the mapped name
            const apiKey = substage.key;
            const mappedName = substageNameMap[apiKey] || apiKey;
            
            console.log('[Pipeline Manager] Looking for substage:', apiKey, '->', mappedName, 'in stage:', stage);
            
            // Look for existing substage - try multiple selectors
            // First try with stage and substage together
            let existingSubstage = document.querySelector(`[data-stage="${stage}"][data-substage="${mappedName}"]`);
            if (!existingSubstage) {
                // Try just substage
                existingSubstage = document.querySelector(`[data-substage="${mappedName}"]`);
            }
            if (!existingSubstage) {
                // Try with original API key
                existingSubstage = document.querySelector(`[data-substage="${apiKey}"]`);
            }
            if (!existingSubstage) {
                // Try with dashes instead of underscores
                const dashedName = mappedName.replace(/_/g, '-');
                existingSubstage = document.querySelector(`[data-substage="${dashedName}"]`);
            }
            
            if (existingSubstage) {
                console.log('[Pipeline Manager] Found existing substage:', mappedName);
                
                // Update existing substage
                const completedAtSpan = existingSubstage.querySelector('.completed-at');
                
                if (completedAtSpan) {
                    if (substage.completed_at) {
                        const timeAgo = this.formatTimeAgo(substage.completed_at);
                        completedAtSpan.textContent = `Completed ${timeAgo}`;
                        console.log('[Pipeline Manager] Updated timestamp for', mappedName, 'to:', timeAgo);
                    } else {
                        // Show progress if in progress
                        if (substage.status === 'in_progress' && substage.progress !== undefined) {
                            completedAtSpan.textContent = `${substage.progress}% complete`;
                        } else {
                            completedAtSpan.textContent = 'Pending';
                        }
                    }
                }
                
                // Update status classes - add green dot indicator for complete
                existingSubstage.className = `substage ${substage.status} automation-enabled`;
                if (substage.status === 'complete') {
                    existingSubstage.classList.add('complete');
                }
                
                // Update icon with green checkmark for complete
                const icon = existingSubstage.querySelector('i');
                if (icon) {
                    if (substage.status === 'complete') {
                        icon.className = 'fas fa-check-circle';
                        icon.style.color = '#10b981'; // Green color
                        console.log('[Pipeline Manager] ✅ Set green checkmark for', mappedName);
                    } else if (substage.status === 'in_progress') {
                        icon.className = 'fas fa-spinner fa-spin';
                        icon.style.color = '#3b82f6'; // Blue color
                    } else {
                        icon.className = 'fas fa-circle';
                        icon.style.color = '#6b7280'; // Gray color
                    }
                } else {
                    console.warn('[Pipeline Manager] No icon found for substage:', mappedName);
                }
                
                // Update progress if available (for multi-section substages)
                if (substage.progress !== undefined) {
                    const progressElement = existingSubstage.querySelector('.substage-progress');
                    if (progressElement) {
                        progressElement.style.width = `${substage.progress}%`;
                    }
                }
            } else {
                console.log('[Pipeline Manager] Substage not found:', mappedName, '(tried:', apiKey, ')');
            }
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
     * Format timestamp as "X hours ago" or "X days ago"
     */
    formatTimeAgo(isoString) {
        if (!isoString) return '';
        
        const date = new Date(isoString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        let interval = seconds / 31536000;
        if (interval > 1) return Math.floor(interval) + " years ago";
        interval = seconds / 2592000;
        if (interval > 1) return Math.floor(interval) + " months ago";
        interval = seconds / 86400;
        if (interval > 1) return Math.floor(interval) + " days ago";
        interval = seconds / 3600;
        if (interval > 1) return Math.floor(interval) + " hours ago";
        interval = seconds / 60;
        if (interval > 1) return Math.floor(interval) + " minutes ago";
        return Math.floor(seconds) + " seconds ago";
    }

    /**
     * Manual test function to update timestamps
     */
    async testUpdateTimestamps() {
        console.log('[Pipeline Manager] Testing manual timestamp update...');
        
        // Test with post ID 69
        const postId = 69;
        
        try {
            const response = await fetch(`/launchpad/one-click-blog/api/pipeline-status/${postId}`);
            const data = await response.json();
            
            if (data.success) {
                console.log('[Pipeline Manager] API response:', data);
                
                // Update authoring substages
                if (data.data.stages.authoring && data.data.stages.authoring.substages) {
                    this.updateSubstagesDisplay('authoring', data.data.stages.authoring.substages);
                }
            } else {
                console.error('[Pipeline Manager] API error:', data.error);
            }
        } catch (error) {
            console.error('[Pipeline Manager] Test error:', error);
        }
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
            'calendar': `/planning/posts/${this.currentPostId}/calendar/ideas`,
            'planning': `/planning/posts/${this.currentPostId}/concept/titling`,
            'concept': `/planning/posts/${this.currentPostId}/concept/titling`,
            'authoring': `/authoring/posts/${this.currentPostId}/sections/author-first-drafts`,
            'imaging': `/imaging/posts/${this.currentPostId}/sections/image-generation`,
            'header': `/header/posts/${this.currentPostId}/title-summary`
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

