/**
 * LLM Prompts Panel - Modular Component
 * Self-contained module for managing LLM prompts with page-specific configuration
 */

class LLMPromptsPanel {
    constructor(options = {}) {
        this.containerId = options.containerId || 'llm-prompts-panel';
        this.postId = options.postId || window.postId;
        
        // Detect page type and get configuration
        this.pageType = this.detectPageType();
        this.config = this.getPageConfig();
        this.storageKey = `${this.pageType}-llm-prompts`;
        
        // Callbacks for external communication
        this.callbacks = {
            onPromptChange: options.onPromptChange || (() => {}),
            onGenerate: options.onGenerate || (() => {}),
            onPromptLoad: options.onPromptLoad || (() => {}),
            onPromptSave: options.onPromptSave || (() => {})
        };
        
        // DOM elements
        this.generateBtn = null;
        this.editPromptBtn = null;
        this.savePromptBtn = null;
        this.cancelEditBtn = null;
        this.promptEditForm = null;
        this.promptDisplay = null;
        this.systemPromptEdit = null;
        this.userPromptEdit = null;
        this.promptTitle = null;
        
        this.isEditing = false;
        this.init();
    }

    init() {
        this.bindElements();
        this.setupEventListeners();
        this.loadPromptState();
        this.loadPromptFromAPI();
        this.restoreAccordionState();
    }

    detectPageType() {
        const substage = window.currentSubstage;
        const mapping = {
            'drafting': 'author_draft',
            'image-concepts': 'image_concepts', 
            'image-prompts': 'image_prompts',
            'image-captions': 'image_captions',
            'image-generation': 'image_generation'
        };
        return mapping[substage] || 'author_draft';
    }

    getPageConfig() {
        // Get configuration from LLM_CONFIGS if available
        if (typeof LLM_CONFIGS !== 'undefined' && LLM_CONFIGS[this.pageType]) {
            return LLM_CONFIGS[this.pageType];
        }
        
        // Fallback configuration
        const fallbackConfigs = {
            'author_draft': {
                promptEndpoint: '/authoring/api/llm/prompts/section-drafting',
                resultsTitle: 'Generated Draft',
                allowEdit: true
            },
            'image_concepts': {
                promptEndpoint: '/authoring/api/llm/prompts/image-concepts',
                resultsTitle: 'Generated Image Concepts',
                allowEdit: true
            },
            'image_prompts': {
                promptEndpoint: '/authoring/api/llm/prompts/image-prompts',
                resultsTitle: 'Generated Image Prompt',
                allowEdit: true
            },
            'image_captions': {
                promptEndpoint: '/authoring/api/llm/prompts/image-captions',
                resultsTitle: 'Generated Image Captions',
                allowEdit: true
            },
            'image_generation': {
                promptEndpoint: '/authoring/api/llm/prompts/image-generation',
                resultsTitle: 'Generated Image',
                allowEdit: false
            }
        };
        
        return fallbackConfigs[this.pageType] || fallbackConfigs['author_draft'];
    }

