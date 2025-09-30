/**
 * LLM Module - Reusable JavaScript class for LLM interactions
 */

class LLMModule {
    constructor(config) {
        this.config = config;
        this.currentPrompt = null;
        this.isEditing = false;
        this.postId = null;
        
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
                this.displayPrompt(data.prompt);
                this.displayConfig(data.llm_config);
            } else {
                this.displayError('Failed to load prompt');
            }
        } catch (error) {
            console.error('Error loading prompt:', error);
            this.displayError('Failed to load prompt');
        }
    }
    
    displayPrompt(prompt) {
        const promptDisplay = document.getElementById('llm-prompt-display');
        if (!promptDisplay) return;
        
        // Update the prompt header with the prompt name
        const promptTitle = document.getElementById('prompt-title');
        if (promptTitle && prompt.name) {
            promptTitle.textContent = `Prompt: ${prompt.name}`;
        }
        
        let promptHTML = '';
        
        // If there's a separate system prompt, display it first
        if (prompt.system_prompt) {
            promptHTML += `<div class="system-prompt">${this.escapeHtml(prompt.system_prompt)}</div>`;
        }
        
        // Display the main prompt text
        if (prompt.prompt_text) {
            // Highlight placeholders like [TOPIC], [IDEA], etc.
            let highlightedText = prompt.prompt_text.replace(/\[([^\]]+)\]/g, '<span class="placeholder">[$1]</span>');
            promptHTML += `<div class="prompt-text">${this.escapeHtml(highlightedText)}</div>`;
        }
        
        promptDisplay.innerHTML = promptHTML;
    }
    
    displayConfig(config) {
        const providerInfo = document.getElementById('llm-provider-info');
        if (!providerInfo) return;
        
        providerInfo.innerHTML = `
            <div class="provider-item">
                <div class="provider-label">Provider</div>
                <div class="provider-value">${config.provider}</div>
            </div>
            <div class="provider-item">
                <div class="provider-label">Model</div>
                <div class="provider-value">${config.model}</div>
            </div>
            <div class="provider-item">
                <div class="provider-label">Temperature</div>
                <div class="provider-value">${config.temperature}</div>
            </div>
            <div class="provider-item">
                <div class="provider-label">Max Tokens</div>
                <div class="provider-value">${config.max_tokens}</div>
            </div>
        `;
    }
    
    displayError(message) {
        const promptDisplay = document.getElementById('llm-prompt-display');
        if (promptDisplay) {
            promptDisplay.innerHTML = `<div class="error">Error: ${message}</div>`;
        }
        
        const resultsDisplay = document.getElementById('llm-results-display');
        if (resultsDisplay) {
            resultsDisplay.innerHTML = `<div class="error">Error: ${message}</div>`;
        }
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
                    this.displayAuthoringResults(data);
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
    
    displayAuthoringResults(data) {
        const resultsDisplay = document.getElementById('llm-results-display');
        const contentEditor = document.getElementById('content-editor');
        
        if (data.draft_content) {
            // Display in results area
            if (resultsDisplay) {
                resultsDisplay.innerHTML = `<div class="generated-content">${data.draft_content}</div>`;
            }
            
            // Also put in content editor
            if (contentEditor) {
                contentEditor.value = data.draft_content;
                contentEditor.disabled = false;
                
                // Update word count
                const wordCount = data.draft_content.trim().split(/\s+/).filter(word => word.length > 0).length;
                const wordCountElement = document.getElementById('word-count');
                if (wordCountElement) {
                    wordCountElement.textContent = `${wordCount} words`;
                }
                
                // Enable save button
                const saveBtn = document.getElementById('save-btn');
                if (saveBtn) {
                    saveBtn.disabled = false;
                }
            }
        } else {
            this.displayError('No content generated');
        }
    }
    
    setPostId(postId) {
        this.postId = postId;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    toggleAccordion() {
        const accordionContent = document.getElementById('llm-accordion-content');
        const accordionIcon = document.getElementById('accordion-icon');
        
        if (!accordionContent || !accordionIcon) return;
        
        if (accordionContent.classList.contains('open')) {
            // Close accordion
            accordionContent.style.display = 'none';
            accordionIcon.style.transform = 'rotate(0deg)';
            accordionContent.classList.remove('open');
            accordionContent.classList.add('closed');
        } else {
            // Open accordion
            accordionContent.style.display = 'block';
            accordionIcon.style.transform = 'rotate(180deg)';
            accordionContent.classList.remove('closed');
            accordionContent.classList.add('open');
        }
    }
    
    displayAuthoringResults(data) {
        const resultsDisplay = document.getElementById('llm-results-display');
        const contentEditor = document.getElementById('content-editor');
        
        if (data.draft_content) {
            // Display in results area
            if (resultsDisplay) {
                resultsDisplay.innerHTML = `<div class="generated-content">${data.draft_content}</div>`;
            }
            
            // Only update content editor if this is the currently selected section
            if (contentEditor && this.isCurrentSection()) {
                contentEditor.value = data.draft_content;
                contentEditor.disabled = false;
                
                // Update word count
                const wordCount = data.draft_content.trim().split(/\s+/).filter(word => word.length > 0).length;
                const wordCountElement = document.getElementById('word-count');
                if (wordCountElement) {
                    wordCountElement.textContent = `${wordCount} words`;
                }
                
                // Enable save button
                const saveBtn = document.getElementById('save-btn');
                if (saveBtn) {
                    saveBtn.disabled = false;
                }
                
                // Auto-save the generated content
                this.autoSaveContent(data.draft_content);
            }
        } else {
            this.displayError('No content generated');
        }
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

// Global accordion toggle function
function toggleLLMAccordion() {
    const accordionContent = document.getElementById('llm-accordion-content');
    const accordionIcon = document.getElementById('accordion-icon');
    
    if (!accordionContent || !accordionIcon) return;
    
    const isOpen = accordionContent.style.display !== 'none';
    
    if (isOpen) {
        // Close accordion
        accordionContent.style.display = 'none';
        accordionIcon.style.transform = 'rotate(0deg)';
        accordionContent.classList.remove('open');
        accordionContent.classList.add('closed');
    } else {
        // Open accordion
        accordionContent.style.display = 'block';
        accordionIcon.style.transform = 'rotate(180deg)';
        accordionContent.classList.remove('closed');
        accordionContent.classList.add('open');
    }
}

// Configuration for different page types
const LLM_CONFIGS = {
    'ideas': {
        promptEndpoint: '/planning/api/llm/prompts/idea-expansion',
        generateEndpoint: '/planning/api/posts/{id}/expanded-idea',
        resultsField: 'expanded_idea',
        resultsTitle: 'Expanded Idea',
        allowEdit: false
    },
    'brainstorm': {
        promptEndpoint: '/planning/api/llm/prompts/topic-brainstorming',
        generateEndpoint: '/planning/api/brainstorm/topics',
        resultsField: 'idea_scope',
        resultsTitle: 'Generated Topics',
        allowEdit: true
    },
    'grouping': {
        promptEndpoint: '/planning/api/llm/prompts/section-planning',
        generateEndpoint: '/planning/api/sections/group',
        resultsField: 'groups',
        resultsTitle: 'Generated Groups',
        allowEdit: true
    },
    'titling': {
        promptEndpoint: '/planning/api/llm/prompts/section-titling',
        generateEndpoint: '/planning/api/sections/title',
        resultsField: 'sections',
        resultsTitle: 'Generated Sections',
        allowEdit: true
    },
    'sections': {
        promptEndpoint: '/planning/api/llm/prompts/section-planning',
        generateEndpoint: '/planning/api/sections/plan',
        resultsField: 'sections',
        resultsTitle: 'Generated Sections',
        allowEdit: true
    },
    'author_draft': { // Config for authoring section drafts
        promptEndpoint: '/authoring/api/llm/prompts/section-drafting',
        generateEndpoint: '/authoring/api/posts/{id}/sections/{section_id}/generate',
        resultsField: 'draft_content',
        resultsTitle: 'Generated Draft',
        allowEdit: true
    }
};

// Initialize LLM module for a specific page type
function initializeLLMModule(pageType, postId, sectionId = null) {
    const config = LLM_CONFIGS[pageType];
    if (!config) {
        console.error(`Unknown page type: ${pageType}`);
        return null;
    }
    
    // Replace {id} placeholder in generate endpoint
    config.generateEndpoint = config.generateEndpoint.replace('{id}', postId);
    
    // Replace {section_id} placeholder if present and sectionId provided
    if (sectionId && config.generateEndpoint.includes('{section_id}')) {
        config.generateEndpoint = config.generateEndpoint.replace('{section_id}', sectionId);
    }
    
    const module = new LLMModule(config);
    module.setPostId(postId);
    
    // Set results title
    const resultsTitle = document.getElementById('results-title');
    if (resultsTitle) {
        resultsTitle.textContent = config.resultsTitle;
    }
    
    return module;
}
