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
    const btn = document.querySelector('[data-action="run-llm"]');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Running...';
    }

    try {
        const url = buildApiUrl(`${API_CONFIG.ENDPOINTS.POSTS}/${postId}/${stage}/${substage}/llm`);
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                step
            })
        });

        const data = await handleApiResponse(response);
        
        if (data.result) {
            // Update all output fields
            const outputs = document.querySelectorAll('[data-section="outputs"]');
            outputs.forEach(output => {
                output.textContent = data.result;
                // Trigger change event
                output.dispatchEvent(new Event('change', { bubbles: true }));
            });
            
            // Update the outputs summary in the accordion header
            const outputsSummary = document.getElementById('outputs-summary');
            if (outputsSummary) {
                const firstLine = data.result.split('\n')[0] || '';
                outputsSummary.innerHTML = `<span class="text-blue-500">[basic_idea]:</span> ${firstLine.substring(0, 100)}${firstLine.length > 100 ? '...' : ''}`;
            }
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
document.addEventListener('DOMContentLoaded', function() {
    const runLLMBtn = document.getElementById('run-llm-btn');
    if (runLLMBtn) {
        runLLMBtn.addEventListener('click', async function() {
            try {
                // Extract workflow context from URL using path segments
                const [, workflow, posts, postId, stage, substage] = window.location.pathname.split('/');
                const urlParams = new URLSearchParams(window.location.search);
                const step = urlParams.get('step') || 'initial';
                
                if (!postId || !stage) {
                    throw new Error('Invalid workflow URL structure');
                }
                
                await runLLM({ postId, stage, substage, step });
            } catch (error) {
                console.error('Error running LLM:', error);
                alert('Error running LLM: ' + error.message);
            }
        });
    }
});

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
