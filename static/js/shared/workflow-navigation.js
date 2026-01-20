/**
 * Workflow Navigation Module
 * Provides "Next" button functionality to navigate between workflow substages
 */

// Prevent duplicate class definition
if (typeof WorkflowNavigation === 'undefined') {
class WorkflowNavigation {
    constructor() {
        this.postId = null;
        this.postType = null;
        this.currentStage = null;
        this.currentSubstage = null;
        this.substages = null;
        this.initialized = false;
    }

    /**
     * Initialize navigation system
     */
    async init(postId, postType) {
        this.postId = postId;
        this.postType = postType || 'themed';
        
        // Get current stage/substage from page context
        this.detectCurrentPosition();
        
        // Load substage configuration and wait for it
        await this.loadSubstages();
        
        // Create and display Next button (wait for it to complete)
        await this.createNextButton();
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
        
        // Normalize substage names (hyphens to underscores to match config keys)
        if (this.currentSubstage) {
            this.currentSubstage = this.normalizeSubstageName(this.currentSubstage);
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
            console.log('[Workflow Navigation] Loading substages for post type:', this.postType);
            const response = await fetch(`/api/workflow/substages?post_type=${this.postType}`);
            const data = await response.json();
            
            if (data.success && data.substages) {
                // API returns {stage: [substage_keys]}
                this.substages = data.substages;
                console.log('[Workflow Navigation] Loaded substages:', this.substages);
            } else {
                // Fallback: Use default configuration
                console.log('[Workflow Navigation] Using default substages');
                this.substages = this.getDefaultSubstages();
            }
        } catch (error) {
            console.error('[Workflow Navigation] Error loading substages:', error);
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
                'research': ['background_research'],
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
            console.log('[Workflow Navigation] Missing data for next substage:', {
                currentStage: this.currentStage,
                currentSubstage: this.currentSubstage,
                hasSubstages: !!this.substages,
                substages: this.substages
            });
            return null;
        }
        
        console.log('[Workflow Navigation] Getting next substage for:', {
            currentStage: this.currentStage,
            currentSubstage: this.currentSubstage
        });

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
        // Stage order - research comes before planning (research feeds into planning background)
        const stageOrder = ['research', 'planning', 'authoring', 'imaging', 'header'];
        const currentStageIndex = stageOrder.indexOf(this.currentStage);
        
        if (currentStageIndex === -1 || currentStageIndex === stageOrder.length - 1) {
            return null; // No next stage
        }
        
        // For non-recipe posts, check if they have research stage
        let nextStageIndex = currentStageIndex + 1;
        if (stageOrder[nextStageIndex] === 'research') {
            // Check if this post type actually has research substages
            const hasResearch = this.substages && this.substages.research && this.substages.research.length > 0;
            if (!hasResearch) {
                nextStageIndex++; // Skip research if no research substages
            }
        }
        
        if (nextStageIndex >= stageOrder.length) {
            return null; // No next stage
        }

        const nextStage = stageOrder[nextStageIndex];
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
     * Builds URL directly from substage key (we already know which substage we want)
     */
    getSubstageRoute(stage, substage) {
        // Build URL directly from substage key - we already know which substage we want
        const routeMap = {
            'ideas': `/planning/posts/${this.postId}/calendar/ideas`,
            'taxonomy': `/planning/posts/${this.postId}/calendar/taxonomy`,
            'topic_brainstorming': `/planning/posts/${this.postId}/concept/brainstorm`,
            'section_structure': `/planning/posts/${this.postId}/concept/section-structure`,
            'topic_allocation': `/planning/posts/${this.postId}/concept/topic-allocation`,
            'section_titling': `/planning/posts/${this.postId}/concept/titling`,
            'research': `/planning/posts/${this.postId}/research`,
            'sources': `/planning/posts/${this.postId}/research/sources`,
            'visuals': `/planning/posts/${this.postId}/research/visuals`,
            'prompts': `/planning/posts/${this.postId}/research/prompts`,
            'verification': `/planning/posts/${this.postId}/research/verification`,
            'background_research': `/research/posts/${this.postId}/background-research`,
            'drafting': `/posts/${this.postId}/sections/drafting`,
            'image_concepts': `/authoring/posts/${this.postId}/sections/image_concepts`,
            'image_prompts': `/authoring/posts/${this.postId}/sections/image_prompts`,
            'image_captions': `/authoring/posts/${this.postId}/sections/image_captions`,
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
            console.log('[Workflow Navigation] No next substage available');
            return; // No next substage available
        }

        console.log('[Workflow Navigation] Next substage:', nextSubstage);
        const route = this.getSubstageRoute(nextSubstage.stage, nextSubstage.substage);
        if (!route) {
            console.warn('[Workflow Navigation] No route available for next substage');
            return; // No route available
        }
        
        console.log('[Workflow Navigation] Next route:', route);

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
     * Normalize substage name (convert hyphens to underscores, handle special cases)
     */
    normalizeSubstageName(substage) {
        if (!substage) return null;
        // Normalize substage names (e.g., 'brainstorm' -> 'topic_brainstorming', 'section-structure' -> 'section_structure')
        const substageMap = {
            'brainstorm': 'topic_brainstorming',
            'ideas': 'ideas',
            'taxonomy': 'taxonomy',
            'section-structure': 'section_structure',
            'section_structure': 'section_structure', // Also handle underscore version
            'topic-allocation': 'topic_allocation',
            'topic_allocation': 'topic_allocation', // Also handle underscore version
            'titling': 'section_titling',
            'section-titling': 'section_titling',
            'section_titling': 'section_titling', // Also handle underscore version
            'drafting': 'drafting',
            'image-concepts': 'image_concepts',
            'image_concepts': 'image_concepts', // Also handle underscore version
            'image-prompts': 'image_prompts',
            'image_prompts': 'image_prompts', // Also handle underscore version
            'image-captions': 'image_captions',
            'image_captions': 'image_captions', // Also handle underscore version
            'image-generation': 'image_generation',
            'image_generation': 'image_generation', // Also handle underscore version
            'optimise': 'optimise',
            'title-summary': 'title_summary',
            'title_summary': 'title_summary', // Also handle underscore version
            'header-image': 'header_image',
            'header_image': 'header_image', // Also handle underscore version
            'seo-meta': 'seo_meta',
            'seo_meta': 'seo_meta' // Also handle underscore version
        };
        // First check map, then fallback to replacing hyphens with underscores
        return substageMap[substage] || substage.replace(/-/g, '_');
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
            'topic_allocation': 'Section Ideas',  // Updated: was "Topic Allocation", now "Section Ideas"
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
            console.log('[Workflow Navigation] Found container, inserting button');
            container.innerHTML = ''; // Clear any existing content
            container.appendChild(button);
            container.style.display = 'flex';
            container.style.justifyContent = 'center';
            container.style.margin = '1rem 0';
            console.log('[Workflow Navigation] Button inserted into container');
            return;
        }
        
        console.warn('[Workflow Navigation] Container not found, trying fallback insertion');
        
        // Try to insert after main content area, before footer/end
        const mainContent = document.querySelector('.page-main') || 
                          document.querySelector('.ideas-main') ||
                          document.querySelector('.ideas-results') ||
                          document.querySelector('.expanded-idea-section') ||
                          document.querySelector('.brainstorm-main') ||
                          document.querySelector('.titling-main') ||
                          document.querySelector('.container > div');
        
        if (mainContent) {
            // Create wrapper div for button
            const wrapper = document.createElement('div');
            wrapper.className = 'workflow-navigation-wrapper';
            wrapper.id = 'workflow-navigation-container';
            wrapper.style.cssText = 'display: flex; justify-content: center; margin: 0.75rem 0;';
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
            wrapper.style.cssText = 'display: flex; justify-content: center; margin: 0.75rem 0;';
            wrapper.appendChild(button);
            
            if (footer) {
                footer.parentNode.insertBefore(wrapper, footer);
            } else {
                document.body.appendChild(wrapper);
            }
        }
    }
};

// Expose to window
window.WorkflowNavigation = WorkflowNavigation;

} // End of if (typeof window.WorkflowNavigation === 'undefined')

// Auto-initialize when DOM is ready
function initializeWorkflowNavigation() {
    // Prevent duplicate initialization
    if (window.workflowNavigation && window.workflowNavigation.initialized) {
        console.log('[Workflow Navigation] Already initialized, skipping');
        return;
    }
    
    // Get post ID and type from page context
    const postId = window.postId || (window.location.pathname.match(/\/posts\/(\d+)/) ? 
                                     parseInt(window.location.pathname.match(/\/posts\/(\d+)/)[1]) : null);
    
    // Try to get post type from page context or header
    let postType = window.postType || 'themed';
    const postTypeElement = document.querySelector('.post-type-value');
    if (postTypeElement) {
        const typeText = postTypeElement.textContent.trim().toLowerCase();
        // Map UI text to actual post type values
        const postTypeMap = {
            'available': 'themed',  // "Available" in UI means "themed" post type
            'recipe': 'recipe',
            'profile': 'profile',
            'generated': 'generated'
        };
        postType = postTypeMap[typeText] || 'themed';
    }

    if (postId) {
        console.log('[Workflow Navigation] Initializing for post:', postId, 'type:', postType);
        
        // Check if WorkflowNavigation class is available
        if (typeof window.WorkflowNavigation === 'undefined') {
            console.warn('[Workflow Navigation] WorkflowNavigation class not yet defined, will retry');
            // Retry after a short delay
            setTimeout(() => {
                if (typeof window.WorkflowNavigation !== 'undefined') {
                    initializeWorkflowNavigation();
                } else {
                    console.error('[Workflow Navigation] WorkflowNavigation class still not defined after retry');
                }
            }, 500);
            return;
        }
        
        try {
            const WorkflowNavClass = window.WorkflowNavigation;
            
            // Check if init method exists
            if (typeof WorkflowNavClass.prototype.init !== 'function') {
                console.error('[Workflow Navigation] WorkflowNavigation.init method not found');
                return;
            }
            
            window.workflowNavigation = new WorkflowNavClass();
            
            // Check if init method exists on instance
            if (typeof window.workflowNavigation.init !== 'function') {
                console.error('[Workflow Navigation] init method not found on instance');
                return;
            }
            
            // Call init and handle Promise or undefined
            const initResult = window.workflowNavigation.init(postId, postType);
            
            if (initResult && typeof initResult.then === 'function') {
                // init returns a Promise
                initResult.then(() => {
                    if (window.workflowNavigation) {
                        window.workflowNavigation.initialized = true;
                    }
                    console.log('[Workflow Navigation] Initialization complete');
                }).catch(error => {
                    console.error('[Workflow Navigation] Initialization error:', error);
                });
            } else {
                // init is synchronous or doesn't return a Promise
                if (window.workflowNavigation) {
                    window.workflowNavigation.initialized = true;
                }
                console.log('[Workflow Navigation] Initialization complete (synchronous)');
            }
        } catch (error) {
            console.error('[Workflow Navigation] Error during initialization:', error);
        }
    } else {
        console.warn('[Workflow Navigation] No post ID found, cannot initialize');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Wait a bit for page to fully load
        setTimeout(initializeWorkflowNavigation, 800); // Wait 800ms for page to fully initialize (increased for ideas page)
        
        // Also try immediately if postId is already set (for pages that set it synchronously)
        if (window.postId) {
            setTimeout(initializeWorkflowNavigation, 100);
        }
    });
} else {
    // DOM already loaded
    setTimeout(initializeWorkflowNavigation, 800);
    if (window.postId) {
        setTimeout(initializeWorkflowNavigation, 100);
    }
}
