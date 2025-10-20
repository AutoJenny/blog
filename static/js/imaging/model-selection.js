// Imaging Model Selection Panel JavaScript

class ModelSelectionPanel {
    constructor() {
        this.currentModel = 'sdxl-lora';
        this.parameters = {};
        this.modelSpecs = {};
        this.init();
    }

    init() {
        console.log('[Model Selection] Initializing model selection panel');
        
        this.setupEventListeners();
        this.loadModelSpecs().then(() => {
            this.loadSavedConfiguration();
        });
    }

    async loadModelSpecs() {
        try {
            console.log('[Model Selection] Loading model specifications');
            const response = await fetch('/imaging/api/model-specs');
            const data = await response.json();
            
            if (data.success) {
                this.modelSpecs = {};
                data.models.forEach(model => {
                    this.modelSpecs[model.model_key] = model;
                });
                
                console.log('[Model Selection] Loaded model specs:', this.modelSpecs);
                this.updateModelSelectOptions();
            } else {
                console.error('[Model Selection] Failed to load model specs:', data.error);
            }
        } catch (error) {
            console.error('[Model Selection] Error loading model specs:', error);
        }
    }

    updateModelSelectOptions() {
        const modelSelect = document.getElementById('image-model-select');
        if (!modelSelect) return;
        
        // Clear existing options
        modelSelect.innerHTML = '';
        
        // Add options from model specs
        Object.values(this.modelSpecs).forEach(model => {
            const option = document.createElement('option');
            option.value = model.model_key;
            option.textContent = `${model.name} (${model.provider})`;
            modelSelect.appendChild(option);
        });
        
        // Set current model
        modelSelect.value = this.currentModel;
    }

    setupEventListeners() {
        // Model selection handler
        const modelSelect = document.getElementById('image-model-select');
        if (modelSelect) {
            modelSelect.addEventListener('change', (e) => {
                this.currentModel = e.target.value;
                this.updateModelParameters();
                this.saveConfiguration();
                console.log('[Model Selection] Model changed to:', this.currentModel);
                
                // Emit custom event for other panels to listen to
                const event = new CustomEvent('modelSelectionChanged', {
                    detail: {
                        model: this.currentModel,
                        parameters: this.parameters,
                        modelSpec: this.modelSpecs[this.currentModel]
                    }
                });
                document.dispatchEvent(event);
            });
        }
        
        // Generate button handler
        const generateBtn = document.getElementById('generate-image-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.handleGenerateImage());
        }
    }

    updateModelParameters() {
        const parametersContainer = document.getElementById('parameters-container');
        if (!parametersContainer) return;
        
        console.log('[Model Selection] Updating parameters for model:', this.currentModel);
        
        const modelSpec = this.modelSpecs[this.currentModel];
        if (!modelSpec) {
            console.warn('[Model Selection] No model spec found for:', this.currentModel);
            return;
        }
        
        // Clear existing parameters
        parametersContainer.innerHTML = '';
        
        // Add model constraints info
        const constraintsInfo = document.createElement('div');
        constraintsInfo.className = 'model-constraints';
        constraintsInfo.innerHTML = `
            <div class="constraints-header">
                <h5>Model Constraints</h5>
                <span class="constraint-badge">Max: ${modelSpec.constraints.max_prompt_chars} chars</span>
            </div>
        `;
        parametersContainer.appendChild(constraintsInfo);
        
        // Add parameters based on model spec
        modelSpec.parameters.forEach(param => {
            const paramGroup = document.createElement('div');
            paramGroup.className = 'parameter-group';
            
            let inputHTML = '';
            
            if (param.type === 'string' && param.options) {
                // Dropdown for string with options
                inputHTML = `
                    <label for="${param.key}">${this.formatParamLabel(param.key)}:</label>
                    <select id="${param.key}" name="${param.key}">
                        ${param.options.map(option => 
                            `<option value="${option}" ${option === param.default_value ? 'selected' : ''}>${option}</option>`
                        ).join('')}
                    </select>
                `;
            } else if (param.type === 'integer' || param.type === 'decimal') {
                // Number input with min/max
                const step = param.type === 'decimal' ? '0.1' : '1';
                inputHTML = `
                    <label for="${param.key}">${this.formatParamLabel(param.key)}:</label>
                    <input type="number" id="${param.key}" name="${param.key}" 
                           min="${param.min_value || ''}" max="${param.max_value || ''}" 
                           step="${step}" value="${param.default_value}">
                `;
            } else {
                // Text input
                inputHTML = `
                    <label for="${param.key}">${this.formatParamLabel(param.key)}:</label>
                    <input type="text" id="${param.key}" name="${param.key}" value="${param.default_value || ''}">
                `;
            }
            
            paramGroup.innerHTML = inputHTML;
            parametersContainer.appendChild(paramGroup);
        });
        
        // Add LoRA controls if model supports it
        if (modelSpec.supports_lora) {
            const loraGroup = document.createElement('div');
            loraGroup.className = 'parameter-group lora-group';
            loraGroup.innerHTML = `
                <h5>LoRA Settings</h5>
                <div class="lora-item" data-lora-id="aether-watercolor">
                    <span class="lora-name">Aether Watercolor & Ink</span>
                    <input type="range" id="lora-scale-aether" name="lora_scale" 
                           min="0" max="2" step="0.1" value="0.85">
                    <span id="lora-scale-value">0.85</span>
                </div>
            `;
            parametersContainer.appendChild(loraGroup);
        }
        
        // Add event listeners to new parameter inputs
        this.setupParameterListeners();
        
        // Update title with model info
        this.updateTitle();
    }

