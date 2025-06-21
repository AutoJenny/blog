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
        // Fetch available fields from the field mappings endpoint
        const response = await fetch('/workflow/api/field_mappings/');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const fieldMappings = await response.json();
        console.log('Field mappings:', fieldMappings);

        // Get all field selector dropdowns
        const selectors = document.querySelectorAll('.field-selector');
        console.log('Found field selectors:', selectors.length);
        
        selectors.forEach(selector => {
            // Clear existing options
            selector.innerHTML = '';
            
            // Add a default "Select field" option
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = '-- Select field --';
            defaultOption.disabled = true;
            selector.appendChild(defaultOption);
            
            // Filter fields based on the current stage/substage
            const relevantFields = fieldMappings.filter(mapping => 
                mapping.stage_name === stage && 
                mapping.substage_name === substage
            );
            console.log('Relevant fields:', relevantFields);
            
            // Add unmapped fields
            const unmappedFields = fieldMappings.filter(mapping => 
                mapping.stage_name === 'Unmapped' && 
                mapping.substage_name === 'Available Fields'
            );
            console.log('Unmapped fields:', unmappedFields);
            
            // Add relevant fields
            if (relevantFields.length > 0) {
                const stageGroup = document.createElement('optgroup');
                stageGroup.label = `${stage} - ${substage}`;
                relevantFields.forEach(field => {
                    const option = document.createElement('option');
                    option.value = field.field_name;
                    option.textContent = field.display_name || field.field_name;
                    stageGroup.appendChild(option);
                });
                selector.appendChild(stageGroup);
            }
            
            // Add unmapped fields
            if (unmappedFields.length > 0) {
                const unmappedGroup = document.createElement('optgroup');
                unmappedGroup.label = 'Available Fields';
                unmappedFields.forEach(field => {
                    const option = document.createElement('option');
                    option.value = field.field_name;
                    option.textContent = field.display_name || field.field_name;
                    unmappedGroup.appendChild(option);
                });
                selector.appendChild(unmappedGroup);
            }
            
            // Set the current value if it exists
            const targetField = selector.dataset.target;
            if (targetField) {
                const textarea = document.getElementById(targetField);
                if (textarea) {
                    const dbField = textarea.dataset.dbField;
                    if (dbField) {
                        selector.value = dbField;
                    }
                }
            }
            
            // Add change event listener
            selector.addEventListener('change', async function() {
                const selectedField = this.value;
                const targetField = this.dataset.target;
                const section = this.dataset.section;
                
                if (targetField) {
                    const textarea = document.getElementById(targetField);
                    if (textarea) {
                        const oldField = textarea.dataset.dbField;
                        textarea.dataset.dbField = selectedField;
                        
                        // Update the field mapping in the database
                        try {
                            const response = await fetch('/workflow/api/update_field_mapping/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    target_id: targetField.replace('_output', ''),
                                    old_field: oldField,
                                    new_field: selectedField,
                                    stage: stage,
                                    substage: substage,
                                    step: step,
                                    section: section
                                })
                            });
                            
                            if (!response.ok) {
                                throw new Error('Failed to update field mapping');
                            }
                            console.log('Field mapping updated successfully');
                            
                            // Reload the page to reflect the changes
                            window.location.reload();
                        } catch (error) {
                            console.error('Error updating field mapping:', error);
                            // Revert the selection on error
                            this.value = oldField;
                            textarea.dataset.dbField = oldField;
                        }
                    }
                }
            });
        });
        
    } catch (error) {
        console.error('Error initializing field dropdowns:', error);
    }
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

// Initialize dropdowns when the DOM is ready
document.addEventListener('DOMContentLoaded', initializeFieldDropdowns); 