/**
 * Format Configuration JavaScript
 * Handles step and post format configuration, preview, and testing
 */

// API base URLs
const FORMAT_API_BASE = '/api/workflow/formats';
const STEP_API_BASE = '/api/workflow/steps';

/**
 * Configure format for a workflow step
 * @param {number} stepId - Step ID
 * @param {number} postId - Post ID (optional, for post-specific configuration)
 * @param {Object} formatConfig - Format configuration
 * @param {number} formatConfig.input_format_id - Input format template ID
 * @param {number} formatConfig.output_format_id - Output format template ID
 * @returns {Promise<Object>} Updated format configuration
 */
export async function configureStepFormat(stepId, postId = null, formatConfig) {
    try {
        const url = postId 
            ? `${STEP_API_BASE}/${stepId}/formats/${postId}`
            : `${STEP_API_BASE}/${stepId}/formats`;
            
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formatConfig)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error configuring step format:', error);
        throw error;
    }
}

/**
 * Get format configuration for a workflow step
 * @param {number} stepId - Step ID
 * @param {number} postId - Post ID (optional, for post-specific configuration)
 * @returns {Promise<Object>} Format configuration
 */
export async function getStepFormatConfig(stepId, postId = null) {
    try {
        const url = postId 
            ? `${STEP_API_BASE}/${stepId}/formats/${postId}`
            : `${STEP_API_BASE}/${stepId}/formats`;
            
        const response = await fetch(url);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error getting step format config:', error);
        throw error;
    }
}

/**
 * Preview format specification
 * @param {number} formatId - Format template ID
 * @returns {Promise<Object>} Format preview data
 */
