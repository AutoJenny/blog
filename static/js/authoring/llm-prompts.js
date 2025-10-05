/**
 * Authoring LLM Prompts Panel Handler
 * Manages prompt display, editing, and generation
 */

class AuthoringLLMPromptsHandler {
    constructor() {
        this.generateBtn = document.getElementById('generate-btn');
        this.editPromptBtn = document.getElementById('edit-prompt-btn');
        this.savePromptBtn = document.getElementById('save-prompt-btn');
        this.cancelEditBtn = document.getElementById('cancel-edit-btn');
        this.promptEditForm = document.getElementById('llm-prompt-edit');
        this.promptDisplay = document.getElementById('llm-prompt-display');
        this.providerInfo = document.getElementById('llm-provider-info');
        this.systemPromptEdit = document.getElementById('system-prompt-edit');
        this.userPromptEdit = document.getElementById('user-prompt-edit');
        
        this.isEditing = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPromptState();
    }

    setupEventListeners() {
        // Generate button
        this.generateBtn?.addEventListener('click', () => {
            this.handleGenerate();
        });

        // Edit prompt button
        this.editPromptBtn?.addEventListener('click', () => {
            this.toggleEdit();
        });

        // Save prompt button
        this.savePromptBtn?.addEventListener('click', () => {
            this.savePrompt();
        });

        // Cancel edit button
        this.cancelEditBtn?.addEventListener('click', () => {
            this.cancelEdit();
        });
    }

    toggleEdit() {
        if (this.isEditing) {
            this.cancelEdit();
        } else {
            this.startEdit();
        }
    }

    startEdit() {
        this.isEditing = true;
        
        // Show edit form, hide display
        this.promptEditForm.style.display = 'block';
        this.promptDisplay.style.display = 'none';
        
        // Update button states
        this.editPromptBtn.textContent = 'Cancel Edit';
        this.editPromptBtn.classList.add('btn-secondary');
        
        // Load current prompt data into edit form
        this.loadPromptIntoEditForm();
        
        console.log('[LLM Prompts] Started editing');
    }

    cancelEdit() {
        this.isEditing = false;
        
        // Show display, hide edit form
        this.promptEditForm.style.display = 'none';
        this.promptDisplay.style.display = 'block';
        
        // Update button states
        this.editPromptBtn.textContent = 'Edit Prompt';
        this.editPromptBtn.classList.remove('btn-secondary');
        
        console.log('[LLM Prompts] Cancelled editing');
    }

    savePrompt() {
        const systemPrompt = this.systemPromptEdit?.value || '';
        const userPrompt = this.userPromptEdit?.value || '';
        
        // Save to localStorage
        const promptData = {
            systemPrompt: systemPrompt,
            userPrompt: userPrompt,
            timestamp: new Date().toISOString()
        };
        
        localStorage.setItem('authoring-llm-prompts', JSON.stringify(promptData));
        
        // Update display
        this.updatePromptDisplay(systemPrompt, userPrompt);
        
        // Exit edit mode
        this.cancelEdit();
        
        console.log('[LLM Prompts] Prompt saved:', promptData);
    }

    loadPromptIntoEditForm() {
        const saved = localStorage.getItem('authoring-llm-prompts');
        if (saved) {
            try {
                const promptData = JSON.parse(saved);
                this.systemPromptEdit.value = promptData.systemPrompt || '';
                this.userPromptEdit.value = promptData.userPrompt || '';
            } catch (error) {
                console.error('[LLM Prompts] Error loading prompt data:', error);
            }
        }
    }

    updatePromptDisplay(systemPrompt, userPrompt) {
        if (this.promptDisplay) {
            let displayText = '';
            
            if (systemPrompt) {
                displayText += `System: ${systemPrompt}\n\n`;
            }
            
            if (userPrompt) {
                displayText += `User: ${userPrompt}`;
            }
            
            this.promptDisplay.textContent = displayText || 'No prompt data available';
        }
    }

    loadPromptState() {
        const saved = localStorage.getItem('authoring-llm-prompts');
        if (saved) {
            try {
                const promptData = JSON.parse(saved);
                this.updatePromptDisplay(promptData.systemPrompt, promptData.userPrompt);
            } catch (error) {
                console.error('[LLM Prompts] Error loading prompt state:', error);
            }
        }
    }

    async handleGenerate() {
        if (!this.generateBtn) return;
        
        // Show loading state
        this.generateBtn.disabled = true;
        this.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        
        try {
            // Call the existing LLM generation logic
            if (window.llmModule && window.llmModule.generateContent) {
                await window.llmModule.generateContent();
            } else {
                console.warn('[LLM Prompts] LLM module not available for generation');
            }
        } catch (error) {
            console.error('[LLM Prompts] Generation error:', error);
        } finally {
            // Reset button state
            this.generateBtn.disabled = false;
            this.generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate';
        }
    }
}

// Accordion functions
function toggleLLMPromptsAccordion() {
    const content = document.getElementById('prompts-accordion-content');
    const icon = document.getElementById('prompts-accordion-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        localStorage.setItem('llm-prompts-accordion-state', 'open');
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        localStorage.setItem('llm-prompts-accordion-state', 'closed');
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Restore accordion state
    const savedState = localStorage.getItem('llm-prompts-accordion-state');
    if (savedState === 'open') {
        const content = document.getElementById('prompts-accordion-content');
        const icon = document.getElementById('prompts-accordion-icon');
        if (content && icon) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
        }
    }
    
    // Initialize prompts handler
    window.authoringLLMPromptsHandler = new AuthoringLLMPromptsHandler();
});
