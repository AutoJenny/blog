/**
 * Field Selector JavaScript
 * Handles field mapping dropdowns and field value persistence in LLM panels
 */

// Clean, modern, dark theme CSS for dropdowns
const style = document.createElement('style');
style.textContent = `
    .field-selector, select.field-selector, select {
        background: #23273a !important;
        color: #e0e0e0 !important;
        border: 1.5px solid #3b4252 !important;
        border-radius: 0.5rem !important;
        font-size: 1rem !important;
        padding: 0.5rem 1.25rem !important;
        min-width: 220px !important;
        height: 2.5rem !important;
        margin-bottom: 0.5rem !important;
        box-shadow: 0 2px 8px 0 rgba(0,0,0,0.18) !important;
        transition: border-color 0.2s, box-shadow 0.2s;
        outline: none !important;
        appearance: none !important;
        display: inline-block !important;
        vertical-align: middle !important;
    }
    .field-selector:focus, select.field-selector:focus, select:focus {
        border-color: #5b9aff !important;
        box-shadow: 0 0 0 2px #5b9aff33 !important;
    }
    .field-selector option, select.field-selector option, select option {
        background: #23273a !important;
        color: #e0e0e0 !important;
        font-size: 1rem !important;
    }
    .field-selector option:hover, select.field-selector option:hover, select option:hover {
        background: #2d3748 !important;
        color: #a5b4fc !important;
    }
    label {
        color: #60a5fa !important;
        font-weight: 500 !important;
        margin-bottom: 0.25rem !important;
        display: inline-block !important;
        font-size: 1rem !important;
    }
    .field-selector-row {
        display: flex !important;
        align-items: center !important;
        gap: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
`;
document.head.appendChild(style);

class FieldSelector {
    constructor(postId, stage, substage) {
        console.log('[DEBUG] FieldSelector constructor called with:', { postId, stage, substage });
        this.postId = postId;
        this.stage = stage;
        this.substage = substage;
        this.fieldValues = {};
        this.fields = {};
        this.groups = [];
        this.isInitializing = false;
        this.initialized = false;
        this.eventHandlers = new Map();
        this.savedMappings = [];
        this.initialize();
    }

