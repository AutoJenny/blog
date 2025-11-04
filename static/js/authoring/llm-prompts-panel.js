/**
 * LLM Prompts Panel - Modular Component
 * Self-contained module for managing LLM prompts with page-specific configuration
 */

class LLMPromptsPanel {
    constructor(options = {}) {
        this.containerId = options.containerId || 'llm-prompts-panel';
        this.postId = options.postId || window.postId;
        
        // Skip initialization on optimise page (doesn't need LLM panels)
        if (window.optimisePage || window.currentSubstage === 'optimise') {
            console.warn('[LLM Prompts Panel] Skipping initialization on optimise page');
            this.config = null;
            this.pageType = null;
            return;
        }
        
        // Detect page type and get configuration
        this.pageType = this.detectPageType();
        console.log('[LLM Prompts Panel] Detected pageType:', this.pageType, 'from substage:', window.currentSubstage);
        this.config = this.getPageConfig();
        
        // If config is null (e.g., on optimise page), don't proceed
        if (!this.config) {
            console.warn('[LLM Prompts Panel] No config available, skipping initialization');
            return;
        }
        
        // Override promptEndpoint if provided in options (for post-specific endpoints)
        if (options.promptEndpoint) {
            this.config.promptEndpoint = options.promptEndpoint;
            console.log('[LLM Prompts Panel] Using custom promptEndpoint from options:', this.config.promptEndpoint);
        } else if (this.config.promptEndpoint && this.config.promptEndpoint.includes('{id}')) {
            // Replace {id} placeholder if present
            this.config.promptEndpoint = this.config.promptEndpoint.replace('{id}', this.postId);
            console.log('[LLM Prompts Panel] Replaced {id} in promptEndpoint:', this.config.promptEndpoint);
        }
        
        console.log('[LLM Prompts Panel] Initialized:', {
            pageType: this.pageType,
            promptEndpoint: this.config.promptEndpoint,
            resultsTitle: this.config.resultsTitle,
            illustrationMethod: window.illustrationMethod
        });
        this.storageKey = `${this.pageType}-llm-prompts`; // legacy key (will not be used)
        this.currentPrompt = { system_prompt: '', prompt_text: '' }; // in-memory source of truth
        
        // Prompt selection support (for category-contingent prompts)
        this.promptSelectionEndpoint = options.promptSelectionEndpoint;
        this.availablePrompts = [];
        this.currentPromptName = null;
        
        // Callbacks for external communication
        this.callbacks = {
            onPromptChange: options.onPromptChange || (() => {}),
            onPromptLoad: options.onPromptLoad || (() => {}),
            onPromptSave: options.onPromptSave || (() => {})
        };
        
        // DOM elements
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
        // Load prompt selection first if endpoint is provided (for category-contingent prompts)
        if (this.promptSelectionEndpoint) {
            this.loadPromptSelection().then(() => {
                // Then load the actual prompt content from database
                this.loadPromptFromAPI();
            });
        } else {
            // Do not use localStorage; rely on DB-backed API
            this.loadPromptFromAPI();
        }
        this.restoreAccordionState();
    }

    detectPageType() {
        const substage = window.currentSubstage;
        const mapping = {
            // Authoring substages
            'drafting': 'author_draft',
            'image-concepts': 'image_concepts', 
            'image-prompts': 'image_prompts',
            'image-captions': 'image_captions',
            'image-generation': 'image_generation',
            // Planning substages
            'ideas': 'ideas',
            'ideas-week': 'ideas', // Week-based ideas page
            'brainstorm': 'brainstorm',
            'section-structure': 'section_structure',
            'topic-allocation': 'topic_allocation',
            'titling': 'titling',
            'topic-refinement': 'topic_refinement',
            'sections': 'sections',
            'grouping': 'grouping'
        };
        return mapping[substage] || (window.currentStage === 'planning' ? 'ideas' : 'author_draft');
    }

