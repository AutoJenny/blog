/**
 * Field Selector Module
 *
 * Responsibilities:
 * - Manage field mapping dropdowns and selections
 * - Handle field value persistence and loading
 * - Provide field selection API for other modules
 * - Handle field selection for all workflow stages
 *
 * Dependencies: logger.js
 * Dependents: input-manager.js, output-manager.js
 *
 * @version 1.0
 */

// Field selector state
const FIELD_SELECTOR_STATE = {
    // Current state
    currentTable: null,
    currentSection: null, // 'input' or 'output'
    selectedField: null, // Currently selected field from dropdown
    
    // Available data
    availableTables: [],
    fieldsByTable: {}, // { tableName: [fields] }
    
    // User preferences
    tablePreferences: {}, // { stepId: { input: table, output: table } }
    
    // Field data (unchanged)
    fields: {},
    fieldValues: {},
    mappings: {},
    
    // UI state
    initialized: false,
    loading: false,
    tableLoading: false
};

/**
 * Field Selector class
 */
class FieldSelector {
    constructor() {
        this.logger = window.logger;
        this.context = null;
        this.initialized = false;
        this.baseUrl = '';
    }

    /**
     * Initialize the field selector
     */
    async initialize(context) {
        this.logger.trace('fieldSelector', 'initialize', 'enter');
        
        // Validate context
        if (!context) {
            this.logger.warn('fieldSelector', 'No context provided, skipping initialization');
            this.initialized = true;
            return;
        }
        
        this.context = context;
        
        // Determine base URL for API calls
        this.baseUrl = this.getBaseUrl();
        
        try {
            // Check if we're in planning stage OR a specific writing step that should use simple template
            const isPlanningStage = context && context.stage === 'planning';
            const isSimpleInputStep = context && context.stage === 'writing' && context.step === 'header_montage_description';
            
            if (isPlanningStage || isSimpleInputStep) {
                // Initialize planning stage simple input
                await this.initializePlanningInput();
            } else {
                // Initialize dynamic inputs (existing logic)
                await this.initializeTableSelector();
                await this.loadFieldData();
                await this.initializeUI();
            }
            
            // Initialize outputs section
            await this.initializeOutputsSection();
            
            this.initialized = true;
            FIELD_SELECTOR_STATE.initialized = true;
            
            this.logger.info('fieldSelector', `Field selector initialized for ${isPlanningStage ? 'planning' : 'writing'} stage`);
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Failed to initialize field selector:', error);
            throw error;
        }
        
        this.logger.trace('fieldSelector', 'initialize', 'exit');
    }

    /**
     * Get base URL for API calls
     */
    getBaseUrl() {
        const isIntegrated = window.location.hostname === 'localhost' && window.location.port === '5001';
        return isIntegrated ? 'http://localhost:5002' : '';
    }

    /**
     * Load field data from API
     */
    async loadFieldData() {
        this.logger.trace('fieldSelector', 'loadFieldData', 'enter');
        
        if (!this.context) {
            this.logger.warn('fieldSelector', 'No context available, skipping field data loading');
            return;
        }
        
        FIELD_SELECTOR_STATE.loading = true;
        
        try {
            const { post_id, stage } = this.context;
            
            if (!post_id || !stage) {
                throw new Error(`Missing required context: post_id=${post_id}, stage=${stage}`);
            }
            
            // Load field values
            await this.loadFieldValues(post_id, stage);
            
            // Load available fields
            await this.loadAvailableFields(stage);
            
            // Load existing mappings
            await this.loadFieldMappings();
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Failed to load field data:', error);
            throw error;
        } finally {
            FIELD_SELECTOR_STATE.loading = false;
        }
        
        this.logger.trace('fieldSelector', 'loadFieldData', 'exit');
    }

    /**
     * Load field values
     */
    async loadFieldValues(postId, stage) {
        this.logger.debug('fieldSelector', `Loading field values for post ${postId}, stage ${stage}`);
        
        try {
            let response;
            if (stage === 'writing') {
                // For writing stage, get section data
                response = await fetch(`${this.baseUrl}/api/workflow/posts/${postId}/sections`);
            } else {
                // For other stages, get post development data
                response = await fetch(`${this.baseUrl}/api/workflow/posts/${postId}/development`);
            }
            
            if (!response.ok) {
                this.logger.warn('fieldSelector', `Failed to load field values (${response.status}): ${response.statusText}`);
                FIELD_SELECTOR_STATE.fieldValues = {};
                return;
            }
            
            const data = await response.json();
            FIELD_SELECTOR_STATE.fieldValues = data || {};
            this.logger.debug('fieldSelector', `Loaded ${Object.keys(FIELD_SELECTOR_STATE.fieldValues).length} field values`);
        } catch (error) {
            this.logger.error('fieldSelector', 'Failed to load field values:', error);
            FIELD_SELECTOR_STATE.fieldValues = {};
        }
    }

