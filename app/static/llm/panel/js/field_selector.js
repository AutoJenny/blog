// Add CSS styles for format validation indicators
const style = document.createElement('style');
style.textContent = `
    .field-selector.format-valid {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 1px #10b981;
    }
    
    .field-selector.format-invalid {
        border-color: #f59e0b !important;
        box-shadow: 0 0 0 1px #f59e0b;
    }
    
    .format-indicator {
        font-size: 0.75rem;
        margin-top: 0.25rem;
    }
    
    .format-compliant {
        color: #10b981;
    }
    
    .format-warning {
        color: #f59e0b;
    }
    
    option.format-compliant {
        color: #10b981;
    }
    
    option.format-warning {
        color: #f59e0b;
    }
    
    /* Dark theme for dropdowns */
    .field-selector {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border: 1px solid #475569 !important;
    }
    
    .field-selector option {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
    }
    
    .field-selector option:hover {
        background-color: #334155 !important;
    }
    
    .field-selector option:checked {
        background-color: #475569 !important;
    }
    
    .field-selector:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }
`;
document.head.appendChild(style);

// Initialize field dropdowns for a panel
export async function initializeFieldDropdowns() {
    console.log('Initializing field dropdowns...');
    
    // Get current navigation state from the panel div
    const panel = document.querySelector('[data-current-stage]');
    const stage = panel?.dataset.currentStage;
    const substage = panel?.dataset.currentSubstage;
    const step = panel?.dataset.currentStep;
    
    console.log('Navigation state:', { stage, substage, step });
    
    if (!stage || !substage || !step) {
        console.error('Missing navigation state');
        return;
    }
    
    try {
        // Fetch format templates instead of database fields
        const response = await fetch('/api/workflow/formats/templates');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const formatTemplates = await response.json();
        console.log('Format templates:', formatTemplates);

        // Get step ID for format validation
        const stepId = await getStepId(stage, substage, step);
        let formatConfig = null;
        
        if (stepId) {
            // Get post ID from the page context
            const postId = document.querySelector('[data-post-id]')?.dataset.postId;
            
            if (postId) {
                // Fetch format configuration for the step and post
                try {
                    const formatResponse = await fetch(`/api/workflow/steps/${stepId}/formats/${postId}`);
                    if (formatResponse.ok) {
                        formatConfig = await formatResponse.json();
                        console.log('Format configuration:', formatConfig);
                    }
                } catch (error) {
                    console.warn('Could not fetch format configuration:', error);
                }
            } else {
                // Fallback to step-level format configuration
                try {
                    const formatResponse = await fetch(`/api/workflow/steps/${stepId}/formats`);
                    if (formatResponse.ok) {
                        formatConfig = await formatResponse.json();
                        console.log('Format configuration (step-level):', formatConfig);
                    }
                } catch (error) {
                    console.warn('Could not fetch format configuration:', error);
                }
            }
        }

        // Get all field selector dropdowns
        const selectors = document.querySelectorAll('.field-selector');
        console.log('Found field selectors:', selectors.length);
        
        selectors.forEach(selector => {
            // Clear existing options
            selector.innerHTML = '';
            
            // Add a default "Select format" option
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '-- Select format template --';
            defaultOption.disabled = true;
            selector.appendChild(defaultOption);
            
            // Add all format templates
            formatTemplates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = `${template.name} (${template.fields.length} fields)`;
                
                // Add format compliance indicator if we have a current format config
                if (formatConfig) {
                    const isCompliant = isFormatCompatible(template, formatConfig);
                    if (isCompliant) {
                        option.textContent += ' ✓';
                        option.classList.add('format-compliant');
                    } else {
                        option.textContent += ' ⚠';
                        option.classList.add('format-warning');
                    }
                }
                
                selector.appendChild(option);
            });
            
            // Set the current value if it exists
            const targetField = selector.dataset.target;
            if (targetField) {
                const textarea = document.getElementById(targetField);
                if (textarea) {
                    const currentFormatId = textarea.dataset.formatId;
                    if (currentFormatId) {
                        selector.value = currentFormatId;
                        
                        // Validate current format against config
                        if (formatConfig) {
                            validateFormatAgainstConfig(selector, currentFormatId, formatConfig, formatTemplates);
                        }
                    }
                }
            }
            
            // Add change event listener
            selector.addEventListener('change', async function() {
                const selectedFormatId = this.value;
                const targetField = this.dataset.target;
                
                if (targetField) {
                    const textarea = document.getElementById(targetField);
                    if (textarea) {
                        const oldFormatId = textarea.dataset.formatId;
                        textarea.dataset.formatId = selectedFormatId;
                        
                        // Update the format configuration in the database
                        try {
                            if (stepId) {
                                // Get post ID from the page context
                                const postId = document.querySelector('[data-post-id]')?.dataset.postId;
                                
                                if (!postId) {
                                    console.warn('Post ID not found, cannot save format configuration');
                                    return;
                                }
                                
                                const updateData = {
                                    input_format_id: selectedFormatId,
                                    output_format_id: null
                                };
                                
                                const response = await fetch(`/api/workflow/steps/${stepId}/formats/${postId}`, {
                                    method: 'PUT',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify(updateData)
                                });
                                
                                if (!response.ok) {
                                    throw new Error(`HTTP error! status: ${response.status}`);
                                }
                                console.log('Format configuration updated successfully');
                                
                                // Refresh the format config
                                const formatResponse = await fetch(`/api/workflow/steps/${stepId}/formats/${postId}`);
                                if (formatResponse.ok) {
                                    formatConfig = await formatResponse.json();
                                }
                            }
                            
                        } catch (error) {
                            console.error('Error saving format configuration:', error);
                            // Revert the selection on error
                            this.value = oldFormatId;
                            textarea.dataset.formatId = oldFormatId;
                        }
                    }
                }
            });
        });
        
    } catch (error) {
        console.error('Error initializing field dropdowns:', error);
    }
}

