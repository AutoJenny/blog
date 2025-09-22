/**
 * Prompt Manager Module
 *
 * Responsibilities:
 * - Handle prompt persistence to database
 * - Update prompt state when selections change
 * - Provide prompt management API
 *
 * Dependencies: logger.js, config-manager.js
 * Dependents: ui-config.js
 *
 * @version 1.0
 */

/**
 * Prompt Manager class
 */
class PromptManager {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
    }

    /**
     * Initialize the prompt manager
     */
    async initialize(context) {
        this.logger.trace('promptManager', 'initialize', 'enter');
        this.context = context;
        this.initialized = true;
        this.logger.info('promptManager', 'Prompt manager initialized');
        this.logger.trace('promptManager', 'initialize', 'exit');
    }

    /**
     * Save step settings to database
     */
    async saveStepSettings() {
        this.logger.trace('promptManager', 'saveStepSettings', 'enter');
        
        if (CONFIG_STATE.saving) {
            this.logger.warn('promptManager', 'Already saving, skipping');
            return;
        }
        
        CONFIG_STATE.saving = true;
        
        try {
            if (!this.context) {
                throw new Error('Context not initialized');
            }
            const { post_id, step_id } = this.context;
            const { taskPromptId, systemPromptId } = CONFIG_STATE.stepConfig;
            
            this.logger.debug('promptManager', `Saving step settings with step_id: ${step_id}, post_id: ${post_id}`);
            this.logger.debug('promptManager', `Context:`, this.context);
            
            const response = await fetch('/api/workflow/step-settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    post_id,
                    step_id,
                    task_prompt_id: taskPromptId,
                    system_prompt_id: systemPromptId
                })
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.logger.info('promptManager', 'Step settings saved successfully');
            
        } catch (error) {
            this.logger.error('promptManager', 'Failed to save step settings:', error);
            throw error;
        } finally {
            CONFIG_STATE.saving = false;
        }
        
        this.logger.trace('promptManager', 'saveStepSettings', 'exit');
    }

    /**
     * Set task prompt
     */
    async setTaskPrompt(promptId) {
        this.logger.debug('promptManager', `Setting task prompt to: ${promptId}`);
        
        CONFIG_STATE.stepConfig.taskPromptId = promptId;
        
        // Find the prompt text
        const action = CONFIG_STATE.actions.find(a => a.id == promptId);
        if (action) {
            CONFIG_STATE.stepConfig.taskPromptText = action.prompt_template;
            this.logger.debug('promptManager', `Found task prompt text: ${action.prompt_template?.substring(0, 50)}...`);
        } else {
            this.logger.warn('promptManager', `No action found for ID: ${promptId}`);
            CONFIG_STATE.stepConfig.taskPromptText = '';
        }
        
        // Auto-save
        await this.saveStepSettings();
    }

    /**
     * Set system prompt
     */
    async setSystemPrompt(promptId) {
        this.logger.debug('promptManager', `Setting system prompt to: ${promptId}`);
        this.logger.debug('promptManager', `Available system prompts:`, CONFIG_STATE.systemPrompts.map(p => ({id: p.id, name: p.name})));
        
        CONFIG_STATE.stepConfig.systemPromptId = promptId;
        
        // Find the prompt text
        const prompt = CONFIG_STATE.systemPrompts.find(p => p.id == promptId);
        if (prompt) {
            CONFIG_STATE.stepConfig.systemPromptText = prompt.prompt_text;
            this.logger.debug('promptManager', `Found system prompt text: ${prompt.prompt_text?.substring(0, 50)}...`);
            this.logger.debug('promptManager', `Updated CONFIG_STATE.stepConfig.systemPromptText to: ${CONFIG_STATE.stepConfig.systemPromptText?.substring(0, 50)}...`);
        } else {
            this.logger.warn('promptManager', `No system prompt found for ID: ${promptId}`);
            CONFIG_STATE.stepConfig.systemPromptText = '';
        }
        
        // Auto-save
        await this.saveStepSettings();
        this.logger.debug('promptManager', 'setSystemPrompt completed');
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('promptManager', 'Destroying prompt manager');
        this.initialized = false;
    }
}

// Create and export global instance
const promptManager = new PromptManager();

// Register the module
window.registerLLMModule('promptManager', promptManager); 