    /**
     * Load available fields
     */
    async loadAvailableFields(stage) {
        this.logger.trace('fieldSelector', 'loadAvailableFields', 'enter');
        
        try {
            let response;
            if (stage === 'writing') {
                // For writing stage, use post_section_fields
                response = await fetch(`${this.baseUrl}/api/workflow/post_section_fields`);
            } else {
                // For other stages, use the original endpoint
                if (!this.context || !this.context.step_id) {
                    this.logger.warn('fieldSelector', 'No step_id available in context for loading available fields');
                    FIELD_SELECTOR_STATE.fields = {};
                    return;
                }
                response = await fetch(`${this.baseUrl}/api/workflow/fields/available?step_id=${this.context.step_id}`);
            }
            
            if (!response.ok) {
                const errorText = await response.text();
                this.logger.warn('fieldSelector', `Failed to load available fields (${response.status}): ${errorText}`);
                FIELD_SELECTOR_STATE.fields = {};
                return;
            }
            
            const fieldsData = await response.json();
            
            // Process fields
            FIELD_SELECTOR_STATE.fields = {};
            if (Array.isArray(fieldsData)) {
                fieldsData.forEach(field => {
                    const fieldName = field.field_name || field.name;
                    FIELD_SELECTOR_STATE.fields[fieldName] = {
                        name: fieldName,
                        display_name: field.display_name || field.name,
                        type: field.type || 'text'
                    };
                });
            }
            
            this.logger.debug('fieldSelector', `Loaded ${Object.keys(FIELD_SELECTOR_STATE.fields).length} available fields`);
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Failed to load available fields:', error);
            FIELD_SELECTOR_STATE.fields = {};
        }
        
        this.logger.trace('fieldSelector', 'loadAvailableFields', 'exit');
    }

