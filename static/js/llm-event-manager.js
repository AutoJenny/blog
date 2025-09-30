/**
 * LLM Event Manager
 * Handles all DOM event listeners and user interactions for LLM module
 */

class LLMEventManager {
    constructor() {
        // No initialization needed - all methods are stateless
    }

    /**
     * Setup all event listeners for the LLM module
     * @param {Object} module - Reference to the LLM module
     */
    setupEventListeners(module) {
        // Generate button
        const generateBtn = document.getElementById('generate-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => module.generateContent());
        }

        // Regenerate button (if exists)
        const regenerateBtn = document.getElementById('regenerate-btn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => module.generateContent());
        }

        // Edit prompt functionality (if allowed)
        if (module.config.allowEdit) {
            const editBtn = document.getElementById('edit-prompt-btn');
            if (editBtn) {
                editBtn.addEventListener('click', () => this.toggleEdit(module));
            }

            const saveBtn = document.getElementById('save-prompt-btn');
            if (saveBtn) {
                saveBtn.addEventListener('click', () => module.savePrompt());
            }

            const cancelBtn = document.getElementById('cancel-prompt-btn');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => this.cancelEdit(module));
            }
        }

        // Accordion toggle
        const accordionHeader = document.getElementById('llm-accordion-header');
        if (accordionHeader) {
            accordionHeader.addEventListener('click', () => module.toggleAccordion());
        }
    }

    /**
     * Toggle edit mode for prompt editing
     * @param {Object} module - Reference to the LLM module
     */
    toggleEdit(module) {
        if (!module.config.allowEdit) return;
        
        const promptDisplay = document.getElementById('llm-prompt-display');
        const promptEdit = document.getElementById('llm-prompt-edit');
        const editBtn = document.getElementById('edit-prompt-btn');
        const saveBtn = document.getElementById('save-prompt-btn');
        const cancelBtn = document.getElementById('cancel-prompt-btn');
        
        if (!promptDisplay || !promptEdit || !editBtn || !saveBtn || !cancelBtn) return;
        
        if (!module.isEditing) {
            // Switch to edit mode
            promptDisplay.style.display = 'none';
            promptEdit.style.display = 'block';
            editBtn.style.display = 'none';
            saveBtn.style.display = 'inline-block';
            cancelBtn.style.display = 'inline-block';
            module.isEditing = true;
            
            // Populate edit fields with current prompt data
            document.getElementById('system-prompt-edit').value = module.currentPrompt?.system_prompt || '';
            document.getElementById('user-prompt-edit').value = module.currentPrompt?.prompt_text || '';
        } else {
            // Switch back to display mode
            this.cancelEdit(module);
        }
    }

    /**
     * Cancel edit mode and return to display mode
     * @param {Object} module - Reference to the LLM module
     */
    cancelEdit(module) {
        if (!module.config.allowEdit) return;
        
        const promptDisplay = document.getElementById('llm-prompt-display');
        const promptEdit = document.getElementById('llm-prompt-edit');
        const editBtn = document.getElementById('edit-prompt-btn');
        const saveBtn = document.getElementById('save-prompt-btn');
        const cancelBtn = document.getElementById('cancel-prompt-btn');
        
        if (!promptDisplay || !promptEdit || !editBtn || !saveBtn || !cancelBtn) return;
        
        // Switch back to display mode
        promptDisplay.style.display = 'block';
        promptEdit.style.display = 'none';
        editBtn.style.display = 'inline-block';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';
        module.isEditing = false;
    }

    /**
     * Add custom event listener
     * @param {string} elementId - ID of the element
     * @param {string} event - Event type
     * @param {Function} handler - Event handler function
     */
    addCustomEventListener(elementId, event, handler) {
        const element = document.getElementById(elementId);
        if (element) {
            element.addEventListener(event, handler);
        }
    }

    /**
     * Remove event listener
     * @param {string} elementId - ID of the element
     * @param {string} event - Event type
     * @param {Function} handler - Event handler function
     */
    removeEventListener(elementId, event, handler) {
        const element = document.getElementById(elementId);
        if (element) {
            element.removeEventListener(event, handler);
        }
    }

    /**
     * Setup keyboard shortcuts
     * @param {Object} module - Reference to the LLM module
     */
    setupKeyboardShortcuts(module) {
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + Enter to generate content
            if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                const generateBtn = document.getElementById('generate-btn');
                if (generateBtn && !generateBtn.disabled) {
                    event.preventDefault();
                    module.generateContent();
                }
            }
            
            // Escape to cancel edit mode
            if (event.key === 'Escape' && module.isEditing) {
                event.preventDefault();
                this.cancelEdit(module);
            }
        });
    }

    /**
     * Setup form validation events
     * @param {Object} module - Reference to the LLM module
     */
    setupFormValidation(module) {
        if (!module.config.allowEdit) return;
        
        const systemPromptEdit = document.getElementById('system-prompt-edit');
        const userPromptEdit = document.getElementById('user-prompt-edit');
        
        if (systemPromptEdit) {
            systemPromptEdit.addEventListener('input', () => {
                this.validatePromptField(systemPromptEdit);
            });
        }
        
        if (userPromptEdit) {
            userPromptEdit.addEventListener('input', () => {
                this.validatePromptField(userPromptEdit);
            });
        }
    }

    /**
     * Validate a prompt field
     * @param {HTMLElement} field - The field to validate
     */
    validatePromptField(field) {
        const value = field.value.trim();
        const isValid = value.length > 0;
        
        // Add/remove validation classes
        if (isValid) {
            field.classList.remove('invalid');
            field.classList.add('valid');
        } else {
            field.classList.remove('valid');
            field.classList.add('invalid');
        }
        
        // Enable/disable save button based on validation
        const saveBtn = document.getElementById('save-prompt-btn');
        if (saveBtn) {
            const systemPrompt = document.getElementById('system-prompt-edit')?.value.trim() || '';
            const userPrompt = document.getElementById('user-prompt-edit')?.value.trim() || '';
            saveBtn.disabled = !(systemPrompt.length > 0 || userPrompt.length > 0);
        }
    }
}
