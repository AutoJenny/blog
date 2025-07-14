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
        } catch (error) {
            console.error('Error in field selector initialization:', error);
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

            // Load saved input field selections from localStorage
            this.loadInputFieldSelections();
        } catch (error) {
            console.error('Error loading field mappings:', error);
            this.savedMappings = [];
        }
    }

    loadInputFieldSelections() {
        try {
            // Get saved input configurations from localStorage using stage/substage-specific key
            const localStorageKey = `multiInputConfig_${this.stage}_${this.substage}`;
            const savedConfig = localStorage.getItem(localStorageKey);
            if (savedConfig) {
                this.savedInputSelections = JSON.parse(savedConfig);
                console.log('[DEBUG] Loaded input field selections from localStorage:', this.savedInputSelections);
            }
        } catch (error) {
            console.error('Error loading input field selections:', error);
            this.savedInputSelections = [];
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
        
        // Get all available fields
        const availableFields = Object.values(this.fields);
        
        // Filter fields based on section and stage
        let filteredFields = availableFields;
        
        // Special handling for Writing stage
        if (this.stage === 'writing') {
            if (section === 'outputs') {
                // For Writing stage outputs, show only post_section fields
                filteredFields = availableFields.filter(field => field.db_table === 'post_section');
            } else {
                // For Writing stage inputs, show post_development fields
                filteredFields = availableFields.filter(field => field.db_table === 'post_development');
            }
        }
        
        // Group fields by stage and substage
        const groupedFields = {};
        filteredFields.forEach(field => {
            const stageName = field.stage || 'Other';
            const substageName = field.substage || 'General';
            
            if (!groupedFields[stageName]) {
                groupedFields[stageName] = {};
            }
            if (!groupedFields[stageName][substageName]) {
                groupedFields[stageName][substageName] = [];
            }
            groupedFields[stageName][substageName].push(field);
        });
        
        // Populate dropdown with grouped options
        Object.entries(groupedFields).forEach(([stageName, substages]) => {
            const stageGroup = document.createElement('optgroup');
            stageGroup.label = stageName;
            
            Object.entries(substages).forEach(([substageName, fields]) => {
                // Add substage label
                const substageLabel = document.createElement('option');
                substageLabel.textContent = substageName;
                substageLabel.disabled = true;
                stageGroup.appendChild(substageLabel);
                
                // Add fields for this substage
                fields.forEach(field => {
                    const option = document.createElement('option');
                    option.value = field.name;
                    option.textContent = field.display_name || field.name;
                    option.dataset.table = field.db_table;
                    option.dataset.dbField = field.db_field;
                    stageGroup.appendChild(option);
                });
            });
            
            selector.appendChild(stageGroup);
        });
        
        // Set initial value based on saved mappings
        let selectedField = null;
        
        if (section === 'outputs' && this.savedOutputFieldSelection) {
            selectedField = this.savedOutputFieldSelection.field;
            console.log('[DEBUG] Setting output field from saved selection:', selectedField);
        } else if (section === 'inputs' && this.savedInputSelections) {
            // For input fields, check localStorage
            const inputId = target.replace('input_', '');
            const savedInput = this.savedInputSelections.find(config => config.inputId === inputId);
            if (savedInput) {
                selectedField = savedInput.selectedField;
                console.log('[DEBUG] Setting input field from localStorage:', selectedField);
            }
        } else if (this.savedMappings && this.savedMappings.length > 0) {
            const mapping = this.savedMappings.find(m => m.target === target);
            if (mapping) {
                selectedField = mapping.field_name;
                console.log('[DEBUG] Setting field from saved mapping:', selectedField);
            }
        }
        
        if (selectedField) {
            selector.value = selectedField;
            console.log('[DEBUG] Set initial value to:', selectedField);
            
            // Load the field content immediately
            await this.loadFieldContent(selectedField, selector);
            
            // Trigger change event to update any associated elements
            const event = new Event('change');
            selector.dispatchEvent(event);
        }
        
        // Add event listener
        this.addFieldSelectorEventListener(selector);
    }

    async loadFieldContent(selectedField, selector) {
        console.log('[DEBUG] Loading field content for:', selectedField);
        const targetId = selector.dataset.target;
        if (!targetId) return;

        const targetElement = document.getElementById(targetId);
        if (!targetElement || targetElement.tagName !== 'TEXTAREA') return;

        const fieldInfo = this.fields[selectedField];
        if (!fieldInfo) return;

        // Set data attributes
        targetElement.dataset.dbField = fieldInfo.db_field || selectedField;
        targetElement.dataset.dbTable = fieldInfo.db_table || 'post_development';
        
        try {
            // Fetch and set value
            if (fieldInfo.db_table === 'post_section') {
                // For post_section fields, fetch section data
                const response = await fetch(`/api/workflow/posts/${this.postId}/sections`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.sections && data.sections.length > 0) {
                        targetElement.value = data.sections[0][fieldInfo.db_field] || '';
                    }
                }
            } else {
                // For post_development fields, use cached values or fetch if needed
                if (selectedField in this.fieldValues) {
                    targetElement.value = this.fieldValues[selectedField] || '';
                } else {
                    // Fetch the latest value
                    const response = await fetch(`/api/workflow/posts/${this.postId}/development`);
                    if (response.ok) {
                        const data = await response.json();
                        this.fieldValues = data;
                        targetElement.value = this.fieldValues[selectedField] || '';
                    }
                }
            }
            console.log('[DEBUG] Field content loaded successfully');
        } catch (error) {
            console.error('Error loading field content:', error);
        }
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

        const handler = async (event) => {
            console.log('[DEBUG] Field selector change event:', event.target.value);
            const selectedField = event.target.value;
            const section = event.target.dataset.section;
            
            if (!selectedField) return;
            
            // Load the field content
            await this.loadFieldContent(selectedField, event.target);
            
            // Save the selection
            if (section === 'outputs') {
                await this.saveOutputFieldSelection(selectedField, event.target);
            } else {
                await this.saveFieldMapping(selectedField, event.target);
            }
        };

        selector.addEventListener('change', handler);
        this.eventHandlers.set(selector, handler);
    }

    async saveFieldMapping(fieldName, selector) {
        try {
            const target = selector.dataset.target;
            const section = selector.dataset.section;
            
            if (section === 'inputs') {
                // Save input field selection to localStorage
                const localStorageKey = `multiInputConfig_${this.stage}_${this.substage}`;
                const savedConfig = JSON.parse(localStorage.getItem(localStorageKey) || '[]');
                const inputId = target.replace('input_', '');
                const existingIndex = savedConfig.findIndex(config => config.inputId === inputId);
                
                if (existingIndex >= 0) {
                    savedConfig[existingIndex].selectedField = fieldName;
                } else {
                    savedConfig.push({ inputId, selectedField: fieldName });
                }
                
                localStorage.setItem(localStorageKey, JSON.stringify(savedConfig));
                console.log('[DEBUG] Saved input field selection to localStorage:', { inputId, fieldName });
            }
            
            // Save field mapping to backend
            const response = await fetch('/api/workflow/fields/mappings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    stage: this.stage,
                    substage: this.substage,
                    target: target,
                    field_name: fieldName
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            console.log('[DEBUG] Saved field mapping:', { target, fieldName });
        } catch (error) {
            console.error('Error saving field mapping:', error);
        }
    }

    async saveOutputFieldSelection(fieldName, selector) {
        try {
            const stepId = this.getCurrentStepId();
            if (!stepId) {
                console.warn('Could not determine current step ID');
                return;
            }
            
            const fieldInfo = this.fields[fieldName];
            const payload = {
                output_field: fieldName,
                output_table: fieldInfo?.db_table || 'post_development'
            };
            
            const response = await fetch(`/api/workflow/steps/${stepId}/field_selection`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
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
        // Try to get step ID from panel data attributes
        const panel = document.querySelector('[data-step-id]');
        if (panel) {
            return panel.dataset.stepId;
        }
        
        // Fallback to URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step');
        
        // Map known step names to IDs
        const stepMap = {
            'section_headings': '24',
            'initial_concept': '41',
            'allocate_facts': '15',
            'structure': '14',
            'interesting_facts': '13',
            'provisional_title': '21',
            'idea_scope': '22'
        };
        
        return stepMap[step] || null;
    }
}

// Export the class
export { FieldSelector };
