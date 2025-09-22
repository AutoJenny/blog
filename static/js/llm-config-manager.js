/**
 * LLM Configuration Manager Module
 * Handles loading and displaying LLM settings for the current workflow step
 */

class LLMConfigManager {
    constructor() {
        this.logger = window.LLM_STATE?.logger || console;
        this.currentStepId = null;
        this.currentSettings = {};
        this.providers = [];
        this.models = [];
    }

    /**
     * Initialize the LLM configuration manager
     */
    async initialize(context) {
        try {
            this.logger.info('llmConfigManager', 'Initializing LLM configuration manager...');
            
            // Get step ID from context or extract from URL
            this.currentStepId = context?.step_id || await this.extractStepIdFromURL();
            if (!this.currentStepId) {
                this.logger.warn('llmConfigManager', 'Could not extract step ID from URL');
                return;
            }
            
            // Load providers and models
            await this.loadProvidersAndModels();
            
            // Load current step settings
            await this.loadCurrentStepSettings();
            
            // Set up event listeners
            this.setupEventListeners();
            
            this.logger.info('llmConfigManager', 'LLM configuration manager initialized successfully');
        } catch (error) {
            this.logger.error('llmConfigManager', 'Failed to initialize LLM configuration manager:', error);
            throw error;
        }
    }

