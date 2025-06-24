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
            const resp = await fetch('/api/v1/llm/ollama/start', { method: 'POST' });
            const data = await resp.json();
            if (resp.ok && data.success) {
                this.innerHTML = '<i class="fa-solid fa-check"></i> Started';
                if (typeof onStarted === 'function') {
                    setTimeout(onStarted, 1500);
                } else {
                    localStorage.setItem('pendingOllamaAction', 'true');
                    setTimeout(() => window.location.reload(), 1000);
                }
            } else {
                this.innerHTML = '<i class="fa-solid fa-play"></i> Start Ollama';
                alert(data.error || 'Failed to start Ollama');
            }
        } catch (e) {
            this.innerHTML = '<i class="fa-solid fa-play"></i> Start Ollama';
            alert('Error starting Ollama: ' + e);
        }
        setTimeout(() => {
            this.disabled = false;
            this.innerHTML = '<i class="fa-solid fa-play"></i> Start Ollama';
        }, 2000);
    };
}

// LLM Panel Functionality
document.addEventListener('DOMContentLoaded', function() {
    const runLLMBtn = document.getElementById('run-llm-btn');
    if (runLLMBtn) {
        runLLMBtn.addEventListener('click', async function() {
            try {
                runLLMBtn.disabled = true;
                runLLMBtn.textContent = 'Processing...';
                
                // Get current workflow context from URL
                const pathParts = window.location.pathname.split('/');
                const postId = pathParts[3];
                const stage = pathParts[4];
                const substage = pathParts[5];
                const urlParams = new URLSearchParams(window.location.search);
                const step = urlParams.get('step') || 'initial';
                
                const response = await fetch('/api/v1/workflow/run_llm/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        post_id: postId,
                        stage: stage,
                        substage: substage,
                        step: step
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    // Update output fields
                    const outputs = document.querySelectorAll('[data-section="outputs"]');
                    outputs.forEach(output => {
                        output.textContent = result.result;
                        // Trigger change event to ensure any listeners are notified
                        output.dispatchEvent(new Event('change', { bubbles: true }));
                    });
                    
                    // Update the outputs summary in the accordion header
                    const outputsSummary = document.getElementById('outputs-summary');
                    if (outputsSummary) {
                        const firstLine = result.result.split('\n')[0];
                        outputsSummary.innerHTML = `<span class="text-blue-500">[basic_idea]:</span> ${firstLine.length > 100 ? 
                            firstLine.substring(0, 97) + '...' : 
                            firstLine}`;
                    }
                } else {
                    throw new Error(result.error || 'Unknown error occurred');
                }
            } catch (error) {
                console.error('Error running LLM:', error);
                alert('Error running LLM: ' + error.message);
            } finally {
                runLLMBtn.disabled = false;
                runLLMBtn.textContent = 'Run LLM';
            }
        });
    }
});

function runLLM(postId, stage, substage, step) {
    const btn = document.querySelector('[data-action="run-llm"]');
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = 'Running...';

    fetch('/workflow/api/v1/workflow/run_llm/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            post_id: postId,
            stage: stage,
            substage: substage,
            step: step
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('LLM Response:', data);
        
        if (data.success && data.result) {
            // Update all output fields
            const outputs = document.querySelectorAll('[data-section="outputs"]');
            console.log('Found output elements:', outputs);
            
            outputs.forEach(output => {
                console.log('Updating output:', output);
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
        } else {
            console.error('LLM Error:', data.error);
            alert('Error running LLM: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('LLM Error:', error);
        alert('Error running LLM: ' + error.message);
    })
    .finally(() => {
        btn.disabled = false;
        btn.textContent = 'Run LLM';
    });
} 