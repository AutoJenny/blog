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
        this.storageKey = `${this.pageType}-llm-prompts`; // legacy key (will not be used)
        this.currentPrompt = { system_prompt: '', prompt_text: '' }; // in-memory source of truth
        this.currentModelKey = '';
        this.currentMaxChars = null;
        
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
        // Do not use localStorage; rely on DB-backed API
        this.loadPromptFromAPI();
        this.restoreAccordionState();
        // Reflect current model constraints if available
        this.setupModelInfoListener();
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
                // On Imaging page, show the Image Prompts template and allow editing
                promptEndpoint: '/authoring/api/llm/prompts/image-prompts',
                resultsTitle: 'Generated Image Prompts',
                allowEdit: true
            }
        };
        
        return fallbackConfigs[this.pageType] || fallbackConfigs['author_draft'];
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

    setupModelInfoListener() {
        // Listen for imaging model selection changes to render model-aware info
        document.addEventListener('modelSelectionChanged', async (event) => {
            try {
                const detail = event?.detail || {};
                let modelKey = detail.model || '';
                let spec = detail.modelSpec || null;

                // If spec missing, fetch model specs and derive
                if (!spec && modelKey) {
                    try {
                        const r = await fetch('/imaging/api/model-specs');
                        const d = await r.json();
                        if (d && d.success && Array.isArray(d.models)) {
                            spec = d.models.find(m => m.model_key === modelKey) || null;
                        }
                    } catch (_) { /* ignore */ }
                }

                const maxChars = spec?.constraints?.max_prompt_chars || '';

                // Cache current model info for substitutions
                this.currentModelKey = modelKey;
                this.currentMaxChars = typeof maxChars === 'number' ? maxChars : (parseInt(maxChars, 10) || null);

                // Create or update an info banner under the display
                const container = document.getElementById('llm-prompt-display');
                if (container) {
                    let info = document.getElementById('llm-model-info');
                    if (!info) {
                        info = document.createElement('div');
                        info.id = 'llm-model-info';
                        info.style.marginTop = '0.5rem';
                        info.style.fontSize = '0.85rem';
                        info.style.color = '#94a3b8';
                        container.parentNode && container.parentNode.insertBefore(info, container);
                    }
                    info.innerHTML = `
                        <div class="llm-model-info-row">
                            <span style="background:#334155;color:#e2e8f0;border-radius:4px;padding:2px 6px;margin-right:6px;">Model: ${this.escapeHtml(modelKey)}</span>
                            ${maxChars ? `<span style="background:#334155;color:#e2e8f0;border-radius:4px;padding:2px 6px;">Max prompt: ${maxChars} chars</span>` : ''}
                        </div>
                    `;
                }

                // Re-render the prompt display with model-aware substitutions (without refetching)
                if (this.currentPrompt) {
                    const sys = this.applyModelAwareSubstitutions(this.currentPrompt.system_prompt || '');
                    const usr = this.applyModelAwareSubstitutions(this.currentPrompt.prompt_text || '');
                    this.updatePromptDisplay(sys, usr);
                }
            } catch (_) { /* ignore */ }
        });
    }

    async loadPromptFromAPI() {
        try {
            const response = await fetch(this.config.promptEndpoint);
            const data = await response.json();
            
            if (data.success && data.prompt) {
                const prompt = data.prompt;
                this.currentPrompt = {
                    system_prompt: prompt.system_prompt || '',
                    prompt_text: (prompt.prompt_text || prompt.text || '')
                };

                // Attempt model-aware substitutions on initial load
                try {
                    if (!this.currentMaxChars) {
                        const select = document.getElementById('image-model-select');
                        const modelKey = select ? select.value : '';
                        if (modelKey) {
                            const r = await fetch('/imaging/api/model-specs');
                            const d = await r.json();
                            if (d && d.success && Array.isArray(d.models)) {
                                const spec = d.models.find(m => m.model_key === modelKey);
                                const maxChars = spec?.constraints?.max_prompt_chars || '';
                                this.currentModelKey = modelKey;
                                this.currentMaxChars = typeof maxChars === 'number' ? maxChars : (parseInt(maxChars, 10) || null);
                            }
                        }
                    }
                } catch (_) { /* ignore */ }

                const sys = this.applyModelAwareSubstitutions(this.currentPrompt.system_prompt);
                const usr = this.applyModelAwareSubstitutions(this.currentPrompt.prompt_text);
                this.updatePromptDisplay(sys, usr);
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

    // Utility: escape HTML to prevent injection in info banner
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = String(text ?? '');
        return div.innerHTML;
    }

    // Apply simple model-aware substitutions to displayed prompts (non-destructive)
    applyModelAwareSubstitutions(text) {
        if (!text || !this.currentMaxChars) return text;
        let t = String(text);
        const max = this.currentMaxChars;
        // Replace common range caps like "380–400 characters" or "380-400 characters"
        t = t.replace(/\b\d{2,4}\s*[–-]\s*\d{2,4}\s*characters?/gi, `up to ${max} characters`);
        // Replace phrases like "exceeds 400 characters"
        t = t.replace(/exceeds\s+\d{2,4}\s*characters?/gi, `exceeds ${max} characters`);
        // Replace "≤ 400" or "<= 400"
        t = t.replace(/(?:≤|<=)\s*\d{2,4}\b/gi, `≤ ${max}`);
        // Replace solitary "400 characters" with "{max} characters" for typical caps (<= 1000)
        t = t.replace(/\b(\d{2,4})\s*characters\b/gi, (m, p1) => {
            const n = parseInt(p1, 10);
            return n <= 1000 ? `${max} characters` : m;
        });
        return t;
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
            }
        } catch (error) {
            console.error(`[LLM Prompts Panel] Error saving prompt:`, error);
        }
    }

    loadPromptIntoEditForm() { /* deprecated - no localStorage */ }

    updatePromptDisplay(systemPrompt, userPrompt) {
        if (this.promptDisplay) {
            // Apply model-aware substitutions at display-time
            const sys = this.applyModelAwareSubstitutions(systemPrompt);
            const usr = this.applyModelAwareSubstitutions(userPrompt);
            this.promptDisplay.innerHTML = `
                <div class="prompt-section">
                    <h6>System Prompt:</h6>
                    <div class="prompt-content">${sys || 'No system prompt set'}</div>
                </div>
                <div class="prompt-section">
                    <h6>User Prompt:</h6>
                    <div class="prompt-content">${usr || 'No user prompt set'}</div>
                </div>
            `;
        }
    }

    loadPromptState() { /* deprecated - no localStorage */ }

    async restoreAccordionState() {
        try {
            const key = `llm-prompts-accordion-state-${this.pageType}`;
            const resp = await fetch(`/authoring/api/ui/preferences/${encodeURIComponent(key)}`);
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
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
        try {
            const substage = window.currentSubstage || 'drafting';
            const key = `llm-prompts-accordion-state-${substage}`;
            fetch(`/authoring/api/ui/preferences/${encodeURIComponent(key)}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ value: 'open' })
            });
        } catch(_) {}
    } else {
        content.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
        try {
            const substage = window.currentSubstage || 'drafting';
            const key = `llm-prompts-accordion-state-${substage}`;
            fetch(`/authoring/api/ui/preferences/${encodeURIComponent(key)}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ value: 'closed' })
            });
        } catch(_) {}
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LLMPromptsPanel;
}
