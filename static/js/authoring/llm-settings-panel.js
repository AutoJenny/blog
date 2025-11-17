/**
 * LLM Settings Panel - Modular Component
 * Self-contained module for managing LLM settings with event-driven architecture
 */

class LLMSettingsPanel {
    constructor(options = {}) {
        this.containerId = options.containerId || 'llm-settings-panel';
        this.storageKey = options.storageKey || 'llm-settings';
        
        // Callbacks for external communication
        this.callbacks = {
            onSettingsChange: options.onSettingsChange || (() => {}),
            onProviderChange: options.onProviderChange || (() => {}),
            onModelChange: options.onModelChange || (() => {}),
            onParameterChange: options.onParameterChange || (() => {})
        };
        
        // DOM elements
        this.providerSelect = null;
        this.modelSelect = null;
        this.temperatureSlider = null;
        this.temperatureValue = null;
        this.maxTokensInput = null;
        this.providerInfo = null;
        this.settingsTitle = null;
        
        this.init();
    }

    init() {
        this.bindElements();
        this.setupEventListeners();
        this.setupSliderDisplays();
        this.loadSettings();
        this.updateProviderInfo();
        this.setupAccordion();
    }

    bindElements() {
        this.providerSelect = document.getElementById('llm-provider-select');
        this.modelSelect = document.getElementById('llm-model-select');
        this.temperatureSlider = document.getElementById('temperature');
        this.temperatureValue = document.getElementById('temperature-value');
        this.maxTokensInput = document.getElementById('max-tokens');
        this.providerInfo = document.getElementById('llm-provider-info');
        this.settingsTitle = document.getElementById('settings-title');
    }

    setupEventListeners() {
        // Provider change handler
        this.providerSelect?.addEventListener('change', () => {
            this.updateModelOptions();
            this.updateProviderInfo();
            this.saveSettings();
            this.callbacks.onProviderChange(this.getSettings());
            this.callbacks.onSettingsChange(this.getSettings());
        });

        // Model change handler
        this.modelSelect?.addEventListener('change', () => {
            this.updateProviderInfo();
            this.saveSettings();
            this.callbacks.onModelChange(this.getSettings());
            this.callbacks.onSettingsChange(this.getSettings());
        });

        // Temperature slider handler
        this.temperatureSlider?.addEventListener('input', () => {
            this.updateTemperatureDisplay();
            this.updateProviderInfo();
            this.saveSettings();
            this.callbacks.onParameterChange(this.getSettings());
            this.callbacks.onSettingsChange(this.getSettings());
        });

        // Max tokens handler
        this.maxTokensInput?.addEventListener('change', () => {
            this.updateProviderInfo();
            this.saveSettings();
            this.callbacks.onParameterChange(this.getSettings());
            this.callbacks.onSettingsChange(this.getSettings());
        });
    }

    setupSliderDisplays() {
        // Temperature slider display
        if (this.temperatureSlider && this.temperatureValue) {
            this.temperatureSlider.addEventListener('input', () => {
                this.temperatureValue.textContent = this.temperatureSlider.value;
            });
        }
    }

    updateModelOptions() {
        const provider = this.providerSelect?.value;
        
        if (!this.modelSelect) return;

        // Clear existing options
        this.modelSelect.innerHTML = '';

        // Add provider-specific models
        if (provider === 'Ollama') {
            this.addModelOption('llama3.2:latest', 'llama3.2:latest');
            this.addModelOption('llama3.1:latest', 'llama3.1:latest');
            this.addModelOption('codellama:latest', 'codellama:latest');
        } else if (provider === 'OpenAI') {
            this.addModelOption('gpt-4', 'GPT-4');
            this.addModelOption('gpt-3.5-turbo', 'GPT-3.5 Turbo');
            this.addModelOption('gpt-4-turbo', 'GPT-4 Turbo');
        }
    }

