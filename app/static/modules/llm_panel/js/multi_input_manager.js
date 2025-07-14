/**
 * MultiInputManager - Handles dynamic input field management for LLM panels
 */
export class MultiInputManager {
    constructor(containerId = 'inputs-container', stage = '', substage = '') {
        this.container = document.getElementById(containerId);
        this.inputCounter = this.getInitialInputCounter();
        this.currentStage = stage;
        this.currentSubstage = substage;
        this.localStorageKey = `multiInputConfig_${this.currentStage}_${this.currentSubstage}`;
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.warn('[MultiInputManager] Container not found:', containerId);
            return;
        }
        this.restoreInputsFromStorage();
        this.bindEvents();
        console.log('[MultiInputManager] Initialized with', this.inputCounter, 'inputs');
    }
    
    getInitialInputCounter() {
        // Count existing input fields to determine next input number
        const existingInputs = this.container?.querySelectorAll('.input-field-group') || [];
        return existingInputs.length;
    }
    
    bindEvents() {
        // Add input button
        const addBtn = document.getElementById('add-input-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                this.addInputField();
            });
        }
        
        // Remove input buttons (delegated event)
        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-input-btn') || 
                e.target.closest('.remove-input-btn')) {
                const removeBtn = e.target.classList.contains('remove-input-btn') ? 
                    e.target : e.target.closest('.remove-input-btn');
                this.removeInputField(removeBtn.closest('.input-field-group'));
            }
        });

        // Field selector change events (delegated)
        this.container.addEventListener('change', (e) => {
            if (e.target.classList.contains('field-selector')) {
                this.persistInputsToStorage();
            }
        });
    }
    
    persistInputsToStorage() {
        const config = [];
        this.container.querySelectorAll('.input-field-group').forEach(group => {
            const inputId = group.dataset.inputId;
            const select = group.querySelector('select.field-selector');
            const textarea = group.querySelector('textarea');
            config.push({ 
                inputId, 
                selectedField: select ? select.value : '',
                value: textarea ? textarea.value : ''
            });
        });
        localStorage.setItem(this.localStorageKey, JSON.stringify(config));
        console.log('[MultiInputManager] Persisted config to', this.localStorageKey, config);
    }
    
    restoreInputsFromStorage() {
        try {
            const config = JSON.parse(localStorage.getItem(this.localStorageKey) || '[]');
            console.log('[MultiInputManager] Restoring config from', this.localStorageKey, config);
            
            if (config.length > 0) {
                // Remove all but the first input
                this.container.querySelectorAll('.input-field-group').forEach((group, idx) => {
                    if (idx > 0) group.remove();
                });
                
                // Add inputs as per config
                for (let i = 1; i < config.length; i++) {
                    this.addInputField();
                }
                
                // Set dropdown values and trigger fieldSelectorInit
                this.container.querySelectorAll('.input-field-group').forEach((group, idx) => {
                    if (!config[idx]) return;
                    
                    const select = group.querySelector('select.field-selector');
                    const textarea = group.querySelector('textarea');
                    
                    if (select) {
                        select.value = config[idx].selectedField || '';
                        // Trigger field selector initialization
                        const event = new CustomEvent('fieldSelectorInit', {
                            detail: { 
                                target: group.dataset.inputId,
                                element: select,
                                value: config[idx].selectedField
                            }
                        });
                        document.dispatchEvent(event);
                    }
                    
                    if (textarea && config[idx].value) {
                        textarea.value = config[idx].value;
                    }
                });
            }
        } catch (error) {
            console.error('[MultiInputManager] Error restoring config:', error);
        }
    }
    
    addInputField() {
        this.inputCounter++;
        const inputId = `input${this.inputCounter}`;
        
        const inputHtml = `
            <div class="input-field-group mb-4 p-3 border border-gray-600 rounded" data-input-id="${inputId}">
                <div class="flex justify-between items-center mb-2">
                    <label for="input_${inputId}" class="block text-sm font-medium">
                        <!-- Removed blue title -->
                    </label>
                    <button type="button" class="remove-input-btn text-red-500 hover:text-red-400 text-sm">
                        <i class="fas fa-trash"></i> Remove
                    </button>
                </div>
                <select class="field-selector bg-dark-bg text-dark-text border border-dark-border rounded p-2 w-full mb-2"
                    data-target="input_${inputId}" data-section="inputs" data-current-substage="${this.currentSubstage}">
                    <option value="">Select field...</option>
                </select>
                <textarea id="input_${inputId}" name="${inputId}"
                    class="w-full bg-dark-bg border border-dark-border text-dark-text rounded p-4"
                    data-db-field="" data-db-table="post_development" rows="4" 
                    placeholder="Enter text..."></textarea>
            </div>
        `;
        
        this.container.insertAdjacentHTML('beforeend', inputHtml);
        
        // Initialize field selector for the new input
        this.initializeFieldSelector(inputId);
        
        this.persistInputsToStorage();
        console.log('[MultiInputManager] Added input field:', inputId);
    }
    
    removeInputField(element) {
        if (!element) return;
        
        const inputId = element.dataset.inputId;
        const totalInputs = this.container.querySelectorAll('.input-field-group').length;
        
        if (totalInputs <= 1) {
            alert('At least one input field is required.');
            return;
        }
        
        element.remove();
        this.persistInputsToStorage();
        console.log('[MultiInputManager] Removed input field:', inputId);
    }
    
    initializeFieldSelector(inputId) {
        // Trigger field selector initialization for the new input
        const fieldSelector = document.querySelector(`[data-target="input_${inputId}"]`);
        if (fieldSelector) {
            // Dispatch custom event to trigger field selector population
            const event = new CustomEvent('fieldSelectorInit', {
                detail: { target: inputId, element: fieldSelector }
            });
            document.dispatchEvent(event);
        }
    }
    
    getAllInputs() {
        const inputs = {};
        this.container.querySelectorAll('.input-field-group').forEach(group => {
            const inputId = group.dataset.inputId;
            const textarea = group.querySelector('textarea');
            const select = group.querySelector('select.field-selector');
            
            if (textarea && select) {
                inputs[inputId] = {
                    field: select.value || '',
                    value: textarea.value || '',
                    db_field: textarea.dataset.dbField || '',
                    db_table: textarea.dataset.dbTable || 'post_development'
                };
            }
        });
        return inputs;
    }
    
    getInputConfiguration() {
        const config = {};
        this.container.querySelectorAll('.input-field-group').forEach(group => {
            const inputId = group.dataset.inputId;
            const textarea = group.querySelector('textarea');
            const select = group.querySelector('select.field-selector');
            
            if (textarea && select) {
                config[inputId] = {
                    type: "textarea",
                    label: inputId.replace('input', 'Input '),
                    db_field: select.value || textarea.dataset.dbField || '',
                    db_table: textarea.dataset.dbTable || 'post_development',
                    required: false,
                    placeholder: "Enter text..."
                };
            }
        });
        return config;
    }
    
    updateInputConfiguration(config) {
        // Clear existing inputs
        this.container.innerHTML = '';
        
        // Add inputs based on configuration
        Object.entries(config).forEach(([inputId, inputConfig]) => {
            this.addInputFieldFromConfig(inputId, inputConfig);
        });
        
        // Update counter
        this.inputCounter = Object.keys(config).length;
    }
    
    addInputFieldFromConfig(inputId, config) {
        const inputHtml = `
            <div class="input-field-group mb-4 p-3 border border-gray-600 rounded" data-input-id="${inputId}">
                <div class="flex justify-between items-center mb-2">
                    <label for="input_${inputId}" class="block text-sm font-medium">
                        <!-- Removed blue title -->
                    </label>
                    ${inputId !== 'input1' ? `
                    <button type="button" class="remove-input-btn text-red-500 hover:text-red-400 text-sm">
                        <i class="fas fa-trash"></i> Remove
                    </button>
                    ` : ''}
                </div>
                <select class="field-selector bg-dark-bg text-dark-text border border-dark-border rounded p-2 w-full mb-2"
                    data-target="input_${inputId}" data-section="inputs" data-current-substage="${this.currentSubstage}">
                    <option value="">Select field...</option>
                </select>
                <textarea id="input_${inputId}" name="${inputId}"
                    class="w-full bg-dark-bg border border-dark-border text-dark-text rounded p-4"
                    data-db-field="${config.db_field || ''}" data-db-table="${config.db_table || 'post_development'}" 
                    rows="4" placeholder="${config.placeholder || 'Enter text...'}">${config.value || ''}</textarea>
            </div>
        `;
        
        this.container.insertAdjacentHTML('beforeend', inputHtml);
        this.initializeFieldSelector(inputId);
    }
} 