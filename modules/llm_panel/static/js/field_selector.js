/**
 * Field Selector JavaScript
 * Handles field mapping dropdowns in LLM panels
 */

class FieldSelector {
    constructor() {
        this.fields = {};
        this.init();
    }

    async init() {
        try {
            // Fetch available fields
            await this.fetchFields();
            
            // Initialize all field selectors
            document.querySelectorAll('.field-selector').forEach(selector => {
                this.initializeSelector(selector);
            });
        } catch (error) {
            console.error('Error initializing field selector:', error);
        }
    }

    async fetchFields() {
        try {
            const response = await fetch('/workflow/api/field_mappings/');
            if (!response.ok) throw new Error('Failed to fetch fields');
            this.fields = await response.json();
        } catch (error) {
            console.error('Error fetching fields:', error);
            throw error;
        }
    }

    initializeSelector(selector) {
        // Get data attributes
        const target = selector.dataset.target;
        const section = selector.dataset.section;
        const currentSubstage = selector.dataset.currentSubstage;

        // Clear existing options
        selector.innerHTML = '';

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '-- Select Field --';
        selector.appendChild(defaultOption);

        // Group fields by stage/substage
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

        // Add change event listener
        selector.addEventListener('change', async (event) => {
            await this.handleFieldSelection(event, target, section);
        });
    }

    async handleFieldSelection(event, target, section) {
        const selectedField = event.target.value;
        const textarea = document.getElementById(target);

        try {
            // Update database mapping
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

            // Show success indicator
            this.showSuccess(event.target);
        } catch (error) {
            console.error('Error updating field mapping:', error);
            this.showError(event.target);
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