    /**
     * Load existing field mappings
     */
    async loadFieldMappings() {
        this.logger.debug('fieldSelector', 'Loading field mappings');
        
        if (!this.context || !this.context.step_id) {
            this.logger.warn('fieldSelector', 'No step_id available in context for loading field mappings');
            FIELD_SELECTOR_STATE.mappings = {};
            return;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/api/workflow/field-mappings?step_id=${this.context.step_id}`);
            
            if (response.ok) {
                const mappings = await response.json();
                FIELD_SELECTOR_STATE.mappings = {};
                if (Array.isArray(mappings)) {
                    mappings.forEach(mapping => {
                        FIELD_SELECTOR_STATE.mappings[mapping.field_name] = mapping.mapped_field;
                    });
                }
                this.logger.debug('fieldSelector', `Loaded ${Object.keys(FIELD_SELECTOR_STATE.mappings).length} field mappings`);
            } else {
                const errorText = await response.text();
                this.logger.warn('fieldSelector', `Failed to load field mappings (${response.status}): ${errorText}`);
                FIELD_SELECTOR_STATE.mappings = {};
            }
        } catch (error) {
            this.logger.error('fieldSelector', 'Failed to load field mappings:', error);
            FIELD_SELECTOR_STATE.mappings = {};
        }
    }

    /**
     * Initialize UI elements
     */
    async initializeUI() {
        this.logger.trace('fieldSelector', 'initializeUI', 'enter');
        
        // Find all field selectors (exclude action-select and system-prompt-select dropdowns)
        const selectors = document.querySelectorAll('.field-selector:not(.action-select):not(#system-prompt-select)');
        this.logger.debug('fieldSelector', `Found ${selectors.length} field selectors`);
        
        for (const selector of selectors) {
            await this.initializeSingleSelector(selector);
        }
        
        this.logger.trace('fieldSelector', 'initializeUI', 'exit');
    }

    /**
     * Initialize a single field selector
     */
    async initializeSingleSelector(selector) {
        const targetId = selector.getAttribute('data-target');
        const section = selector.getAttribute('data-section');
        
        this.logger.debug('fieldSelector', `Initializing selector for target: ${targetId}, section: ${section}`);
        
        // Get saved mapping first
        const savedMapping = FIELD_SELECTOR_STATE.mappings[targetId];
        
        // For input field selector, handle table-aware restoration
        if (targetId === 'input-content') {
            // Check if we have a saved mapping with table info
            if (savedMapping && savedMapping.includes('.')) {
                const tableName = savedMapping.split('.')[0];
                const fieldName = savedMapping.split('.')[1];
                
                this.logger.debug('fieldSelector', `Found saved table-aware mapping: ${tableName}.${fieldName}`);
                
                // Set the table selector first
                const tableSelector = document.getElementById('table-selector');
                if (tableSelector) {
                    tableSelector.value = tableName;
                    
                    // Load fields for this table and restore selection
                    await this.loadTableFields(tableName);
                    await this.populateFieldSelector(tableName);
                    
                    // Now set the field selection
                    selector.value = savedMapping;
                    await this.loadFieldContent(targetId, savedMapping);
                    
                    this.logger.debug('fieldSelector', `Restored table-aware mapping: ${tableName} -> ${fieldName}`);
                } else {
                    // Fallback: just set the field selector to show the mapping
                    selector.innerHTML = '<option value="">Select a table first...</option>';
                    selector.value = savedMapping;
                }
            } else {
                // No saved mapping or legacy format
                selector.innerHTML = '<option value="">Select a table first...</option>';
                
                // If we have a saved mapping in legacy format, preserve it
                if (savedMapping) {
                    selector.value = savedMapping;
                }
            }
        } else {
            // For other selectors (like output), use the legacy approach for now
            selector.innerHTML = '<option value="">Select field...</option>';
            
            // Add field options from legacy fields
            const fieldNames = Object.keys(FIELD_SELECTOR_STATE.fields).sort();
            for (const fieldName of fieldNames) {
                const field = FIELD_SELECTOR_STATE.fields[fieldName];
                const option = document.createElement('option');
                option.value = fieldName;
                option.textContent = field.display_name;
                selector.appendChild(option);
            }
            
            // Set saved selection if any
            if (savedMapping) {
                selector.value = savedMapping;
                await this.loadFieldContent(targetId, savedMapping);
            }
        }
        
        // Add event listener
        this.addSelectorEventListener(selector);
    }

    /**
     * Add event listener to field selector
     */
    addSelectorEventListener(selector) {
        const handler = async (event) => {
            const selectedField = event.target.value;
            const targetId = selector.getAttribute('data-target');
            const section = selector.getAttribute('data-section');
            
            this.logger.debug('fieldSelector', `Field selection changed: ${targetId} -> ${selectedField}`);
            
            // Store selected field in global state
            FIELD_SELECTOR_STATE.selectedField = selectedField;
            
            // Load content for selected field
            await this.loadFieldContent(targetId, selectedField);
            
            // Save field mapping
            await this.saveFieldMapping(targetId, selectedField, section);
        };
        
        selector.addEventListener('change', handler);
    }

    /**
     * Load field content into target element
     */
    async loadFieldContent(targetId, selectedField) {
        const targetElement = document.getElementById(targetId);
        
        if (!targetElement) {
            this.logger.warn('fieldSelector', `Target element not found: ${targetId}`);
            return;
        }
        
        if (!selectedField) {
            // Clear content
            targetElement.value = '';
            return;
        }
        
        try {
            let content = '';
            
            // Check if we have the content in local state first
            if (FIELD_SELECTOR_STATE.fieldValues[selectedField]) {
                content = FIELD_SELECTOR_STATE.fieldValues[selectedField];
            } else {
                // Load content from API based on table-aware field ID
                content = await this.loadFieldContentFromAPI(selectedField);
            }
            
            targetElement.value = content || '';
            this.logger.debug('fieldSelector', `Loaded content for ${selectedField} into ${targetId}`);
            
        } catch (error) {
            this.logger.error('fieldSelector', `Error loading content for ${selectedField}:`, error);
            targetElement.value = '';
        }
    }

    /**
     * Load field content from API based on table-aware field ID
     */
    async loadFieldContentFromAPI(fieldId) {
        this.logger.trace('fieldSelector', 'loadFieldContentFromAPI', 'enter', { fieldId });
        
        try {
            // Parse field ID to get table and field name
            let tableName, fieldName;
            
            if (fieldId.includes('.')) {
                // Full field ID format: table.field
                [tableName, fieldName] = fieldId.split('.');
            } else {
                // Legacy format: just field name
                tableName = FIELD_SELECTOR_STATE.currentTable || 'post_development';
                fieldName = fieldId;
            }
            
            // Determine the appropriate API endpoint based on table
            let apiUrl;
            if (tableName === 'post_section') {
                // Use the post_section_fields endpoint
                apiUrl = `${this.baseUrl}/api/workflow/post_section_fields`;
            } else if (tableName === 'post') {
                // Use the post data endpoint
                const postId = this.context?.post_id;
                if (!postId) {
                    throw new Error('No post_id available for post table');
                }
                apiUrl = `${this.baseUrl}/api/workflow/posts/${postId}/post`;
            } else {
                // Default to post_development
                const postId = this.context?.post_id;
                if (!postId) {
                    throw new Error('No post_id available for post_development table');
                }
                apiUrl = `${this.baseUrl}/api/workflow/posts/${postId}/development`;
            }
            
            // Load the data
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
            
            const data = await response.json();
            
            // Extract the field value
            const fieldValue = data[fieldName] || '';
            
            // Cache the value in local state
            FIELD_SELECTOR_STATE.fieldValues[fieldId] = fieldValue;
            
            this.logger.debug('fieldSelector', `Loaded content from API: ${fieldId} = ${fieldValue}`);
            return fieldValue;
            
        } catch (error) {
            this.logger.error('fieldSelector', `Error loading field content from API for ${fieldId}:`, error);
            throw error;
        }
        
        this.logger.trace('fieldSelector', 'loadFieldContentFromAPI', 'exit');
    }

    /**
     * Save field mapping
     */
    async saveFieldMapping(fieldName, selectedField, section) {
        this.logger.debug('fieldSelector', `Saving field mapping with step_id: ${this.context.step_id}`);
        this.logger.debug('fieldSelector', `Context:`, this.context);
        
        if (!this.context.step_id) {
            throw new Error('No step_id available in context for saving field mapping');
        }
        
        try {
            // Update local state first
            FIELD_SELECTOR_STATE.mappings[fieldName] = selectedField;
            
            // Prepare all current mappings
            const allMappings = [];
            for (const [key, value] of Object.entries(FIELD_SELECTOR_STATE.mappings)) {
                if (value) { // Only include mappings that have a value
                    // Extract table name from full field ID if present
                    let tableName = 'post_development'; // default
                    if (value.includes('.')) {
                        tableName = value.split('.')[0];
                    } else if (FIELD_SELECTOR_STATE.currentTable) {
                        tableName = FIELD_SELECTOR_STATE.currentTable;
                    }
                    
                    allMappings.push({
                        field_name: key,
                        mapped_field: value,
                        section: this.getSectionForKey(key),
                        table_name: tableName
                    });
                }
            }
            
            const requestData = {
                step_id: this.context.step_id,
                mappings: allMappings
            };
            
            this.logger.debug('fieldSelector', 'Sending request data:', requestData);
            
            const response = await fetch(`${this.baseUrl}/api/workflow/field-mappings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                this.logger.error('fieldSelector', `HTTP ${response.status} response:`, errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            this.logger.debug('fieldSelector', `Field mapping saved: ${fieldName} -> ${selectedField}`);
            
            // Emit event for message manager
            document.dispatchEvent(new CustomEvent('fieldMappingsChanged', {
                detail: { 
                    fieldName, 
                    selectedField, 
                    allMappings: FIELD_SELECTOR_STATE.mappings 
                }
            }));
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error saving field mapping:', error);
            throw error;
        }
    }
    
    /**
     * Get section for a given field key
     */
    getSectionForKey(fieldKey) {
        // Map field keys to sections based on data-target attributes
        if (fieldKey === 'input-content') return 'input';
        if (fieldKey === 'output-content') return 'output';
        return 'unknown';
    }

    /**
     * Get field value
     */
    getFieldValue(fieldName) {
        return FIELD_SELECTOR_STATE.fieldValues[fieldName] || '';
    }

    /**
     * Get field mapping
     */
    getFieldMapping(fieldName) {
        return FIELD_SELECTOR_STATE.mappings[fieldName] || null;
    }

    /**
     * Get available fields
     */
    getAvailableFields() {
        return { ...FIELD_SELECTOR_STATE.fields };
    }

    /**
     * Refresh field data
     */
    async refresh() {
        this.logger.info('fieldSelector', 'Refreshing field data');
        await this.loadFieldData();
        await this.initializeUI();
    }

    /**
     * Get current state
     */
    getState() {
        return { ...FIELD_SELECTOR_STATE };
    }

    /**
     * Load available tables
     */
    async loadAvailableTables() {
        this.logger.trace('fieldSelector', 'loadAvailableTables', 'enter');
        
        try {
            const response = await fetch(`${this.baseUrl}/api/workflow/available-tables`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
            
            const tables = await response.json();
            FIELD_SELECTOR_STATE.availableTables = tables;
            this.populateTableSelector();
            
            this.logger.debug('fieldSelector', `Loaded ${tables.length} available tables`);
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error loading available tables:', error);
            throw error;
        }
        
        this.logger.trace('fieldSelector', 'loadAvailableTables', 'exit');
    }

    /**
     * Load fields for a specific table
     */
    async loadTableFields(tableName) {
        this.logger.trace('fieldSelector', 'loadTableFields', 'enter', { tableName });
        
        // Return if already loaded
        if (FIELD_SELECTOR_STATE.fieldsByTable[tableName]) {
            this.logger.debug('fieldSelector', `Fields for table ${tableName} already loaded`);
            return;
        }
        
        try {
            FIELD_SELECTOR_STATE.tableLoading = true;
            
            const response = await fetch(`${this.baseUrl}/api/workflow/fields/by-table?table=${tableName}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
            
            const fields = await response.json();
            FIELD_SELECTOR_STATE.fieldsByTable[tableName] = fields;
            
            this.logger.debug('fieldSelector', `Loaded ${fields.length} fields for table ${tableName}`);
            
        } catch (error) {
            this.logger.error('fieldSelector', `Error loading fields for table ${tableName}:`, error);
            throw error;
        } finally {
            FIELD_SELECTOR_STATE.tableLoading = false;
        }
        
        this.logger.trace('fieldSelector', 'loadTableFields', 'exit');
    }

    /**
     * Populate table selector dropdown
     */
    populateTableSelector() {
        const tableSelector = document.getElementById('table-selector');
        if (!tableSelector) {
            this.logger.warn('fieldSelector', 'Table selector not found');
            return;
        }
        
        // Clear existing options
        tableSelector.innerHTML = '<option value="">Select a table...</option>';
        
        // Add table options
        FIELD_SELECTOR_STATE.availableTables.forEach(table => {
            const option = document.createElement('option');
            option.value = table.name;
            option.textContent = `${table.display_name} - ${table.description}`;
            tableSelector.appendChild(option);
        });
        
        this.logger.debug('fieldSelector', 'Table selector populated');
    }

    /**
     * Handle table change
     */
    async handleTableChange(newTable) {
        this.logger.trace('fieldSelector', 'handleTableChange', 'enter', { newTable });
        
        try {
            // Show loading state
            this.showTableLoadingState(true);
            
            // 1. Update current table
            FIELD_SELECTOR_STATE.currentTable = newTable;
            
            // 2. Load fields if not already loaded
            await this.loadTableFields(newTable);
            
            // 3. Update field dropdown with new table's fields
            this.populateFieldSelector(newTable);
            
            // 4. Restore saved field selections for this table
            this.restoreFieldSelectionsForTable(newTable);
            
            // 5. Update UI elements
            this.updateTableDisplay(newTable);
            
            // 6. Save user preference
            await this.saveTablePreference(newTable);
            
            this.logger.info('fieldSelector', `Table changed to ${newTable}`);
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error handling table change:', error);
            // Show error state
            this.showTableErrorState(error.message);
            throw error;
        } finally {
            // Hide loading state
            this.showTableLoadingState(false);
        }
        
        this.logger.trace('fieldSelector', 'handleTableChange', 'exit');
    }

    /**
     * Show/hide table loading state
     */
    showTableLoadingState(show) {
        const tableSelector = document.getElementById('table-selector');
        const fieldSelector = document.getElementById('input-field-select');
        const inputGroup = document.querySelector('.input-field-group');
        
        if (show) {
            if (tableSelector) tableSelector.classList.add('loading');
            if (fieldSelector) fieldSelector.disabled = true;
            if (inputGroup) inputGroup.classList.add('loading');
        } else {
            if (tableSelector) tableSelector.classList.remove('loading');
            if (fieldSelector) fieldSelector.disabled = false;
            if (inputGroup) inputGroup.classList.remove('loading');
        }
    }

    /**
     * Show table error state
     */
    showTableErrorState(errorMessage) {
        const tableDescription = document.getElementById('table-description');
        if (tableDescription) {
            tableDescription.textContent = `Error: ${errorMessage}`;
            tableDescription.style.color = '#ef4444';
            tableDescription.style.background = 'rgba(239, 68, 68, 0.1)';
            tableDescription.style.borderLeftColor = '#ef4444';
            
            // Clear error after 5 seconds
            setTimeout(() => {
                tableDescription.textContent = '';
                tableDescription.style.color = '';
                tableDescription.style.background = '';
                tableDescription.style.borderLeftColor = '';
            }, 5000);
        }
    }

    /**
     * Restore saved field selections for the current table
     */
    restoreFieldSelectionsForTable(tableName) {
        this.logger.trace('fieldSelector', 'restoreFieldSelectionsForTable', 'enter', { tableName });
        
        try {
            // Find the input field selector
            const fieldSelector = document.getElementById('input-field-select');
            if (!fieldSelector) {
                this.logger.warn('fieldSelector', 'Input field selector not found');
                return;
            }
            
            // Look for saved mappings that belong to this table
            const savedMapping = FIELD_SELECTOR_STATE.mappings['input-content'];
            if (savedMapping) {
                let belongsToCurrentTable = false;
                let fieldName = savedMapping;
                
                // Handle table-aware format (table.field)
                if (savedMapping.includes('.')) {
                    const mappingTable = savedMapping.split('.')[0];
                    fieldName = savedMapping.split('.')[1];
                    belongsToCurrentTable = (mappingTable === tableName);
                } else {
                    // Handle legacy format (just field name)
                    // For legacy format, we assume it belongs to the current table
                    // since we don't have table context in the old format
                    belongsToCurrentTable = true;
                }
                
                if (belongsToCurrentTable) {
                    // Restore the selection
                    fieldSelector.value = savedMapping;
                    this.loadFieldContent('input-content', savedMapping);
                    this.logger.debug('fieldSelector', `Restored field selection: ${savedMapping} for table ${tableName}`);
                } else {
                    // Clear the selection if it's from a different table
                    fieldSelector.value = '';
                    const targetElement = document.getElementById('input-content');
                    if (targetElement) {
                        targetElement.value = '';
                    }
                    this.logger.debug('fieldSelector', `Cleared field selection (different table: ${savedMapping} vs ${tableName})`);
                }
            } else {
                this.logger.debug('fieldSelector', 'No saved mapping found for input-content');
            }
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error restoring field selections:', error);
        }
        
        this.logger.trace('fieldSelector', 'restoreFieldSelectionsForTable', 'exit');
    }

    /**
     * Populate field selector with fields from specific table
     */
    populateFieldSelector(tableName) {
        const fieldSelector = document.getElementById('input-field-select');
        if (!fieldSelector) {
            this.logger.warn('fieldSelector', 'Field selector not found');
            return;
        }
        
        // Clear existing options
        fieldSelector.innerHTML = '<option value="">Select a field...</option>';
        
        // Get fields for the selected table
        const fields = FIELD_SELECTOR_STATE.fieldsByTable[tableName] || [];
        
        // Add field options
        fields.forEach(field => {
            const option = document.createElement('option');
            option.value = field.full_field_id;
            option.textContent = field.display_name;
            fieldSelector.appendChild(option);
        });
        
        this.logger.debug('fieldSelector', `Field selector populated with ${fields.length} fields from ${tableName}`);
    }

    /**
     * Update table display in UI
     */
    updateTableDisplay(tableName) {
        // Update database indicator
        const currentTableDisplay = document.getElementById('current-table-display');
        if (currentTableDisplay) {
            currentTableDisplay.textContent = tableName;
        }
        
        // Update table description
        const tableDescription = document.getElementById('table-description');
        if (tableDescription) {
            const table = FIELD_SELECTOR_STATE.availableTables.find(t => t.name === tableName);
            if (table) {
                tableDescription.textContent = table.description;
            } else {
                tableDescription.textContent = '';
            }
        }
    }

    /**
     * Load user's table preferences
     */
    async loadTablePreferences() {
        this.logger.trace('fieldSelector', 'loadTablePreferences', 'enter');
        
        if (!this.context || !this.context.step_id) {
            this.logger.warn('fieldSelector', 'No step_id available, skipping preference loading');
            return;
        }
        
        try {
            const stepId = this.context.step_id;
            const section = 'input'; // For now, just handle input section
            
            const response = await fetch(`${this.baseUrl}/api/workflow/table-preferences?step_id=${stepId}&section=${section}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
            
            const result = await response.json();
            
            // Store preference
            if (!FIELD_SELECTOR_STATE.tablePreferences[stepId]) {
                FIELD_SELECTOR_STATE.tablePreferences[stepId] = {};
            }
            FIELD_SELECTOR_STATE.tablePreferences[stepId][section] = result.preferred_table;
            
            this.logger.debug('fieldSelector', `Loaded table preference: ${result.preferred_table}`);
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error loading table preferences:', error);
            // Don't throw - preferences are optional
        }
        
        this.logger.trace('fieldSelector', 'loadTablePreferences', 'exit');
    }

    /**
     * Save user's table preference
     */
    async saveTablePreference(tableName) {
        this.logger.trace('fieldSelector', 'saveTablePreference', 'enter', { tableName });
        
        if (!this.context || !this.context.step_id) {
            this.logger.warn('fieldSelector', 'No step_id available, skipping preference saving');
            return;
        }
        
        try {
            const stepId = this.context.step_id;
            const section = 'input'; // For now, just handle input section
            
            const response = await fetch(`${this.baseUrl}/api/workflow/table-preferences`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    step_id: stepId,
                    section: section,
                    preferred_table: tableName
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
            
            // Update local state
            if (!FIELD_SELECTOR_STATE.tablePreferences[stepId]) {
                FIELD_SELECTOR_STATE.tablePreferences[stepId] = {};
            }
            FIELD_SELECTOR_STATE.tablePreferences[stepId][section] = tableName;
            
            this.logger.debug('fieldSelector', `Saved table preference: ${tableName}`);
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error saving table preference:', error);
            // Don't throw - preferences are optional
        }
        
        this.logger.trace('fieldSelector', 'saveTablePreference', 'exit');
    }

    /**
     * Set default table based on context
     */
    async setDefaultTable() {
        this.logger.trace('fieldSelector', 'setDefaultTable', 'enter');
        
        try {
            // Check for saved field mappings first (highest priority)
            const savedInputMapping = FIELD_SELECTOR_STATE.mappings['input-content'];
            if (savedInputMapping && savedInputMapping.includes('.')) {
                const defaultTable = savedInputMapping.split('.')[0];
                this.logger.debug('fieldSelector', `Using table from saved mapping: ${defaultTable}`);
                await this.handleTableChange(defaultTable);
                return;
            }
            
            // Check for user preference second
            if (this.context && this.context.step_id) {
                const stepId = this.context.step_id;
                const section = 'input';
                const preference = FIELD_SELECTOR_STATE.tablePreferences[stepId]?.[section];
                
                if (preference) {
                    this.logger.debug('fieldSelector', `Using user preference: ${preference}`);
                    await this.handleTableChange(preference);
                    return;
                }
            }
            
            // Fallback to current hardcoded logic
            if (this.context && this.context.stage === 'writing') {
                this.logger.debug('fieldSelector', 'Using hardcoded default for writing stage: post_section');
                await this.handleTableChange('post_section');
            } else {
                this.logger.debug('fieldSelector', 'Using hardcoded default: post_development');
                await this.handleTableChange('post_development');
            }
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error setting default table:', error);
            // Fallback to post_development
            await this.handleTableChange('post_development');
        }
        
        this.logger.trace('fieldSelector', 'setDefaultTable', 'exit');
    }

    /**
     * Initialize table selector
     */
    async initializeTableSelector() {
        this.logger.trace('fieldSelector', 'initializeTableSelector', 'enter');
        
        try {
            // Load available tables
            await this.loadAvailableTables();
            
            // Load user preferences
            await this.loadTablePreferences();
            
            // Set up table selector event listener
            const tableSelector = document.getElementById('table-selector');
            if (tableSelector) {
                tableSelector.addEventListener('change', async (event) => {
                    const selectedTable = event.target.value;
                    if (selectedTable) {
                        await this.handleTableChange(selectedTable);
                    }
                });
            }
            
            // Set default table
            await this.setDefaultTable();
            
            this.logger.debug('fieldSelector', 'Table selector initialized');
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error initializing table selector:', error);
            throw error;
        }
        
        this.logger.trace('fieldSelector', 'initializeTableSelector', 'exit');
    }

    /**
     * Initialize planning input
     */
    async initializePlanningInput() {
        this.logger.trace('fieldSelector', 'initializePlanningInput', 'enter');
        
        try {
            // Check if this is a writing step that needs field selection
            const isWritingStep = this.context && this.context.stage === 'writing' && this.context.step === 'header_montage_description';
            
            if (isWritingStep) {
                // For writing step: load field values and set up field selection
                await this.loadFieldValues(this.context.post_id, 'writing');
                await this.setupFieldSelectionForWritingStep();
            } else {
                // For planning stage: set up simple input field with field selection
                await this.loadFieldValues(this.context.post_id, 'planning');
                await this.setupFieldSelectionForPlanningStep();
            }
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error initializing planning input:', error);
            throw error;
        }
        
        this.logger.trace('fieldSelector', 'initializePlanningInput', 'exit');
    }



    /**
     * Set up field selection for planning step with simple input template
     */
    async setupFieldSelectionForPlanningStep() {
        this.logger.trace('fieldSelector', 'setupFieldSelectionForPlanningStep', 'enter');
        
        try {
            // Create a field selector dropdown in the planning-input section
            const planningInputSection = document.querySelector('.planning-input-section');
            if (!planningInputSection) {
                this.logger.warn('fieldSelector', 'Planning input section not found');
                return;
            }
            
            // Find the existing textarea
            const planningInput = document.getElementById('planning-input');
            if (!planningInput) {
                this.logger.warn('fieldSelector', 'Planning input element not found');
                return;
            }
            
            // Create field selector dropdown
            const fieldSelector = document.createElement('select');
            fieldSelector.id = 'field-select';
            fieldSelector.className = 'field-selector-dropdown';
            fieldSelector.style.cssText = 'width: 100%; padding: 8px; border: 1px solid var(--llm-border); border-radius: 4px; background: var(--llm-surface); color: var(--llm-text); margin-bottom: 10px;';
            
            // Add default option
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a field...';
            fieldSelector.appendChild(defaultOption);
            
            // Add field options from post_development table
            const fieldOptions = [
                { value: 'post_development.basic_idea', label: 'Basic Idea' },
                { value: 'post_development.expanded_idea', label: 'Expanded Idea' },
                { value: 'post_development.section_headings', label: 'Section Headings' },
                { value: 'post_development.idea_seed', label: 'Idea Seed' }
            ];
            
            fieldOptions.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.value;
                optionElement.textContent = option.label;
                fieldSelector.appendChild(optionElement);
            });
            
            // Insert the dropdown before the textarea
            planningInput.parentNode.insertBefore(fieldSelector, planningInput);
            
            // Set up event listener for field selection
            fieldSelector.addEventListener('change', async (event) => {
                const selectedField = event.target.value;
                if (selectedField) {
                    // Store selected field in global state
                    FIELD_SELECTOR_STATE.selectedField = selectedField;
                    
                    // Load content for selected field
                    const fieldName = selectedField.split('.').pop();
                    let fieldContent = FIELD_SELECTOR_STATE.fieldValues[fieldName] || '';
                    
                    // If not found, try to load from API
                    if (!fieldContent) {
                        this.logger.debug('fieldSelector', `Field content not found in state, loading from API: ${fieldName}`);
                        fieldContent = await this.loadFieldContentFromAPI(selectedField);
                    }
                    
                    // Update the textarea with selected field content
                    planningInput.value = fieldContent;
                    
                    // Update the label to show the selected field name
                    const label = planningInput.parentNode.querySelector('.field-label');
                    if (label) {
                        const selectedOption = fieldOptions.find(opt => opt.value === selectedField);
                        if (selectedOption) {
                            label.textContent = `${selectedOption.label}:`;
                        }
                    }
                    
                    this.logger.debug('fieldSelector', `Field selection changed: ${selectedField} -> ${fieldContent.substring(0, 50)}...`);
                }
            });
            
            // Set default selection to section_headings for planning
            fieldSelector.value = 'post_development.section_headings';
            fieldSelector.dispatchEvent(new Event('change'));
            
            this.logger.debug('fieldSelector', 'Field selection for planning step initialized');
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error setting up field selection for planning step:', error);
            throw error;
        }
        
        this.logger.trace('fieldSelector', 'setupFieldSelectionForPlanningStep', 'exit');
    }

    /**
     * Set up field selection for writing step with simple input template
     */
    async setupFieldSelectionForWritingStep() {
        this.logger.trace('fieldSelector', 'setupFieldSelectionForWritingStep', 'enter');
        
        try {
            // Create a field selector dropdown in the planning-input section
            const planningInputSection = document.querySelector('.planning-input-section');
            if (!planningInputSection) {
                this.logger.warn('fieldSelector', 'Planning input section not found');
                return;
            }
            
            // Find the existing textarea
            const planningInput = document.getElementById('planning-input');
            if (!planningInput) {
                this.logger.warn('fieldSelector', 'Planning input element not found');
                return;
            }
            
            // Create field selector dropdown
            const fieldSelector = document.createElement('select');
            fieldSelector.id = 'field-select';
            fieldSelector.className = 'field-selector-dropdown';
            fieldSelector.style.cssText = 'width: 100%; padding: 8px; border: 1px solid var(--llm-border); border-radius: 4px; background: var(--llm-surface); color: var(--llm-text); margin-bottom: 10px;';
            
            // Add default option
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a field...';
            fieldSelector.appendChild(defaultOption);
            
            // Add field options from post_development table
            const fieldOptions = [
                { value: 'post_development.basic_idea', label: 'Basic Idea' },
                { value: 'post_development.expanded_idea', label: 'Expanded Idea' },
                { value: 'post_development.section_headings', label: 'Section Headings' },
                { value: 'post_development.idea_seed', label: 'Idea Seed' }
            ];
            
            fieldOptions.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.value;
                optionElement.textContent = option.label;
                fieldSelector.appendChild(optionElement);
            });
            
            // Insert the dropdown before the textarea
            planningInput.parentNode.insertBefore(fieldSelector, planningInput);
            
            // Set up event listener for field selection
            fieldSelector.addEventListener('change', async (event) => {
                const selectedField = event.target.value;
                if (selectedField) {
                    // Store selected field in global state
                    FIELD_SELECTOR_STATE.selectedField = selectedField;
                    
                    // Load content for selected field
                    const fieldName = selectedField.split('.').pop();
                    let fieldContent = FIELD_SELECTOR_STATE.fieldValues[fieldName] || '';
                    
                    // If not found, try to load from API
                    if (!fieldContent) {
                        this.logger.debug('fieldSelector', `Field content not found in state, loading from API: ${fieldName}`);
                        fieldContent = await this.loadFieldContentFromAPI(selectedField);
                    }
                    
                    // Update the textarea with selected field content
                    planningInput.value = fieldContent;
                    
                    this.logger.debug('fieldSelector', `Field selection changed: ${selectedField} -> ${fieldContent.substring(0, 50)}...`);
                }
            });
            
            // Set default selection to section_headings
            fieldSelector.value = 'post_development.section_headings';
            fieldSelector.dispatchEvent(new Event('change'));
            
            this.logger.debug('fieldSelector', 'Field selection for writing step initialized');
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error setting up field selection for writing step:', error);
            throw error;
        }
        
        this.logger.trace('fieldSelector', 'setupFieldSelectionForWritingStep', 'exit');
    }

