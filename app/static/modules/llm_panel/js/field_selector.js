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
        // Get step_id, substage_id, stage_id from panel data attributes if available
        const panel = document.querySelector('[data-step-id]');
        this.stepId = panel ? panel.getAttribute('data-step-id') : null;
        this.stageId = panel ? panel.getAttribute('data-stage-id') : null;
        this.substageId = panel ? panel.getAttribute('data-substage-id') : null;
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
            console.log('[DEBUG] Sample field values:', {
                'basic_idea': this.fieldValues.basic_idea ? this.fieldValues.basic_idea.substring(0, 50) + '...' : 'null',
                'idea_seed': this.fieldValues.idea_seed ? this.fieldValues.idea_seed.substring(0, 50) + '...' : 'null'
            });
            
            // Get all available fields with their groupings
            console.log('[DEBUG] Fetching available fields...');
            
            // For Writing stage, we need post_section fields for both inputs and outputs
            let fieldsData;
            if (this.stage === 'writing') {
                // Get post_section fields (for both inputs and outputs)
                let query = '';
                if (this.stepId) query += `step_id=${this.stepId}`;
                if (this.substageId) query += (query ? '&' : '') + `substage_id=${this.substageId}`;
                if (this.stageId) query += (query ? '&' : '') + `stage_id=${this.stageId}`;
                const sectionResponse = await fetch(`/api/workflow/fields/available${query ? '?' + query : ''}`);
                if (!sectionResponse.ok) {
                    throw new Error(`HTTP error! status: ${sectionResponse.status}`);
                }
                fieldsData = await sectionResponse.json();
                console.log('[DEBUG] Post section fields loaded:', fieldsData.fields.length, 'fields');
            } else {
                // For other stages, use the original logic
                let query = '';
                if (this.stepId) query += `step_id=${this.stepId}`;
                if (this.substageId) query += (query ? '&' : '') + `substage_id=${this.substageId}`;
                if (this.stageId) query += (query ? '&' : '') + `stage_id=${this.stageId}`;
                const fieldsResponse = await fetch(`/api/workflow/fields/available${query ? '?' + query : ''}`);
                if (!fieldsResponse.ok) {
                    throw new Error(`HTTP error! status: ${fieldsResponse.status}`);
                }
                fieldsData = await fieldsResponse.json();
                console.log('[DEBUG] Available fields loaded:', fieldsData.fields.length, 'fields');
            }
            
            // Store the complete fieldsData for access in initializeSingleFieldSelector
            this.fieldsData = fieldsData;
            
            // Process unified fields list
            this.fields = {};
            fieldsData.fields.forEach(field => {
                this.fields[field.field_name] = {
                    name: field.field_name,
                    display_name: field.display_name,
                    db_table: field.db_table,
                    db_field: field.db_field,
                    // For post_development fields, include mapping info if present
                    ...(field.mappings && field.mappings.length > 0 && {
                        stage: field.mappings[0].stage_name,
                        substage: field.mappings[0].substage_name,
                        step: field.mappings[0].step_name,
                        stage_id: field.mappings[0].stage_id,
                        substage_id: field.mappings[0].sub_stage_id,
                        step_id: field.mappings[0].step_id,
                        stage_order: field.mappings[0].stage_order,
                        substage_order: field.mappings[0].sub_stage_order,
                        step_order: field.mappings[0].step_order,
                        order: field.mappings[0].order_index,
                        mappings: field.mappings
                    })
                };
            });
            
            // Store groups for organizing dropdowns
            this.groups = fieldsData.groups || [];
            console.log('[DEBUG] Groups loaded:', this.groups.length, 'groups');
            // Load saved field mappings
            console.log('[DEBUG] Loading saved field mappings...');
            await this.loadFieldMappings();
            console.log('[DEBUG] Field mappings loaded:', this.savedMappings);
            // Initialize field selectors
            console.log('[DEBUG] Initializing field selectors...');
            await this.initializeFieldSelectors();
            // Mark initialization as complete
            this.isInitializing = false;
            this.initialized = true;
            console.log('[DEBUG] Field selector initialization complete');
            // Dispatch custom event to signal ready
            document.dispatchEvent(new CustomEvent('fieldSelectorReady'));
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
            
            const response = await fetch(`/api/workflow/steps/${stepId}/field_selection`);
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

    async initializeFieldSelectors() {
        console.log('[DEBUG] initializeFieldSelectors() called');
        // Get all field selectors
        const selectors = document.querySelectorAll('.field-selector, #input_field_select, #output_field_select');
        console.log('[DEBUG] Found', selectors.length, 'field selectors');
        for (const selector of selectors) {
            await this.initializeSingleFieldSelector(selector);
        }
        // Listen for dynamic field selector initialization
        document.addEventListener('fieldSelectorInit', async (event) => {
            console.log('[DEBUG] fieldSelectorInit event received:', event.detail);
            const { element } = event.detail;
            if (element) {
                await this.initializeSingleFieldSelector(element);
            }
        });
    }

    async initializeSingleFieldSelector(selector) {
        if (!selector) return;
        // Clear existing options
        selector.innerHTML = '<option value="">Select field...</option>';
        // Get section (inputs/outputs) and target field
        const section = selector.dataset.section;
        const target = selector.dataset.target;
        
        // Use the original working logic - filter fields based on stage and section
        this.initializeSingleFieldSelectorFallback(selector, section, target);
        
        // Set initial value based on saved mappings
        let selectedField = null;
        console.log('[DEBUG] Initializing selector for section:', section, 'target:', target);
        console.log('[DEBUG] Saved mappings:', this.savedMappings);
        console.log('[DEBUG] Saved output selection:', this.savedOutputFieldSelection);
        
        // Set initial value based on saved mappings
        if (section === 'outputs' && this.savedOutputFieldSelection && this.savedOutputFieldSelection.field) {
            selectedField = this.savedOutputFieldSelection.field;
        } else if (this.savedMappings && this.savedMappings.length > 0) {
            const mapping = this.savedMappings.find(m => m.target === target);
            if (mapping) {
                selectedField = mapping.field_name;
            }
        }
        
        if (selectedField) {
            selector.value = selectedField;
            console.log('[DEBUG] Set initial value to:', selectedField);
        }
        
        // Add event listener
        this.addFieldSelectorEventListener(selector);
    }

    initializeSingleFieldSelectorFallback(selector, section, target) {
        let selectedField = null; // Declare selectedField at the beginning
        let filteredFields = Object.values(this.fields);
        // For Writing stage outputs, always show all post_section fields
        if (this.stage === 'writing' && section === 'outputs') {
            filteredFields = filteredFields.filter(field => field.db_table === 'post_section');
            // If for some reason no post_section fields are present, show a warning option
            if (filteredFields.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = '[No post_section fields available]';
                selector.appendChild(option);
                return;
            }
            // Populate dropdown with all post_section fields
            filteredFields.forEach(field => {
                const option = document.createElement('option');
                option.value = field.name;
                option.textContent = field.display_name || field.name;
                option.dataset.table = field.db_table;
                option.dataset.dbField = field.db_field;
                selector.appendChild(option);
            });
        } else {
            // Original fallback for other cases
            // Group fields by db_table
            const groupedFields = {};
            filteredFields.forEach(field => {
                if (!groupedFields[field.db_table]) groupedFields[field.db_table] = [];
                groupedFields[field.db_table].push(field);
            });
            Object.keys(groupedFields).forEach(tableName => {
                const optgroup = document.createElement('optgroup');
                optgroup.label = tableName;
                selector.appendChild(optgroup);
                groupedFields[tableName].forEach(field => {
                    const option = document.createElement('option');
                    option.value = field.name;
                    option.textContent = field.display_name || field.name;
                    option.dataset.table = field.db_table;
                    option.dataset.dbField = field.db_field;
                    optgroup.appendChild(option);
                });
            });
        }
        
        if (section === 'outputs' && this.savedOutputFieldSelection) {
            selectedField = this.savedOutputFieldSelection.field;
            console.log('[DEBUG] Using saved output field:', selectedField);
        } else if (this.savedMappings && this.savedMappings.length > 0) {
            let savedMapping = null;
            if (target) {
                const targetElement = document.getElementById(target);
                if (targetElement && targetElement.dataset.dbField) {
                    savedMapping = this.savedMappings.find(m => m.field_name === targetElement.dataset.dbField);
                    console.log('[DEBUG] Found mapping by target dbField:', savedMapping);
                }
            }
            if (!savedMapping) {
                const allSelectors = document.querySelectorAll('.field-selector, #input_field_select, #output_field_select');
                const selectorIndex = Array.from(allSelectors).indexOf(selector);
                savedMapping = this.savedMappings.find(m => m.order_index === selectorIndex);
                console.log('[DEBUG] Found mapping by selector index:', selectorIndex, 'mapping:', savedMapping);
            }
            if (savedMapping) {
                selectedField = savedMapping.field_name;
                console.log('[DEBUG] Using saved mapping field:', selectedField);
            }
        } else if (target) {
            const targetElement = document.getElementById(target);
            if (targetElement && targetElement.dataset.dbField) {
                selectedField = targetElement.dataset.dbField;
                console.log('[DEBUG] Using target dbField:', selectedField);
            }
        }
        if (selectedField) {
            selector.value = selectedField;
            console.log('[DEBUG] Set selector value to:', selectedField);
            // Update target textarea with the selected field's content
            const targetId = selector.dataset.target;
            if (targetId) {
                const targetElement = document.getElementById(targetId);
                if (targetElement && targetElement.tagName === 'TEXTAREA') {
                    targetElement.dataset.dbField = selectedField;
                    const fieldValue = this.fieldValues[selectedField] || '';
                    targetElement.value = fieldValue;
                    console.log('[DEBUG] Set textarea value for field:', selectedField, 'value length:', fieldValue.length);
                }
            }
        }
        this.addFieldSelectorEventListener(selector);
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
            console.log('[DEBUG][HANDLER] Change event fired for selector:', event.target, 'section:', event.target.dataset.section, 'value:', event.target.value);
            const selectedField = event.target.value;
            const targetId = event.target.dataset.target;
            const section = event.target.dataset.section;
            
            if (section === 'outputs') {
                console.log('[DEBUG][OUTPUTS] fieldValues:', this.fieldValues);
                console.log('[DEBUG][OUTPUTS] selectedField:', selectedField);
                if (this.fieldValues && selectedField && this.fieldValues[selectedField]) {
                    console.log('[DEBUG][OUTPUTS] Value found for selectedField:', this.fieldValues[selectedField]);
                } else {
                    console.log('[DEBUG][OUTPUTS] Value NOT found for selectedField');
                }
            }
            
            if (targetId) {
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    // Always update textarea value and data-db-field for both inputs and outputs
                    if (targetElement.tagName === 'TEXTAREA') {
                        targetElement.dataset.dbField = selectedField;
                        
                        // Handle different field types
                        const selectedFieldData = this.fieldsData.fields.find(sf => sf.field_name === selectedField);
                        if (selectedFieldData) {
                                                    if (selectedFieldData.db_table === 'post_section') {
                            // For post_section fields, fetch the section data and populate with actual values
                            targetElement.dataset.dbTable = 'post_section';
                            targetElement.dataset.dbField = selectedFieldData.db_field;
                            // Fetch section data for this post
                            this.fetchSectionData(selectedFieldData.db_field, targetElement);
                        } else {
                                // For post_development fields
                                targetElement.value = this.fieldValues[selectedField] || '';
                                targetElement.dataset.dbTable = 'post_development';
                            }
                        } else {
                            // Fallback for any other field types
                            targetElement.value = this.fieldValues[selectedField] || '';
                            targetElement.dataset.dbTable = 'post_development';
                        }
                    } else if (targetElement === event.target) {
                        targetElement.dataset.dbField = selectedField;
                    }
                }
            }
            
            // Save field mapping based on section
            if (selectedField) {
                if (section === 'outputs') {
                    this.saveOutputFieldSelection(selectedField, event.target);
                } else {
                    this.saveFieldMapping(selectedField, event.target);
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
            
            // Determine the table based on the selected field
            let outputTable = 'post_development';  // Default table for post fields
            let outputField = fieldName;
            
            // Check if this is a section field
            if (this.fieldsData && this.fieldsData.fields && this.fieldsData.fields.find(sf => sf.field_name === fieldName)) {
                outputTable = 'post_section';
                outputField = fieldName; // Use the field name directly
                
                const payload = {
                    output_field: outputField,
                    output_table: outputTable
                };
                
                console.log('[DEBUG] Sending section output field selection payload:', payload);
                
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
                
                console.log('Section output field selection saved successfully');
                return;
            }
            
            const payload = {
                output_field: outputField,
                output_table: outputTable
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

    async fetchSectionData(fieldName, targetElement) {
        try {
            console.log('[DEBUG] fetchSectionData called for field:', fieldName);
            const response = await fetch(`/api/workflow/posts/${this.postId}/sections`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('[DEBUG] Section data loaded:', data);
            
            // For now, just show the first section's data for the selected field
            // In the future, this could be enhanced to show data from specific sections
            if (data.sections && data.sections.length > 0) {
                const firstSection = data.sections[0];
                let fieldValue = '';
                
                // Map field names to section data properties
                switch (fieldName) {
                    case 'section_heading':
                        fieldValue = firstSection.title || '';
                        break;
                    case 'section_description':
                        fieldValue = firstSection.description || '';
                        break;
                    case 'ideas_to_include':
                        fieldValue = firstSection.elements?.ideas?.join('\n') || '';
                        break;
                    case 'facts_to_include':
                        fieldValue = firstSection.elements?.facts?.join('\n') || '';
                        break;
                    default:
                        fieldValue = `Section data available for field: ${fieldName}`;
                }
                
                targetElement.value = fieldValue;
                console.log('[DEBUG] Set section field value:', fieldValue);
            } else {
                targetElement.value = 'No sections found for this post';
            }
        } catch (error) {
            console.error('Error fetching section data:', error);
            targetElement.value = 'Error loading section data';
        }
    }

    getCurrentStepId() {
        console.log('[DEBUG] getCurrentStepId() called');
        console.log('[DEBUG] Current stage/substage:', this.stage, this.substage);
        
        // Method 1: Try to get step ID from the panel data attributes with more specific selector
        const panel = document.querySelector('.space-y-4[data-step-id]');
        if (panel) {
            const stepId = panel.dataset.stepId;
            console.log('[DEBUG] Found step ID from panel data attribute:', stepId);
            return stepId;
        }
        
        // Method 2: Try broader selector as fallback
        const anyPanel = document.querySelector('[data-step-id]');
        if (anyPanel) {
            const stepId = anyPanel.dataset.stepId;
            console.log('[DEBUG] Found step ID from any data-step-id element:', stepId);
            return stepId;
        }
        
        // Method 3: Try to get from URL parameters and map to known step IDs
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step');
        console.log('[DEBUG] Step from URL params:', step);
        
        if (step) {
            // Map known step names to their IDs
            const stepIdMap = {
                'initial_concept': '41',
                'allocate_facts': '15',
                'structure': '14',
                'interesting_facts': '13',
                'provisional_title': '21',
                'idea_scope': '22'
            };
            
            const mappedStepId = stepIdMap[step];
            if (mappedStepId) {
                console.log('[DEBUG] Mapped step ID from URL:', mappedStepId);
                return mappedStepId;
            }
        }
        
        // Method 4: Fallback to hardcoded logic for known combinations
        if (this.stage === 'planning' && this.substage === 'idea' && step === 'initial_concept') {
            console.log('[DEBUG] Using hardcoded step ID for initial_concept: 41');
            return '41';
        }
        
        console.warn('[DEBUG] Could not determine step ID. Stage:', this.stage, 'Substage:', this.substage, 'Step:', step);
        console.warn('[DEBUG] Available data-step-id elements:', document.querySelectorAll('[data-step-id]').length);
        return null;
    }
}

// Export the class
export { FieldSelector };
