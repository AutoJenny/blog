/**
 * LLM Module - Reusable JavaScript class for LLM interactions
 */

class LLMModule {
    constructor(config) {
        this.config = config;
        this.currentPrompt = null;
        this.isEditing = false;
        this.postId = null;
        this.uiManager = new LLMUIManager();
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadPrompt();
    }
    
    setupEventListeners() {
        // Generate button
        const generateBtn = document.getElementById('generate-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateContent());
        }
        
        // Edit buttons (if editing is enabled)
        if (this.config.allowEdit) {
            this.setupEditButtons();
        }
    }
    
    setupEditButtons() {
        // Create edit buttons dynamically
        const promptActions = document.getElementById('prompt-actions');
        if (promptActions) {
            promptActions.innerHTML = `
                <button class="btn btn-secondary" id="edit-prompt-btn">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-success" id="save-prompt-btn" style="display: none;">
                    <i class="fas fa-save"></i> Save
                </button>
                <button class="btn btn-secondary" id="cancel-prompt-btn" style="display: none;">
                    <i class="fas fa-times"></i> Cancel
                </button>
            `;
            
            // Add event listeners
            document.getElementById('edit-prompt-btn').addEventListener('click', () => this.toggleEdit());
            document.getElementById('save-prompt-btn').addEventListener('click', () => this.savePrompt());
            document.getElementById('cancel-prompt-btn').addEventListener('click', () => this.cancelEdit());
        }
    }
    
    async loadPrompt() {
        try {
            const response = await fetch(this.config.promptEndpoint);
            const data = await response.json();
            
            if (data.success) {
                this.currentPrompt = data.prompt;
                this.uiManager.displayPrompt(data.prompt);
                this.uiManager.displayConfig(data.llm_config);
            } else {
                this.uiManager.displayError('Failed to load prompt');
            }
        } catch (error) {
            console.error('Error loading prompt:', error);
            this.uiManager.displayError('Failed to load prompt');
        }
    }
    
    displayPrompt(prompt) {
        this.uiManager.displayPrompt(prompt);
    }
    
    displayConfig(config) {
        this.uiManager.displayConfig(config);
    }
    
    displayError(message) {
        this.uiManager.displayError(message);
    }
    
    toggleEdit() {
        if (!this.config.allowEdit) return;
        
        const promptDisplay = document.getElementById('llm-prompt-display');
        const promptEdit = document.getElementById('llm-prompt-edit');
        const editBtn = document.getElementById('edit-prompt-btn');
        const saveBtn = document.getElementById('save-prompt-btn');
        const cancelBtn = document.getElementById('cancel-prompt-btn');
        
        if (this.isEditing) {
            // Hide edit mode
            promptDisplay.style.display = 'block';
            promptEdit.style.display = 'none';
            editBtn.style.display = 'inline-block';
            saveBtn.style.display = 'none';
            cancelBtn.style.display = 'none';
            this.isEditing = false;
        } else {
            // Show edit mode
            promptDisplay.style.display = 'none';
            promptEdit.style.display = 'block';
            editBtn.style.display = 'none';
            saveBtn.style.display = 'inline-block';
            cancelBtn.style.display = 'inline-block';
            this.isEditing = true;
            
            // Populate edit fields
            document.getElementById('system-prompt-edit').value = this.currentPrompt?.system_prompt || '';
            document.getElementById('user-prompt-edit').value = this.currentPrompt?.prompt_text || '';
        }
    }
    
    async savePrompt() {
        if (!this.config.allowEdit) return;
        
        const systemPrompt = document.getElementById('system-prompt-edit').value;
        const userPrompt = document.getElementById('user-prompt-edit').value;
        
        try {
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
                this.currentPrompt = data.prompt;
                this.displayPrompt(data.prompt);
                this.cancelEdit();
            } else {
                this.displayError('Failed to save prompt');
            }
        } catch (error) {
            console.error('Error saving prompt:', error);
            this.displayError('Failed to save prompt');
        }
    }
    
    cancelEdit() {
        if (!this.config.allowEdit) return;
        
        const promptDisplay = document.getElementById('llm-prompt-display');
        const promptEdit = document.getElementById('llm-prompt-edit');
        const editBtn = document.getElementById('edit-prompt-btn');
        const saveBtn = document.getElementById('save-prompt-btn');
        const cancelBtn = document.getElementById('cancel-prompt-btn');
        
        // Hide edit mode
        promptDisplay.style.display = 'block';
        promptEdit.style.display = 'none';
        editBtn.style.display = 'inline-block';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';
        this.isEditing = false;
    }
    
    async generateContent() {
        const generateBtn = document.getElementById('generate-btn');
        const resultsDisplay = document.getElementById('llm-results-display');
        
        if (!generateBtn || !resultsDisplay) return;
        
        // Show loading state
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        resultsDisplay.innerHTML = '<div class="loading">Generating content...</div>';
        
        try {
            const response = await fetch(this.config.generateEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    post_id: this.postId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Handle different response formats based on config
                if (this.config.resultsField === 'draft_content') {
                    // For authoring, put content directly in the editor
                    this.uiManager.displayAuthoringResults(data, this);
                } else {
                    // For other modules, use standard display
                    this.displayResults(data.results || data);
                }
            } else {
                this.displayError(data.error || 'Generation failed');
            }
        } catch (error) {
            console.error('Error generating content:', error);
            this.displayError('Generation failed');
        } finally {
            // Reset button state
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate';
        }
    }
    
    setPostId(postId) {
        this.postId = postId;
    }
    
    escapeHtml(text) {
        return window.escapeHtml ? window.escapeHtml(text) : escapeHtml(text);
    }
    
    toggleAccordion() {
        toggleLLMAccordion();
    }
    
    displayResults(data) {
        this.uiManager.displayResults(data);
    }
    
    isCurrentSection() {
        // Check if this LLM module is for the currently selected section
        const currentSectionId = window.currentSelectedSectionId;
        if (!currentSectionId) return false;
        
        // Extract section ID from the generate endpoint
        const endpointMatch = this.config.generateEndpoint.match(/\/sections\/(\d+)\/generate/);
        if (!endpointMatch) return false;
        
        const moduleSectionId = parseInt(endpointMatch[1]);
        return moduleSectionId === currentSectionId;
    }
    
    async autoSaveContent(content) {
        const currentSectionId = window.currentSelectedSectionId;
        if (!currentSectionId) return;
        
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections/${currentSectionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    draft_content: content,
                    status: 'complete'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update last saved indicator
                const lastSavedElement = document.getElementById('last-saved');
                if (lastSavedElement) {
                    lastSavedElement.textContent = 'Auto-saved just now';
                }
                
                // Update section status in UI
                const sectionItem = document.querySelector(`[data-section-id="${currentSectionId}"]`);
                if (sectionItem) {
                    sectionItem.setAttribute('data-status', 'complete');
                    const statusElement = sectionItem.querySelector('.section-status');
                    if (statusElement) {
                        statusElement.textContent = 'Complete';
                        statusElement.className = 'section-status complete';
                    }
                }
                
                console.log('Content auto-saved successfully');
            } else {
                console.error('Auto-save failed:', data.error);
            }
        } catch (error) {
            console.error('Error auto-saving content:', error);
        }
    }
}

// Note: Configuration and utilities are now in separate files:
// - llm-config.js: Contains LLM_CONFIGS and initializeLLMModule()
// - llm-utils.js: Contains utility functions like escapeHtml() and toggleLLMAccordion()
