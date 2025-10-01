/**
 * LLM Module - Core orchestration class for LLM interactions
 * 
 * This class coordinates between specialized managers:
 * - UI Manager: Handles all display and DOM manipulation
 * - API Client: Manages all HTTP requests and API interactions  
 * - Event Manager: Handles user interactions and event listeners
 * 
 * The main class focuses on business logic and orchestration,
 * delegating specific concerns to appropriate managers.
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
            this.uiManager.setupEditButtons(this);
        }
        this.loadPrompt();
    }
    
    setupEventListeners() {
        this.eventManager.setupEventListeners(this);
        this.eventManager.setupKeyboardShortcuts(this);
        this.eventManager.setupFormValidation(this);
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
            this.eventManager.cancelEdit(this);
        } else {
            this.uiManager.displayError(result.error);
        }
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
            // Display raw LLM response
            this.displayRawResponse(result.raw_response || result.content || 'No raw response available');
            
            // Handle different response formats based on config
            if (this.config.resultsField === 'draft_content') {
                // For authoring, put content directly in the editor
                this.uiManager.displayAuthoringResults(result, this);
            } else {
                // For other modules, use standard display
                this.uiManager.displayResults(result.results || result);
            }
        } else {
            this.uiManager.displayError(result.error);
        }
        
        // Reset button state
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate';
    }
    
    displayRawResponse(rawResponse) {
        const rawResponseElement = document.getElementById('raw-llm-response');
        if (rawResponseElement) {
            rawResponseElement.textContent = rawResponse;
        }
    }
    
    setPostId(postId) {
        this.postId = postId;
    }
    
    toggleEdit() {
        this.eventManager.toggleEdit(this);
    }
    
    cancelEdit() {
        this.eventManager.cancelEdit(this);
    }
    
    toggleAccordion() {
        toggleLLMAccordion();
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

// Note: LLM Module has been refactored into modular components:
// - llm-config.js: Configuration and initialization functions
// - llm-utils.js: Utility functions (escapeHtml, toggleLLMAccordion)
// - llm-ui-manager.js: All display and DOM manipulation logic
// - llm-api-client.js: All HTTP requests and API interactions
// - llm-event-manager.js: All event handling and user interactions
// - llm-module.js: Core orchestration and business logic (this file)
