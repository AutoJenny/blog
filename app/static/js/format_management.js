/**
 * Format Management JavaScript
 * Handles CRUD operations for format templates and validation
 */

// API base URL
const API_BASE = '/api/workflow/formats';

/**
 * Create a new format template
 * @param {Object} formatData - Format template data
 * @param {string} formatData.name - Template name
 * @param {string} formatData.description - Template description
 * @param {Array} formatData.fields - Array of field definitions
 * @returns {Promise<Object>} Created format template
 */
export async function createFormatTemplate(formatData) {
    try {
        const response = await fetch(`${API_BASE}/templates`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formatData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error creating format template:', error);
        throw error;
    }
}

/**
 * Update an existing format template
 * @param {number} templateId - Template ID to update
 * @param {Object} formatData - Updated format template data
 * @param {string} formatData.name - Template name
 * @param {string} formatData.description - Template description
 * @param {Array} formatData.fields - Array of field definitions
 * @returns {Promise<Object>} Updated format template
 */
export async function updateFormatTemplate(templateId, formatData) {
    try {
        const response = await fetch(`${API_BASE}/templates/${templateId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formatData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error updating format template:', error);
        throw error;
    }
}

/**
 * Delete a format template
 * @param {number} templateId - Template ID to delete
 * @returns {Promise<boolean>} Success status
 */
export async function deleteFormatTemplate(templateId) {
    try {
        const response = await fetch(`${API_BASE}/templates/${templateId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        return true;
    } catch (error) {
        console.error('Error deleting format template:', error);
        throw error;
    }
}

/**
 * Validate a format specification against test data
 * @param {Array} fields - Array of field definitions
 * @param {Object} testData - Test data to validate
 * @returns {Promise<Object>} Validation result
 */
export async function validateFormat(fields, testData) {
    try {
        const response = await fetch(`${API_BASE}/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                fields: fields,
                test_data: testData
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error validating format:', error);
        throw error;
    }
}

/**
 * Get all format templates
 * @returns {Promise<Array>} Array of format templates
 */
export async function getFormatTemplates() {
    try {
        const response = await fetch(`${API_BASE}/templates`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching format templates:', error);
        throw error;
    }
}

/**
 * Get a specific format template by ID
 * @param {number} templateId - Template ID
 * @returns {Promise<Object>} Format template
 */
export async function getFormatTemplate(templateId) {
    try {
        const response = await fetch(`${API_BASE}/templates/${templateId}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching format template:', error);
        throw error;
    }
}

/**
 * Create a default field definition
 * @param {string} name - Field name
 * @param {string} type - Field type (string, number, boolean, array, object)
 * @param {boolean} required - Whether field is required
 * @param {string} description - Field description
 * @returns {Object} Field definition object
 */
export function createFieldDefinition(name, type = 'string', required = false, description = '') {
    return {
        name: name,
        type: type,
        required: required,
        description: description
    };
}

/**
 * Validate field definition structure
 * @param {Object} field - Field definition to validate
 * @returns {Object} Validation result
 */
export function validateFieldDefinition(field) {
    const errors = [];
    
    if (!field.name || typeof field.name !== 'string') {
        errors.push('Field name is required and must be a string');
    }
    
    if (!field.type || !['string', 'number', 'boolean', 'array', 'object'].includes(field.type)) {
        errors.push('Field type must be one of: string, number, boolean, array, object');
    }
    
    if (typeof field.required !== 'boolean') {
        errors.push('Field required must be a boolean');
    }
    
    if (field.description && typeof field.description !== 'string') {
        errors.push('Field description must be a string');
    }
    
    return {
        valid: errors.length === 0,
        errors: errors
    };
}

/**
 * Validate format template data structure
 * @param {Object} formatData - Format template data to validate
 * @returns {Object} Validation result
 */
export function validateFormatTemplate(formatData) {
    const errors = [];
    
    if (!formatData.name || typeof formatData.name !== 'string') {
        errors.push('Template name is required and must be a string');
    }
    
    if (!formatData.description || typeof formatData.description !== 'string') {
        errors.push('Template description is required and must be a string');
    }
    
    if (!Array.isArray(formatData.fields)) {
        errors.push('Fields must be an array');
    } else {
        formatData.fields.forEach((field, index) => {
            const fieldValidation = validateFieldDefinition(field);
            if (!fieldValidation.valid) {
                fieldValidation.errors.forEach(error => {
                    errors.push(`Field ${index + 1}: ${error}`);
                });
            }
        });
    }
    
    return {
        valid: errors.length === 0,
        errors: errors
    };
}

/**
 * Display validation result in UI
 * @param {string} elementId - Element ID to display result in
 * @param {Object} validationResult - Validation result object
 */
export function displayValidationResult(elementId, validationResult) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error(`Element with ID '${elementId}' not found`);
        return;
    }
    
    if (validationResult.valid) {
        element.innerHTML = `
            <div class="flex items-center gap-2 text-green-400">
                <i class="fas fa-check"></i>
                <span>Format validation passed</span>
            </div>
        `;
        element.className = 'validation-result valid';
    } else {
        element.innerHTML = `
            <div class="text-red-400">
                <div class="flex items-center gap-2 mb-1">
                    <i class="fas fa-times"></i>
                    <span>Format validation failed</span>
                </div>
                <ul class="list-disc list-inside pl-2 text-sm">
                    ${validationResult.errors.map(error => `<li>${error}</li>`).join('')}
                </ul>
            </div>
        `;
        element.className = 'validation-result invalid';
    }
}

/**
 * Show error message in UI
 * @param {string} elementId - Element ID to display error in
 * @param {string} message - Error message
 */
export function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-red-400">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
            </div>
        `;
        element.className = 'error-message';
    }
}

/**
 * Show success message in UI
 * @param {string} elementId - Element ID to display success in
 * @param {string} message - Success message
 */
export function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-green-400">
                <i class="fas fa-check"></i>
                <span>${message}</span>
            </div>
        `;
        element.className = 'success-message';
    }
} 