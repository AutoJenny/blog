/**
 * Field Selector JavaScript
 * Handles field mapping dropdowns and field value persistence in LLM panels
 */

export class FieldSelector {
    constructor() {
        this.fields = {};
        this.fieldValues = {};
        this.postId = this.getPostIdFromUrl();
        this.stage = this.getStageFromUrl();
        this.substage = this.getSubstageFromUrl();
        this.init();
    }

    getPostIdFromUrl() {
        const match = window.location.pathname.match(/\/posts\/(\d+)/);
        return match ? match[1] : null;
    }

    getStageFromUrl() {
        const parts = window.location.pathname.split('/');
        const postsIndex = parts.indexOf('posts');
        return postsIndex >= 0 && parts.length > postsIndex + 2 ? parts[postsIndex + 2] : 'planning';
    }

    getSubstageFromUrl() {
        const parts = window.location.pathname.split('/');
        const postsIndex = parts.indexOf('posts');
        return postsIndex >= 0 && parts.length > postsIndex + 3 ? parts[postsIndex + 3] : 'idea';
    }

    async init() {
        try {
            // Fetch available fields
            await this.fetchFields();
            
            // Fetch current field values
            await this.fetchFieldValues();
            
            // Initialize all field selectors
            document.querySelectorAll('.field-selector').forEach(selector => {
                this.initializeSelector(selector);
            });

            // Initialize all textareas
            document.querySelectorAll('textarea[data-db-field]').forEach(textarea => {
                this.initializeTextarea(textarea);
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
            console.log('Fields fetched:', this.fields);
        } catch (error) {
            console.error('Error fetching fields:', error);
        }
    }

    async fetchFieldValues() {
        if (!this.postId) return;
        try {
            const response = await fetch(`/blog/api/v1/post/${this.postId}/development`);
            if (!response.ok) throw new Error('Failed to fetch field values');
            this.fieldValues = await response.json();
            console.log('Field values fetched:', this.fieldValues);
        } catch (error) {
            console.error('Error fetching field values:', error);
        }
    }

    initializeSelector(selector) {
        const target = selector.dataset.target;
        const section = selector.dataset.section;
        const textarea = document.getElementById(target);

        if (textarea && textarea.dataset.dbField) {
            selector.value = textarea.dataset.dbField;
            this.setTextareaValue(textarea, textarea.dataset.dbField);
        }

        selector.addEventListener('change', (event) => {
            this.handleFieldSelection(event, target, section);
        });
    }

    initializeTextarea(textarea) {
        const fieldName = textarea.dataset.dbField;
        if (fieldName) {
            this.setTextareaValue(textarea, fieldName);
        }

        textarea.addEventListener('change', () => {
            this.handleTextareaChange(textarea);
        });
    }

    async setTextareaValue(textarea, fieldName) {
        if (this.fieldValues && fieldName in this.fieldValues) {
            textarea.value = this.fieldValues[fieldName] || '';
        }
    }

    async handleFieldSelection(event, target, section) {
        const selectedField = event.target.value;
        const textarea = document.getElementById(target);

        try {
            console.log('Updating field mapping:', { target, selectedField, section, stage: this.stage, substage: this.substage });
            // Update database mapping
            const response = await fetch('/workflow/api/update_field_mapping/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target_id: target,
                    field_name: selectedField,
                    section: section,
                    stage: this.stage,
                    substage: this.substage
                })
            });

            if (!response.ok) throw new Error('Failed to update field mapping');

            // Update textarea attributes
            const mapping = await response.json();
            console.log('Field mapping updated:', mapping);
            textarea.dataset.dbField = mapping.field_name;
            textarea.dataset.dbTable = mapping.table_name;

            // Update textarea value with current field value
            await this.setTextareaValue(textarea, mapping.field_name);

            // Show success indicator
            this.showSuccess(event.target);
        } catch (error) {
            console.error('Error updating field mapping:', error);
            this.showError(event.target);
        }
    }

    async handleTextareaChange(textarea) {
        if (!this.postId) return;

        const fieldName = textarea.dataset.dbField;
        if (!fieldName) return;

        try {
            const response = await fetch(`/blog/api/v1/post/${this.postId}/development`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    [fieldName]: textarea.value
                })
            });

            if (!response.ok) throw new Error('Failed to update field value');

            // Update local state
            this.fieldValues[fieldName] = textarea.value;

            // Show success indicator
            this.showSuccess(textarea);
        } catch (error) {
            console.error('Error updating field value:', error);
            this.showError(textarea);
        }
    }

    showSuccess(element) {
        element.classList.add('success');
        setTimeout(() => element.classList.remove('success'), 2000);
    }

    showError(element) {
        element.classList.add('error');
        setTimeout(() => element.classList.remove('error'), 2000);
    }
}

// Initialize the field selector when the module is loaded
window.fieldSelector = new FieldSelector(); 