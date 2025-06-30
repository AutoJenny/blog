// LLM utility functions
import { API_CONFIG, buildApiUrl, handleApiResponse } from './config/api.js';

/**
 * Run an LLM operation
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
        // Use the correct endpoint path that matches the backend route
        const url = `/api/workflow/posts/${postId}/${stage}/${substage}/llm`;
        const requestBody = { step: step };
        
        console.log('[LLM_UTILS] Sending request to:', url);
        console.log('[LLM_UTILS] Request body:', requestBody);
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            console.log('[LLM_UTILS] Response status:', response.status);
            const data = await handleApiResponse(response);
            console.log('[LLM_UTILS] Response data:', data);
            
            if (data.data && data.data.result) {
                // Update all output textarea fields (not select elements)
                const outputs = document.querySelectorAll('[data-section="outputs"] textarea');
                outputs.forEach(output => {
                    output.value = data.data.result;
                    // Trigger change event
                    output.dispatchEvent(new Event('change', { bubbles: true }));
                });
                
                // Update the outputs summary in the accordion header
                const outputsSummary = document.getElementById('outputs-summary');
                if (outputsSummary) {
                    const firstLine = data.data.result.split('\n')[0] || '';
                    outputsSummary.innerHTML = `<span class="text-blue-500">[basic_idea]:</span> ${firstLine.substring(0, 100)}${firstLine.length > 100 ? '...' : ''}`;
                }
            }

            return data;
        } catch (fetchError) {
            console.error('[LLM_UTILS] Fetch error:', fetchError);
            throw fetchError;
        }
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
