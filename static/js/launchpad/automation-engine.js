/**
 * Automation Engine
 * Handles execution of substages for automation
 */

class AutomationEngine {
    constructor() {
        this.settings = {};
        this.init();
    }

    init() {
        console.log('[Automation Engine] Initializing...');
        this.loadSettings();
    }

    /**
     * Load substage automation settings
     */
    async loadSettings() {
        try {
            const response = await fetch('/launchpad/one-click-blog/api/substage-settings');
            const data = await response.json();
            
            if (data.success) {
                this.settings = data.settings;
                console.log('[Automation Engine] Settings loaded:', this.settings);
            } else {
                console.error('[Automation Engine] Failed to load settings:', data.error);
            }
        } catch (error) {
            console.error('[Automation Engine] Error loading settings:', error);
        }
    }

    /**
     * Get automation mode for a substage
     */
    getAutomationMode(stage, substage) {
        return this.settings[stage]?.[substage]?.mode || 'manual';
    }

    /**
     * Update automation mode for a substage
     */
    async updateAutomationMode(stage, substage, mode) {
        try {
            const response = await fetch(`/launchpad/one-click-blog/api/substage-settings/${stage}/${substage}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ automation_mode: mode })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update local settings
                if (!this.settings[stage]) {
                    this.settings[stage] = {};
                }
                this.settings[stage][substage] = {
                    mode: mode,
                    updated_at: data.updated_at
                };
                
                console.log(`[Automation Engine] Updated ${stage}/${substage} to ${mode}`);
                return true;
            } else {
                console.error('[Automation Engine] Failed to update setting:', data.error);
                return false;
            }
        } catch (error) {
            console.error('[Automation Engine] Error updating setting:', error);
            return false;
        }
    }

    /**
     * Execute a substage (for automation)
     */
    async executeSubstage(stage, substage, postId, options = {}) {
        console.log(`[Automation Engine] Executing ${stage}/${substage} for post ${postId}`);
        
        try {
            const response = await fetch(`/launchpad/one-click-blog/api/substage-execute/${stage}/${substage}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    post_id: postId,
                    ...options
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log(`[Automation Engine] Successfully executed ${stage}/${substage}`);
                return { success: true, data: data };
            } else {
                // Handle "Hold" mode
                if (data.automation_mode === 'hold') {
                    this.showHoldAlert(stage, substage, data.error);
                }
                
                console.error(`[Automation Engine] Failed to execute ${stage}/${substage}:`, data.error);
                return { success: false, error: data.error, automation_mode: data.automation_mode };
            }
        } catch (error) {
            console.error('[Automation Engine] Error executing substage:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Show alert for "Hold" mode
     */
    showHoldAlert(stage, substage, message) {
        console.log(`[Automation Engine] Hold alert: ${message}`);
        
        // Add to header Messages system
        if (window.headerMessages) {
            window.headerMessages.addMessage({
                type: 'warning',
                title: 'Automation Blocked',
                message: message,
                stage: stage,
                substage: substage,
                timestamp: new Date().toISOString()
            });
        } else {
            // Fallback to browser notification
            alert(`Automation Blocked: ${message}`);
        }
    }

    /**
     * Execute Topic Brainstorming specifically
     */
    async executeTopicBrainstorming(postId, brainstormType = 'comprehensive') {
        return await this.executeSubstage('planning', 'topic_brainstorming', postId, {
            brainstorm_type: brainstormType
        });
    }

    /**
     * Check if a substage should run automatically
     */
    shouldRunAutomatically(stage, substage) {
        const mode = this.getAutomationMode(stage, substage);
        return mode === 'automatic';
    }

    /**
     * Check if a substage is on hold
     */
    isOnHold(stage, substage) {
        const mode = this.getAutomationMode(stage, substage);
        return mode === 'hold';
    }

    /**
     * Get automation mode display text
     */
    getModeDisplayText(mode) {
        const modeTexts = {
            'manual': 'Manual',
            'automatic': 'Auto',
            'hold': 'Hold'
        };
        return modeTexts[mode] || 'Manual';
    }

    /**
     * Get automation mode CSS class
     */
    getModeCssClass(mode) {
        const modeClasses = {
            'manual': 'manual',
            'automatic': 'automatic',
            'hold': 'hold'
        };
        return modeClasses[mode] || 'manual';
    }
}