    async initialize() {
        console.log('[DEBUG] FieldSelector.initialize() called');
        console.log('[DEBUG] isInitializing:', this.isInitializing, 'initialized:', this.initialized);
        
        if (this.isInitializing || this.initialized) {
            console.log('[DEBUG] Already initializing or initialized, returning');
            return;
        }
        
        this.isInitializing = true;
        console.log('[DEBUG] Starting initialization...');
        
        try {
            // Fetch current field values
            console.log('[DEBUG] Fetching field values for post:', this.postId);
            const response = await fetch(`/api/workflow/posts/${this.postId}/development`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.fieldValues = data;
            console.log('[DEBUG] Field values loaded:', Object.keys(this.fieldValues));
            
            // Get all available fields with their groupings
            console.log('[DEBUG] Fetching available fields...');
            const fieldsResponse = await fetch('/api/workflow/fields/available');
            if (!fieldsResponse.ok) {
                throw new Error(`HTTP error! status: ${fieldsResponse.status}`);
            }
            const fieldsData = await fieldsResponse.json();
            console.log('[DEBUG] Available fields loaded:', fieldsData.fields.length, 'fields');
            
            // Process fields and groups
            this.fields = {};
            fieldsData.fields.forEach(field => {
                // Get the primary mapping (first one in the array)
                const primaryMapping = field.mappings[0];
                this.fields[field.field_name] = {
                    name: field.field_name,
                    stage: primaryMapping.stage_name,
                    substage: primaryMapping.substage_name,
                    step: primaryMapping.step_name,
                    stage_id: primaryMapping.stage_id,
                    substage_id: primaryMapping.substage_id,
                    step_id: primaryMapping.step_id,
                    stage_order: primaryMapping.stage_order,
                    substage_order: primaryMapping.sub_stage_order,
                    step_order: primaryMapping.step_order,
                    order: primaryMapping.order_index,
                    // Store all mappings for reference
                    mappings: field.mappings
                };
            });
            
            // Store groups for organizing dropdowns
            this.groups = fieldsData.groups;
            console.log('[DEBUG] Groups loaded:', this.groups.length, 'groups');
            
            // Load saved field mappings
            console.log('[DEBUG] Loading saved field mappings...');
            await this.loadFieldMappings();
            
            // Initialize field selectors
            console.log('[DEBUG] Initializing field selectors...');
            this.initializeFieldSelectors();
            
            // Mark initialization as complete
            this.isInitializing = false;
            this.initialized = true;
            
            console.log('[DEBUG] Field selector initialization complete');
        } catch (error) {
            console.error('Error fetching field values:', error);
            this.isInitializing = false;
        }
    }

    async loadFieldMappings() {
        try {
            // Find the current stage and substage IDs from the groups
            const currentStage = this.groups.find(g => g.name === this.stage);
            const currentSubstage = currentStage?.substages.find(s => s.name === this.substage);
            
            if (!currentStage || !currentSubstage) {
                console.warn('Current stage or substage not found for loading mappings');
                return;
            }
            
            // Load saved mappings for this stage/substage
            const response = await fetch(`/api/workflow/fields/mappings?stage=${this.stage}&substage=${this.substage}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const mappings = await response.json();
            console.log('[DEBUG] Loaded field mappings:', mappings);
            
            // Store the mappings for use in initializeFieldSelectors
            this.savedMappings = mappings;
            
            // Load saved output field selections
            await this.loadOutputFieldSelections();
        } catch (error) {
            console.error('Error loading field mappings:', error);
            this.savedMappings = [];
        }
    }

    async loadOutputFieldSelections() {
        try {
            const stepId = this.getCurrentStepId();
            if (!stepId) {
                console.warn('Could not determine current step ID for loading output field selections');
                return;
            }
            
            const response = await fetch(`/api/workflow/steps/${stepId}/field_selection/${this.postId}`);
            if (!response.ok) {
                if (response.status === 404) {
                    console.log('[DEBUG] No saved output field selection found, using defaults');
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success && data.data) {
                console.log('[DEBUG] Loaded output field selection:', data.data);
                this.savedOutputFieldSelection = data.data;
            }
        } catch (error) {
            console.error('Error loading output field selections:', error);
        }
    }

    initializeFieldSelectors() {
        console.log('[DEBUG] initializeFieldSelectors() called');
        
        // Get all field selectors
        const selectors = document.querySelectorAll('.field-selector, #input_field_select, #output_field_select');
        console.log('[DEBUG] Found', selectors.length, 'field selectors');
        
        selectors.forEach((selector, index) => {
            console.log(`[DEBUG] Processing selector ${index}:`, selector.id || selector.className);
            
            if (!selector) {
                console.warn('Field selector element not found');
                return;
            }

            // Clear existing options
            selector.innerHTML = '<option value="">Select field...</option>';
            
            // Get section (inputs/outputs) and target field
            const section = selector.dataset.section;
            const target = selector.dataset.target;
            const currentSubstage = selector.dataset.currentSubstage;
            
            console.log(`[DEBUG] Selector ${index} data:`, { section, target, currentSubstage });
            
            // Group fields by stage/substage/step
            let lastGroup = null;
            let optgroup = null;
            
            console.log(`[DEBUG] Adding ${Object.keys(this.fields).length} fields to selector ${index}`);
            
            // Add all fields, organized by their primary location
            Object.values(this.fields)
                .sort((a, b) => {
                    // Sort by stage order, substage order, step order, then field order
                    if (a.stage_order !== b.stage_order) return a.stage_order - b.stage_order;
                    if (a.substage_order !== b.substage_order) return a.substage_order - b.substage_order;
                    if (a.step_order !== b.step_order) return a.step_order - b.step_order;
                    return a.order - b.order;
                })
                .forEach(field => {
                    // Create new optgroup if needed
                    const groupLabel = `${field.stage}: ${field.substage} - ${field.step}`;
                    if (groupLabel !== lastGroup) {
                        optgroup = document.createElement('optgroup');
                        optgroup.label = groupLabel;
                        selector.appendChild(optgroup);
                        lastGroup = groupLabel;
                    }
                    
                    // Add option to current group
                    const option = document.createElement('option');
                    option.value = field.name;
                    option.textContent = field.name;
                    optgroup.appendChild(option);
                });
            
            console.log(`[DEBUG] Selector ${index} now has ${selector.options.length} options`);
            
            // Set initial value based on saved mappings
            if (section === 'outputs' && this.savedOutputFieldSelection) {
                // For output fields, prioritize saved output field selection
                console.log(`[DEBUG] Using saved output field selection for selector ${index}:`, this.savedOutputFieldSelection);
                selector.value = this.savedOutputFieldSelection.field;
                
                // Update target element if it exists
                if (target) {
                    const targetElement = document.getElementById(target);
                    if (targetElement) {
                        targetElement.dataset.dbField = this.savedOutputFieldSelection.field;
                        if (this.fieldValues[this.savedOutputFieldSelection.field]) {
                            targetElement.value = this.fieldValues[this.savedOutputFieldSelection.field];
                        }
                    }
                }
            }
            else if (this.savedMappings && this.savedMappings.length > 0) {
                console.log(`[DEBUG] Checking saved mappings for selector ${index}:`, this.savedMappings);
                
                // Try to find a mapping that matches this selector's target
                let savedMapping = null;
                
                // First, try to match by target element's current db_field
                if (target) {
                    const targetElement = document.getElementById(target);
                    if (targetElement && targetElement.dataset.dbField) {
                        savedMapping = this.savedMappings.find(m => m.field_name === targetElement.dataset.dbField);
                        console.log(`[DEBUG] Found mapping by target db_field:`, savedMapping);
                    }
                }
                
                // If no match found, try to match by selector position (for field mapping panel)
                if (!savedMapping) {
                    const selectorIndex = Array.from(selectors).indexOf(selector);
                    savedMapping = this.savedMappings.find(m => m.order_index === selectorIndex);
                    console.log(`[DEBUG] Found mapping by selector index ${selectorIndex}:`, savedMapping);
                }
                
                if (savedMapping) {
                    selector.value = savedMapping.field_name;
                    console.log(`[DEBUG] Set selector ${index} for target "${target}" to field: ${savedMapping.field_name}`);
                    
                    // Update target element if it exists
                    if (target) {
                        const targetElement = document.getElementById(target);
                        if (targetElement) {
                            targetElement.dataset.dbField = savedMapping.field_name;
                            if (this.fieldValues[savedMapping.field_name]) {
                                targetElement.value = this.fieldValues[savedMapping.field_name];
                            }
                        }
                    }
                }
            }
            // Fallback to target element's dataset if no saved mapping
            else if (target) {
                const targetElement = document.getElementById(target);
                if (targetElement && targetElement.dataset.dbField) {
                    selector.value = targetElement.dataset.dbField;
                    console.log(`[DEBUG] Set selector ${index} to fallback value: ${targetElement.dataset.dbField}`);
                }
            }
            
            // Add change event listener
            this.addFieldSelectorEventListener(selector);
        });
    }

    addFieldSelectorEventListener(selector) {
        if (!selector) {
            console.warn('Cannot add event listener to null selector');
            return;
        }

        // Remove existing handler if any
        const existingHandler = this.eventHandlers.get(selector);
        if (existingHandler) {
            selector.removeEventListener('change', existingHandler);
        }

        const handler = (event) => {
            const selectedField = event.target.value;
            const targetId = event.target.dataset.target;
            const section = event.target.dataset.section;
            
            if (targetId) {
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    // If the target is a textarea, update its value and dataset
                    if (targetElement.tagName === 'TEXTAREA') {
                        targetElement.dataset.dbField = selectedField;
                        if (this.fieldValues[selectedField]) {
                            targetElement.value = this.fieldValues[selectedField];
                        }
                    }
                    // If the target is the same as the selector, just update the dataset for mapping
                    else if (targetElement === selector) {
                        targetElement.dataset.dbField = selectedField;
                    }
                }
            }
            
            // Save field mapping based on section
            if (selectedField) {
                if (section === 'outputs') {
                    // Use new API for output field selections
                    this.saveOutputFieldSelection(selectedField, selector);
                } else {
                    // Use existing API for input field mappings
                    this.saveFieldMapping(selectedField, selector);
                }
            }
        };

        selector.addEventListener('change', handler);
        this.eventHandlers.set(selector, handler);
    }

    async saveFieldMapping(fieldName, selector) {
        try {
            console.log('[DEBUG] saveFieldMapping called with:', { fieldName, stage: this.stage, substage: this.substage });
            console.log('[DEBUG] this.groups:', this.groups);
            
            // Find the current stage and substage IDs from the groups
            const currentStage = this.groups.find(g => g.name === this.stage);
            const currentSubstage = currentStage?.substages.find(s => s.name === this.substage);
            
            console.log('[DEBUG] Found stage:', currentStage);
            console.log('[DEBUG] Found substage:', currentSubstage);
            
            if (!currentStage || !currentSubstage) {
                throw new Error('Current stage or substage not found');
            }
            
            // Get the position of this selector among all field selectors
            const allSelectors = document.querySelectorAll('.field-selector, #input_field_select, #output_field_select');
            const selectorIndex = Array.from(allSelectors).indexOf(selector);
            
            const payload = {
                field_name: fieldName,
                stage_id: currentStage.id,
                substage_id: currentSubstage.id,
                order_index: selectorIndex
            };
            
            console.log('[DEBUG] Sending payload:', payload);
            
            const response = await fetch('/api/workflow/fields/mappings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            console.log('Field mapping saved successfully');
        } catch (error) {
            console.error('Error saving field mapping:', error);
        }
    }

    async saveOutputFieldSelection(fieldName, selector) {
        try {
            console.log('[DEBUG] saveOutputFieldSelection called with:', { fieldName });
            
            // Get the step ID from the current page context
            const stepId = this.getCurrentStepId();
            if (!stepId) {
                console.warn('Could not determine current step ID');
                return;
            }
            
            const payload = {
                post_id: this.postId,
                output_field: fieldName,
                output_table: 'post_development'  // Default table for post fields
            };
            
            console.log('[DEBUG] Sending output field selection payload:', payload);
            
            const response = await fetch(`/api/workflow/steps/${stepId}/field_selection`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            console.log('Output field selection saved successfully');
        } catch (error) {
            console.error('Error saving output field selection:', error);
        }
    }

    getCurrentStepId() {
        // Try to get step ID from the panel data attributes
        const panel = document.querySelector('[data-step-id]');
        if (panel) {
            return panel.dataset.stepId;
        }
        
        // Try to get from URL parameters or other page context
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step');
        
        // For now, return a default step ID for the Initial Concept step
        // This should be enhanced to dynamically determine the step ID
        if (this.stage === 'planning' && this.substage === 'idea' && step === 'initial_concept') {
            return '41'; // Hard-coded for Initial Concept step
        }
        
        return null;
    }
}

// Export the class
export { FieldSelector };