export async function previewFormat(formatId) {
    try {
        const response = await fetch(`${FORMAT_API_BASE}/templates/${formatId}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        const format = await response.json();
        
        // Generate preview data based on format fields
        const previewData = generatePreviewData(format.fields);
        
        return {
            format: format,
            preview: previewData,
            schema: format.fields
        };
    } catch (error) {
        console.error('Error previewing format:', error);
        throw error;
    }
}

/**
 * Generate preview data based on format fields
 * @param {Array} fields - Array of field definitions
 * @returns {Object} Preview data object
 */
function generatePreviewData(fields) {
    const preview = {};
    
    fields.forEach(field => {
        switch (field.type) {
            case 'string':
                preview[field.name] = field.required ? `Sample ${field.name}` : '';
                break;
            case 'number':
                preview[field.name] = field.required ? 42 : null;
                break;
            case 'boolean':
                preview[field.name] = field.required ? true : false;
                break;
            case 'array':
                preview[field.name] = field.required ? ['item1', 'item2'] : [];
                break;
            case 'object':
                preview[field.name] = field.required ? { key: 'value' } : {};
                break;
            default:
                preview[field.name] = field.required ? 'sample_value' : '';
        }
    });
    
    return preview;
}

/**
 * Test format with sample data
 * @param {Array} fields - Array of field definitions
 * @param {Object} testData - Test data to validate
 * @returns {Promise<Object>} Validation result
 */
export async function testFormat(fields, testData) {
    try {
        const response = await fetch(`${FORMAT_API_BASE}/validate`, {
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
        console.error('Error testing format:', error);
        throw error;
    }
}

/**
 * Get all available format templates
 * @returns {Promise<Array>} Array of format templates
 */
export async function getAvailableFormats() {
    try {
        const response = await fetch(`${FORMAT_API_BASE}/templates`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error getting available formats:', error);
        throw error;
    }
}

/**
 * Display format preview in UI
 * @param {string} elementId - Element ID to display preview in
 * @param {Object} previewData - Preview data object
 */
export function displayFormatPreview(elementId, previewData) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error(`Element with ID '${elementId}' not found`);
        return;
    }
    
    element.innerHTML = `
        <div class="format-preview">
            <h4 class="text-sm font-medium text-indigo-300 mb-2">Format Preview</h4>
            <pre class="bg-[#23273a] p-3 rounded text-sm overflow-x-auto">${JSON.stringify(previewData, null, 2)}</pre>
        </div>
    `;
}

/**
 * Display format testing interface
 * @param {string} elementId - Element ID to display interface in
 * @param {Array} fields - Array of field definitions
 * @param {Function} onTest - Callback function for test button
 */
export function displayFormatTestingInterface(elementId, fields, onTest) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error(`Element with ID '${elementId}' not found`);
        return;
    }
    
    // Generate test data form
    const testDataForm = generateTestDataForm(fields);
    
    element.innerHTML = `
        <div class="format-testing-interface">
            <h4 class="text-sm font-medium text-indigo-300 mb-2">Test Format</h4>
            <div class="space-y-3">
                ${testDataForm}
                <button id="testFormatBtn" class="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded text-sm">
                    Test Format
                </button>
                <div id="testResult" class="mt-2"></div>
            </div>
        </div>
    `;
    
    // Add event listener for test button
    const testBtn = element.querySelector('#testFormatBtn');
    if (testBtn && onTest) {
        testBtn.addEventListener('click', onTest);
    }
}

/**
 * Generate test data form based on fields
 * @param {Array} fields - Array of field definitions
 * @returns {string} HTML form string
 */
function generateTestDataForm(fields) {
    let formHtml = '';
    
    fields.forEach(field => {
        const required = field.required ? 'required' : '';
        const requiredClass = field.required ? 'border-red-500' : 'border-gray-600';
        
        switch (field.type) {
            case 'string':
                formHtml += `
                    <div>
                        <label class="block text-xs text-dark-text mb-1">
                            ${field.name} ${field.required ? '*' : ''}
                        </label>
                        <input type="text" 
                               name="${field.name}" 
                               placeholder="Enter ${field.name}"
                               class="w-full bg-[#23273a] border ${requiredClass} rounded px-2 py-1 text-sm text-white"
                               ${required}>
                    </div>
                `;
                break;
            case 'number':
                formHtml += `
                    <div>
                        <label class="block text-xs text-dark-text mb-1">
                            ${field.name} ${field.required ? '*' : ''}
                        </label>
                        <input type="number" 
                               name="${field.name}" 
                               placeholder="Enter ${field.name}"
                               class="w-full bg-[#23273a] border ${requiredClass} rounded px-2 py-1 text-sm text-white"
                               ${required}>
                    </div>
                `;
                break;
            case 'boolean':
                formHtml += `
                    <div>
                        <label class="flex items-center gap-2">
                            <input type="checkbox" 
                                   name="${field.name}" 
                                   class="rounded"
                                   ${field.required ? 'required' : ''}>
                            <span class="text-xs text-dark-text">${field.name} ${field.required ? '*' : ''}</span>
                        </label>
                    </div>
                `;
                break;
            case 'array':
                formHtml += `
                    <div>
                        <label class="block text-xs text-dark-text mb-1">
                            ${field.name} ${field.required ? '*' : ''} (comma-separated)
                        </label>
                        <input type="text" 
                               name="${field.name}" 
                               placeholder="item1, item2, item3"
                               class="w-full bg-[#23273a] border ${requiredClass} rounded px-2 py-1 text-sm text-white"
                               ${required}>
                    </div>
                `;
                break;
            case 'object':
                formHtml += `
                    <div>
                        <label class="block text-xs text-dark-text mb-1">
                            ${field.name} ${field.required ? '*' : ''} (JSON)
                        </label>
                        <textarea name="${field.name}" 
                                  placeholder='{"key": "value"}'
                                  class="w-full bg-[#23273a] border ${requiredClass} rounded px-2 py-1 text-sm text-white"
                                  rows="2"
                                  ${required}></textarea>
                    </div>
                `;
                break;
        }
    });
    
    return formHtml;
}

/**
 * Collect test data from form
 * @param {string} formId - Form element ID
 * @returns {Object} Collected test data
 */
export function collectTestData(formId) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error(`Form with ID '${formId}' not found`);
        return {};
    }
    
    const formData = new FormData(form);
    const testData = {};
    
    for (const [key, value] of formData.entries()) {
        if (value.trim() !== '') {
            // Try to parse as JSON for object fields
            try {
                testData[key] = JSON.parse(value);
            } catch {
                // Handle array fields (comma-separated)
                if (value.includes(',')) {
                    testData[key] = value.split(',').map(item => item.trim());
                } else {
                    testData[key] = value;
                }
            }
        }
    }
    
    return testData;
}

/**
 * Display error message in UI
 * @param {string} elementId - Element ID to display error in
 * @param {string} message - Error message
 */
export function displayError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-red-400 text-sm">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
            </div>
        `;
        element.className = 'error-message';
    }
}

/**
 * Display success message in UI
 * @param {string} elementId - Element ID to display success in
 * @param {string} message - Success message
 */
export function displaySuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-green-400 text-sm">
                <i class="fas fa-check"></i>
                <span>${message}</span>
            </div>
        `;
        element.className = 'success-message';
    }
}

/**
 * Initialize format configuration interface
 * @param {string} containerId - Container element ID
 * @param {number} stepId - Step ID
 * @param {number} postId - Post ID (optional)
 */
export async function initializeFormatConfiguration(containerId, stepId, postId = null) {
    try {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }
        
        // Get available formats
        const formats = await getAvailableFormats();
        
        // Get current step format configuration
        let currentConfig = {};
        try {
            currentConfig = await getStepFormatConfig(stepId, postId);
        } catch (error) {
            console.log('No existing format configuration found');
        }
        
        // Generate configuration interface
        container.innerHTML = generateConfigurationInterface(formats, currentConfig);
        
        // Add event listeners
        addConfigurationEventListeners(container, stepId, postId);
        
    } catch (error) {
        console.error('Error initializing format configuration:', error);
        displayError(containerId, 'Failed to initialize format configuration');
    }
}

/**
 * Generate configuration interface HTML
 * @param {Array} formats - Available format templates
 * @param {Object} currentConfig - Current format configuration
 * @returns {string} HTML string
 */
function generateConfigurationInterface(formats, currentConfig) {
    return `
        <div class="format-configuration">
            <h3 class="text-lg font-medium text-white mb-4">Format Configuration</h3>
            
            <div class="grid grid-cols-2 gap-6">
                <!-- Input Format -->
                <div>
                    <label class="block text-sm font-medium text-dark-text mb-2">Input Format</label>
                    <select id="inputFormatSelect" class="w-full bg-[#23273a] border border-dark-border rounded px-3 py-2 text-white">
                        <option value="">Select Input Format...</option>
                        ${formats.map(format => `
                            <option value="${format.id}" ${currentConfig.input_format_id === format.id ? 'selected' : ''}>
                                ${format.name}
                            </option>
                        `).join('')}
                    </select>
                    <div id="inputFormatPreview" class="mt-2"></div>
                </div>
                
                <!-- Output Format -->
                <div>
                    <label class="block text-sm font-medium text-dark-text mb-2">Output Format</label>
                    <select id="outputFormatSelect" class="w-full bg-[#23273a] border border-dark-border rounded px-3 py-2 text-white">
                        <option value="">Select Output Format...</option>
                        ${formats.map(format => `
                            <option value="${format.id}" ${currentConfig.output_format_id === format.id ? 'selected' : ''}>
                                ${format.name}
                            </option>
                        `).join('')}
                    </select>
                    <div id="outputFormatPreview" class="mt-2"></div>
                </div>
            </div>
            
            <div class="mt-6">
                <button id="saveFormatConfig" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded">
                    Save Configuration
                </button>
                <div id="configResult" class="mt-2"></div>
            </div>
        </div>
    `;
}

/**
 * Add event listeners to configuration interface
 * @param {HTMLElement} container - Container element
 * @param {number} stepId - Step ID
 * @param {number} postId - Post ID (optional)
 */
function addConfigurationEventListeners(container, stepId, postId) {
    // Input format change
    const inputSelect = container.querySelector('#inputFormatSelect');
    if (inputSelect) {
        inputSelect.addEventListener('change', async (e) => {
            if (e.target.value) {
                try {
                    const preview = await previewFormat(parseInt(e.target.value));
                    displayFormatPreview('inputFormatPreview', preview.preview);
                } catch (error) {
                    displayError('inputFormatPreview', 'Failed to load format preview');
                }
            } else {
                document.getElementById('inputFormatPreview').innerHTML = '';
            }
        });
    }
    
    // Output format change
    const outputSelect = container.querySelector('#outputFormatSelect');
    if (outputSelect) {
        outputSelect.addEventListener('change', async (e) => {
            if (e.target.value) {
                try {
                    const preview = await previewFormat(parseInt(e.target.value));
                    displayFormatPreview('outputFormatPreview', preview.preview);
                } catch (error) {
                    displayError('outputFormatPreview', 'Failed to load format preview');
                }
            } else {
                document.getElementById('outputFormatPreview').innerHTML = '';
            }
        });
    }
    
    // Save configuration
    const saveBtn = container.querySelector('#saveFormatConfig');
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const inputFormatId = inputSelect?.value || null;
            const outputFormatId = outputSelect?.value || null;
            
            try {
                await configureStepFormat(stepId, postId, {
                    input_format_id: inputFormatId,
                    output_format_id: outputFormatId
                });
                displaySuccess('configResult', 'Format configuration saved successfully');
            } catch (error) {
                displayError('configResult', 'Failed to save format configuration');
            }
        });
    }
} 