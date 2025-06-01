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