// Get step ID from stage, substage, and step names
async function getStepId(stage, substage, step) {
    try {
        const response = await fetch('/api/workflow/steps');
        if (!response.ok) {
            return null;
        }
        const steps = await response.json();
        
        const matchingStep = steps.find(s => 
            s.stage_name === stage && 
            s.substage_name === substage && 
            s.step_name === step
        );
        
        return matchingStep ? matchingStep.id : null;
    } catch (error) {
        console.warn('Could not fetch step ID:', error);
        return null;
    }
}

// Check if a format template is compatible with current format config
function isFormatCompatible(template, formatConfig) {
    if (!formatConfig || !formatConfig.input_format) {
        return true; // No current config, so any format is compatible
    }
    
    // Simple compatibility check - could be enhanced
    const currentFields = formatConfig.input_format.fields || [];
    const templateFields = template.fields || [];
    
    // Check if template has at least some of the required fields
    const currentFieldNames = currentFields.map(f => f.name);
    const templateFieldNames = templateFields.map(f => f.name);
    
    return templateFieldNames.some(name => currentFieldNames.includes(name));
}

// Validate format against current config
function validateFormatAgainstConfig(selector, formatId, formatConfig, formatTemplates) {
    const template = formatTemplates.find(t => t.id == formatId);
    if (!template) return false;
    
    const isCompatible = isFormatCompatible(template, formatConfig);
    
    if (isCompatible) {
        selector.classList.remove('format-invalid');
        selector.classList.add('format-valid');
    } else {
        selector.classList.remove('format-valid');
        selector.classList.add('format-invalid');
    }
    
    return isCompatible;
}

// Field dropdown rendering functionality
function renderFieldDropdown(select, mappings, selected) {
    console.log('Rendering field dropdown:', { select, selected });
    select.innerHTML = '';
    
    // Add a default "Select Field" option
    const defaultOpt = document.createElement('option');
    defaultOpt.value = '';
    defaultOpt.textContent = 'Select Field...';
    defaultOpt.disabled = true;
    defaultOpt.selected = !selected;
    select.appendChild(defaultOpt);

    // Group fields by stage/substage
    let lastStage = null;
    let lastSubstage = null;
    let stageOptGroup = null;

    // Sort mappings by stage_name and substage_name
    mappings.sort((a, b) => {
        if (a.stage_name !== b.stage_name) {
            return a.stage_name.localeCompare(b.stage_name);
        }
        return a.substage_name.localeCompare(b.substage_name);
    });

    for (const m of mappings) {
        if (m.stage_name !== lastStage) {
            stageOptGroup = document.createElement('optgroup');
            stageOptGroup.label = m.stage_name;
            select.appendChild(stageOptGroup);
            lastStage = m.stage_name;
            lastSubstage = null;
        }
        if (m.substage_name !== lastSubstage) {
            const substageLabel = document.createElement('option');
            substageLabel.textContent = m.substage_name;
            substageLabel.disabled = true;
            stageOptGroup.appendChild(substageLabel);
            lastSubstage = m.substage_name;
        }
        const opt = document.createElement('option');
        opt.value = m.field_name;
        opt.textContent = m.display_name || m.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        if (selected === m.field_name) {
            opt.selected = true;
        }
        stageOptGroup.appendChild(opt);
    }

    // Add dark theme classes
    select.classList.add('bg-dark-bg', 'text-dark-text', 'border', 'border-dark-border', 'rounded', 'p-2', 'w-full', 'mb-2');
} 