    /**
     * Extract step ID from current URL
     */
    async extractStepIdFromURL() {
        try {
            // URL format: /workflow/posts/{post_id}/{stage}/{substage}/{step}
            const pathParts = window.location.pathname.split('/');
            if (pathParts.length >= 7) {
                const stage = pathParts[4];
                const substage = pathParts[5];
                const step = pathParts[6];
                
                this.logger.debug('llmConfigManager', `Extracted: stage=${stage}, substage=${substage}, step=${step}`);
                
                // Query the database to get the actual step ID
                const response = await fetch(`http://localhost:5000/api/workflow/step-id?stage=${stage}&substage=${substage}&step=${step}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.step_id) {
                        this.logger.debug('llmConfigManager', `Found step ID: ${data.step_id}`);
                        return data.step_id;
                    }
                }
                
                // Fallback to a default step ID if query fails
                this.logger.warn('llmConfigManager', 'Could not find step ID, using default');
                return 1; // Default step ID
            }
            return null;
        } catch (error) {
            this.logger.error('llmConfigManager', 'Error extracting step ID:', error);
            return 1; // Default step ID
        }
    }

    /**
     * Load available providers and models
     */
    async loadProvidersAndModels() {
        try {
            // Load providers
            const providersResponse = await fetch('http://localhost:5000/api/llm/providers');
            const providersData = await providersResponse.json();
            this.providers = providersData.providers || [];
            
            // Load models
            const modelsResponse = await fetch('http://localhost:5000/api/llm/models');
            const modelsData = await modelsResponse.json();
            this.models = modelsData.models || [];
            
            this.logger.debug('llmConfigManager', `Loaded ${this.providers.length} providers and ${this.models.length} models`);
        } catch (error) {
            this.logger.error('llmConfigManager', 'Failed to load providers and models:', error);
        }
    }

    /**
     * Load LLM settings for the current step
     */
    async loadCurrentStepSettings() {
        try {
            if (!this.currentStepId) {
                this.logger.warn('llmConfigManager', 'No step ID available for loading settings');
                return;
            }
            
            const response = await fetch(`http://localhost:5000/api/step/${this.currentStepId}/llm-settings`);
            const data = await response.json();
            this.currentSettings = data.llm_settings || {};
            
            // Convert string provider/model names to IDs for dropdown compatibility
            if (this.currentSettings.provider && !this.currentSettings.provider_id) {
                const provider = this.providers.find(p => 
                    p.name.toLowerCase().includes(this.currentSettings.provider.toLowerCase()) ||
                    p.type.toLowerCase() === this.currentSettings.provider.toLowerCase()
                );
                if (provider) {
                    this.currentSettings.provider_id = provider.id;
                    this.currentSettings.provider_name = provider.name;
                    this.currentSettings.api_base = provider.api_url;
                }
            }
            
            if (this.currentSettings.model && !this.currentSettings.model_id) {
                const model = this.models.find(m => 
                    m.name === this.currentSettings.model
                );
                if (model) {
                    this.currentSettings.model_id = model.id;
                    this.currentSettings.model_name = model.name;
                }
            }
            
            // Extract parameters from nested structure if they exist
            if (this.currentSettings.parameters) {
                this.currentSettings.temperature = this.currentSettings.parameters.temperature;
                this.currentSettings.max_tokens = this.currentSettings.parameters.max_tokens;
            }
            
            this.updateDisplay();
            this.logger.debug('llmConfigManager', 'Loaded current step settings:', this.currentSettings);
        } catch (error) {
            this.logger.error('llmConfigManager', 'Failed to load current step settings:', error);
            // Set default values
            this.currentSettings = {
                provider_id: 1,
                provider_name: 'Ollama (local)',
                model_id: 20,
                model_name: 'llama3:latest',
                api_base: 'http://localhost:11434',
                status: 'active',
                temperature: 0.7,
                max_tokens: 1000,
                timeout: 60
            };
            this.updateDisplay();
        }
    }

    /**
     * Update the configuration display
     */
    updateDisplay() {
        try {
            // Update provider dropdown
            const providerSelect = document.getElementById('config-provider');
            if (providerSelect) {
                providerSelect.innerHTML = '<option value="">Select Provider...</option>';
                this.providers.forEach(provider => {
                    const option = document.createElement('option');
                    option.value = provider.id;
                    option.textContent = provider.name;
                    if (this.currentSettings.provider_id === provider.id) {
                        option.selected = true;
                    }
                    providerSelect.appendChild(option);
                });
            }
            
            // Update model dropdown (filtered by selected provider)
            this.updateModelDropdown();
            
            // Update API base input
            const apiBaseInput = document.getElementById('config-api-base');
            if (apiBaseInput) {
                apiBaseInput.value = this.currentSettings.api_base || '';
            }
            
            // Update status (read-only)
            const statusElement = document.getElementById('config-status');
            if (statusElement) {
                statusElement.textContent = this.currentSettings.status || 'Unknown';
            }
            
            // Update temperature input
            const temperatureInput = document.getElementById('config-temperature');
            if (temperatureInput) {
                temperatureInput.value = this.currentSettings.temperature || 0.7;
            }
            
            // Update max tokens input
            const maxTokensInput = document.getElementById('config-max-tokens');
            if (maxTokensInput) {
                maxTokensInput.value = this.currentSettings.max_tokens || 1000;
            }
            
            // Update timeout input
            const timeoutInput = document.getElementById('config-timeout');
            if (timeoutInput) {
                timeoutInput.value = this.currentSettings.timeout || 60;
            }
            
            this.logger.debug('llmConfigManager', 'Updated configuration display');
        } catch (error) {
            this.logger.error('llmConfigManager', 'Failed to update display:', error);
        }
    }

    /**
     * Update model dropdown based on selected provider
     */
    updateModelDropdown() {
        const modelSelect = document.getElementById('config-model');
        const providerSelect = document.getElementById('config-provider');
        
        if (!modelSelect || !providerSelect) return;
        
        const selectedProviderId = parseInt(providerSelect.value);
        const modelsForProvider = this.models.filter(model => model.provider_id === selectedProviderId);
        
        modelSelect.innerHTML = '<option value="">Select Model...</option>';
        modelsForProvider.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            if (this.currentSettings.model_id === model.id) {
                option.selected = true;
            }
            modelSelect.appendChild(option);
        });
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        try {
            // Provider dropdown change
            const providerSelect = document.getElementById('config-provider');
            if (providerSelect) {
                providerSelect.addEventListener('change', (e) => {
                    this.handleProviderChange(e.target.value);
                });
            }
            
            // Model dropdown change
            const modelSelect = document.getElementById('config-model');
            if (modelSelect) {
                modelSelect.addEventListener('change', (e) => {
                    this.handleModelChange(e.target.value);
                });
            }
            
            // Input field changes
            const inputs = ['config-api-base', 'config-temperature', 'config-max-tokens', 'config-timeout'];
            inputs.forEach(inputId => {
                const input = document.getElementById(inputId);
                if (input) {
                    input.addEventListener('blur', () => {
                        this.handleInputChange(inputId, input.value);
                    });
                    input.addEventListener('keypress', (e) => {
                        if (e.key === 'Enter') {
                            this.handleInputChange(inputId, input.value);
                        }
                    });
                }
            });
            
            this.logger.debug('llmConfigManager', 'Event listeners set up');
        } catch (error) {
            this.logger.error('llmConfigManager', 'Failed to set up event listeners:', error);
        }
    }

