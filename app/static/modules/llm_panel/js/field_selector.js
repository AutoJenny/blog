/**
 * Field Selector JavaScript
 * Handles field mapping dropdowns and field value persistence in LLM panels
 */

export class FieldSelector {
    static instance = null;

    constructor() {
        // Prevent multiple instances
        if (FieldSelector.instance) {
            console.log('[DEBUG] Returning existing FieldSelector instance');
            return FieldSelector.instance;
        }

        console.log('[DEBUG] Creating new FieldSelector instance');
        this.fields = {};
        this.fieldValues = {};
        this.postId = this.getPostIdFromUrl();
        this.stage = this.getStageFromUrl();
        this.substage = this.getSubstageFromUrl();
        this.isInitializing = true;
        this.initialized = false;
        this.eventHandlers = new WeakMap();
        
        this.initialize();
        FieldSelector.instance = this;
    }

    async initialize() {
        console.log('[DEBUG] Initializing FieldSelector');
        await this.fetchFields();
        await this.fetchFieldValues();
        this.initializeSelectors();
        this.isInitializing = false;
        this.initialized = true;
    }

    async fetchFields() {
        console.log('[DEBUG] Fetching fields');
        try {
            const response = await fetch(`/workflow/api/field_mappings/?stage=${this.stage}&substage=${this.substage}`);
            const data = await response.json();
            this.fields = data;
            console.log('[DEBUG] Fields fetched:', this.fields);
        } catch (error) {
            console.error('Error fetching fields:', error);
        }
    }

    async fetchFieldValues() {
        console.log('[DEBUG] Fetching field values');
        try {
            const response = await fetch(`/blog/api/v1/post/${this.postId}/development`);
            const data = await response.json();
            this.fieldValues = data;
            console.log('[DEBUG] Field values fetched:', this.fieldValues);
        } catch (error) {
            console.error('Error fetching field values:', error);
        }
    }

    initializeSelectors() {
        console.log('[DEBUG] Initializing selectors');
        const selectors = document.querySelectorAll('.field-selector');
        selectors.forEach(selector => {
            if (this.eventHandlers.has(selector)) {
                console.log('[DEBUG] Selector already initialized, skipping');
                return;
            }

            const section = selector.dataset.section;
            const substage = selector.dataset.currentSubstage;
            const targetId = selector.dataset.target;

            console.log(`[DEBUG] Initializing selector for ${section}/${substage}/${targetId}`);

            // Clear existing options
            selector.innerHTML = '';

            // Add default option
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a field...';
            selector.appendChild(defaultOption);

            // Add field options
            if (this.fields[this.stage]?.[substage]?.[section]) {
                this.fields[this.stage][substage][section].forEach(field => {
                    const option = document.createElement('option');
                    option.value = field.field_name;
                    option.textContent = field.display_name;
                    selector.appendChild(option);
                });
            }

            // Set initial value and update textarea
            const textarea = document.getElementById(targetId);
            if (textarea) {
                // Get the current value from the step config
                const currentField = textarea.dataset.dbField;
                
                if (currentField) {
                    console.log(`[DEBUG] Setting initial value for ${targetId} to ${currentField}`);
                    selector.value = currentField;
                    textarea.value = this.fieldValues[currentField] || '';
                }
            }

            // Add change event handler
            const handler = this.handleFieldSelection.bind(this);
            this.eventHandlers.set(selector, handler);
            selector.addEventListener('change', handler);
        });
    }

    getCurrentStep() {
        // First try to get from URL query parameters
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step');
        console.log('[DEBUG] Step from URL params:', step);

        // Then try to get from data attribute on the panel
        const panel = document.querySelector('[data-current-step]');
        console.log('[DEBUG] Panel data-current-step:', panel?.dataset?.currentStep);

        if (step) return step;
        if (panel && panel.dataset.currentStep) return panel.dataset.currentStep;

        // Default to 'initial'
        console.log('[DEBUG] Using default step: initial');
        return 'initial';
    }

    async handleFieldSelection(event) {
        if (this.isInitializing) {
            console.log('[DEBUG] Still initializing, skipping field selection handler');
            return;
        }

        const selector = event.target;
        const targetId = selector.dataset.target;
        const section = selector.dataset.section;
        const fieldName = selector.value;
        const step = this.getCurrentStep();

        console.log(`[DEBUG] Handling field selection:`, {
            targetId,
            fieldName,
            section,
            stage: this.stage,
            substage: this.substage,
            step
        });

        const textarea = document.getElementById(targetId);
        if (textarea) {
            // Update the textarea value with the selected field's value
            textarea.value = this.fieldValues[fieldName] || '';
            // Update the data attribute to maintain state
            textarea.dataset.dbField = fieldName;

            // Update the field mapping in the step config
            try {
                const response = await fetch('/workflow/api/update_field_mapping/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        target_id: targetId,
                        field_name: fieldName,
                        section: section,
                        stage: this.stage,
                        substage: this.substage,
                        step: step
                    })
                });

                const result = await response.json();
                if (result.error) {
                    console.error('[DEBUG] Error updating field mapping:', result.error);
                } else {
                    console.log('[DEBUG] Field mapping updated:', result);
                }
            } catch (error) {
                console.error('Error updating field mapping:', error);
            }
        }
    }

    getPostIdFromUrl() {
        const match = window.location.pathname.match(/\/posts\/(\d+)/);
        return match ? match[1] : null;
    }

    getStageFromUrl() {
        const match = window.location.pathname.match(/\/posts\/\d+\/([^/]+)/);
        return match ? match[1] : null;
    }

    getSubstageFromUrl() {
        const match = window.location.pathname.match(/\/posts\/\d+\/[^/]+\/([^/]+)/);
        return match ? match[1] : null;
    }
}

// Initialize the field selector when the module is loaded
if (!window.fieldSelector) {
    console.log('Creating global fieldSelector instance');
    window.fieldSelector = new FieldSelector();
} else {
    console.log('Global fieldSelector already exists');
} 