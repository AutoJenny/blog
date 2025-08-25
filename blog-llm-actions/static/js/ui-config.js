/**
 * UI Configuration Manager - Handles UI updates and event listeners
 */

class UIConfig {
    constructor() {
        this.logger = window.logger || console;
        this.initialized = false;
        this.eventListenersAttached = false;
    }

    /**
     * Initialize UI configuration
     */
    async initialize() {
        this.logger.trace('uiConfig', 'initialize', 'enter');
        
        if (this.initialized) {
            this.logger.warn('uiConfig', 'Already initialized, skipping');
            return;
        }

        try {
            // Wait for config manager to be loaded
            if (!configManager || !configManager.isLoaded()) {
                this.logger.warn('uiConfig', 'Config manager not ready, waiting...');
                // Wait for config to be loaded
                while (!configManager || !configManager.isLoaded()) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
            }

            // Populate dropdowns and attach event listeners
            this.populateDropdowns();
            this.attachEventListeners();
            this.updateUI();
            
            this.initialized = true;
            this.logger.info('uiConfig', 'UI configuration initialized successfully');
            
        } catch (error) {
            this.logger.error('uiConfig', 'Failed to initialize UI configuration:', error);
            throw error;
        }
        
        this.logger.trace('uiConfig', 'initialize', 'exit');
    }

    /**
     * Populate all dropdowns with available options
     */
    populateDropdowns() {
        this.logger.debug('uiConfig', 'Populating dropdowns...');
        
        // Populate task prompt dropdown
        const actionSelect = document.getElementById('action-select');
        if (actionSelect) {
            actionSelect.innerHTML = '<option value="">Select a task prompt...</option>';
            CONFIG_STATE.actions.forEach(action => {
                const option = document.createElement('option');
                option.value = action.id;
                option.textContent = action.field_name;
                actionSelect.appendChild(option);
            });
            this.logger.debug('uiConfig', `Populated action dropdown with ${CONFIG_STATE.actions.length} options`);
        }

        // Populate system prompt dropdown
        const systemPromptSelect = document.getElementById('system-prompt-select');
        if (systemPromptSelect) {
            systemPromptSelect.innerHTML = '<option value="">Select a system prompt...</option>';
            CONFIG_STATE.systemPrompts.forEach(prompt => {
                const option = document.createElement('option');
                option.value = prompt.id;
                option.textContent = prompt.name;
                systemPromptSelect.appendChild(option);
            });
            this.logger.debug('uiConfig', `Populated system prompt dropdown with ${CONFIG_STATE.systemPrompts.length} options`);
        }
    }

    /**
     * Attach event listeners to UI elements
     */
    attachEventListeners() {
        if (this.eventListenersAttached) {
            this.logger.warn('uiConfig', 'Event listeners already attached, skipping');
            return;
        }

        this.logger.debug('uiConfig', 'Attaching event listeners...');

        // Task prompt selection
        const actionSelect = document.getElementById('action-select');
        if (actionSelect) {
            actionSelect.addEventListener('change', async (event) => {
                const promptId = event.target.value;
                if (promptId) {
                    try {
                        await promptManager.setTaskPrompt(promptId);
                        this.logger.debug('uiConfig', 'Task prompt changed successfully');
                        
                        // Emit event for message manager
                        document.dispatchEvent(new CustomEvent('taskPromptChanged', {
                            detail: { promptId, promptText: CONFIG_STATE.stepConfig.taskPromptText }
                        }));
                    } catch (error) {
                        this.logger.error('uiConfig', 'Failed to set task prompt:', error);
                        // Reset dropdown to previous value
                        event.target.value = CONFIG_STATE.stepConfig.taskPromptId || '';
                    }
                }
            });
        }

        // System prompt selection
        const systemPromptSelect = document.getElementById('system-prompt-select');
        if (systemPromptSelect) {
            systemPromptSelect.addEventListener('change', async (event) => {
                const promptId = event.target.value;
                if (promptId) {
                    try {
                        await promptManager.setSystemPrompt(promptId);
                        this.logger.debug('uiConfig', 'System prompt changed successfully');
                        
                        // Emit event for message manager
                        document.dispatchEvent(new CustomEvent('systemPromptChanged', {
                            detail: { promptId, promptText: CONFIG_STATE.stepConfig.systemPromptText }
                        }));
                    } catch (error) {
                        this.logger.error('uiConfig', 'Failed to set system prompt:', error);
                        // Reset dropdown to previous value
                        event.target.value = CONFIG_STATE.stepConfig.systemPromptId || '';
                    }
                }
            });
        }

        this.eventListenersAttached = true;
        this.logger.debug('uiConfig', 'Event listeners attached successfully');
    }

    /**
     * Update UI to reflect current state
     */
    updateUI() {
        this.logger.debug('uiConfig', 'Updating UI...');
        
        // Update task prompt dropdown selection
        const actionSelect = document.getElementById('action-select');
        if (actionSelect) {
            actionSelect.value = CONFIG_STATE.stepConfig.taskPromptId || '';
        }

        // Update system prompt dropdown selection
        const systemPromptSelect = document.getElementById('system-prompt-select');
        if (systemPromptSelect) {
            systemPromptSelect.value = CONFIG_STATE.stepConfig.systemPromptId || '';
        }

        // Update task prompt display
        this.updateTaskPromptDisplay();

        // Update system prompt display
        this.updateSystemPromptDisplay();

        this.logger.debug('uiConfig', 'UI updated successfully');
    }

    /**
     * Update task prompt display
     */
    updateTaskPromptDisplay() {
        const display = document.getElementById('prompt-display');
        if (display) {
            const text = CONFIG_STATE.stepConfig.taskPromptText || '';
            display.textContent = text;
            display.style.display = text ? 'block' : 'none';
            this.logger.debug('uiConfig', `Updated task prompt display: ${text.substring(0, 50)}...`);
        }
    }

    /**
     * Update system prompt display
     */
    updateSystemPromptDisplay() {
        const display = document.getElementById('system-prompt-display');
        if (display) {
            const text = CONFIG_STATE.stepConfig.systemPromptText || '';
            display.textContent = text;
            display.style.display = text ? 'block' : 'none';
            this.logger.debug('uiConfig', `Updated system prompt display: ${text.substring(0, 50)}...`);
        }
    }

    /**
     * Refresh UI data
     */
    async refresh() {
        this.logger.info('uiConfig', 'Refreshing UI...');
        
        try {
            // Refresh config data
            await configManager.refresh();
            
            // Update UI
            this.populateDropdowns();
            this.updateUI();
            
            this.logger.info('uiConfig', 'UI refreshed successfully');
        } catch (error) {
            this.logger.error('uiConfig', 'Failed to refresh UI:', error);
            throw error;
        }
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('uiConfig', 'Destroying UI configuration');
        this.initialized = false;
        this.eventListenersAttached = false;
    }
}

// Create and export global instance
const uiConfig = new UIConfig();
window.uiConfig = uiConfig;

// Register module with orchestrator
window.registerLLMModule('uiConfig', uiConfig);

// Log initialization
if (window.logger) {
    window.logger.info('uiConfig', 'UI Config Module loaded');
} 