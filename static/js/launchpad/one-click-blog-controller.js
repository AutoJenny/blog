/**
 * One-Click Blog Main Controller
 * Orchestrates all micro-modules for the One-Click Blog system
 */

class OneClickBlogController {
    constructor() {
        this.scheduleManager = null;
        this.nextUpPanel = null;
        this.pipelineManager = null;
        this.automationEngine = null;
        this.init();
    }

    init() {
        console.log('[One-Click Blog Controller] Initializing...');
        
        // Initialize micro-modules
        console.log('[One-Click Blog Controller] Creating ScheduleManager...');
        this.scheduleManager = new ScheduleManager();
        console.log('[One-Click Blog Controller] ScheduleManager created:', this.scheduleManager);
        
        console.log('[One-Click Blog Controller] Creating NextUpPanel...');
        this.nextUpPanel = new NextUpPanel();
        console.log('[One-Click Blog Controller] NextUpPanel created:', this.nextUpPanel);
        
        console.log('[One-Click Blog Controller] Creating PipelineManager...');
        this.pipelineManager = new PipelineManager();
        console.log('[One-Click Blog Controller] PipelineManager created:', this.pipelineManager);
        
        console.log('[One-Click Blog Controller] Creating AutomationEngine...');
        this.automationEngine = new AutomationEngine();
        console.log('[One-Click Blog Controller] AutomationEngine created:', this.automationEngine);
        console.log('[One-Click Blog Controller] AutomationEngine type:', typeof this.automationEngine);
        
        // Set up global event handlers
        console.log('[One-Click Blog Controller] Setting up global handlers...');
        this.setupGlobalHandlers();
        
        // Make modules globally accessible for HTML onclick handlers
        window.nextUpPanel = this.nextUpPanel;
        window.scheduleManager = this.scheduleManager;
        window.pipelineManager = this.pipelineManager;
        window.automationEngine = this.automationEngine;
        
        // Load initial data
        console.log('[One-Click Blog Controller] Loading initial data...');
        this.loadInitialData();
        
        console.log('[One-Click Blog Controller] ✅ Initialized successfully');
        console.log('[One-Click Blog Controller] Global showScheduleModal:', typeof window.showScheduleModal);
    }

    setupGlobalHandlers() {
        // Schedule button handler
        window.showScheduleModal = () => {
            console.log('[One-Click Blog Controller] showScheduleModal() called globally');
            console.log('[One-Click Blog Controller] scheduleManager:', this.scheduleManager);
            if (this.scheduleManager) {
                console.log('[One-Click Blog Controller] Calling scheduleManager.showScheduleModal()');
                this.scheduleManager.showScheduleModal();
            } else {
                console.error('[One-Click Blog Controller] scheduleManager is null!');
            }
        };

        // Schedule modal handlers
        window.closeScheduleModal = () => {
            this.scheduleManager.closeScheduleModal();
        };

        window.schedulePost = () => {
            this.handleSchedulePost();
        };

        // Production button handler
        window.handleProductionAction = () => {
            this.handleProductionAction();
        };
        
        // Automation handlers
        window.executeSubstage = (stage, substage) => {
            this.executeSubstage(stage, substage);
        };
        
        window.toggleAutomationMode = (stage, substage) => {
            this.toggleAutomationMode(stage, substage);
        };
        
        window.openSubstageEdit = (stage, substage) => {
            this.openSubstageEdit(stage, substage);
        };
    }

    async loadInitialData() {
        console.log('[One-Click Blog Controller] Loading initial data...');
        
        try {
            // Load next up data
            await this.nextUpPanel.loadNextUp();
            
            // Load schedule data
            await this.scheduleManager.loadCurrentSchedule();
            
            // Initialize pipeline with Next Up post ID
            const nextUpPostId = this.nextUpPanel.currentPostId;
            if (nextUpPostId) {
                console.log('[One-Click Blog Controller] Setting pipeline to Next Up post:', nextUpPostId);
                await this.pipelineManager.setPostId(nextUpPostId);
            }
            
            console.log('[One-Click Blog Controller] Initial data loaded');
        } catch (error) {
            console.error('[One-Click Blog Controller] Error loading initial data:', error);
        }
    }

    async handleSchedulePost() {
        const dateInput = document.getElementById('publish-date');
        const timeInput = document.getElementById('publish-time');
        
        if (!dateInput || !timeInput) {
            console.error('[One-Click Blog Controller] Schedule inputs not found');
            return;
        }

        const newDate = dateInput.value;
        const newTime = timeInput.value;
        
        if (!newDate || !newTime) {
            console.error('[One-Click Blog Controller] Missing date or time');
            return;
        }

        console.log('[One-Click Blog Controller] Scheduling post for:', newDate, newTime);
        
        const success = await this.scheduleManager.updateSchedule(newDate, newTime);
        
        if (success) {
            this.showNotification('Schedule updated successfully!', 'success');
        } else {
            this.showNotification('Failed to update schedule', 'error');
        }
    }

    handleProductionAction() {
        const productionBtn = document.querySelector('.production-btn');
        if (!productionBtn) return;
        
        const btnText = productionBtn.querySelector('.btn-text').textContent;
        
        switch (btnText) {
            case 'Start Production':
                this.startProduction();
                break;
            case 'View Progress':
                this.viewProgress();
                break;
            case 'Completed':
                this.viewCompleted();
                break;
        }
    }