    /**
     * Get current settings
     */
    getCurrentSettings() {
        return { ...this.currentSettings };
    }

    /**
     * Update settings
     */
    async updateSettings(newSettings) {
        try {
            if (!this.currentStepId) {
                throw new Error('No step ID available for updating settings');
            }
            
            const response = await fetch(`http://localhost:5000/api/step/${this.currentStepId}/llm-settings`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    llm_settings: newSettings
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.currentSettings = { ...this.currentSettings, ...newSettings };
                this.updateDisplay();
                this.logger.info('llmConfigManager', 'Settings updated successfully');
                return true;
            } else {
                throw new Error('Failed to update settings');
            }
        } catch (error) {
            this.logger.error('llmConfigManager', 'Failed to update settings:', error);
            return false;
        }
    }

    /**
     * Get available providers
     */
    getProviders() {
        return [...this.providers];
    }

    /**
     * Get available models
     */
    getModels() {
        return [...this.models];
    }

    /**
     * Get models for a specific provider
     */
    getModelsForProvider(providerId) {
        return this.models.filter(model => model.provider_id === providerId);
    }

    /**
     * Handle provider dropdown change
     */
    async handleProviderChange(providerId) {
        try {
            if (!providerId) return;
            
            const provider = this.providers.find(p => p.id === parseInt(providerId));
            if (!provider) return;
            
            // Update current settings
            this.currentSettings.provider_id = parseInt(providerId);
            this.currentSettings.provider_name = provider.name;
            this.currentSettings.api_base = provider.api_url;
            
            // Clear model selection when provider changes
            this.currentSettings.model_id = null;
            this.currentSettings.model_name = null;
            
            // Update model dropdown
            this.updateModelDropdown();
            
            // Update API base input
            const apiBaseInput = document.getElementById('config-api-base');
            if (apiBaseInput) {
                apiBaseInput.value = provider.api_url || '';
            }
            
            // Save to database
            await this.updateSettings(this.currentSettings);
            
            this.logger.debug('llmConfigManager', `Provider changed to: ${provider.name}`);
        } catch (error) {
            this.logger.error('llmConfigManager', 'Failed to handle provider change:', error);
        }
    }

    /**
     * Handle model dropdown change
     */
    async handleModelChange(modelId) {
        try {
            if (!modelId) return;
            
            const model = this.models.find(m => m.id === parseInt(modelId));
            if (!model) return;
            
            // Update current settings
            this.currentSettings.model_id = parseInt(modelId);
            this.currentSettings.model_name = model.name;
            
            // Save to database
            await this.updateSettings(this.currentSettings);
            
            this.logger.debug('llmConfigManager', `Model changed to: ${model.name}`);
        } catch (error) {
            this.logger.error('llmConfigManager', 'Failed to handle model change:', error);
        }
    }

    /**
     * Handle input field changes
     */
    async handleInputChange(inputId, value) {
        try {
            let fieldName = '';
            let validatedValue = value;
            
            // Map input ID to field name and validate
            switch (inputId) {
                case 'config-api-base':
                    fieldName = 'api_base';
                    validatedValue = value.trim();
                    break;
                case 'config-temperature':
                    fieldName = 'temperature';
                    validatedValue = Math.max(0, Math.min(2, parseFloat(value) || 0.7));
                    break;
                case 'config-max-tokens':
                    fieldName = 'max_tokens';
                    validatedValue = Math.max(1, Math.min(100000, parseInt(value) || 1000));
                    break;
                case 'config-timeout':
                    fieldName = 'timeout';
                    validatedValue = Math.max(1, Math.min(3600, parseInt(value) || 60));
                    break;
                default:
                    return;
            }
            
            // Update current settings
            this.currentSettings[fieldName] = validatedValue;
            
            // Update input value with validated value
            const input = document.getElementById(inputId);
            if (input) {
                input.value = validatedValue;
            }
            
            // Save to database
            await this.updateSettings(this.currentSettings);
            
            this.logger.debug('llmConfigManager', `${fieldName} changed to: ${validatedValue}`);
        } catch (error) {
            this.logger.error('llmConfigManager', 'Failed to handle input change:', error);
        }
    }
}

// Create and register the module instance
const llmConfigManager = new LLMConfigManager();
window.llmConfigManager = llmConfigManager;
window.registerLLMModule('llmConfigManager', llmConfigManager); 