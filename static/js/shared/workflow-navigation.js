/**
 * Workflow Navigation Module
 * Provides "Next" button functionality to navigate between workflow substages
 */

class WorkflowNavigation {
    constructor() {
        this.postId = null;
        this.postType = null;
        this.currentStage = null;
        this.currentSubstage = null;
        this.substages = null;
    }

    /**
     * Initialize navigation system
     */
    init(postId, postType) {
        this.postId = postId;
        this.postType = postType || 'themed';
        
        // Get current stage/substage from page context
        this.detectCurrentPosition();
        
        // Load substage configuration
        this.loadSubstages();
        
        // Create and display Next button
        this.createNextButton();
    }

    /**
     * Detect current stage and substage from page context
     */
    detectCurrentPosition() {
        // Try to get from window context (set by pages)
        if (window.currentStage) {
            this.currentStage = window.currentStage;
        }
        if (window.currentSubstage) {
            this.currentSubstage = window.currentSubstage;
        }

        // Fallback: Parse from URL
        if (!this.currentStage || !this.currentSubstage) {
            const pathParts = window.location.pathname.split('/').filter(p => p);
            
            // Look for stage names in path
            const stageIndex = pathParts.findIndex(part => 
                ['planning', 'authoring', 'imaging', 'header', 'research'].includes(part)
            );
            
            if (stageIndex !== -1) {
                this.currentStage = pathParts[stageIndex];
                
                // Try to find substage in path
                const substageMap = {
                    'ideas': 'ideas',
                    'taxonomy': 'taxonomy',
                    'brainstorm': 'topic_brainstorming',
                    'section-structure': 'section_structure',
                    'topic-allocation': 'topic_allocation',
                    'titling': 'section_titling',
                    'drafting': 'drafting',
                    'image-concepts': 'image_concepts',
                    'image-prompts': 'image_prompts',
                    'image-captions': 'image_captions',
                    'image-generation': 'image_generation',
                    'optimise': 'optimise',
                    'title-summary': 'title_summary',
                    'header-image': 'header_image',
                    'seo-meta': 'seo_meta'
                };
                
                // Check path parts for substage indicators
                for (let i = stageIndex + 1; i < pathParts.length; i++) {
                    const part = pathParts[i];
                    if (substageMap[part]) {
                        this.currentSubstage = substageMap[part];
                        break;
                    }
                }
                
                // Special case: ideas page
                if (pathParts.includes('ideas') && !this.currentSubstage) {
                    this.currentSubstage = 'ideas';
                }
            }
        }

        // Normalize stage names
        if (this.currentStage === 'concept') {
            this.currentStage = 'planning';
        }
        
        console.log('Detected position:', {
            stage: this.currentStage,
            substage: this.currentSubstage
        });
    }

    /**
     * Load substage configuration from API
     */
    async loadSubstages() {
        try {
            const response = await fetch(`/api/workflow/substages?post_type=${this.postType}`);
            const data = await response.json();
            
            if (data.success && data.substages) {
                // API returns {stage: [substage_keys]}
                this.substages = data.substages;
            } else {
                // Fallback: Use default configuration
                this.substages = this.getDefaultSubstages();
            }
        } catch (error) {
            console.error('Error loading substages:', error);
            // Fallback: Use default configuration
            this.substages = this.getDefaultSubstages();
        }
    }

    /**
     * Get default substage configuration (fallback)
     */
    getDefaultSubstages() {
        // Default order for different post types
        const defaultOrders = {
            'themed': {
                'planning': ['ideas', 'taxonomy', 'topic_brainstorming', 'section_structure', 'topic_allocation', 'section_titling'],
                'research': ['research', 'sources', 'visuals', 'prompts', 'verification'],
                'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
                'imaging': ['image_generation', 'optimise'],
                'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
            },
            'profile': {
                'planning': ['taxonomy', 'section_structure', 'topic_allocation', 'section_titling'],
                'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
                'imaging': ['image_generation', 'optimise'],
                'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
            },
            'recipe': {
                'planning': ['taxonomy', 'section_structure', 'topic_allocation', 'section_titling'],
                'authoring': ['drafting', 'recipe_image_style_prompt', 'image_captions'],
                'imaging': ['image_generation', 'optimise'],
                'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
            }
        };
        
        return defaultOrders[this.postType] || defaultOrders['themed'];
    }

