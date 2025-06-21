// Initialize field dropdowns for a panel
export async function initializeFieldDropdowns() {
    // Fetch available fields
    const response = await fetch('/workflow/api/field_mappings/');
    if (!response.ok) {
        console.error('Failed to fetch field mappings');
        return;
    }
    const mappings = await response.json();
    
    // Get current navigation state
    const stage = document.querySelector('[data-current-stage]')?.dataset.currentStage;
    const substage = document.querySelector('[data-current-substage]')?.dataset.currentSubstage;
    const step = document.querySelector('[data-current-step]')?.dataset.currentStep;
    
    if (!stage || !substage || !step) {
        console.error('Missing navigation state');
        return;
    }
    
    // Initialize all field dropdowns in the panel
    document.querySelectorAll('.field-selector').forEach(select => {
        const targetId = select.dataset.target;
        const section = select.dataset.section; // 'inputs' or 'outputs'
        const textarea = document.getElementById(targetId);
        const currentField = textarea?.dataset.dbField;
        
        renderFieldDropdown(select, mappings, currentField);
        
        // Add change handler to persist the selection
        select.addEventListener('change', async (event) => {
            if (textarea) {
                const oldField = textarea.dataset.dbField;
                const newField = event.target.value;
                
                // Update the textarea's data attribute
                textarea.dataset.dbField = newField;
                
                // Update the field mapping in the database
                try {
                    const response = await fetch('/workflow/api/update_field_mapping/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            target_id: targetId,
                            old_field: oldField,
                            new_field: newField,
                            stage: stage,
                            substage: substage,
                            step: step,
                            section: section
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error('Failed to update field mapping');
                    }
                } catch (error) {
                    console.error('Error updating field mapping:', error);
                    // Revert the selection on error
                    select.value = oldField;
                    textarea.dataset.dbField = oldField;
                }
            }
        });
    });
}

// Field dropdown rendering functionality
function renderFieldDropdown(select, mappings, selected) {
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
        opt.textContent = m.display_name;
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