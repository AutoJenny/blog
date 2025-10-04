// Imaging Prompt Construction Panel JavaScript

class PromptConstructionPanel {
    constructor() {
        this.systemPrompt = '';
        this.userPrompt = '';
        this.init();
    }

    init() {
        console.log('[Prompt Construction] Initializing prompt construction panel');
        
        this.setupEventListeners();
        this.loadPromptConfiguration();
        this.updateTitle();
    }

    setupEventListeners() {
        // Save button handler
        const saveBtn = document.getElementById('save-prompts-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.handleSavePrompts());
        }
        
        // Load button handler
        const loadBtn = document.getElementById('load-prompts-btn');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => this.handleLoadPrompts());
        }
        
        // Character count tracking
        const systemPrompt = document.getElementById('system-prompt');
        const userPrompt = document.getElementById('user-prompt');
        
        if (systemPrompt) {
            systemPrompt.addEventListener('input', () => this.updateCharacterCount('system'));
        }
        
        if (userPrompt) {
            userPrompt.addEventListener('input', () => this.updateCharacterCount('user'));
        }
    }

    async loadPromptConfiguration() {
        try {
            console.log('[Prompt Construction] Loading prompt configuration');
            const response = await fetch('/imaging/prompts/image-generation');
            const data = await response.json();
            
            if (data.success) {
                console.log('[Prompt Construction] Configuration loaded:', data);
                
                // Update prompt fields
                if (data.prompt) {
                    const systemPromptEl = document.getElementById('system-prompt');
                    const userPromptEl = document.getElementById('user-prompt');
                    
                    if (systemPromptEl && data.prompt.system_prompt) {
                        systemPromptEl.value = data.prompt.system_prompt;
                        this.systemPrompt = data.prompt.system_prompt;
                    }
                    if (userPromptEl && data.prompt.prompt_text) {
                        userPromptEl.value = data.prompt.prompt_text;
                        this.userPrompt = data.prompt.prompt_text;
                    }
                }
                
                this.updateCharacterCount('system');
                this.updateCharacterCount('user');
            } else {
                throw new Error(data.error || 'Failed to load configuration');
            }
        } catch (error) {
            console.error('[Prompt Construction] Error loading configuration:', error);
            this.updateTitle('Error');
        }
    }

    updateCharacterCount(type) {
        const textarea = document.getElementById(`${type}-prompt`);
        if (!textarea) return;
        
        const count = textarea.value.length;
        const maxLength = type === 'system' ? 500 : 2000;
        
        // Remove existing count indicator
        const existingCount = textarea.parentNode.querySelector('.char-count');
        if (existingCount) {
            existingCount.remove();
        }
        
        // Add new count indicator
        const countEl = document.createElement('div');
        countEl.className = 'char-count';
        
        if (count > maxLength * 0.9) {
            countEl.classList.add('error');
        } else if (count > maxLength * 0.7) {
            countEl.classList.add('warning');
        }
        
        countEl.textContent = `${count}/${maxLength}`;
        textarea.parentNode.appendChild(countEl);
    }

    updateTitle(status = 'Ready') {
        const title = document.getElementById('prompt-title');
        if (title) {
            title.textContent = `Prompt Construction: ${status}`;
        }
    }

    async handleSavePrompts() {
        console.log('[Prompt Construction] Save prompts button clicked');
        
        // Collect prompt data
        const systemPromptEl = document.getElementById('system-prompt');
        const userPromptEl = document.getElementById('user-prompt');
        
        const prompts = {
            system_prompt: systemPromptEl ? systemPromptEl.value : '',
            user_prompt: userPromptEl ? userPromptEl.value : ''
        };
        
        // Update internal state
        this.systemPrompt = prompts.system_prompt;
        this.userPrompt = prompts.user_prompt;
        
        try {
            const response = await fetch('/imaging/prompts/image-generation', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(prompts)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.updateTitle('Saved');
                alert('Prompts saved successfully!');
            } else {
                throw new Error(result.error || 'Failed to save prompts');
            }
        } catch (error) {
            console.error('[Prompt Construction] Error saving prompts:', error);
            alert('Error saving prompts: ' + error.message);
            this.updateTitle('Error');
        }
    }

    async handleLoadPrompts() {
        console.log('[Prompt Construction] Load prompts button clicked');
        
        // Reload the prompt configuration
        await this.loadPromptConfiguration();
        this.updateTitle('Loaded');
        alert('Prompts loaded successfully!');
    }

    getPromptData() {
        const systemPromptEl = document.getElementById('system-prompt');
        const userPromptEl = document.getElementById('user-prompt');
        
        return {
            system_prompt: systemPromptEl ? systemPromptEl.value : '',
            user_prompt: userPromptEl ? userPromptEl.value : ''
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.promptConstructionPanel = new PromptConstructionPanel();
});

// Accordion functionality
function togglePromptConstructionAccordion() {
    const content = document.getElementById('prompt-accordion-content');
    const icon = document.getElementById('prompt-accordion-icon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        localStorage.setItem('imaging-prompt-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        localStorage.setItem('imaging-prompt-accordion-state', 'closed');
    }
}

// Restore accordion state on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedState = localStorage.getItem('imaging-prompt-accordion-state');
    if (savedState === 'open') {
        const content = document.getElementById('prompt-accordion-content');
        const icon = document.getElementById('prompt-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        }
    }
});
