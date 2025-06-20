/**
 * LLM Actions Panel JavaScript
 * 
 * This file handles:
 * 1. Accordion interactions
 * 2. Form submissions
 * 3. API calls
 * 4. Response handling
 * 
 * Key endpoints used:
 * - GET /api/v1/llm/actions
 * - POST /api/v1/llm/actions/{action_id}/execute
 * - GET /api/v1/llm/prompts
 * - GET /api/v1/llm/models
 * 
 * Note: This is a placeholder file. Implementation will be discussed.
 */

// Example API call structure:
async function executeLLMAction(actionId, params) {
    try {
        const response = await fetch(`/api/v1/llm/actions/${actionId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params)
        });
        return await response.json();
    } catch (error) {
        console.error('Error executing LLM action:', error);
        throw error;
    }
}

// Example form handling:
document.addEventListener('DOMContentLoaded', function() {
    const inputForm = {
        type: document.getElementById('inputType'),
        value: document.getElementById('inputValue'),
        systemPrompt: document.getElementById('systemPrompt'),
        taskPrompt: document.getElementById('taskPrompt'),
        model: document.getElementById('model'),
        temperature: document.getElementById('temperature'),
        output: document.getElementById('output')
    };
    
    // Form submission handler will be implemented here
});

// Panel Toggle Functionality
function togglePanel(panelId) {
    const panel = document.getElementById(`${panelId}-panel`);
    const content = document.getElementById(`${panelId}-content`);
    const header = panel.querySelector('.panel-header');
    
    // Toggle aria-expanded state
    const isExpanded = header.getAttribute('aria-expanded') === 'true';
    header.setAttribute('aria-expanded', !isExpanded);
    
    // Toggle content visibility
    content.classList.toggle('active');
}

// Initialize panels
document.addEventListener('DOMContentLoaded', function() {
    // Set initial states
    const panels = document.querySelectorAll('.llm-panel');
    panels.forEach(panel => {
        const header = panel.querySelector('.panel-header');
        const content = panel.querySelector('.panel-content');
        
        // Set initial aria-expanded state
        header.setAttribute('aria-expanded', 'false');
        
        // Show the first panel by default
        if (panel.id === 'input-panel') {
            header.setAttribute('aria-expanded', 'true');
            content.classList.add('active');
        }
    });

    // Initialize temperature range input
    const temperatureInput = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperature-value');
    
    if (temperatureInput && temperatureValue) {
        temperatureInput.addEventListener('input', function() {
            temperatureValue.textContent = this.value;
        });
    }
}); 