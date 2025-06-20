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

// Initialize panels
document.addEventListener('DOMContentLoaded', function() {
    console.log('LLM Actions Panel JS loaded');
    
    // Initialize panel functionality
    const panels = document.querySelectorAll('.accordion-panel');
    console.log('Found accordion panels:', panels.length);
    
    panels.forEach(panel => {
        const header = panel.querySelector('.panel-header');
        const content = panel.querySelector('.panel-content');
        
        if (!header || !content) {
            console.error('Accordion panel missing header or content:', panel.id);
            return;
        }
        
        header.addEventListener('click', (e) => {
            console.log('Panel clicked:', panel.id);
            const isExpanded = header.getAttribute('aria-expanded') === 'true';
            
            // Close all other panels
            panels.forEach(otherPanel => {
                if (otherPanel !== panel) {
                    const otherHeader = otherPanel.querySelector('.panel-header');
                    if (otherHeader) {
                        otherHeader.setAttribute('aria-expanded', 'false');
                    }
                }
            });
            
            // Toggle current panel
            header.setAttribute('aria-expanded', !isExpanded);
            
            // Prevent any parent elements from handling the click
            e.stopPropagation();
        });
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