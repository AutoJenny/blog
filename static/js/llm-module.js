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
        this.apiClient = new LLMAPIClient();
        this.eventManager = new LLMEventManager();
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        if (this.config.allowEdit) {
            this.setupEditButtons();
        }
        this.loadPrompt();
    }
    
    setupEventListeners() {
        this.eventManager.setupEventListeners(this);
        this.eventManager.setupKeyboardShortcuts(this);
        this.eventManager.setupFormValidation(this);
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
        }
    }
    
    async loadPrompt() {
        const result = await this.apiClient.loadPrompt(this.config.promptEndpoint);
        
        if (result.success) {
            this.currentPrompt = result.prompt;
            this.uiManager.displayPrompt(result.prompt);
            this.uiManager.displayConfig(result.llm_config);
        } else {
            this.uiManager.displayError(result.error);
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
        this.eventManager.toggleEdit(this);
    }
    
    async savePrompt() {
        if (!this.config.allowEdit) return;
        
        const systemPrompt = document.getElementById('system-prompt-edit').value;
        const userPrompt = document.getElementById('user-prompt-edit').value;
        
        const promptData = {
            system_prompt: systemPrompt,
            prompt_text: userPrompt
        };
        
        const result = await this.apiClient.savePrompt(this.config.promptEndpoint, promptData);
        
        if (result.success) {
            this.currentPrompt = result.prompt;
            this.uiManager.displayPrompt(result.prompt);
            this.cancelEdit();
        } else {
            this.uiManager.displayError(result.error);
        }
    }
    
    cancelEdit() {
        this.eventManager.cancelEdit(this);
    }
    
    async generateContent() {
        const generateBtn = document.getElementById('generate-btn');
        const resultsDisplay = document.getElementById('llm-results-display');
        
        if (!generateBtn || !resultsDisplay) return;
        
        // Show loading state
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        resultsDisplay.innerHTML = '<div class="loading">Generating content...</div>';
        
        const requestData = {
            post_id: this.postId
        };
        
        const result = await this.apiClient.generateContent(this.config.generateEndpoint, requestData);
        
        if (result.success) {
            // Handle different response formats based on config
            if (this.config.resultsField === 'draft_content') {
                // For authoring, put content directly in the editor
                this.uiManager.displayAuthoringResults(result, this);
            } else {
                // For other modules, use standard display
                this.displayResults(result.results || result);
            }
        } else {
            this.uiManager.displayError(result.error);
        }
        
        // Reset button state
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate';
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
}

// Note: Configuration and utilities are now in separate files:
// - llm-config.js: Contains LLM_CONFIGS and initializeLLMModule()
// - llm-utils.js: Contains utility functions like escapeHtml() and toggleLLMAccordion()
