// LLM utility functions
import { API_CONFIG, buildApiUrl, handleApiResponse } from './config/api.js';

/**
 * Run an LLM operation
 * @param {Object} params - Parameters for the LLM operation
 * @param {number} params.postId - The post ID
 * @param {string} params.stage - The workflow stage
 * @param {string} params.substage - The workflow substage
 * @param {string} params.step - The workflow step
 * @param {Object} params.inputs - Multiple input values from MultiInputManager
 * @returns {Promise<Object>} The LLM response
 */
async function runLLM({ postId, stage, substage, step, inputs = {} }) {
    console.log('[LLM_UTILS] runLLM function called with params:', { postId, stage, substage, step, inputs });
    
    const btn = document.querySelector('[data-action="run-llm"]');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Running...';
    }

    try {
        // Determine which endpoint to use based on stage
        let url;
        let requestBody;
        
        if (stage === 'writing') {
            // WRITING STAGE: Use separate endpoint with section selection
            url = `/api/workflow/posts/${postId}/${stage}/${substage}/writing_llm`;
            
            // Get selected section IDs from the page
            const selectedSections = getSelectedSectionIds();
            console.log('[LLM_UTILS] Selected sections for Writing stage:', selectedSections);
            
            requestBody = { 
                step: step,
                selected_section_ids: selectedSections,
                inputs: inputs  // Include multiple inputs in request
            };
        } else {
            // PLANNING STAGE: Use original endpoint
            url = `/api/workflow/posts/${postId}/${stage}/${substage}/llm`;
            requestBody = { 
                step: step,
                inputs: inputs  // Include multiple inputs in request
            };
        }
        
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
            
            // Handle standardized LLM response format
            if (data.success && data.results) {
                // Handle results object with section IDs as keys (Writing stage format)
                if (typeof data.results === 'object' && !Array.isArray(data.results)) {
                    Object.entries(data.results).forEach(([sectionId, result]) => {
                        if (result.success && result.result) {
                            // Update specific section output
                            const sectionOutput = document.querySelector(`[data-section-id="${sectionId}"] textarea[data-field="output"]`);
                            if (sectionOutput) {
                                sectionOutput.value = result.result;
                                sectionOutput.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        } else if (result.error) {
                            console.error(`Error processing section ${sectionId}:`, result.error);
                        }
                    });
                } else if (Array.isArray(data.results)) {
                    // Handle results array (Planning stage format)
                    data.results.forEach(result => {
                        const sectionId = result.section_id;
                        const output = result.output;
                        
                        if (sectionId) {
                            // Update specific section output
                            const sectionOutput = document.querySelector(`[data-section-id="${sectionId}"] textarea[data-field="output"]`);
                            if (sectionOutput) {
                                sectionOutput.value = output;
                                sectionOutput.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        } else {
                            // Update all outputs (for section creation or planning stage)
                            const outputs = document.querySelectorAll('[data-section="outputs"] textarea');
                            outputs.forEach(outputElement => {
                                outputElement.value = output;
                                outputElement.dispatchEvent(new Event('change', { bubbles: true }));
                            });
                            
                            // Update the outputs summary in the accordion header
                            const outputsSummary = document.getElementById('outputs-summary');
                            if (outputsSummary) {
                                const firstLine = output.split('\n')[0] || '';
                                outputsSummary.innerHTML = `<span class="text-blue-500">[output]:</span> ${firstLine.substring(0, 100)}${firstLine.length > 100 ? '...' : ''}`;
                            }
                        }
                    });
                }
                
                // Update parameters display if available
                if (data.parameters) {
                    updateParametersDisplay(data.parameters);
                }
            } else if (data.data && data.data.result) {
                // Fallback for old response format (planning stage)
                const outputs = document.querySelectorAll('[data-section="outputs"] textarea');
                outputs.forEach(output => {
                    output.value = data.data.result;
                    output.dispatchEvent(new Event('change', { bubbles: true }));
                });
                
                const outputsSummary = document.getElementById('outputs-summary');
                if (outputsSummary) {
                    const firstLine = data.data.result.split('\n')[0] || '';
                    outputsSummary.innerHTML = `<span class="text-blue-500">[basic_idea]:</span> ${firstLine.substring(0, 100)}${firstLine.length > 100 ? '...' : ''}`;
                }
            } else {
                console.error('Invalid response format:', data);
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
