/**
 * Field Selector JavaScript
 * Handles field mapping dropdowns and field value persistence in LLM panels
 */

class FieldSelector {
    constructor(postId, stage, substage) {
        this.fields = {};
        this.postId = postId || this.getPostIdFromUrl();
        this.stage = stage || this.getStageFromUrl();
        this.substage = substage || this.getSubstageFromUrl();
        this.init();
    }

    getPostIdFromUrl() {
        const match = window.location.pathname.match(/\/posts\/(\d+)/);
        return match ? match[1] : null;
    }

    getStageFromUrl() {
        const pathParts = window.location.pathname.split('/');
        return pathParts[4] || null;
    }

    getSubstageFromUrl() {
        const pathParts = window.location.pathname.split('/');
        return pathParts[5] || null;
    }

    async init() {
        try {
            console.log('[FieldSelector] Initializing with stage:', this.stage, 'substage:', this.substage);
            
            // Fetch available fields based on current stage
            await this.fetchFields();
            
            // Fetch current field values
            await this.fetchFieldValues();
            
            // Initialize all field selectors
            const selectors = document.querySelectorAll('.field-selector');
            console.log('[FieldSelector] Found', selectors.length, 'field selectors');
            
            selectors.forEach((selector, index) => {
                console.log(`[FieldSelector] Initializing selector ${index + 1}:`, selector.dataset);
                this.initializeSelector(selector);
            });

            // Add change listeners to textareas
            const textareas = document.querySelectorAll('textarea[data-db-field]');
            console.log('[FieldSelector] Found', textareas.length, 'textareas with data-db-field');
            
            textareas.forEach(textarea => {
                this.initializeTextarea(textarea);
            });
        } catch (error) {
            console.error('Error initializing field selector:', error);
        }
    }

    async fetchFields() {
        try {
            console.log('[FieldSelector] fetchFields called, stage:', this.stage);
            
            // Check if we're in the Writing stage
            if (this.stage === 'writing' || this.stage === 'Writing') {
                console.log('[FieldSelector] Detected Writing stage, fetching post_section fields...');
                // For Writing stage, fetch post_section fields
                const response = await fetch('/api/workflow/fields/post_section');
                if (!response.ok) throw new Error('Failed to fetch post_section fields');
                this.fields = await response.json();
                console.log('[FieldSelector] Fetched post_section fields:', this.fields);
            } else {
                console.log('[FieldSelector] Not Writing stage, fetching regular fields...');
                // For other stages, fetch regular field mappings
                const response = await fetch('/workflow/api/field_mappings/');
                if (!response.ok) throw new Error('Failed to fetch fields');
                this.fields = await response.json();
                console.log('[FieldSelector] Fetched regular fields:', this.fields);
            }
        } catch (error) {
            console.error('Error fetching fields:', error);
            throw error;
        }
    }

    async fetchFieldValues() {
        if (!this.postId) return;
        try {
            // For Writing stage, we need to fetch from post_section table
            if (this.stage === 'writing' || this.stage === 'Writing') {
                const response = await fetch(`/api/workflow/posts/${this.postId}/sections`);
                if (!response.ok) throw new Error('Failed to fetch section field values');
                const data = await response.json();
                // Flatten section data for easier access
                this.fieldValues = {};
                if (data.sections) {
                    data.sections.forEach(section => {
                        Object.keys(section).forEach(key => {
                            if (key !== 'id' && key !== 'post_id' && key !== 'section_order') {
                                this.fieldValues[key] = section[key];
                            }
                        });
                    });
                }
            } else {
                // For other stages, fetch from post_development
                const response = await fetch(`/blog/api/v1/post/${this.postId}/development`);
                if (!response.ok) throw new Error('Failed to fetch field values');
                this.fieldValues = await response.json();
            }
        } catch (error) {
            console.error('Error fetching field values:', error);
            throw error;
        }
    }