    addModelOption(value, text) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        this.modelSelect?.appendChild(option);
    }

    updateTemperatureDisplay() {
        if (this.temperatureValue && this.temperatureSlider) {
            this.temperatureValue.textContent = this.temperatureSlider.value;
        }
    }

    getSettings() {
        return {
            provider: this.providerSelect?.value || 'Ollama',
            model: this.modelSelect?.value || 'llama3.2:latest',
            temperature: parseFloat(this.temperatureSlider?.value || '0.7'),
            maxTokens: parseInt(this.maxTokensInput?.value || '2000')
        };
    }

    setSettings(settings) {
        if (settings.provider) {
            this.providerSelect.value = settings.provider;
            this.updateModelOptions();
        }
        if (settings.model) {
            this.modelSelect.value = settings.model;
        }
        if (settings.temperature) {
            this.temperatureSlider.value = settings.temperature;
            this.updateTemperatureDisplay();
        }
        if (settings.maxTokens) {
            this.maxTokensInput.value = settings.maxTokens;
        }
    }

    saveSettings() {
        // Settings are not persisted since localStorage is banned
        const settings = this.getSettings();
        console.log('[LLM Settings Panel] Settings updated (not persisted):', settings);
    }

    loadSettings() {
        // Use default settings since localStorage is banned
        const defaultSettings = {
            provider: 'Ollama',
            model: 'llama3.2:latest',
            temperature: 0.7,
            maxTokens: 2000
        };
        
        this.setSettings(defaultSettings);
        console.log('[LLM Settings Panel] Default settings loaded:', defaultSettings);
    }

    updateProviderInfo() {
        const settings = this.getSettings();
        
        if (this.providerInfo) {
            this.providerInfo.innerHTML = `
                <strong>Provider:</strong> ${settings.provider}<br>
                <strong>Model:</strong> ${settings.model}<br>
                <strong>Temperature:</strong> ${settings.temperature}<br>
                <strong>Max Tokens:</strong> ${settings.maxTokens}
            `;
        }
        
        // Update the panel title
        if (this.settingsTitle) {
            this.settingsTitle.textContent = `${settings.provider} - ${settings.model}`;
        }
    }

    setupAccordion() {
        this.restoreAccordionState();
    }

    restoreAccordionState() {
        const savedState = sessionStorage.getItem('llm-settings-accordion-state');
        const content = document.getElementById('llm-settings-accordion-content');
        const icon = document.getElementById('llm-settings-accordion-icon');
        
        if (content && icon) {
            if (savedState === 'open') {
                content.style.display = 'block';
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            } else {
                content.style.display = 'none';
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            }
        }
    }

    toggleAccordion() {
        const content = document.getElementById('llm-settings-accordion-content');
        const icon = document.getElementById('llm-settings-accordion-icon');
        
        if (!content || !icon) return;
        
        const isCollapsed = content.style.display === 'none' || content.style.display === '';
        
        if (isCollapsed) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
            sessionStorage.setItem('llm-settings-accordion-state', 'open');
        } else {
            content.style.display = 'none';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
            sessionStorage.setItem('llm-settings-accordion-state', 'closed');
        }
    }

    // Public API methods
    getCurrentSettings() {
        return this.getSettings();
    }

    updateSettings(settings) {
        this.setSettings(settings);
        this.updateProviderInfo();
        this.saveSettings();
    }

    resetToDefaults() {
        const defaults = {
            provider: 'Ollama',
            model: 'llama3.2:latest',
            temperature: 0.7,
            maxTokens: 2000
        };
        this.updateSettings(defaults);
    }
}

// Accordion function for settings panel
function toggleLLMSettingsAccordion() {
    const content = document.getElementById('settings-accordion-content');
    const icon = document.getElementById('settings-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    }
}

// Initialize LLM Settings Panel when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the LLM Settings Panel
    const llmSettingsPanel = new LLMSettingsPanel({
        containerId: 'llm-settings-panel',
        storageKey: 'llm-settings'
    });
    
    // Make it globally accessible if needed
    window.llmSettingsPanel = llmSettingsPanel;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LLMSettingsPanel;
}
