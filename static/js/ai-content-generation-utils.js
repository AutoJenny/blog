/**
 * AI Content Generation Utils Module
 * Utility functions and notifications
 */

// Add utility methods to AIContentGenerationManager prototype
Object.assign(AIContentGenerationManager.prototype, {
    
    // Update AI Content Generation header status
    updateAIStatusHeader() {
        const aiStatusElement = document.getElementById('ai-content-status');
        if (!aiStatusElement) return;
        
        if (!this.selectedProduct) {
            aiStatusElement.textContent = 'No item selected';
            return;
        }
        
        if (this.generatedContent && this.generatedContent.trim() !== '') {
            const truncatedContent = this.generatedContent.length > 50 
                ? this.generatedContent.substring(0, 50) + '...'
                : this.generatedContent;
            aiStatusElement.textContent = truncatedContent;
        } else {
            aiStatusElement.textContent = 'Needs generation';
        }
    },
    
    // Show notification message
    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Use global notification function if available
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            // Fallback to alert
            alert(message);
        }
    },
    
    // Check Ollama status and update UI
    async checkOllamaStatus() {
        const btn = document.getElementById('start-ollama-btn');
        if (!btn) return;
        
        try {
            const response = await fetch('http://localhost:11434/api/tags', {
                method: 'GET',
                timeout: 3000
            });
            
            if (response.ok) {
                btn.innerHTML = '<i class="fas fa-check"></i> Ollama Ready';
                btn.classList.remove('btn-secondary');
                btn.classList.add('btn-success');
                btn.disabled = true;
                this.updateGenerateButton();
            } else {
                throw new Error('Ollama not responding');
            }
        } catch (error) {
            console.log('Ollama not running, showing start button');
            btn.innerHTML = '<i class="fas fa-play"></i> Start Ollama';
            btn.classList.remove('btn-success', 'btn-warning');
            btn.classList.add('btn-secondary');
            btn.disabled = false;
        }
    },
    
    // Start Ollama service
    async startOllama() {
        const btn = document.getElementById('start-ollama-btn');
        if (!btn) return;
        
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        btn.disabled = true;
        
        try {
            // Check if Ollama is already running
            const response = await fetch('http://localhost:11434/api/tags', {
                method: 'GET',
                timeout: 3000
            });
            
            if (response.ok) {
                // Ollama is already running
                btn.innerHTML = '<i class="fas fa-check"></i> Ollama Ready';
                btn.classList.remove('btn-secondary', 'btn-warning');
                btn.classList.add('btn-success');
                this.updateGenerateButton();
                this.showNotification('Ollama is already running', 'success');
            } else {
                throw new Error('Ollama not responding');
            }
        } catch (error) {
            // Ollama is not running
            btn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Ollama Not Running';
            btn.classList.remove('btn-secondary', 'btn-success');
            btn.classList.add('btn-warning');
            btn.disabled = false;
            this.showNotification('Ollama is not running. Please start it manually or check the service.', 'warning');
        }
    }
});
