// Simplified LLM Actions for Planning Pages
// Self-contained module with all functionality, no complex dependencies

class SimplifiedLLMActions {
    constructor(container) {
        this.container = container;
        this.postId = container.dataset.postId;
        this.stage = container.dataset.stage;
        this.substage = container.dataset.substage;
        this.step = container.dataset.step;
        
        this.systemPrompts = [];
        this.taskPrompts = [];
        this.selectedSystemPrompt = null;
        this.selectedTaskPrompt = null;
        
        this.init();
    }
    
    async init() {
        console.log('[Simplified LLM] Initializing...');
        await this.loadData();
        this.setupUI();
        this.bindEvents();
        console.log('[Simplified LLM] Initialized successfully');
    }
    
    async loadData() {
        try {
            // Load system prompts
            const systemResponse = await fetch('/planning/api/llm/system-prompts');
            const systemData = await systemResponse.json();
            this.systemPrompts = systemData.system_prompts || [];
            
            // Load task prompts
            const taskResponse = await fetch('/planning/api/llm/actions');
            const taskData = await taskResponse.json();
            this.taskPrompts = taskData.task_prompts || [];
            
            console.log(`[Simplified LLM] Loaded ${this.systemPrompts.length} system prompts, ${this.taskPrompts.length} task prompts`);
        } catch (error) {
            console.error('[Simplified LLM] Error loading data:', error);
        }
    }
    
    setupUI() {
        // Populate system prompt dropdown
        const systemSelect = this.container.querySelector('#system-prompt-select');
        if (systemSelect) {
            systemSelect.innerHTML = '<option value="">Choose a system prompt...</option>';
            this.systemPrompts.forEach(prompt => {
                const option = document.createElement('option');
                option.value = prompt.id;
                option.textContent = prompt.name;
                systemSelect.appendChild(option);
            });
        }
        
        // Populate task prompt dropdown
        const taskSelect = this.container.querySelector('#action-select');
        if (taskSelect) {
            taskSelect.innerHTML = '<option value="">Choose an action...</option>';
            this.taskPrompts.forEach(prompt => {
                const option = document.createElement('option');
                option.value = prompt.id;
                option.textContent = prompt.name;
                taskSelect.appendChild(option);
            });
        }
        
        // Setup provider dropdown
        const providerSelect = this.container.querySelector('#config-provider');
        if (providerSelect) {
            providerSelect.innerHTML = `
                <option value="openai">OpenAI</option>
                <option value="ollama">Ollama</option>
            `;
        }
        
        // Setup model dropdown
        const modelSelect = this.container.querySelector('#config-model');
        if (modelSelect) {
            modelSelect.innerHTML = `
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="llama2">Llama 2</option>
            `;
        }
    }
    
    bindEvents() {
        // System prompt selection
        const systemSelect = this.container.querySelector('#system-prompt-select');
        if (systemSelect) {
            systemSelect.addEventListener('change', (e) => {
                const promptId = parseInt(e.target.value);
                this.selectedSystemPrompt = this.systemPrompts.find(p => p.id === promptId);
                this.updateSystemPromptDisplay();
            });
        }
        
        // Task prompt selection
        const taskSelect = this.container.querySelector('#action-select');
        if (taskSelect) {
            taskSelect.addEventListener('change', (e) => {
                const promptId = parseInt(e.target.value);
                this.selectedTaskPrompt = this.taskPrompts.find(p => p.id === promptId);
                this.updateTaskPromptDisplay();
            });
        }
        
        // Run LLM button
        const runButton = this.container.querySelector('.btn-run-llm');
        if (runButton) {
            runButton.addEventListener('click', () => this.runLLM());
        }
        
        // Start Ollama button
        const ollamaButton = this.container.querySelector('.btn-start-ollama');
        if (ollamaButton) {
            ollamaButton.addEventListener('click', () => this.startOllama());
        }
    }
    
    updateSystemPromptDisplay() {
        const display = this.container.querySelector('#system-prompt-display');
        if (display && this.selectedSystemPrompt) {
            display.textContent = this.selectedSystemPrompt.system_prompt || this.selectedSystemPrompt.prompt_text || 'No content available';
        }
    }
    
    updateTaskPromptDisplay() {
        const display = this.container.querySelector('#prompt-display');
        if (display && this.selectedTaskPrompt) {
            display.textContent = this.selectedTaskPrompt.prompt_text || 'No content available';
        }
    }
    
    async runLLM() {
        if (!this.selectedTaskPrompt) {
            alert('Please select a task prompt first');
            return;
        }
        
        const input = this.container.querySelector('#planning-input');
        if (!input || !input.value.trim()) {
            alert('Please enter some input text');
            return;
        }
        
        const provider = this.container.querySelector('#config-provider').value;
        const model = this.container.querySelector('#config-model').value;
        
        console.log('[Simplified LLM] Running LLM...');
        
        try {
            const response = await fetch('/planning/api/run-llm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    post_id: this.postId,
                    stage: this.stage,
                    substage: this.substage,
                    step: this.step,
                    provider: provider,
                    model: model,
                    system_prompt: this.selectedSystemPrompt?.system_prompt || '',
                    task_prompt: this.selectedTaskPrompt.prompt_text,
                    input_data: input.value
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('[Simplified LLM] LLM execution completed:', result);
            
            // Update output field
            const outputField = this.container.querySelector('#output-content');
            if (outputField) {
                outputField.value = result.content || 'No output received';
            }
            
            alert('LLM execution completed successfully!');
            
        } catch (error) {
            console.error('[Simplified LLM] Error running LLM:', error);
            alert(`Error running LLM: ${error.message}`);
        }
    }
    
    async startOllama() {
        console.log('[Simplified LLM] Starting Ollama...');
        
        try {
            const response = await fetch('/planning/api/ollama/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('[Simplified LLM] Ollama start result:', result);
            alert('Ollama service started successfully!');
            
        } catch (error) {
            console.error('[Simplified LLM] Error starting Ollama:', error);
            alert(`Error starting Ollama: ${error.message}`);
        }
    }
}

// Global functions for backward compatibility
window.startOllama = function() {
    const container = document.querySelector('.llm-container');
    if (container && container.llmActions) {
        container.llmActions.startOllama();
    }
};

window.runLLM = function() {
    const container = document.querySelector('.llm-container');
    if (container && container.llmActions) {
        container.llmActions.runLLM();
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.llm-container');
    if (container) {
        container.llmActions = new SimplifiedLLMActions(container);
    }
});
