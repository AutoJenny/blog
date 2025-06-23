/**
 * LLM Actions Panel JavaScript
 * 
 * This file handles:
 * 1. Loading LLM actions
 * 2. Loading post development fields
 * 3. Executing LLM actions
 * 4. Saving output to fields
 */

// Load LLM actions for the current substage
async function loadLLMActions(substage) {
    try {
        const response = await fetch(`/api/v1/llm/actions?substage=${substage}`);
        const actions = await response.json();
        
        // Populate action select
        const actionSelect = document.getElementById('actionSelect');
        actionSelect.innerHTML = '<option value="">Select an action...</option>';
        actions.forEach(action => {
            const option = document.createElement('option');
            option.value = action.id;
            option.textContent = action.name;
            actionSelect.appendChild(option);
        });
        
        // Show prompt when action is selected
        actionSelect.addEventListener('change', function() {
            const selectedAction = actions.find(a => a.id === parseInt(this.value));
            if (selectedAction) {
                document.getElementById('actionPromptPanel').textContent = selectedAction.prompt_template;
            }
        });
    } catch (error) {
        console.error('Error loading LLM actions:', error);
    }
}

// Load post development fields
async function loadPostDevFields(postId) {
    try {
        const response = await fetch(`/api/v1/post/${postId}/development`);
        const fields = await response.json();
        
        // Populate input/output selects
        const inputSelect = document.getElementById('inputFieldSelect');
        const outputSelect = document.getElementById('outputFieldSelect');
        inputSelect.innerHTML = '<option value="">Select input field...</option>';
        outputSelect.innerHTML = '<option value="">Select output field...</option>';
        
        Object.entries(fields).forEach(([field, value]) => {
            if (field !== 'id' && field !== 'post_id') {
                const inputOption = document.createElement('option');
                inputOption.value = field;
                inputOption.textContent = field;
                inputSelect.appendChild(inputOption.cloneNode(true));
                
                const outputOption = document.createElement('option');
                outputOption.value = field;
                outputOption.textContent = field;
                outputSelect.appendChild(outputOption);
            }
        });
        
        // Show field value when selected
        inputSelect.addEventListener('change', function() {
            if (this.value) {
                document.getElementById('inputFieldValue').textContent = fields[this.value] || '';
            }
        });
        
        outputSelect.addEventListener('change', function() {
            if (this.value) {
                document.getElementById('outputFieldValue').textContent = fields[this.value] || '';
            }
        });
        
        // Display all fields in grid
        const fieldsPanel = document.getElementById('postDevFieldsPanel');
        fieldsPanel.innerHTML = '';
        Object.entries(fields).forEach(([field, value]) => {
            if (field !== 'id' && field !== 'post_id') {
                const card = document.createElement('div');
                card.className = 'field-card';
                card.innerHTML = `
                    <h4>${field}</h4>
                    <div class="field-value">${value || ''}</div>
                `;
                fieldsPanel.appendChild(card);
            }
        });
    } catch (error) {
        console.error('Error loading post development fields:', error);
    }
}

// Execute LLM action
async function executeLLMAction(actionId, input) {
    try {
        const response = await fetch(`/api/v1/llm/actions/${actionId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ input })
        });
        const result = await response.json();
        document.getElementById('actionOutputPanel').textContent = result.output;
    } catch (error) {
        console.error('Error executing LLM action:', error);
    }
}

// Save output to field
async function saveOutput(postId, field, value) {
    try {
        const response = await fetch(`/api/v1/post/${postId}/development`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ [field]: value })
        });
        if (response.ok) {
            // Reload fields to show updated value
            await loadPostDevFields(postId);
        }
    } catch (error) {
        console.error('Error saving output:', error);
    }
}

// Initialize panels
document.addEventListener('DOMContentLoaded', function() {
    const root = document.getElementById('llm-workflow-root');
    if (!root) return;
    
    const substage = root.dataset.substage;
    const postId = parseInt(root.dataset.postId);
    
    // Load initial data
    loadLLMActions(substage);
    loadPostDevFields(postId);
    
    // Handle run action button
    document.getElementById('runActionBtn').addEventListener('click', async function() {
        const actionId = document.getElementById('actionSelect').value;
        const input = document.getElementById('inputFieldValue').textContent;
        if (actionId && input) {
            await executeLLMAction(actionId, input);
        }
    });
    
    // Handle save output button
    document.getElementById('saveOutputBtn').addEventListener('click', async function() {
        const field = document.getElementById('outputFieldSelect').value;
        const value = document.getElementById('actionOutputPanel').textContent;
        if (field && value) {
            await saveOutput(postId, field, value);
        }
    });
}); 