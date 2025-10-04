// Imaging Model Selection Panel JavaScript

class ModelSelectionPanel {
    constructor() {
        this.currentModel = 'sdxl-lora';
        this.parameters = {};
        this.init();
    }

    init() {
        console.log('[Model Selection] Initializing model selection panel');
        
        this.setupEventListeners();
        this.loadSavedConfiguration();
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
        console.log('[Model Selection] Parameters container HTML before:', parametersContainer.innerHTML.substring(0, 200));
        
        let parametersHTML = '';
        
        if (this.currentModel === 'sdxl-lora') {
            parametersHTML = `
                <div class="parameter-group">
                    <label for="image-dimensions">Image Dimensions:</label>
                    <select id="image-dimensions" name="image_dimensions">
                        <option value="1024x1024">1024x1024 (Square)</option>
                        <option value="1792x1024">1792x1024 (Landscape)</option>
                        <option value="1024x1792">1024x1792 (Portrait)</option>
                    </select>
                </div>
                <div class="parameter-group">
                    <label for="steps">Steps:</label>
                    <input type="number" id="steps" name="steps" min="10" max="50" value="20">
                </div>
                <div class="parameter-group">
                    <label for="cfg">CFG Scale:</label>
                    <input type="number" id="cfg" name="cfg" min="1" max="20" step="0.5" value="7">
                </div>
                <div class="parameter-group">
                    <label for="seed">Seed (optional):</label>
                    <input type="number" id="seed" name="seed" min="0" max="999999999" placeholder="Random">
                </div>
            `;
        } else if (this.currentModel.startsWith('dall-e')) {
            parametersHTML = `
                <div class="parameter-group">
                    <label for="image-size">Image Size:</label>
                    <select id="image-size" name="image_size">
                        <option value="1024x1024">1024x1024 (Square)</option>
                        <option value="1792x1024">1792x1024 (Landscape)</option>
                        <option value="1024x1792">1024x1792 (Portrait)</option>
                    </select>
                </div>
                <div class="parameter-group">
                    <label for="quality">Quality:</label>
                    <select id="quality" name="quality">
                        <option value="standard">Standard</option>
                        <option value="hd">HD</option>
                    </select>
                </div>
                <div class="parameter-group">
                    <label for="style">Style:</label>
                    <select id="style" name="style">
                        <option value="vivid">Vivid</option>
                        <option value="natural">Natural</option>
                    </select>
                </div>
            `;
        }
        
        // Don't overwrite the HTML - it's already in the template
        // parametersContainer.innerHTML = parametersHTML;
        
        console.log('[Model Selection] Parameters container HTML after:', parametersContainer.innerHTML.substring(0, 200));
        
        // Add event listeners to new parameter inputs
        this.setupParameterListeners();
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

    updateTitle() {
        const title = document.getElementById('model-title');
        if (title) {
            title.textContent = 'Model Selection: Ready';
        }
    }

    async handleGenerateImage() {
        console.log('[Model Selection] Generate image button clicked');
        
        // Collect current parameters
        this.collectParameters();
        
        if (window.imagingOutputPanel) {
            try {
                // Disable button during generation
                const generateBtn = document.getElementById('generate-image-btn');
                if (generateBtn) {
                    generateBtn.disabled = true;
                    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
                }
                
                await window.imagingOutputPanel.handleGenerateButton();
                
                // Re-enable button
                if (generateBtn) {
                    generateBtn.disabled = false;
                    generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Image';
                }
            } catch (error) {
                console.error('[Model Selection] Error generating image:', error);
                alert('Error generating image: ' + error.message);
                
                // Re-enable button on error
                const generateBtn = document.getElementById('generate-image-btn');
                if (generateBtn) {
                    generateBtn.disabled = false;
                    generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Image';
                }
            }
        } else {
            console.error('[Model Selection] Output panel not available');
            alert('Output panel not available');
        }
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
                
                console.log('[Model Selection] Configuration loaded from database:', config);
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

// Restore accordion state on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedState = localStorage.getItem('imaging-model-accordion-state');
    if (savedState === 'open') {
        const content = document.getElementById('model-accordion-content');
        const icon = document.getElementById('model-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
    
    // Set up slider value displays
    setupSliderDisplays();
});

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
