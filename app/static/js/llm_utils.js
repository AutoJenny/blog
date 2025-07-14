// LLM utility functions
import { API_CONFIG, buildApiUrl, handleApiResponse } from './config/api.js';

/**
 * Run an LLM operation using the visible preview content
 * @param {Object} params - Parameters for the LLM operation
 * @param {number} params.postId - The post ID
 * @param {string} params.stage - The workflow stage
 * @param {string} params.substage - The workflow substage
 * @param {string} params.step - The workflow step
 * @returns {Promise<Object>} The LLM response
 */
async function runLLM({ postId, stage, substage, step }) {
    console.log('[LLM_UTILS] runLLM function called with params:', { postId, stage, substage, step });
    
    const btn = document.querySelector('[data-action="run-llm"]');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Running...';
    }

    try {
        // Get the visible preview content - use the correct element ID
        const previewElement = document.getElementById('enhanced-prompt-preview');
        
        if (!previewElement) {
            console.error('Live Preview element not found. Available elements with "preview" in ID:', document.querySelectorAll('[id*="preview"]'));
            throw new Error('Live Preview not found. Please open the LLM Message Management panel first.');
        }
        
        const previewContent = previewElement.textContent || previewElement.innerText;
        console.log('Found preview content:', previewContent);
        
        // Check if the enhanced LLM message manager is available and has content
        if (window.enhancedLLMMessageManager) {
            // Use the enhanced system's content assembly logic
            const enhancedContent = window.enhancedLLMMessageManager.getAssembledContent();
            if (enhancedContent && enhancedContent.trim()) {
                console.log('Using enhanced LLM message manager content');
                previewContent = enhancedContent;
            }
        }
        
        // If still no content, try to get content from the enhanced preview element
        if (!previewContent || previewContent === 'No enabled elements to preview' || previewContent === 'Message preview will appear here as you organize elements...') {
            const enhancedPreview = document.getElementById('enhanced-prompt-preview');
            if (enhancedPreview && enhancedPreview.textContent.trim()) {
                previewContent = enhancedPreview.textContent.trim();
                console.log('Using enhanced preview content:', previewContent.substring(0, 100) + '...');
            }
        }
        
        if (!previewContent || previewContent === 'No enabled elements to preview' || previewContent === 'Message preview will appear here as you organize elements...') {
            throw new Error('No content in Live Preview. Please enable some elements in the LLM Message Management panel.');
        }
        
        console.log('[LLM_UTILS] Using Live Preview content:', previewContent);
        
        // Send the preview content directly to LLM
        const response = await fetch('/api/workflow/llm/direct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: previewContent,
                post_id: postId,
                step: step
            })
        });

        console.log('[LLM_UTILS] Response status:', response.status);
        const data = await handleApiResponse(response);
        console.log('[LLM_UTILS] Response data:', data);
        
        // Update output fields with the result
        if (data.success && data.result) {
            const outputs = document.querySelectorAll('[data-section="outputs"] textarea');
            outputs.forEach(output => {
                output.value = data.result;
                output.dispatchEvent(new Event('change', { bubbles: true }));
            });
            
            // Update the outputs summary in the accordion header
            const outputsSummary = document.getElementById('outputs-summary');
            if (outputsSummary) {
                const firstLine = data.result.split('\n')[0] || '';
                outputsSummary.innerHTML = `<span class="text-blue-500">[output]:</span> ${firstLine.substring(0, 100)}${firstLine.length > 100 ? '...' : ''}`;
            }
        } else {
            console.error('Invalid response format:', data);
        }

        return data;
    } catch (error) {
        console.error('LLM Error:', error);
        throw error;
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Run LLM';
        }
    }
}

/**
 * Get selected section IDs from the Writing stage interface
 * @returns {Array} Array of section IDs that are selected/checked
 */
function getSelectedSectionIds() {
    const selectedSections = [];
    
    // Look for checked section checkboxes or selected section elements
    const checkedSections = document.querySelectorAll('input[type="checkbox"][data-section-id]:checked');
    checkedSections.forEach(checkbox => {
        const sectionId = checkbox.getAttribute('data-section-id');
        if (sectionId) {
            selectedSections.push(parseInt(sectionId));
        }
    });
    
    // If no sections are explicitly selected, get all section IDs from the page
    if (selectedSections.length === 0) {
        const allSections = document.querySelectorAll('[data-section-id]');
        allSections.forEach(element => {
            const sectionId = element.getAttribute('data-section-id');
            if (sectionId && !selectedSections.includes(parseInt(sectionId))) {
                selectedSections.push(parseInt(sectionId));
            }
        });
    }
    
    console.log('[LLM_UTILS] Found section IDs:', selectedSections);
    return selectedSections;
}

/**
 * Update UI with LLM call parameters (tokens, model, etc.)
 * @param {Object} parameters - LLM call parameters
 */
function updateParametersDisplay(parameters) {
    const paramsContainer = document.getElementById('llm-parameters');
    if (paramsContainer) {
        paramsContainer.innerHTML = `
            <div class="text-sm text-gray-600">
                <span class="font-semibold">Model:</span> ${parameters.model || 'Unknown'} | 
                <span class="font-semibold">Temperature:</span> ${parameters.temperature || 'Unknown'} | 
                <span class="font-semibold">Tokens:</span> ${parameters.tokens_used || 'Unknown'}
            </div>
        `;
    }
}

// Utility to show the Ollama start alert/button
export function showStartOllamaButton(container, onStarted) {
    container.innerHTML += `
        <div class="mt-4 p-4 bg-yellow-100 rounded">
            <b>Ollama is not running.</b>
            <button id="start-ollama-btn" class="ml-2 px-3 py-1 bg-green-600 text-white rounded">
                <i class="fa-solid fa-play"></i> Start Ollama
            </button>
        </div>
    `;
    document.getElementById('start-ollama-btn').onclick = async function () {
        this.disabled = true;
        this.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Starting...';
        try {
            const url = buildApiUrl(`${API_CONFIG.ENDPOINTS.LLM}/ollama/start`);
            const response = await fetch(url, { method: 'POST' });
            const data = await handleApiResponse(response);
            
            this.innerHTML = '<i class="fa-solid fa-check"></i> Started';
            if (typeof onStarted === 'function') {
                setTimeout(onStarted, 1500);
            } else {
                localStorage.setItem('pendingOllamaAction', 'true');
                setTimeout(() => window.location.reload(), 1000);
            }
        } catch (error) {
            this.innerHTML = '<i class="fa-solid fa-play"></i> Start Ollama';
            alert('Error starting Ollama: ' + error.message);
        }
        setTimeout(() => {
            this.disabled = false;
            this.innerHTML = '<i class="fa-solid fa-play"></i> Start Ollama';
        }, 2000);
    };
}

// Initialize LLM functionality
// Note: Event listener is handled in the panel template to avoid duplicates
// This file only exports the runLLM function for use by other modules

export async function fetchPostDevelopment(postId) {
    const url = buildApiUrl(`${API_CONFIG.ENDPOINTS.POSTS}/${postId}/development`);
    const response = await fetch(url);
    return handleApiResponse(response);
}

export async function updatePostDevelopmentField(postId, field, value) {
    const url = buildApiUrl(`${API_CONFIG.ENDPOINTS.POSTS}/${postId}/development`);
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: value })
    });
    return handleApiResponse(response);
}

// Export functions
export {
    runLLM
};