    /**
     * Initialize outputs section with correct table and fields
     */
    async initializeOutputsSection() {
        this.logger.trace('fieldSelector', 'initializeOutputsSection', 'enter');
        
        try {
            // Determine the correct output table based on step
            let outputTable = 'post_development'; // default
            let outputTableDisplay = 'post_development (fixed)';
            
            // Note: header_montage_description step now uses post_development table for outputs
            
            // Update the table display indicator
            const tableDisplayElement = document.getElementById('output-table-display');
            if (tableDisplayElement) {
                tableDisplayElement.textContent = outputTableDisplay;
            }
            
            // Load output fields from the correct table
            await this.loadOutputFields(outputTable);
            
            this.logger.debug('fieldSelector', `Outputs section initialized for table: ${outputTable}`);
            
        } catch (error) {
            this.logger.error('fieldSelector', 'Error initializing outputs section:', error);
        }
        
        this.logger.trace('fieldSelector', 'initializeOutputsSection', 'exit');
    }
    
    /**
     * Load output fields from specified table
     */
    async loadOutputFields(tableName) {
        this.logger.trace('fieldSelector', 'loadOutputFields', 'enter');
        
        try {
            const response = await fetch(`${this.baseUrl}/api/workflow/fields/by-table?table=${tableName}`);
            if (!response.ok) {
                this.logger.warn('fieldSelector', `Failed to load output fields for table ${tableName}: ${response.status}`);
                return;
            }
            
            const fields = await response.json();
            
            // Populate the output field selector
            const outputFieldSelect = document.getElementById('output-field-select');
            if (outputFieldSelect) {
                // Clear existing options
                outputFieldSelect.innerHTML = '<option value="">Select output field...</option>';
                
                // Add field options
                fields.forEach(field => {
                    const option = document.createElement('option');
                    option.value = field.full_field_id;
                    option.textContent = field.display_name;
                    outputFieldSelect.appendChild(option);
                });
                
                this.logger.debug('fieldSelector', `Loaded ${fields.length} output fields for table ${tableName}`);
            }
            
        } catch (error) {
            this.logger.error('fieldSelector', `Error loading output fields for table ${tableName}:`, error);
        }
        
        this.logger.trace('fieldSelector', 'loadOutputFields', 'exit');
    }

    /**
     * Cleanup
     */
    destroy() {
        this.logger.info('fieldSelector', 'Destroying field selector');
        this.initialized = false;
        FIELD_SELECTOR_STATE.initialized = false;
    }
}

// Create and export global instance
const fieldSelector = new FieldSelector();
window.fieldSelector = fieldSelector;
window.FIELD_SELECTOR_STATE = FIELD_SELECTOR_STATE;

// Register module with orchestrator
if (window.registerLLMModule) {
    window.registerLLMModule('fieldSelector', fieldSelector);
    console.log('[LLM-ACTIONS] Field Selector Module registered successfully');
} else {
    console.warn('[LLM-ACTIONS] registerLLMModule not available, Field Selector Module not registered');
}

// Log initialization
if (window.logger) {
    window.logger.info('fieldSelector', 'Field Selector Module loaded');
} 