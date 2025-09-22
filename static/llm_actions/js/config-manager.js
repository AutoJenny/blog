/**
 * Configuration Manager - Centralized state management for LLM actions
 */

// Global configuration state
const CONFIG_STATE = {
    loaded: false,
    loading: false,
    actions: [],
    systemPrompts: [],
    stepConfig: {
        taskPromptId: null,
        systemPromptId: null,
        taskPromptText: '',
        systemPromptText: ''
    },
    saving: false
};

class ConfigManager {
    constructor() {
        this.logger = window.logger || console;
        this.initialized = false;
        this.context = null;
    }

    /**
     * Initialize the configuration manager
     * This is the ONLY entry point for loading data
     */
    async initialize(context) {
        this.logger.trace('configManager', 'initialize', 'enter');
        
        if (this.initialized) {
            this.logger.warn('configManager', 'Already initialized, skipping');
            return;
        }

        this.context = context;
        this.initialized = true;

        try {
            // Load all data in sequence to ensure consistency
            await this.loadAllData();
            CONFIG_STATE.loaded = true;
            this.logger.info('configManager', 'Configuration manager initialized successfully');
        } catch (error) {
            this.logger.error('configManager', 'Failed to initialize:', error);
            throw error;
        }

        this.logger.trace('configManager', 'initialize', 'exit');
    }

    /**
     * Load all configuration data in the correct order
     */
    async loadAllData() {
        this.logger.debug('configManager', 'Loading all configuration data...');
        
        if (CONFIG_STATE.loading) {
            this.logger.warn('configManager', 'Already loading, waiting...');
            // Wait for current loading to complete
            while (CONFIG_STATE.loading) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            return;
        }

        CONFIG_STATE.loading = true;

        try {
            // Step 1: Load available actions and system prompts
            await Promise.all([
                this.loadActions(),
                this.loadSystemPrompts()
            ]);

            // Step 2: Load step-specific settings (depends on actions/prompts being loaded)
            await this.loadStepSettings();

            this.logger.info('configManager', 'All configuration data loaded successfully');
        } catch (error) {
            this.logger.error('configManager', 'Failed to load configuration data:', error);
            throw error;
        } finally {
            CONFIG_STATE.loading = false;
        }
    }

    /**
     * Load available LLM actions
     */
    async loadActions() {
        this.logger.debug('configManager', 'Loading actions...');
        
        try {
            const response = await fetch('/api/llm/actions');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const actions = await response.json();
            CONFIG_STATE.actions = actions;
            
            this.logger.info('configManager', `Loaded ${actions.length} actions`);
            
        } catch (error) {
            this.logger.error('configManager', 'Failed to load actions:', error);
            CONFIG_STATE.actions = [];
            throw error;
        }
    }

    /**
     * Load available system prompts
     */
    async loadSystemPrompts() {
        this.logger.debug('configManager', 'Loading system prompts...');
        
        try {
            const response = await fetch('/api/llm/system-prompts');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const prompts = await response.json();
            CONFIG_STATE.systemPrompts = prompts;
            
            this.logger.info('configManager', `Loaded ${prompts.length} system prompts`);
            
        } catch (error) {
            this.logger.error('configManager', 'Failed to load system prompts:', error);
            CONFIG_STATE.systemPrompts = [];
            throw error;
        }
    }

    /**
     * Load step settings and populate prompt text
     */
    async loadStepSettings() {
        this.logger.debug('configManager', 'Loading step settings...');
        
        try {
            const { post_id, step_id } = this.context;
            
            if (!step_id) {
                throw new Error('No step_id available in context');
            }
            
            const response = await fetch(`/api/workflow/step-settings?post_id=${post_id}&step_id=${step_id}`);
            
            if (response.ok) {
                const settings = await response.json();
                
                // Set the IDs
                CONFIG_STATE.stepConfig.taskPromptId = settings.task_prompt_id;
                CONFIG_STATE.stepConfig.systemPromptId = settings.system_prompt_id;
                
                // Populate the text content
                this.populatePromptText();
                
                this.logger.info('configManager', 'Step settings loaded and populated');
            } else {
                // No saved settings - initialize with empty values
                CONFIG_STATE.stepConfig = {
                    taskPromptId: null,
                    systemPromptId: null,
                    taskPromptText: '',
                    systemPromptText: ''
                };
                this.logger.info('configManager', 'No saved settings found, initialized with empty values');
            }
            
        } catch (error) {
            this.logger.error('configManager', 'Failed to load step settings:', error);
            // Initialize with empty values on error
            CONFIG_STATE.stepConfig = {
                taskPromptId: null,
                systemPromptId: null,
                taskPromptText: '',
                systemPromptText: ''
            };
            throw error;
        }
    }