    getPageConfig() {
        // ONLY use LLM_CONFIGS - no fallbacks
        if (typeof LLM_CONFIGS === 'undefined') {
            console.error('[LLM Prompts Panel] LLM_CONFIGS not loaded!');
            // Don't throw error if on optimise page (which doesn't need LLM panels)
            if (window.optimisePage || window.currentSubstage === 'optimise') {
                console.warn('[LLM Prompts Panel] Skipping initialization on optimise page');
                return null;
            }
            throw new Error('LLM_CONFIGS not loaded - llm-config.js must be included on page');
        }
        
        if (!LLM_CONFIGS[this.pageType]) {
            console.error('[LLM Prompts Panel] No config for pageType:', this.pageType);
            console.error('[LLM Prompts Panel] Available configs:', Object.keys(LLM_CONFIGS));
            // Don't throw error if on optimise page
            if (window.optimisePage || window.currentSubstage === 'optimise') {
                console.warn('[LLM Prompts Panel] Skipping initialization on optimise page');
                return null;
            }
            throw new Error(`No LLM config found for page type: ${this.pageType}`);
        }
        
        return LLM_CONFIGS[this.pageType];
    }

    bindElements() {
        this.editPromptBtn = document.getElementById('edit-prompt-btn');
        this.savePromptBtn = document.getElementById('save-prompt-btn');
        this.cancelEditBtn = document.getElementById('cancel-edit-btn');
        this.promptEditForm = document.getElementById('llm-prompt-edit');
        this.promptDisplay = document.getElementById('llm-prompt-display');
        this.systemPromptEdit = document.getElementById('system-prompt-edit');
        this.userPromptEdit = document.getElementById('user-prompt-edit');
        this.promptTitle = document.getElementById('llm-prompt-title');
    }

    setupEventListeners() {
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


    async loadPromptSelection() {
        if (!this.promptSelectionEndpoint) return;
        
        try {
            const response = await fetch(this.promptSelectionEndpoint);
            const data = await response.json();
            
            if (data.success) {
                this.availablePrompts = data.available_prompts || [];
                this.currentPromptName = data.current_selection;
                
                // Update header to show selected prompt name
                this.updatePromptTitle(this.currentPromptName || 'No prompt selected');
                
                // Show prompt selector if multiple options available
                if (this.availablePrompts.length > 1) {
                    this.showPromptSelector();
                }
            }
        } catch (error) {
            console.error('[LLM Prompts Panel] Error loading prompt selection:', error);
        }
    }
    
    showPromptSelector() {
        // Create dropdown selector in panel header
        const header = document.querySelector('.llm-prompts-panel .panel-header');
        if (!header) return;
        
        // Remove existing selector if present
        const existing = header.querySelector('.prompt-selector');
        if (existing) existing.remove();
        
        const selector = document.createElement('select');
        selector.className = 'prompt-selector';
        selector.style.cssText = 'margin-left: 1rem; padding: 0.25rem 0.5rem; background: #1e293b; border: 1px solid #334155; border-radius: 4px; color: #f1f5f9; font-size: 0.875rem;';
        
        this.availablePrompts.forEach(prompt => {
            const option = document.createElement('option');
            option.value = prompt.name;
            // Format display: "Default" for default, category name for category-specific
            if (prompt.is_default) {
                option.textContent = 'Default';
            } else {
                // Extract category name from prompt name
                // Handle both "Expanded Idea Generation (History)" and "Topic Brainstorming (History)" formats
                const match = prompt.name.match(/(?:Expanded Idea Generation|Topic Brainstorming|Section Structure Design|Topic Allocation|Section Titling|Section Drafting) \(([^)]+)\)/);
                if (match) {
                    option.textContent = match[1];
                } else {
                    // Fallback: use the prompt name as-is
                    option.textContent = prompt.name;
                }
            }
            if (prompt.name === this.currentPromptName) {
                option.selected = true;
            }
            selector.appendChild(option);
        });
        
        selector.addEventListener('change', async (e) => {
            await this.selectPrompt(e.target.value);
        });
        
        header.appendChild(selector);
    }
    