    bindElements() {
        this.generateBtn = document.getElementById('generate-btn');
        this.editPromptBtn = document.getElementById('edit-prompt-btn');
        this.savePromptBtn = document.getElementById('save-prompt-btn');
        this.cancelEditBtn = document.getElementById('cancel-edit-btn');
        this.promptEditForm = document.getElementById('llm-prompt-edit');
        this.promptDisplay = document.getElementById('llm-prompt-display');
        this.systemPromptEdit = document.getElementById('system-prompt-edit');
        this.userPromptEdit = document.getElementById('user-prompt-edit');
        this.promptTitle = document.getElementById('prompt-title');
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

    async loadPromptFromAPI() {
        try {
            const response = await fetch(this.config.promptEndpoint);
            const data = await response.json();
            
            if (data.success && data.prompt) {
                const prompt = data.prompt;
                this.updatePromptDisplay(prompt.system_prompt || '', prompt.prompt_text || '');
                this.updatePromptTitle(prompt.name || this.config.resultsTitle);
                this.callbacks.onPromptLoad(prompt);
            } else {
                console.warn(`[LLM Prompts Panel] No prompt found for ${this.pageType}`);
                this.updatePromptDisplay('', '');
                this.updatePromptTitle(this.config.resultsTitle);
            }
        } catch (error) {
            console.error(`[LLM Prompts Panel] Error loading prompt for ${this.pageType}:`, error);
            this.updatePromptDisplay('', '');
            this.updatePromptTitle(this.config.resultsTitle);
        }
    }

    updatePromptTitle(title) {
        if (this.promptTitle) {
            this.promptTitle.textContent = title;
        }
    }

    toggleEdit() {
        if (this.isEditing) {
            this.cancelEdit();
        } else {
            this.startEdit();
        }
    }

    startEdit() {
        if (!this.config.allowEdit) {
            console.warn(`[LLM Prompts Panel] Editing not allowed for ${this.pageType}`);
            return;
        }

        this.isEditing = true;
        
        // Show edit form, hide display
        this.promptEditForm.style.display = 'block';
        this.promptDisplay.style.display = 'none';
        
        // Update button states
        this.editPromptBtn.textContent = 'Cancel Edit';
        this.editPromptBtn.classList.add('btn-secondary');
        
        // Load current prompt data into edit form
        this.loadPromptIntoEditForm();
        
        console.log(`[LLM Prompts Panel] Started editing for ${this.pageType}`);
    }

    cancelEdit() {
        this.isEditing = false;
        
        // Show display, hide edit form
        this.promptEditForm.style.display = 'none';
        this.promptDisplay.style.display = 'block';
        
        // Update button states
        this.editPromptBtn.textContent = 'Edit Prompt';
        this.editPromptBtn.classList.remove('btn-secondary');
        
        console.log(`[LLM Prompts Panel] Cancelled editing for ${this.pageType}`);
    }

    async savePrompt() {
        const systemPrompt = this.systemPromptEdit?.value || '';
        const userPrompt = this.userPromptEdit?.value || '';
        
        try {
            // Save to API
            const response = await fetch(this.config.promptEndpoint, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    system_prompt: systemPrompt,
                    prompt_text: userPrompt
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Save to localStorage as backup
                const promptData = {
                    systemPrompt: systemPrompt,
                    userPrompt: userPrompt,
                    timestamp: new Date().toISOString()
                };
                localStorage.setItem(this.storageKey, JSON.stringify(promptData));
                
                // Update display
                this.updatePromptDisplay(systemPrompt, userPrompt);
                
                // Exit edit mode
                this.cancelEdit();
                
                // Emit callback
                this.callbacks.onPromptSave(promptData);
                
                console.log(`[LLM Prompts Panel] Prompt saved for ${this.pageType}`);
            } else {
                console.error(`[LLM Prompts Panel] Error saving prompt:`, data);
            }
        } catch (error) {
            console.error(`[LLM Prompts Panel] Error saving prompt:`, error);
        }
    }

    loadPromptIntoEditForm() {
        const saved = localStorage.getItem(this.storageKey);
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
                console.error(`[LLM Prompts Panel] Error loading prompt data:`, error);
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
        const saved = localStorage.getItem(this.storageKey);
        if (saved) {
            try {
                const promptData = JSON.parse(saved);
                this.updatePromptDisplay(promptData.systemPrompt, promptData.userPrompt);
            } catch (error) {
                console.error(`[LLM Prompts Panel] Error loading prompt state:`, error);
            }
        }
    }

    handleGenerate() {
        // Emit callback for generation - let parent handle the actual generation
        this.callbacks.onGenerate({
            pageType: this.pageType,
            config: this.config,
            postId: this.postId
        });
        
        console.log(`[LLM Prompts Panel] Generate requested for ${this.pageType}`);
    }

    restoreAccordionState() {
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
    }

    // Public API methods
    getCurrentPrompt() {
        return {
            systemPrompt: this.systemPromptEdit?.value || '',
            userPrompt: this.userPromptEdit?.value || '',
            pageType: this.pageType,
            config: this.config
        };
    }

    updatePrompt(systemPrompt, userPrompt) {
        this.updatePromptDisplay(systemPrompt, userPrompt);
        this.savePrompt();
    }

    refreshPrompt() {
        this.loadPromptFromAPI();
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

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LLMPromptsPanel;
}