    startProduction() {
        console.log('[One-Click Blog Controller] Starting production...');
        this.showNotification('Production started!', 'success');
        // This would trigger the automation pipeline
    }

    viewProgress() {
        console.log('[One-Click Blog Controller] Viewing progress...');
        this.showNotification('Opening progress view...', 'info');
        // This would open a detailed progress modal
    }

    viewCompleted() {
        console.log('[One-Click Blog Controller] Viewing completed post...');
        this.showNotification('Opening completed post...', 'info');
        // This would open the completed post
    }

    showNotification(message, type = 'info') {
        // Simple notification system - could be enhanced
        console.log(`[One-Click Blog Controller] ${type.toUpperCase()}: ${message}`);
        
        // Create a simple notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            border-radius: 4px;
            z-index: 10000;
            font-size: 14px;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    /**
     * Execute a substage
     */
    async executeSubstage(stage, substage) {
        console.log(`[One-Click Blog Controller] Executing ${stage}/${substage}`);
        
        if (!this.automationEngine) {
            console.error('[One-Click Blog Controller] AutomationEngine not initialized');
            return;
        }
        
        const postId = this.pipelineManager?.currentPostId || this.nextUpPanel?.currentPostId;
        if (!postId) {
            console.error('[One-Click Blog Controller] No post ID available');
            this.showNotification('No post selected', 'error');
            return;
        }
        
        try {
            this.showNotification(`Running ${substage}...`, 'info');
            
            const result = await this.automationEngine.executeSubstage(stage, substage, postId);
            
            if (result.success) {
                this.showNotification(`${substage} completed successfully!`, 'success');
                // Refresh pipeline data
                if (this.pipelineManager) {
                    await this.pipelineManager.loadPipelineData(postId);
                }
            } else {
                this.showNotification(`Failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('[One-Click Blog Controller] Error executing substage:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    /**
     * Toggle automation mode for a substage
     */
    async toggleAutomationMode(stage, substage) {
        console.log(`[One-Click Blog Controller] Toggling automation mode for ${stage}/${substage}`);
        console.log('[One-Click Blog Controller] automationEngine:', this.automationEngine);
        console.log('[One-Click Blog Controller] automationEngine type:', typeof this.automationEngine);
        
        if (!this.automationEngine) {
            console.error('[One-Click Blog Controller] AutomationEngine not initialized');
            return;
        }
        
        const currentMode = this.automationEngine.getAutomationMode(stage, substage);
        const modes = ['manual', 'automatic', 'hold'];
        const currentIndex = modes.indexOf(currentMode);
        const nextMode = modes[(currentIndex + 1) % modes.length];
        
        try {
            const success = await this.automationEngine.updateAutomationMode(stage, substage, nextMode);
            
            if (success) {
                this.updateAutomationModeDisplay(stage, substage, nextMode);
                this.showNotification(`${substage} set to ${nextMode}`, 'success');
            } else {
                this.showNotification(`Failed to update ${substage} mode`, 'error');
            }
        } catch (error) {
            console.error('[One-Click Blog Controller] Error toggling automation mode:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    /**
     * Update automation mode display in UI
     */
    updateAutomationModeDisplay(stage, substage, mode) {
        const elementId = `automation-mode-${stage}-${substage}`;
        const element = document.getElementById(elementId);
        
        if (element) {
            element.textContent = this.automationEngine.getModeDisplayText(mode);
            element.className = `automation-mode ${this.automationEngine.getModeCssClass(mode)}`;
        }
    }
    
    /**
     * Open substage edit page
     */
    openSubstageEdit(stage, substage) {
        const postId = this.pipelineManager?.currentPostId || this.nextUpPanel?.currentPostId;
        if (!postId) {
            console.error('[One-Click Blog Controller] No post ID available');
            this.showNotification('No post selected', 'error');
            return;
        }
        
        // Map substages to their edit URLs
        const substageUrls = {
            'planning': {
                'topic_brainstorming': `/planning/posts/${postId}/concept/brainstorm`,
                'section_structure': `/planning/posts/${postId}/concept/section-structure`,
                'topic_allocation': `/planning/posts/${postId}/concept/topic-allocation`,
                'titling': `/planning/posts/${postId}/concept/titling`,
                'outline': `/planning/posts/${postId}/concept/outline`
            },
            'authoring': {
                'author_first_drafts': `/authoring/posts/${postId}/sections/author-first-drafts`,
                'fix_language': `/authoring/posts/${postId}/sections/fix-language`,
                'image_concepts': `/authoring/posts/${postId}/sections/image-concepts`,
                'image_prompts': `/authoring/posts/${postId}/sections/image-prompts`
            },
            'imaging': {
                'image_generation': `/imaging/posts/${postId}/sections`,
                'optimize_images': `/imaging/posts/${postId}/optimize`
            }
        };
        
        const url = substageUrls[stage]?.[substage];
        if (url) {
            window.location.href = url;
        } else {
            console.error('[One-Click Blog Controller] Unknown substage:', stage, substage);
            this.showNotification(`Edit page not found for ${substage}`, 'error');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.oneClickBlogController = new OneClickBlogController();
});
