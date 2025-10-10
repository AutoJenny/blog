/**
 * Section Drafting LLM Prompts Handler
 * Focused micro-module for managing LLM prompts on section drafting page
 */

class SectionDraftingLLMPrompts {
    constructor() {
        this.generateBtn = document.getElementById('generate-btn');
        this.editPromptBtn = document.getElementById('edit-prompt-btn');
        this.savePromptBtn = document.getElementById('save-prompt-btn');
        this.cancelEditBtn = document.getElementById('cancel-edit-btn');
        this.promptEditForm = document.getElementById('llm-prompt-edit');
        this.promptDisplay = document.getElementById('llm-prompt-display');
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
        
        console.log('[Section Drafting LLM Prompts] Started editing');
    }

    cancelEdit() {
        this.isEditing = false;
        
        // Show display, hide edit form
        this.promptEditForm.style.display = 'none';
        this.promptDisplay.style.display = 'block';
        
        // Update button states
        this.editPromptBtn.textContent = 'Edit Prompt';
        this.editPromptBtn.classList.remove('btn-secondary');
        
        console.log('[Section Drafting LLM Prompts] Cancelled editing');
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
        
        localStorage.setItem('section-drafting-llm-prompts', JSON.stringify(promptData));
        
        // Update display
        this.updatePromptDisplay(systemPrompt, userPrompt);
        
        // Exit edit mode
        this.cancelEdit();
        
        console.log('[Section Drafting LLM Prompts] Prompt saved');
    }

    loadPromptIntoEditForm() {
        const saved = localStorage.getItem('section-drafting-llm-prompts');
        if (saved) {
            try {
                const promptData = JSON.parse(saved);
                if (this.systemPromptEdit) {
                    this.systemPromptEdit.value = promptData.systemPrompt || '';
                }
                if (this.userPromptEdit) {
                    this.userPromptEdit.value = promptData.userPrompt || '';
                }
            } catch (error) {
                console.error('[Section Drafting LLM Prompts] Error loading prompt data:', error);
            }
        }
    }

    updatePromptDisplay(systemPrompt, userPrompt) {
        if (this.promptDisplay) {
            this.promptDisplay.innerHTML = `
                <div class="prompt-section">
                    <h6>System Prompt:</h6>
                    <div class="prompt-content">${systemPrompt || 'No system prompt set'}</div>
                </div>
                <div class="prompt-section">
                    <h6>User Prompt:</h6>
                    <div class="prompt-content">${userPrompt || 'No user prompt set'}</div>
                </div>
            `;
        }
    }

    loadPromptState() {
        const saved = localStorage.getItem('section-drafting-llm-prompts');
        if (saved) {
            try {
                const promptData = JSON.parse(saved);
                this.updatePromptDisplay(promptData.systemPrompt, promptData.userPrompt);
            } catch (error) {
                console.error('[Section Drafting LLM Prompts] Error loading prompt state:', error);
            }
        } else {
            // Show default state
            this.updatePromptDisplay('', '');
        }
    }

    handleGenerate() {
        // This will be handled by the main LLM module
        console.log('[Section Drafting LLM Prompts] Generate button clicked');
    }
}

// Accordion function for prompts panel
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
    window.sectionDraftingLLMPrompts = new SectionDraftingLLMPrompts();
});
