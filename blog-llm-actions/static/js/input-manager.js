/**
 * Input Manager Module
 *
 * Responsibilities:
 * - Manage input fields (text areas, inputs, etc.)
 * - Handle input field interactions and validation
 * - Coordinate with field selector for data loading
 * - Provide input data to other modules
 * - Stage-aware data sourcing (planning vs writing)
 *
 * Dependencies: logger.js, field-selector.js
 * Dependents: llm-processor.js
 *
 * @version 1.0
 */

// Input state
const INPUT_STATE = {
    // Input field data
    inputs: {},
    
    // Input field elements
    elements: {},
    
    // Validation state
    validation: {},
    
    // UI state
    initialized: false,
    loading: false
};

/**
 * Input Manager class
 */
class InputManager {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
    }

    /**
     * Initialize the input manager
     */
    async initialize(context) {
        this.logger.trace('inputManager', 'initialize', 'enter');
        this.context = context;
        
        try {
            // Initialize input fields
            await this.initializeInputFields();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Load initial data
            await this.loadInputData();
            
            this.initialized = true;
            INPUT_STATE.initialized = true;
            
            this.logger.info('inputManager', 'Input manager initialized');
            
        } catch (error) {
            this.logger.error('inputManager', 'Failed to initialize input manager:', error);
            throw error;
        }
        
        this.logger.trace('inputManager', 'initialize', 'exit');
    }

    /**
     * Initialize input fields
     */
    async initializeInputFields() {
        this.logger.trace('inputManager', 'initializeInputFields', 'enter');
        
        // Find all input fields
        const inputElements = document.querySelectorAll('input[type="text"], textarea, .input-field');
        this.logger.debug('inputManager', `Found ${inputElements.length} input elements`);
        
        for (const element of inputElements) {
            await this.initializeSingleInput(element);
        }
        
        this.logger.trace('inputManager', 'initializeInputFields', 'exit');
    }

    /**
     * Initialize a single input field
     */
    async initializeSingleInput(element) {
        const inputId = element.id || element.getAttribute('data-input-id');
        const inputType = element.getAttribute('data-input-type') || 'text';
        const inputLabel = element.getAttribute('data-input-label') || inputId;
        
        this.logger.debug('inputManager', `Initializing input: ${inputId} (${inputType})`);
        
        // Store element reference
        INPUT_STATE.elements[inputId] = {
            element: element,
            type: inputType,
            label: inputLabel,
            value: element.value || ''
        };
        
        // Initialize validation
        INPUT_STATE.validation[inputId] = {
            valid: true,
            errors: []
        };
        
        // Set up input-specific event listeners
        this.setupInputEventListeners(element, inputId);
    }

    /**
     * Set up input-specific event listeners
     */
    setupInputEventListeners(element, inputId) {
        // Input change event
        element.addEventListener('input', (event) => {
            this.handleInputChange(inputId, event.target.value);
        });
        
        // Focus event
        element.addEventListener('focus', () => {
            this.handleInputFocus(inputId);
        });
        
        // Blur event
        element.addEventListener('blur', () => {
            this.handleInputBlur(inputId);
        });
        
        // Auto-resize for textareas
        if (element.tagName === 'TEXTAREA') {
            element.addEventListener('input', () => {
                this.autoResizeTextarea(element);
            });
        }
    }

    /**
     * Handle input change
     */
    handleInputChange(inputId, value) {
        this.logger.debug('inputManager', `Input changed: ${inputId} = "${value}"`);
        
        // Update state
        if (INPUT_STATE.elements[inputId]) {
            INPUT_STATE.elements[inputId].value = value;
        }
        
        // Validate input
        this.validateInput(inputId, value);
        
        // Emit change event
        this.emitInputChangeEvent(inputId, value);
    }

    /**
     * Handle input focus
     */
    handleInputFocus(inputId) {
        this.logger.debug('inputManager', `Input focused: ${inputId}`);
        
        const element = INPUT_STATE.elements[inputId]?.element;
        if (element) {
            element.classList.add('input-focused');
        }
    }

    /**
     * Handle input blur
     */
    handleInputBlur(inputId) {
        this.logger.debug('inputManager', `Input blurred: ${inputId}`);
        
        const element = INPUT_STATE.elements[inputId]?.element;
        if (element) {
            element.classList.remove('input-focused');
        }
        
        // Final validation on blur
        const value = INPUT_STATE.elements[inputId]?.value || '';
        this.validateInput(inputId, value);
    }

    /**
     * Auto-resize textarea
     */
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }

    /**
     * Validate input
     */
    validateInput(inputId, value) {
        const input = INPUT_STATE.elements[inputId];
        if (!input) return;
        
        const errors = [];
        
        // Required field validation
        if (input.element.hasAttribute('required') && !value.trim()) {
            errors.push('This field is required');
        }
        
        // Min length validation
        const minLength = input.element.getAttribute('minlength');
        if (minLength && value.length < parseInt(minLength)) {
            errors.push(`Minimum length is ${minLength} characters`);
        }
        
        // Max length validation
        const maxLength = input.element.getAttribute('maxlength');
        if (maxLength && value.length > parseInt(maxLength)) {
            errors.push(`Maximum length is ${maxLength} characters`);
        }
        
        // Update validation state
        INPUT_STATE.validation[inputId] = {
            valid: errors.length === 0,
            errors: errors
        };
        
        // Update UI
        this.updateInputValidationUI(inputId);
    }

    /**
     * Update input validation UI
     */
    updateInputValidationUI(inputId) {
        const input = INPUT_STATE.elements[inputId];
        if (!input) return;
        
        const validation = INPUT_STATE.validation[inputId];
        const element = input.element;
        
        // Remove existing validation classes
        element.classList.remove('input-valid', 'input-invalid');
        
        // Add appropriate class
        if (validation.valid) {
            element.classList.add('input-valid');
        } else {
            element.classList.add('input-invalid');
        }
        
        // Update error display
        this.updateErrorDisplay(inputId, validation.errors);
    }

    /**
     * Update error display
     */
    updateErrorDisplay(inputId, errors) {
        // Find or create error display element
        let errorElement = document.getElementById(`${inputId}-error`);
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.id = `${inputId}-error`;
            errorElement.className = 'input-error';
            
            const input = INPUT_STATE.elements[inputId];
            if (input && input.element.parentNode) {
                input.element.parentNode.insertBefore(errorElement, input.element.nextSibling);
            }
        }
        
        // Update error content
        if (errors.length > 0) {
            errorElement.innerHTML = errors.map(error => `<span>${error}</span>`).join('');
            errorElement.style.display = 'block';
        } else {
            errorElement.style.display = 'none';
        }
    }

    /**
     * Load input data from field selector
     */
    async loadInputData() {
        this.logger.trace('inputManager', 'loadInputData', 'enter');
        
        INPUT_STATE.loading = true;
        
        try {
            // Wait for field selector to be ready
            if (window.fieldSelector && !window.fieldSelector.initialized) {
                this.logger.debug('inputManager', 'Waiting for field selector to initialize');
                await this.waitForFieldSelector();
            }
            
            // Load data for each input field
            for (const [inputId, input] of Object.entries(INPUT_STATE.elements)) {
                await this.loadInputFieldData(inputId, input);
            }
            
        } catch (error) {
            this.logger.error('inputManager', 'Failed to load input data:', error);
        } finally {
            INPUT_STATE.loading = false;
        }
        
        this.logger.trace('inputManager', 'loadInputData', 'exit');
    }

    /**
     * Wait for field selector to be ready
     */
    async waitForFieldSelector() {
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max
        
        while (!window.fieldSelector?.initialized && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (!window.fieldSelector?.initialized) {
            throw new Error('Field selector not ready after 5 seconds');
        }
    }

    /**
     * Load data for a single input field
     */
    async loadInputFieldData(inputId, input) {
        // Check if this input has a field mapping
        if (window.fieldSelector) {
            const mappedField = window.fieldSelector.getFieldMapping(inputId);
            if (mappedField) {
                const fieldValue = window.fieldSelector.getFieldValue(mappedField);
                this.setInputValue(inputId, fieldValue);
                this.logger.debug('inputManager', `Loaded field data for ${inputId}: ${mappedField} -> "${fieldValue}"`);
            }
        }
    }

    /**
     * Set input value
     */
    setInputValue(inputId, value) {
        const input = INPUT_STATE.elements[inputId];
        if (!input) {
            this.logger.warn('inputManager', `Input not found: ${inputId}`);
            return;
        }
        
        input.element.value = value;
        input.value = value;
        
        // Auto-resize if textarea
        if (input.element.tagName === 'TEXTAREA') {
            this.autoResizeTextarea(input.element);
        }
        
        // Validate
        this.validateInput(inputId, value);
        
        this.logger.debug('inputManager', `Set input value: ${inputId} = "${value}"`);
    }

    /**
     * Get input value
     */
    getInputValue(inputId) {
        const input = INPUT_STATE.elements[inputId];
        return input ? input.value : '';
    }

    /**
     * Get all input values
     */
    getAllInputValues() {
        const values = {};
        for (const [inputId, input] of Object.entries(INPUT_STATE.elements)) {
            values[inputId] = input.value;
        }
        return values;
    }

    /**
     * Validate all inputs
     */
    validateAllInputs() {
        const results = {};
        let allValid = true;
        
        for (const [inputId, input] of Object.entries(INPUT_STATE.elements)) {
            this.validateInput(inputId, input.value);
            const validation = INPUT_STATE.validation[inputId];
            results[inputId] = validation;
            
            if (!validation.valid) {
                allValid = false;
            }
        }
        
        return {
            valid: allValid,
            results: results
        };
    }

    /**
     * Clear all inputs
     */
    clearAllInputs() {
        for (const [inputId, input] of Object.entries(INPUT_STATE.elements)) {
            this.setInputValue(inputId, '');
        }
        this.logger.info('inputManager', 'All inputs cleared');
    }

    /**
     * Set up global event listeners
     */
    setupEventListeners() {
        // Listen for field selector changes
        if (window.fieldSelector) {
            document.addEventListener('fieldMappingChanged', (event) => {
                this.handleFieldMappingChange(event.detail);
            });
        }
        
        // Listen for form submission
        document.addEventListener('submit', (event) => {
            this.handleFormSubmit(event);
        });
    }

    /**
     * Handle field mapping change
     */
    handleFieldMappingChange(detail) {
        const { fieldName, mappedField } = detail;
        
        // Reload data for this field
        if (INPUT_STATE.elements[fieldName]) {
            this.loadInputFieldData(fieldName, INPUT_STATE.elements[fieldName]);
        }
    }

    /**
     * Handle form submit
     */
    handleFormSubmit(event) {
        const validation = this.validateAllInputs();
        
        if (!validation.valid) {
            event.preventDefault();
            this.logger.warn('inputManager', 'Form submission blocked due to validation errors');
            
            // Focus first invalid input
            for (const [inputId, result] of Object.entries(validation.results)) {
                if (!result.valid) {
                    INPUT_STATE.elements[inputId]?.element.focus();
                    break;
                }
            }
        }
    }

    /**
     * Emit input change event
     */
    emitInputChangeEvent(inputId, value) {
        const event = new CustomEvent('inputChanged', {
            detail: {
                inputId: inputId,
                value: value,
                timestamp: Date.now()
            }
        });
        document.dispatchEvent(event);
    }

    /**
     * Get current state
     */
    getState() {
        return { ...INPUT_STATE };
    }

    /**
     * Refresh input data
     */
    async refresh() {
        this.logger.info('inputManager', 'Refreshing input data');
        await this.loadInputData();
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('inputManager', 'Destroying input manager');
        this.initialized = false;
        INPUT_STATE.initialized = false;
    }
}

// Create and export global instance
const inputManager = new InputManager();
window.inputManager = inputManager;
window.INPUT_STATE = INPUT_STATE;

// Log initialization
if (window.logger) {
    window.logger.info('inputManager', 'Input Manager Module loaded');
} 