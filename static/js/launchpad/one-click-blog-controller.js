/**
 * One-Click Blog Main Controller
 * Orchestrates all micro-modules for the One-Click Blog system
 */

class OneClickBlogController {
    constructor() {
        this.scheduleManager = null;
        this.nextUpPanel = null;
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
        
        // Set up global event handlers
        console.log('[One-Click Blog Controller] Setting up global handlers...');
        this.setupGlobalHandlers();
        
        // Make modules globally accessible for HTML onclick handlers
        window.nextUpPanel = this.nextUpPanel;
        window.scheduleManager = this.scheduleManager;
        
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
    }

    async loadInitialData() {
        console.log('[One-Click Blog Controller] Loading initial data...');
        
        try {
            // Load next up data
            await this.nextUpPanel.loadNextUp();
            
            // Load schedule data
            await this.scheduleManager.loadCurrentSchedule();
            
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
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.oneClickBlogController = new OneClickBlogController();
});