    formatParamLabel(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    setupParameterListeners() {
        const paramInputs = document.querySelectorAll('#parameters-container select, #parameters-container input');
        paramInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.collectParameters();
                this.saveConfiguration();
            });
        });
    }

    collectParameters() {
        this.parameters = {};
        const paramInputs = document.querySelectorAll('#parameters-container select, #parameters-container input');
        paramInputs.forEach(input => {
            if (input.value) {
                this.parameters[input.name] = input.value;
            }
        });
        console.log('[Model Selection] Parameters collected:', this.parameters);
    }

    updateTitle(status = 'Ready') {
        const title = document.getElementById('model-title');
        if (title) {
            const modelSelect = document.getElementById('image-model-select');
            const model = modelSelect ? modelSelect.value : '';
            const modelNames = {
                'sdxl-lora': 'SDXL LoRA',
                'dall-e-3': 'DALL-E 3',
                'dall-e-2': 'DALL-E 2'
            };
            const display = modelNames[model] || model || status;
            title.innerHTML = `<span class="panel-name-green">Model Selection:</span> ${display}`;
        }
    }

    async handleGenerateImage() {
        console.log('[Model Selection] Generate image button clicked');
        
        // Check if a section is selected
        if (!window.currentSectionId) {
            alert('Please select a section first');
            return;
        }
        
        // Collect current parameters
        this.collectParameters();
        
        try {
            // Disable button during generation
            const generateBtn = document.getElementById('generate-image-btn');
            if (generateBtn) {
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            }
            
            // Call the imaging API to generate image with new renderer system
            const endpoint = `/imaging/api/image-generation/posts/${window.postId}/sections/${window.currentSectionId}/generate-image`;
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model_name: this.currentModel,
                    parameters: this.parameters,
                    use_renderer: true  // Use new renderer system
                })
            });
            
            // Check if response is HTML (404 error page)
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('text/html')) {
                throw new Error('Image generation API not implemented yet. Please check backend implementation.');
            }
            
            const data = await response.json();
            
            if (data.success) {
                console.log('[Model Selection] Image generated successfully');
                console.log('[Model Selection] Debug info:', data.debug_info);
                
                // Update output panel with new image
                if (window.imagingOutputPanel) {
                    window.imagingOutputPanel.onImageGenerated({ 
                        image_path: data.image_path,
                        debug_info: data.debug_info,
                        generation_time_ms: data.generation_time_ms
                    });
                }
                
                // Show success message with renderer info
                const source = data.debug_info?.source || 'unknown';
                const charCount = data.debug_info?.char_count || 0;
                const maxChars = data.debug_info?.max_chars || 0;
                
                alert(`Image generated successfully!\n\nRenderer: ${source}\nPrompt length: ${charCount}/${maxChars} chars\nGeneration time: ${data.generation_time_ms}ms`);
            } else {
                throw new Error(data.error || 'Failed to generate image');
            }
            
        } catch (error) {
            console.error('[Model Selection] Error generating image:', error);
            alert('Error generating image: ' + error.message);
        } finally {
            // Re-enable button
            const generateBtn = document.getElementById('generate-image-btn');
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Image';
            }
        }
    }
    
    getCurrentPrompt() {
        // Try to get prompt from imaging prompt construction panel
        const promptTextEl = document.querySelector('.prompt-text');
        if (promptTextEl && promptTextEl.textContent.trim()) {
            console.log('[Model Selection] Found prompt from Generated Image Prompts panel:', promptTextEl.textContent.trim());
            return promptTextEl.textContent.trim();
        }
        
        // Fallback: Get from sections data if available
        if (window.currentSectionId && window.sectionsData) {
            const section = window.sectionsData.find(s => s.id == window.currentSectionId);
            if (section && section.image_prompts) {
                // Handle JSON object
                if (typeof section.image_prompts === 'object') {
                    return section.image_prompts.image_prompt || '';
                } else if (typeof section.image_prompts === 'string') {
                    try {
                        const parsed = JSON.parse(section.image_prompts);
                        return parsed.image_prompt || section.image_prompts;
                    } catch (e) {
                        return section.image_prompts;
                    }
                }
            }
        }
        
        return null;
    }

    async loadSavedConfiguration() {
        try {
            console.log('[Model Selection] Loading saved configuration from database');
            const response = await fetch('/imaging/api/model-selection');
            const data = await response.json();
            
            if (data.success) {
                this.currentModel = data.model || 'sdxl-lora';
                this.parameters = data.parameters || {};
                
                // Update UI
                this.updateModelSelect();
                this.updateModelParameters();
                this.updateParameterValues();
                this.updateTitle();
                
                // Emit initial model selection event
                const event = new CustomEvent('modelSelectionChanged', {
                    detail: {
                        model: this.currentModel,
                        parameters: this.parameters
                    }
                });
                document.dispatchEvent(event);
                
                console.log('[Model Selection] Configuration loaded from database:', data);
            } else {
                // Use defaults
                this.updateModelParameters();
                this.updateTitle();
            }
        } catch (error) {
            console.error('[Model Selection] Error loading configuration:', error);
            this.updateModelParameters();
            this.updateTitle();
        }
    }

    updateModelSelect() {
        const modelSelect = document.getElementById('image-model-select');
        if (modelSelect) {
            modelSelect.value = this.currentModel;
        }
    }

    updateParameterValues() {
        const paramInputs = document.querySelectorAll('#parameters-container select, #parameters-container input');
        paramInputs.forEach(input => {
            const paramName = input.name;
            if (this.parameters[paramName] !== undefined) {
                input.value = this.parameters[paramName];
            }
        });
    }

    async saveConfiguration() {
        try {
            this.collectParameters();
            
            const configData = {
                model: this.currentModel,
                parameters: this.parameters
            };
            
            const response = await fetch('/imaging/api/model-selection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(configData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('[Model Selection] Configuration saved to database:', configData);
            } else {
                console.error('[Model Selection] Failed to save configuration:', result.error);
            }
        } catch (error) {
            console.error('[Model Selection] Error saving configuration:', error);
        }
    }

    getModelData() {
        this.collectParameters();
        return {
            model: this.currentModel,
            parameters: this.parameters
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.modelSelectionPanel = new ModelSelectionPanel();
    
    // Respond to global imaging events (from imaging-core)
    document.addEventListener('imaging:model-changed', function(e) {
        if (window.modelSelectionPanel) {
            window.modelSelectionPanel.updateTitle();
        }
    });
    
    // Restore accordion state
    const savedState = localStorage.getItem('imaging-model-accordion-state');
    if (savedState === 'open') {
        const content = document.getElementById('model-accordion-content');
        const icon = document.getElementById('model-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
});

// Accordion functionality
function toggleModelSelectionAccordion() {
    const content = document.getElementById('model-accordion-content');
    const icon = document.getElementById('model-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('imaging-model-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('imaging-model-accordion-state', 'closed');
    }
}

// Set up slider value displays
function setupSliderDisplays() {
    // Steps slider
    const stepsSlider = document.getElementById('steps');
    const stepsValue = document.getElementById('steps-value');
    if (stepsSlider && stepsValue) {
        stepsSlider.addEventListener('input', function() {
            stepsValue.textContent = this.value;
        });
    }
    
    // CFG slider
    const cfgSlider = document.getElementById('cfg');
    const cfgValue = document.getElementById('cfg-value');
    if (cfgSlider && cfgValue) {
        cfgSlider.addEventListener('input', function() {
            cfgValue.textContent = this.value;
        });
    }
    
    // LoRA scale slider
    const loraScaleSlider = document.getElementById('lora-scale-aether');
    const loraScaleValue = document.getElementById('lora-scale-value');
    if (loraScaleSlider && loraScaleValue) {
        loraScaleSlider.addEventListener('input', function() {
            loraScaleValue.textContent = this.value;
        });
    }
}

// Generate random seed
function generateRandomSeed() {
    const seedInput = document.getElementById('seed');
    if (seedInput) {
        const randomSeed = Math.floor(Math.random() * 999999999);
        seedInput.value = randomSeed;
        console.log('[Model Selection] Generated random seed:', randomSeed);
    }
}
