/**
 * Authoring LLM Settings Panel Handler
 * Manages LLM provider, model, and parameter settings
 */

class AuthoringLLMSettingsHandler {
    constructor() {
        this.providerSelect = document.getElementById('llm-provider-select');
        this.modelSelect = document.getElementById('llm-model-select');
        this.temperatureSlider = document.getElementById('temperature');
        this.temperatureValue = document.getElementById('temperature-value');
        this.maxTokensInput = document.getElementById('max-tokens');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSliderDisplays();
        this.loadSettings();
        this.updateProviderInfo();
        this.loadImagingModelSelection();
        // Update compiled preview after everything is loaded
        setTimeout(() => this.updateCompiledPreview(), 100);
    }

    setupEventListeners() {
        // Provider change handler
        this.providerSelect?.addEventListener('change', () => {
            this.updateModelOptions();
            this.updateProviderInfo();
            this.saveSettings();
        });

        // Model change handler
        this.modelSelect?.addEventListener('change', () => {
            this.updateProviderInfo();
            this.saveSettings();
        });

        // Temperature slider handler
        this.temperatureSlider?.addEventListener('input', () => {
            this.updateTemperatureDisplay();
            this.updateProviderInfo();
            this.saveSettings();
        });

        // Max tokens handler
        this.maxTokensInput?.addEventListener('change', () => {
            this.updateProviderInfo();
            this.saveSettings();
        });

        // Imaging model change handler
        const imagingModelSelect = document.getElementById('imaging-model-select');
        imagingModelSelect?.addEventListener('change', () => {
            this.updateTokenLimitInstructions();
            this.saveImagingModelSelection();
            this.updateCompiledPreview();
        });

        // System prompt change handler
        const systemPromptField = document.getElementById('system-prompt-display');
        systemPromptField?.addEventListener('blur', () => {
            this.saveSystemPrompt();
        });
        systemPromptField?.addEventListener('input', () => {
            this.updateCompiledPreview();
        });

        // Style guidelines change handler
        const styleGuidelinesField = document.getElementById('style-guidelines-display');
        styleGuidelinesField?.addEventListener('blur', () => {
            this.saveStyleGuidelines();
        });
        styleGuidelinesField?.addEventListener('input', () => {
            this.updateCompiledPreview();
        });

        // Generate button handler
        const generateBtn = document.getElementById('generate-prompt-btn');
        generateBtn?.addEventListener('click', () => {
            this.generateImagePrompt();
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
        const settings = this.getSettings();
        localStorage.setItem('authoring-llm-settings', JSON.stringify(settings));
        console.log('[LLM Settings] Settings saved:', settings);
    }

    loadSettings() {
        const saved = localStorage.getItem('authoring-llm-settings');
        if (saved) {
            try {
                const settings = JSON.parse(saved);
                this.setSettings(settings);
                console.log('[LLM Settings] Settings loaded:', settings);
            } catch (error) {
                console.error('[LLM Settings] Error loading settings:', error);
            }
        }
    }

    updateProviderInfo() {
        const settings = this.getSettings();
        const providerInfo = document.getElementById('llm-provider-info');
        const settingsTitle = document.getElementById('settings-title');
        
        if (providerInfo) {
            providerInfo.innerHTML = `
                <strong>Provider:</strong> ${settings.provider}<br>
                <strong>Model:</strong> ${settings.model}<br>
                <strong>Temperature:</strong> ${settings.temperature}<br>
                <strong>Max Tokens:</strong> ${settings.maxTokens}
            `;
        }
        
        // Update the panel title
        if (settingsTitle) {
            settingsTitle.textContent = `LLM Settings: ${settings.provider} - ${settings.model}`;
        }
    }

            updateTokenLimitInstructions() {
        const imagingModelSelect = document.getElementById('imaging-model-select');
        const tokenLimitField = document.getElementById('token-limit-display');
        
        if (!tokenLimitField || !imagingModelSelect) return;
        
        // Get token limit for the selected imaging model
        const selectedImagingModel = imagingModelSelect.value;
        const tokenLimit = this.getModelTokenLimit(selectedImagingModel);
        
        if (tokenLimit) {
                    tokenLimitField.value = `Generate a single imaging prompt up to ${tokenLimit} characters for ${selectedImagingModel} compatibility. Include: subject, setting, 2–3 key elements, composition/framing, lighting, color palette, texture/materials, mood, vantage/time. Keep to the Style Guidelines. No meta text. Respond ONLY as JSON: {"image_prompt":"..."}`;
        } else {
            tokenLimitField.value = 'Token limit instructions will appear here based on selected imaging LLM...';
        }

                // Refresh compiled preview when token limit guidance changes
                this.updateCompiledPreview();
    }

    getModelTokenLimit(modelName) {
        // Token limits for imaging models
        const tokenLimits = {
            'dall-e-3': 4000,
            'dall-e-2': 1000,
            'sdxl-lora': 400,
            'gpt-image-1': 2000
        };
        
        return tokenLimits[modelName] || null;
    }

    saveImagingModelSelection() {
        const imagingModelSelect = document.getElementById('imaging-model-select');
        if (!imagingModelSelect) return;
        
        const selectedModel = imagingModelSelect.value;
        
        // Save to localStorage for session persistence
        localStorage.setItem('imaging-model-selection', selectedModel);
        
        // Save to database for permanent persistence
        this.saveImagingModelToDatabase(selectedModel);
        
        console.log('[Imaging Model] Selection saved:', selectedModel);
    }

    loadImagingModelSelection() {
        const imagingModelSelect = document.getElementById('imaging-model-select');
        if (!imagingModelSelect) return;
        
        // Try to load from localStorage first
        const savedModel = localStorage.getItem('imaging-model-selection');
        if (savedModel) {
            imagingModelSelect.value = savedModel;
            this.updateTokenLimitInstructions();
            return;
        }
        
        // Fallback to default
        imagingModelSelect.value = 'dall-e-3';
        this.updateTokenLimitInstructions();
    }

    async saveImagingModelToDatabase(modelName) {
        try {
            const response = await fetch('/authoring/api/save-imaging-model-selection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    imaging_model: modelName,
                    post_id: window.postId 
                })
            });
            
            if (!response.ok) {
                console.error('Failed to save imaging model selection to database');
            }
        } catch (error) {
            console.error('Error saving imaging model selection:', error);
        }
    }

    updateSectionContent(section) {
        const sectionContentField = document.getElementById('section-content-display');
        if (!sectionContentField) return;
        
        if (section && section.selected_image_concept && section.image_concepts) {
            try {
                // Parse the image_concepts JSON
                const conceptsData = JSON.parse(section.image_concepts);
                
                // Find the selected concept
                const selectedConcept = conceptsData.concepts?.find(
                    concept => concept.concept_id === section.selected_image_concept
                );
                
                if (selectedConcept) {
                    // Extract the description (not the title)
                    sectionContentField.value = selectedConcept.concept_description || '';
                } else {
                    sectionContentField.value = 'Selected concept not found in image concepts data.';
                }
            } catch (error) {
                console.error('Error parsing image concepts:', error);
                sectionContentField.value = 'Error parsing image concepts data.';
            }
        } else {
            sectionContentField.value = 'Select a section to see its content...';
        }
        
        // Also update the compiled preview
        this.updateCompiledPreview();
    }

    updateCompiledPreview() {
        const compiledPreviewField = document.getElementById('compiled-preview');
        if (!compiledPreviewField) return;
        
        // Get all the component texts
        const systemPrompt = document.getElementById('system-prompt-display')?.value || '';
        const tokenLimits = document.getElementById('token-limit-display')?.value || '';
        const styleGuidelines = document.getElementById('style-guidelines-display')?.value || '';
        const sectionContent = document.getElementById('section-content-display')?.value || '';
        
        // Combine them in the optimal order for LLM processing
        const compiledText = `${systemPrompt}\n\n${tokenLimits}\n\n${styleGuidelines}\n\n${sectionContent}`;
        
        compiledPreviewField.value = compiledText;
    }

    async saveSystemPrompt() {
        const systemPromptField = document.getElementById('system-prompt-display');
        if (!systemPromptField) return;
        
        const systemPrompt = systemPromptField.value.trim();
        
        try {
            const response = await fetch('/authoring/api/save-system-prompt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    system_prompt: systemPrompt,
                    prompt_name: 'Image Prompts Generation'
                })
            });
            
            if (!response.ok) {
                console.error('Failed to save system prompt to database');
                return;
            }
            
            console.log('[System Prompt] Saved successfully');
            this.updateCompiledPreview();
            
        } catch (error) {
            console.error('Error saving system prompt:', error);
        }
    }

    async saveStyleGuidelines() {
        const styleGuidelinesField = document.getElementById('style-guidelines-display');
        if (!styleGuidelinesField) return;
        
        const styleGuidelines = styleGuidelinesField.value.trim();
        
        try {
            const response = await fetch('/authoring/api/save-style-guidelines', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    style_guidelines: styleGuidelines,
                    image_format_id: 2
                })
            });
            
            if (!response.ok) {
                console.error('Failed to save style guidelines to database');
                return;
            }
            
            console.log('[Style Guidelines] Saved successfully');
            this.updateCompiledPreview();
            
        } catch (error) {
            console.error('Error saving style guidelines:', error);
        }
    }

    async generateImagePrompt() {
        const generateBtn = document.getElementById('generate-prompt-btn');
        const outputField = document.getElementById('image-prompts-display');
        
        if (!generateBtn || !outputField) return;
        
        // Get the compiled prompt
        const compiledPrompt = document.getElementById('compiled-preview')?.value || '';
        if (!compiledPrompt.trim()) {
            alert('Please ensure all fields are filled in the Prompt Builder');
            return;
        }
        
        // Get current LLM settings
        const settings = this.getSettings();
        
        // Disable button and show loading
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        
        try {
            const response = await fetch('/authoring/api/generate-image-prompt-from-builder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    compiled_prompt: compiledPrompt,
                    llm_provider: settings.provider,
                    llm_model: settings.model,
                    temperature: settings.temperature,
                    max_tokens: settings.maxTokens,
                    post_id: window.postId,
                    section_id: this.getCurrentSectionId()
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Display the generated prompt in the output field
                this.displayGeneratedPrompt(result.generated_prompt);
                console.log('[Generate] Image prompt generated successfully');
            } else {
                throw new Error(result.error || 'Unknown error occurred');
            }
            
        } catch (error) {
            console.error('Error generating image prompt:', error);
            alert(`Error generating image prompt: ${error.message}`);
        } finally {
            // Re-enable button
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate';
        }
    }

    getCurrentSectionId() {
        // Get the currently selected section ID from localStorage or sections panel
        const savedSectionId = localStorage.getItem('authoring-selected-section');
        return savedSectionId || null;
    }

    displayGeneratedPrompt(generatedPrompt) {
        const outputField = document.getElementById('image-prompts-display');
        if (!outputField) return;
        
        // Show the output panel
        outputField.style.display = 'block';
        
        // Update the prompts container with the generated content
        const promptsContainer = document.getElementById('prompts-container');
        if (promptsContainer) {
            promptsContainer.innerHTML = `
                <div class="prompt-card">
                    <div class="prompt-content">
                        <div class="prompt-text">${generatedPrompt}</div>
                    </div>
                </div>
            `;
        }
    }
}

// Accordion functions
function toggleLLMSettingsAccordion() {
    const content = document.getElementById('settings-accordion-content');
    const icon = document.getElementById('settings-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        localStorage.setItem('llm-settings-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        localStorage.setItem('llm-settings-accordion-state', 'closed');
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Restore accordion state
    const savedState = localStorage.getItem('llm-settings-accordion-state');
    if (savedState === 'open') {
        const content = document.getElementById('settings-accordion-content');
        const icon = document.getElementById('settings-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }
    
    // Initialize settings handler
    window.authoringLLMSettingsHandler = new AuthoringLLMSettingsHandler();
    
    // Make updateSectionContent available globally
    window.updatePromptBuilderSectionContent = (section) => {
        window.authoringLLMSettingsHandler?.updateSectionContent(section);
    };
});