    initializeSelector(selector) {
        // Get data attributes
        const target = selector.dataset.target;
        const section = selector.dataset.section;
        const currentSubstage = selector.dataset.currentSubstage;

        console.log('[FieldSelector] initializeSelector called with:', { target, section, currentSubstage, stage: this.stage });

        // Clear existing options
        selector.innerHTML = '';

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '-- Select Field --';
        selector.appendChild(defaultOption);

        // Check if we're in Writing stage
        if (this.stage === 'writing' || this.stage === 'Writing') {
            console.log('[FieldSelector] Writing stage detected, showing post_section fields...');
            // For Writing stage, show post_section fields directly
            if (this.fields && Array.isArray(this.fields)) {
                console.log('[FieldSelector] Adding', this.fields.length, 'post_section fields to dropdown');
                this.fields.forEach(field => {
                    const option = document.createElement('option');
                    option.value = field.field_name;
                    option.textContent = field.display_name || field.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    if (field.field_name === target) option.selected = true;
                    selector.appendChild(option);
                });
                console.log('[FieldSelector] Dropdown populated with post_section fields');
            } else {
                console.error('[FieldSelector] No fields found or fields is not an array:', this.fields);
            }
        } else {
            console.log('[FieldSelector] Not Writing stage, showing regular fields...');
            // For other stages, group fields by stage/substage
            Object.entries(this.fields).forEach(([stage, substages]) => {
                Object.entries(substages).forEach(([substage, fields]) => {
                    const group = document.createElement('optgroup');
                    group.label = `${stage} > ${substage}`;

                    fields.forEach(field => {
                        const option = document.createElement('option');
                        option.value = field.field_name;
                        option.textContent = field.display_name || field.field_name;
                        if (field.field_name === target) option.selected = true;
                        group.appendChild(option);
                    });

                    selector.appendChild(group);
                });
            });
        }

        // Add change event listener
        selector.addEventListener('change', async (event) => {
            await this.handleFieldSelection(event, target, section);
        });
    }

    initializeTextarea(textarea) {
        let timeout;
        textarea.addEventListener('input', (event) => {
            // Clear any existing timeout
            if (timeout) clearTimeout(timeout);
            
            // Set a new timeout to save after 500ms of no typing
            timeout = setTimeout(() => {
                this.saveFieldValue(textarea);
            }, 500);
        });
    }

    async handleFieldSelection(event, target, section) {
        const selectedField = event.target.value;
        const textarea = document.getElementById(target);

        try {
            // For Writing stage, handle post_section field mapping differently
            if (this.stage === 'writing' || this.stage === 'Writing') {
                // Update textarea attributes for post_section
                textarea.dataset.dbField = selectedField;
                textarea.dataset.dbTable = 'post_section';
                
                // Update textarea value with current field value
                if (this.fieldValues && selectedField in this.fieldValues) {
                    textarea.value = this.fieldValues[selectedField] || '';
                }
            } else {
                // Update database mapping for other stages
                const response = await fetch('/workflow/api/update_field_mapping/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        target_id: target,
                        field_name: selectedField,
                        section: section
                    })
                });

                if (!response.ok) throw new Error('Failed to update field mapping');

                // Update textarea attributes
                const mapping = await response.json();
                textarea.dataset.dbField = mapping.field_name;
                textarea.dataset.dbTable = mapping.table_name;

                // Update textarea value with current field value
                if (this.fieldValues && mapping.field_name in this.fieldValues) {
                    textarea.value = this.fieldValues[mapping.field_name] || '';
                }
            }

            // Show success indicator
            this.showSuccess(event.target);
        } catch (error) {
            console.error('Error updating field mapping:', error);
            this.showError(event.target);
        }
    }

    async saveFieldValue(textarea) {
        if (!this.postId) return;
        
        const fieldName = textarea.dataset.dbField;
        const tableName = textarea.dataset.dbTable;
        if (!fieldName) return;

        try {
            let response;
            
            // For Writing stage, save to post_section table
            if (tableName === 'post_section') {
                response = await fetch(`/api/workflow/posts/${this.postId}/sections/1/fields`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        [fieldName]: textarea.value
                    })
                });
            } else {
                // For other stages, save to post_development
                response = await fetch(`/blog/api/v1/post/${this.postId}/development`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        [fieldName]: textarea.value
                    })
                });
            }

            if (!response.ok) throw new Error('Failed to save field value');

            // Update local field values
            this.fieldValues = {
                ...this.fieldValues,
                [fieldName]: textarea.value
            };

            // Show success indicator
            this.showSuccess(textarea);
        } catch (error) {
            console.error('Error saving field value:', error);
            this.showError(textarea);
        }
    }

    showSuccess(element) {
        element.classList.add('border-green-500');
        setTimeout(() => {
            element.classList.remove('border-green-500');
        }, 2000);
    }

    showError(element) {
        element.classList.add('border-red-500');
        setTimeout(() => {
            element.classList.remove('border-red-500');
        }, 2000);
    }
}

// Export the initialization function
export function initializeFieldDropdowns() {
    return new FieldSelector();
} 