    /**
     * Populate prompt text from loaded actions and system prompts
     * This is called after loading step settings to set the actual text content
     */
    populatePromptText() {
        this.logger.debug('configManager', 'Populating prompt text...');
        
        // Populate task prompt text
        if (CONFIG_STATE.stepConfig.taskPromptId) {
            const action = CONFIG_STATE.actions.find(a => a.id == CONFIG_STATE.stepConfig.taskPromptId);
            if (action) {
                CONFIG_STATE.stepConfig.taskPromptText = action.prompt_template || '';
                this.logger.debug('configManager', `Populated task prompt text for ID ${CONFIG_STATE.stepConfig.taskPromptId}: ${CONFIG_STATE.stepConfig.taskPromptText.substring(0, 50)}...`);
            } else {
                this.logger.warn('configManager', `No action found for task prompt ID: ${CONFIG_STATE.stepConfig.taskPromptId}`);
                CONFIG_STATE.stepConfig.taskPromptText = '';
            }
        }
        
        // Populate system prompt text
        if (CONFIG_STATE.stepConfig.systemPromptId) {
            const prompt = CONFIG_STATE.systemPrompts.find(p => p.id == CONFIG_STATE.stepConfig.systemPromptId);
            if (prompt) {
                // Use system_prompt field consistently
                CONFIG_STATE.stepConfig.systemPromptText = prompt.system_prompt || '';
                this.logger.debug('configManager', `Populated system prompt text for ID ${CONFIG_STATE.stepConfig.systemPromptId}: ${CONFIG_STATE.stepConfig.systemPromptText.substring(0, 50)}...`);
            } else {
                this.logger.warn('configManager', `No system prompt found for ID: ${CONFIG_STATE.stepConfig.systemPromptId}`);
                CONFIG_STATE.stepConfig.systemPromptText = '';
            }
        }
    }

    /**
     * Set task prompt - unified method for setting task prompt
     */
    async setTaskPrompt(promptId) {
        this.logger.debug('configManager', `Setting task prompt to: ${promptId}`);
        
        if (!CONFIG_STATE.loaded) {
            throw new Error('Configuration not loaded. Call initialize() first.');
        }
        
        // Find the action
        const action = CONFIG_STATE.actions.find(a => a.id == promptId);
        if (!action) {
            throw new Error(`No action found for ID: ${promptId}`);
        }
        
        // Update state
        CONFIG_STATE.stepConfig.taskPromptId = promptId;
        CONFIG_STATE.stepConfig.taskPromptText = action.prompt_template || '';
        
        this.logger.info('configManager', `Task prompt set to: ${action.field_name} (${promptId})`);
        
        // Trigger UI update
        this.notifyUIUpdate();
    }

    /**
     * Set system prompt - unified method for setting system prompt
     */
    async setSystemPrompt(promptId) {
        this.logger.debug('configManager', `Setting system prompt to: ${promptId}`);
        
        if (!CONFIG_STATE.loaded) {
            throw new Error('Configuration not loaded. Call initialize() first.');
        }
        
        // Find the prompt
        const prompt = CONFIG_STATE.systemPrompts.find(p => p.id == promptId);
        if (!prompt) {
            throw new Error(`No system prompt found for ID: ${promptId}`);
        }
        
        // Update state
        CONFIG_STATE.stepConfig.systemPromptId = promptId;
        CONFIG_STATE.stepConfig.systemPromptText = prompt.system_prompt || '';
        
        this.logger.info('configManager', `System prompt set to: ${prompt.name} (${promptId})`);
        
        // Trigger UI update
        this.notifyUIUpdate();
    }

    /**
     * Notify UI modules to update
     */
    notifyUIUpdate() {
        if (window.LLM_STATE && window.LLM_STATE.modules) {
            if (window.LLM_STATE.modules.uiConfig) {
                window.LLM_STATE.modules.uiConfig.updateUI();
            }
        }
    }

    /**
     * Get current configuration
     */
    getConfig() {
        return { ...CONFIG_STATE };
    }

    /**
     * Get task prompt text
     */
    getTaskPrompt() {
        return CONFIG_STATE.stepConfig.taskPromptText || '';
    }

    /**
     * Get system prompt text
     */
    getSystemPrompt() {
        return CONFIG_STATE.stepConfig.systemPromptText || '';
    }

    /**
     * Get full prompt (system + task)
     */
    getFullPrompt() {
        const system = CONFIG_STATE.stepConfig.systemPromptText;
        const task = CONFIG_STATE.stepConfig.taskPromptText;
        
        if (system && task) {
            return `${system}\n\n${task}`;
        }
        return task || system || '';
    }

    /**
     * Check if configuration is complete
     */
    isConfigured() {
        return !!(CONFIG_STATE.stepConfig.taskPromptId && CONFIG_STATE.stepConfig.systemPromptId);
    }

    /**
     * Check if data is loaded
     */
    isLoaded() {
        return CONFIG_STATE.loaded;
    }

    /**
     * Refresh configuration data
     */
    async refresh() {
        this.logger.info('configManager', 'Refreshing configuration data');
        CONFIG_STATE.loaded = false;
        await this.loadAllData();
        CONFIG_STATE.loaded = true;
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('configManager', 'Destroying configuration manager');
        this.initialized = false;
        CONFIG_STATE.loaded = false;
        CONFIG_STATE.loading = false;
    }
}

// Create and export global instance
const configManager = new ConfigManager();
window.configManager = configManager;
window.CONFIG_STATE = CONFIG_STATE;

// Register module with orchestrator
window.registerLLMModule('configManager', configManager);

// Log initialization
if (window.logger) {
    window.logger.info('configManager', 'Configuration Manager Module loaded');
} 