    /**
     * Get next substage in sequence
     */
    getNextSubstage() {
        if (!this.currentStage || !this.currentSubstage || !this.substages) {
            console.log('Missing data for next substage:', {
                currentStage: this.currentStage,
                currentSubstage: this.currentSubstage,
                hasSubstages: !!this.substages
            });
            return null;
        }

        // Handle both array format (from API) and object format (from defaults)
        let stageSubstages = this.substages[this.currentStage];
        if (!stageSubstages) {
            console.log('No substages for stage:', this.currentStage, 'Available stages:', Object.keys(this.substages));
            return null;
        }
        
        // If it's an array of objects, extract keys
        if (Array.isArray(stageSubstages) && stageSubstages.length > 0 && typeof stageSubstages[0] === 'object') {
            stageSubstages = stageSubstages.map(s => s.key || s);
        }
        
        if (!Array.isArray(stageSubstages)) {
            console.log('Substages not an array for stage:', this.currentStage, 'Type:', typeof stageSubstages);
            return null;
        }

        const currentIndex = stageSubstages.indexOf(this.currentSubstage);
        if (currentIndex === -1) {
            console.log('Current substage not found in stage substages:', {
                currentSubstage: this.currentSubstage,
                availableSubstages: stageSubstages
            });
            return null;
        }
        
        if (currentIndex === stageSubstages.length - 1) {
            // Last substage in current stage - check if there's a next stage
            return this.getNextStageFirstSubstage();
        }

        // Next substage in current stage
        return {
            stage: this.currentStage,
            substage: stageSubstages[currentIndex + 1]
        };
    }

    /**
     * Get first substage of next stage
     */
    getNextStageFirstSubstage() {
        const stageOrder = ['planning', 'research', 'authoring', 'imaging', 'header'];
        const currentStageIndex = stageOrder.indexOf(this.currentStage);
        
        if (currentStageIndex === -1 || currentStageIndex === stageOrder.length - 1) {
            return null; // No next stage
        }

        const nextStage = stageOrder[currentStageIndex + 1];
        let nextStageSubstages = this.substages[nextStage];
        
        if (!nextStageSubstages || nextStageSubstages.length === 0) {
            return null;
        }
        
        // Handle both array format (from API) and object format (from defaults)
        if (Array.isArray(nextStageSubstages) && nextStageSubstages.length > 0 && typeof nextStageSubstages[0] === 'object') {
            nextStageSubstages = nextStageSubstages.map(s => s.key || s);
        }
        
        const firstSubstage = Array.isArray(nextStageSubstages) ? nextStageSubstages[0] : null;
        if (!firstSubstage) {
            return null;
        }

        return {
            stage: nextStage,
            substage: firstSubstage
        };
    }

    /**
     * Get route URL for a substage
     * Uses API to get next substage URL
     */
    async getSubstageRoute(stage, substage) {
        try {
            const response = await fetch(
                `/api/workflow/next-substage?post_id=${this.postId}&stage=${stage}&substage=${substage}`
            );
            const data = await response.json();
            
            if (data.success && data.next && data.next.url) {
                return data.next.url;
            }
        } catch (error) {
            console.error('Error getting next substage URL:', error);
        }
        
        // Fallback: Build URL from pattern
        const routeMap = {
            'ideas': `/planning/posts/${this.postId}/calendar/ideas`,
            'taxonomy': `/planning/posts/${this.postId}/calendar/taxonomy`,
            'topic_brainstorming': `/planning/posts/${this.postId}/concept/brainstorm`,
            'section_structure': `/planning/posts/${this.postId}/concept/section-structure`,
            'topic_allocation': `/planning/posts/${this.postId}/concept/topic-allocation`,
            'section_titling': `/planning/posts/${this.postId}/concept/titling`,
            'drafting': `/authoring/posts/${this.postId}/sections/drafting`,
            'image_concepts': `/authoring/posts/${this.postId}/sections/image-concepts`,
            'image_prompts': `/authoring/posts/${this.postId}/sections/image-prompts`,
            'image_captions': `/authoring/posts/${this.postId}/sections/image-captions`,
            'image_generation': `/imaging/posts/${this.postId}/sections/image-generation`,
            'optimise': `/imaging/posts/${this.postId}/sections/optimise`,
            'title_summary': `/header/posts/${this.postId}/title-summary`,
            'header_image': `/header/posts/${this.postId}/header-image`,
            'seo_meta': `/header/posts/${this.postId}/seo-meta`,
            'final_review': `/header/posts/${this.postId}/preview`
        };

        return routeMap[substage] || null;
    }

