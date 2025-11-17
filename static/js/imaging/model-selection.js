// Imaging Model Selection Panel JavaScript

class ModelSelectionPanel {
    constructor() {
        this.currentModel = 'gpt-image-1';
        this.parameters = {};
        this.modelSpecs = {};
        this.init();
    }

    init() {
        console.log('[Model Selection] Initializing model selection panel');
        
        this.setupEventListeners();
        this.setupAccordion();
        this.loadModelSpecs().then(() => {
            this.loadSavedConfiguration();
        });
    }

    setupAccordion() {
        this.restoreAccordionState();
    }

    restoreAccordionState() {
        const savedState = sessionStorage.getItem('model-selection-accordion-state');
        const content = document.getElementById('model-selection-accordion-content');
        const icon = document.getElementById('model-selection-accordion-icon');
        
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
        const content = document.getElementById('model-selection-accordion-content');
        const icon = document.getElementById('model-selection-accordion-icon');
        
        if (!content || !icon) return;
        
        const isCollapsed = content.style.display === 'none' || content.style.display === '';
        
        if (isCollapsed) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
            sessionStorage.setItem('model-selection-accordion-state', 'open');
        } else {
            content.style.display = 'none';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
            sessionStorage.setItem('model-selection-accordion-state', 'closed');
        }
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
        
        // Generate button handler - removed (handled by image-generation-handler.js)
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
        // Image generation - REMOVED
        alert('Image generation has been removed');
        return;
    }
    
    async generateImageWithRetry(maxRetries = 3) {
        // Image generation - REMOVED
        throw new Error('Image generation has been removed');
    }
    
    isRetryableError(errorMessage) {
        const retryablePatterns = [
            'timeout',
            'rate limit',
            'busy',
            'service unavailable',
            'temporary',
            'try again',
            'network',
            'connection',
            'server error',
            'internal server error',
            '502',
            '503',
            '504',
            '429', // Too Many Requests
            '500', // Internal Server Error
            'openai', // OpenAI-specific errors
            'api.openai.com',
            'read timed out',
            'connection pool',
            'ssl',
            'certificate',
            'dns',
            'name resolution'
        ];
        
        const lowerError = errorMessage.toLowerCase();
        return retryablePatterns.some(pattern => lowerError.includes(pattern));
    }
    
    getRetryDelay(attempt) {
        // Exponential backoff: 2s, 4s, 8s
        return Math.min(2000 * Math.pow(2, attempt - 1), 10000);
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
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
            const pid = window.postId || '';
            const url = pid ? `/imaging/api/model-selection?post_id=${encodeURIComponent(pid)}` : '/imaging/api/model-selection';
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                this.currentModel = data.model || 'gpt-image-1';
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

                // Persist selection per-post to ensure backend coherence (even if unchanged)
                try {
                    await this.saveConfiguration();
                } catch (e) {
                    console.warn('[Model Selection] Could not persist selection on load:', e);
                }
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
                parameters: this.parameters,
                post_id: window.postId || null
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

// Diagnostic button handler
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('run-pipeline-diagnostic')?.addEventListener('click', async () => {
        const postId = window.postId;
        const sectionId = window.currentSectionId || 1;
        const modelKey = document.getElementById('image-model-select').value;
        
        const resultsDiv = document.getElementById('diagnostic-results');
        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = '<p style="color: #60a5fa;">Running diagnostics...</p>';
        
        try {
            const response = await fetch(`/imaging/api/diagnostic/posts/${postId}/sections/${sectionId}/prompt-pipeline?model_key=${modelKey}`);
            const results = await response.json();
            
            let html = `<div style="background: #1e293b; padding: 0.75rem; border-radius: 4px; font-size: 0.875rem; max-height: 400px; overflow-y: auto;">`;
            html += `<h6 style="color: ${results.overall_status === 'passed' ? '#10b981' : '#ef4444'};">Overall: ${results.overall_status.toUpperCase()}</h6>`;
            
            for (const [stageName, stageData] of Object.entries(results.stages)) {
                const status = stageData.success ? '✅' : '❌';
                html += `<div style="margin-top: 0.5rem;"><strong>${status} ${stageName}</strong>`;
                if (stageData.error) {
                    html += `<div style="color: #ef4444; margin-left: 1.5rem;">${stageData.error}</div>`;
                }
                html += `</div>`;
            }
            
            html += `</div>`;
            resultsDiv.innerHTML = html;
        } catch (error) {
            resultsDiv.innerHTML = `<p style="color: #ef4444;">Error running diagnostics: ${error.message}</p>`;
        }
    });
});

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.modelSelectionPanel = new ModelSelectionPanel();
    
    // Respond to global imaging events (from imaging-core)
    document.addEventListener('imaging:model-changed', function(e) {
        if (window.modelSelectionPanel) {
            window.modelSelectionPanel.updateTitle();
        }
    });
    
    // Restore accordion state - use HeaderAccordionManager if in header context
    if (window.currentStage === 'header' && window.headerAccordionManager) {
        // Use HeaderAccordionManager for header context
        window.headerAccordionManager.initializeAccordion(
            'model-selection',
            'model-selection-accordion-content',
            'model-selection-accordion-icon'
        );
    } else {
        // Use localStorage for imaging context
        const savedState = localStorage.getItem('model-selection-accordion-state');
        if (savedState === 'open') {
            const content = document.getElementById('model-selection-accordion-content');
            const icon = document.getElementById('model-selection-accordion-icon');
            if (content && icon) {
                content.style.display = 'block';
                icon.className = 'fas fa-chevron-up';
            }
        }
    }
});

// Accordion functionality
function toggleModelSelectionAccordion() {
    // If HeaderAccordionManager is handling this, let it do its work
    if (window.currentStage === 'header' && window.headerAccordionManager) {
        // The HeaderAccordionManager will handle this via the global function it creates
        return;
    }
    
    // Fallback to localStorage for imaging context
    const content = document.getElementById('model-selection-accordion-content');
    const icon = document.getElementById('model-selection-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('model-selection-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('model-selection-accordion-state', 'closed');
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