    async selectPrompt(promptName) {
        if (!this.promptSelectionEndpoint) return;
        
        try {
            // Save selection to database immediately via API - NO localStorage/sessionStorage/cookies
            // Selection is persisted in post.extra_settings JSONB field
            const response = await fetch(this.promptSelectionEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt_name: promptName })
            });
            
            const data = await response.json();
            if (data.success) {
                // Update local state (this is just UI state, actual persistence is in database)
                this.currentPromptName = promptName;
                this.updatePromptTitle(promptName);
                // Reload the prompt content from database
                await this.loadPromptFromAPI();
            } else {
                alert(`Error selecting prompt: ${data.error}`);
            }
        } catch (error) {
            console.error('[LLM Prompts Panel] Error selecting prompt:', error);
            alert(`Error selecting prompt: ${error.message}`);
        }
    }
    
    async loadPromptFromAPI() {
        try {
            // Load selection from database first (not from localStorage/sessionStorage)
            if (!this.currentPromptName && this.promptSelectionEndpoint) {
                await this.loadPromptSelection();
            }
            
            // Build endpoint with selected prompt name from database
            let url = this.config.promptEndpoint;
            
            // Add prompt_name parameter if we have a selection
            if (this.currentPromptName) {
                const separator = url.includes('?') ? '&' : '?';
                url = `${url}${separator}prompt_name=${encodeURIComponent(this.currentPromptName)}`;
            }
            
            // Append illustration_method to endpoint if available and endpoint is for image-concepts or image-prompts
            if ((url.includes('/image-concepts') || url.includes('/image-prompts')) && window.illustrationMethod) {
                const separator = url.includes('?') ? '&' : '?';
                url = `${url}${separator}illustration_method=${encodeURIComponent(window.illustrationMethod)}`;
                console.log('[LLM Prompts Panel] Added illustration_method to URL:', window.illustrationMethod, 'URL:', url);
            }

            console.log('[LLM Prompts Panel] Loading prompt from:', url);
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}: ${response.statusText}` }));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.prompt) {
                const prompt = data.prompt;
                let systemPrompt = prompt.system_prompt || '';
                let userPrompt = prompt.prompt_text || prompt.text || '';
                
                // If system_prompt is null/empty but prompt_text contains [system] markers, parse it
                if (!systemPrompt && userPrompt.includes('[system]')) {
                    const parts = userPrompt.split('[system]');
                    if (parts.length > 1) {
                        // Extract system prompt (everything before the last [system] marker)
                        systemPrompt = parts.slice(0, -1).join('[system]').trim();
                        // User prompt is everything after the last [system] marker
                        userPrompt = parts[parts.length - 1].trim();
                    }
                }
                
                this.currentPrompt = {
                    system_prompt: systemPrompt,
                    prompt_text: userPrompt
                };

                console.log('[LLM Prompts Panel] API Response:', {
                    endpoint: url,
                    promptName: prompt.name,
                    systemPromptPreview: this.currentPrompt.system_prompt.substring(0, 50),
                    userPromptPreview: this.currentPrompt.prompt_text.substring(0, 50)
                });

                // Display raw prompt without transformations
                this.updatePromptDisplay(this.currentPrompt.system_prompt, this.currentPrompt.prompt_text);
                this.updatePromptTitle(prompt.name || this.config.resultsTitle);
                this.callbacks.onPromptLoad(prompt);
            } else {
                const errorMsg = data.error || `Prompt not found for ${this.pageType}`;
                console.warn(`[LLM Prompts Panel] ${errorMsg}`);
                this.updatePromptDisplay('', errorMsg);
                this.updatePromptTitle(errorMsg);
            }
        } catch (error) {
            console.error(`[LLM Prompts Panel] Error loading prompt for ${this.pageType}:`, error);
            const errorMsg = `Error: ${error.message || 'Failed to load prompt'}`;
            this.updatePromptDisplay('', errorMsg);
            this.updatePromptTitle(errorMsg);
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
        
        // Load current prompt data into edit form from in-memory API data
        if (this.systemPromptEdit) this.systemPromptEdit.value = this.currentPrompt.system_prompt || '';
        if (this.userPromptEdit) this.userPromptEdit.value = this.currentPrompt.prompt_text || '';
        
        console.log('[LLM Prompts Panel] Starting edit with:', {
            pageType: this.pageType,
            systemPromptPreview: this.currentPrompt.system_prompt?.substring(0, 50),
            userPromptPreview: this.currentPrompt.prompt_text?.substring(0, 50)
        });
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
            console.log('[LLM Prompts Panel] Saving prompt to:', this.config.promptEndpoint);
            
            // Save to API (DB only)
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
            
            // Check if response is OK before trying to parse JSON
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[LLM Prompts Panel] HTTP ${response.status} error:`, errorText);
                throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 100)}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Update in-memory and display
                this.currentPrompt = { system_prompt: systemPrompt, prompt_text: userPrompt };
                this.updatePromptDisplay(systemPrompt, userPrompt);
                
                // Exit edit mode
                this.cancelEdit();
                
                // Emit callback
                this.callbacks.onPromptSave(this.currentPrompt);
                
                console.log(`[LLM Prompts Panel] Prompt saved for ${this.pageType}`);
            } else {
                console.error(`[LLM Prompts Panel] Error saving prompt:`, data);
                alert(`Error saving prompt: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error(`[LLM Prompts Panel] Error saving prompt:`, error);
            alert(`Error saving prompt: ${error.message}`);
        }
    }

    loadPromptIntoEditForm() { /* deprecated - no localStorage */ }

    updatePromptDisplay(systemPrompt, userPrompt) {
        if (this.promptDisplay) {
            // Update endpoint display
            const endpointDisplay = document.getElementById('prompt-endpoint-display');
            if (endpointDisplay) {
                endpointDisplay.textContent = this.config.promptEndpoint;
            }
            
            // Display raw prompts without any transformations
            this.promptDisplay.innerHTML = `
                <div class="prompt-section">
                    <h6>System Prompt: <span class="field-source">(llm_prompt.system_prompt)</span></h6>
                    <div class="prompt-content">${systemPrompt || 'No system prompt set'}</div>
                </div>
                <div class="prompt-section">
                    <h6>User Prompt: <span class="field-source">(llm_prompt.prompt_text)</span></h6>
                    <div class="prompt-content">${userPrompt || 'No user prompt set'}</div>
                </div>
            `;
        }
    }

    loadPromptState() { /* deprecated - no localStorage */ }

    async restoreAccordionState() {
        try {
            const key = `llm-prompts-accordion-state-${this.pageType}`;
            // Use planning API for planning pages, authoring API for authoring pages
            const apiBase = (window.currentStage === 'planning' || window.currentStage === 'concept') 
                ? '/planning/api/ui/preferences' 
                : '/authoring/api/ui/preferences';
            const resp = await fetch(`${apiBase}/${encodeURIComponent(key)}`);
            if (!resp.ok) {
                // Silently fail if API endpoint doesn't exist (404) or other errors
                return;
            }
            const data = await resp.json();
            const state = data && data.value ? (typeof data.value === 'string' ? data.value : (data.value.state||'')) : '';
            if (state === 'open') {
                const content = document.getElementById('prompts-accordion-content');
                const icon = document.getElementById('prompts-accordion-icon');
                if (content && icon) {
                    content.style.display = 'block';
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            }
        } catch(_) {}
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
    
    // Use planning API for planning pages, authoring API for authoring pages
    const apiBase = (window.currentStage === 'planning' || window.currentStage === 'concept') 
        ? '/planning/api/ui/preferences' 
        : '/authoring/api/ui/preferences';
    
    // Get pageType from existing panel instance if available, otherwise detect it
    let pageType = window.currentSubstage || 'drafting';
    if (window.llmPromptsPanel && window.llmPromptsPanel.pageType) {
        pageType = window.llmPromptsPanel.pageType;
    } else {
        // Map substage to pageType (simplified version of detectPageType)
        const mapping = {
            'drafting': 'author_draft',
            'image-concepts': 'image_concepts',
            'image-prompts': 'image_prompts',
            'image-captions': 'image_captions',
            'image-generation': 'image_generation',
            'ideas': 'ideas',
            'ideas-week': 'ideas',
            'brainstorm': 'brainstorm',
            'section-structure': 'section_structure',
            'topic-allocation': 'topic_allocation',
            'titling': 'titling',
            'topic-refinement': 'topic_refinement',
            'sections': 'sections',
            'grouping': 'grouping'
        };
        pageType = mapping[window.currentSubstage] || pageType;
    }
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        try {
            const key = `llm-prompts-accordion-state-${pageType}`;
            fetch(`${apiBase}/${encodeURIComponent(key)}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ value: 'open' })
            }).catch(() => {}); // Silently fail if API doesn't exist
        } catch(_) {}
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        try {
            const key = `llm-prompts-accordion-state-${pageType}`;
            fetch(`${apiBase}/${encodeURIComponent(key)}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ value: 'closed' })
            }).catch(() => {}); // Silently fail if API doesn't exist
        } catch(_) {}
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LLMPromptsPanel;
}