    /**
     * Create and display Next button
     */
    async createNextButton() {
        const nextSubstage = this.getNextSubstage();
        
        if (!nextSubstage) {
            return; // No next substage available
        }

        const route = await this.getSubstageRoute(nextSubstage.stage, nextSubstage.substage);
        if (!route) {
            return; // No route available
        }

        // Check if button already exists
        let nextButton = document.getElementById('workflow-next-button');
        if (nextButton) {
            nextButton.remove();
        }

        // Create button
        nextButton = document.createElement('button');
        nextButton.id = 'workflow-next-button';
        nextButton.className = 'workflow-next-btn';
        nextButton.innerHTML = `
            <span>Next: ${this.formatSubstageLabel(nextSubstage.substage)}</span>
            <i class="fas fa-arrow-right"></i>
        `;
        
        // Add click handler
        nextButton.addEventListener('click', () => {
            // Preserve year/week parameters if present
            const urlParams = new URLSearchParams(window.location.search);
            const year = urlParams.get('year');
            const week = urlParams.get('week');
            
            let nextUrl = route;
            const params = [];
            if (year) params.push(`year=${year}`);
            if (week) params.push(`week=${week}`);
            
            if (params.length > 0) {
                nextUrl += (nextUrl.includes('?') ? '&' : '?') + params.join('&');
            }
            
            window.location.href = nextUrl;
        });

        // Insert button into page
        this.insertNextButton(nextButton);
    }

    /**
     * Format substage label for display
     */
    formatSubstageLabel(substage) {
        const labelMap = {
            'ideas': 'Ideas',
            'taxonomy': 'Taxonomy',
            'topic_brainstorming': 'Topic Brainstorming',
            'section_structure': 'Section Structure',
            'topic_allocation': 'Topic Allocation',
            'section_titling': 'Section Titling',
            'drafting': 'Drafting',
            'image_concepts': 'Image Concepts',
            'image_prompts': 'Image Prompts',
            'image_captions': 'Image Captions',
            'image_generation': 'Image Generation',
            'optimise': 'Optimise',
            'title_summary': 'Title & Summary',
            'header_image': 'Header Image',
            'seo_meta': 'SEO Meta',
            'final_review': 'Final Review'
        };

        return labelMap[substage] || substage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Insert Next button into page
     */
    insertNextButton(button) {
        // First, try to find dedicated container
        const container = document.getElementById('workflow-navigation-container');
        if (container) {
            container.innerHTML = ''; // Clear any existing content
            container.appendChild(button);
            container.style.display = 'flex';
            return;
        }
        
        // Try to insert after main content area, before footer/end
        const mainContent = document.querySelector('.page-main') || 
                          document.querySelector('.ideas-main') ||
                          document.querySelector('.ideas-results') ||
                          document.querySelector('.expanded-idea-section') ||
                          document.querySelector('.container > div');
        
        if (mainContent) {
            // Create wrapper div for button
            const wrapper = document.createElement('div');
            wrapper.className = 'workflow-navigation-wrapper';
            wrapper.id = 'workflow-navigation-container';
            wrapper.style.cssText = 'display: flex; justify-content: center; margin: 2rem 0;';
            wrapper.appendChild(button);
            
            // Insert after main content
            if (mainContent.parentNode) {
                mainContent.parentNode.insertBefore(wrapper, mainContent.nextSibling);
            } else {
                mainContent.appendChild(wrapper);
            }
        } else {
            // Fallback: Insert before footer or at end of body
            const footer = document.querySelector('footer');
            const wrapper = document.createElement('div');
            wrapper.className = 'workflow-navigation-wrapper';
            wrapper.id = 'workflow-navigation-container';
            wrapper.style.cssText = 'display: flex; justify-content: center; margin: 2rem 0;';
            wrapper.appendChild(button);
            
            if (footer) {
                footer.parentNode.insertBefore(wrapper, footer);
            } else {
                document.body.appendChild(wrapper);
            }
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for page to fully load
    setTimeout(() => {
        // Get post ID and type from page context
        const postId = window.postId || (window.location.pathname.match(/\/posts\/(\d+)/) ? 
                                         parseInt(window.location.pathname.match(/\/posts\/(\d+)/)[1]) : null);
        
        // Try to get post type from page context or header
        let postType = window.postType || 'themed';
        const postTypeElement = document.querySelector('.post-type-value');
        if (postTypeElement) {
            const typeText = postTypeElement.textContent.trim().toLowerCase();
            postType = typeText || 'themed';
        }

        if (postId) {
            console.log('[Workflow Navigation] Initializing for post:', postId, 'type:', postType);
            window.workflowNavigation = new WorkflowNavigation();
            window.workflowNavigation.init(postId, postType);
        } else {
            console.warn('[Workflow Navigation] No post ID found, cannot initialize');
        }
    }, 800); // Wait 800ms for page to fully initialize (increased for ideas page)
});
