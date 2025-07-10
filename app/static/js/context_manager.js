/**
 * Context Management System
 * Handles parsing and managing LLM prompt context sections
 */

class ContextManager {
    constructor() {
        this.modal = null;
        this.contextSections = [];
        this.currentPrompt = '';
        this.init();
    }

    init() {
        this.modal = document.getElementById('context-management-modal');
        this.bindEvents();
    }

    bindEvents() {
        // Modal controls
        document.getElementById('close-context-modal')?.addEventListener('click', () => this.hide());
        document.getElementById('refresh-context')?.addEventListener('click', () => this.refreshContext());
        document.getElementById('save-context-config')?.addEventListener('click', () => this.saveConfiguration());
        document.getElementById('run-with-context')?.addEventListener('click', () => this.runWithContext());

        // Close modal on outside click
        this.modal?.addEventListener('click', (e) => {
            if (e.target === this.modal) this.hide();
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal && !this.modal.classList.contains('hidden')) {
                this.hide();
            }
        });
    }

    show() {
        if (this.modal) {
            this.modal.classList.remove('hidden');
            this.loadContext();
        }
    }

    hide() {
        if (this.modal) {
            this.modal.classList.add('hidden');
        }
    }

    async loadContext() {
        try {
            // Get current workflow context from URL
            const pathParts = window.location.pathname.split('/');
            const postId = pathParts[3];
            const stage = pathParts[4];
            const substage = pathParts[5];
            
            // Get step from panel data attributes
            const panel = document.querySelector('[data-current-stage]');
            let step = null;
            if (panel && panel.dataset.currentStep) {
                step = panel.dataset.currentStep;
            } else {
                const urlParams = new URLSearchParams(window.location.search);
                const urlStep = urlParams.get('step');
                if (urlStep) {
                    step = urlStep.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                }
            }

            console.log('[CONTEXT_MANAGER] Loading context for:', { postId, stage, substage, step });

            // Fetch the current diagnostic log
            const response = await fetch(`/api/workflow/debug/context/${postId}/${stage}/${substage}/${encodeURIComponent(step)}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch context: ${response.status}`);
            }

            const contextData = await response.json();
            console.log('[CONTEXT_MANAGER] Raw diagnostic_log:', contextData.diagnostic_log);
            this.parseContext(contextData);
            this.renderContext();
            this.updatePreview();

        } catch (error) {
            console.error('[CONTEXT_MANAGER] Error loading context:', error);
            // Fallback: try to parse from existing diagnostic logs
            this.parseFromDiagnosticLogs();
        }
    }

    parseContext(contextData) {
        this.contextSections = [];
        
        // Don't parse diagnostic log for context sections as it contains specimen prompt
        // Only use the prompt from the Prompt panel
        console.log('[CONTEXT_MANAGER] Skipping diagnostic log parsing to avoid specimen prompt');
    }

    parseDiagnosticLog(logContent) {
        // This method is no longer used since diagnostic log contains specimen prompt
        return [];
    }

    parseFromDiagnosticLogs() {
        // Fallback: try to parse from the most recent diagnostic log
        console.log('[CONTEXT_MANAGER] Using fallback parsing from diagnostic logs');
        
        // No hardcoded sections - let the prompt panel handle the content
        this.contextSections = [];
    }

    renderContext() {
        const container = document.getElementById('context-sections');
        if (!container) return;

        container.innerHTML = '';

        this.contextSections.forEach((section, index) => {
            const sectionElement = this.createSectionElement(section, index);
            container.appendChild(sectionElement);
        });

        this.updateSummary();
    }

    createSectionElement(section, index) {
        const template = document.getElementById('context-section-template');
        const clone = template.content.cloneNode(true);
        
        const sectionDiv = clone.querySelector('.context-section');
        sectionDiv.dataset.sectionId = section.id;
        
        const toggle = clone.querySelector('.section-toggle');
        toggle.checked = section.enabled;
        toggle.addEventListener('change', (e) => {
            section.enabled = e.target.checked;
            this.updatePreview();
            this.updateSummary();
        });

        const title = clone.querySelector('.section-title');
        title.textContent = section.title;

        const content = clone.querySelector('.section-content');
        content.innerHTML = `<div class="text-sm text-gray-300 whitespace-pre-wrap">${section.content}</div>`;

        // Add move buttons functionality
        const moveUp = clone.querySelector('.move-up-btn');
        const moveDown = clone.querySelector('.move-down-btn');
        
        moveUp.addEventListener('click', () => this.moveSection(index, -1));
        moveDown.addEventListener('click', () => this.moveSection(index, 1));

        return clone;
    }

    moveSection(index, direction) {
        const newIndex = index + direction;
        if (newIndex >= 0 && newIndex < this.contextSections.length) {
            const section = this.contextSections.splice(index, 1)[0];
            this.contextSections.splice(newIndex, 0, section);
            this.renderContext();
            this.updatePreview();
        }
    }

    updatePreview() {
        const preview = document.getElementById('prompt-preview');
        const charCount = document.getElementById('preview-char-count');
        if (!preview) return;

        // Get current prompt from the Prompt panel dropdowns
        const systemPrompt = document.getElementById('system_prompt')?.value || '';
        const taskPrompt = document.getElementById('task_prompt')?.value || '';
        
        // Show ONLY the prompt from the Prompt panel (no context sections)
        let previewText = '';
        if (systemPrompt.trim()) {
            previewText += systemPrompt + '\n\n';
        }
        if (taskPrompt.trim()) {
            previewText += taskPrompt;
        }
        
        preview.textContent = previewText;
        charCount.textContent = previewText.length;
        this.currentPrompt = previewText;
    }

    updateSummary() {
        const summary = document.getElementById('context-summary');
        if (!summary) return;

        const enabledCount = this.contextSections.filter(s => s.enabled).length;
        const totalCount = this.contextSections.length;
        summary.textContent = `${enabledCount}/${totalCount} sections enabled`;
    }

    async saveConfiguration() {
        try {
            // Get current workflow context
            const pathParts = window.location.pathname.split('/');
            const postId = pathParts[3];
            const stage = pathParts[4];
            const substage = pathParts[5];
            
            const panel = document.querySelector('[data-current-stage]');
            let step = null;
            if (panel && panel.dataset.currentStep) {
                step = panel.dataset.currentStep;
            } else {
                const urlParams = new URLSearchParams(window.location.search);
                const urlStep = urlParams.get('step');
                if (urlStep) {
                    step = urlStep.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                }
            }

            const config = {
                step_id: panel?.dataset.stepId,
                context_sections: this.contextSections,
                created_at: new Date().toISOString()
            };

            const response = await fetch(`/api/workflow/steps/${config.step_id}/context-config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                console.log('[CONTEXT_MANAGER] Configuration saved successfully');
                alert('Context configuration saved successfully!');
            } else {
                throw new Error(`Failed to save configuration: ${response.status}`);
            }

        } catch (error) {
            console.error('[CONTEXT_MANAGER] Error saving configuration:', error);
            alert('Failed to save configuration: ' + error.message);
        }
    }

    async runWithContext() {
        try {
            // Get current workflow context
            const pathParts = window.location.pathname.split('/');
            const postId = pathParts[3];
            const stage = pathParts[4];
            const substage = pathParts[5];
            
            const panel = document.querySelector('[data-current-stage]');
            let step = null;
            if (panel && panel.dataset.currentStep) {
                step = panel.dataset.currentStep;
            } else {
                const urlParams = new URLSearchParams(window.location.search);
                const urlStep = urlParams.get('step');
                if (urlStep) {
                    step = urlStep.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                }
            }

            // Get all input values from MultiInputManager
            const allInputs = window.multiInputManager?.getAllInputs() || {};

            // Use the regular LLM endpoint with the prompt from the Prompt panel
            // The context management is for organization/preview only
            const requestBody = {
                step: step,
                inputs: allInputs
            };

            console.log('[CONTEXT_MANAGER] Running LLM with regular endpoint (prompt from panel):', requestBody);

            // Use the existing LLM endpoint (which uses the prompt from the Prompt panel)
            const url = stage === 'writing' 
                ? `/api/workflow/posts/${postId}/${stage}/${substage}/writing_llm`
                : `/api/workflow/posts/${postId}/${stage}/${substage}/llm`;

            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            const result = await response.json();
            
            if (result.success) {
                console.log('[CONTEXT_MANAGER] LLM run successful:', result);
                this.hide();
                // The existing LLM result handling will take care of updating the UI
            } else {
                throw new Error(result.error || 'Unknown error occurred');
            }

        } catch (error) {
            console.error('[CONTEXT_MANAGER] Error running LLM with context:', error);
            alert('Error running LLM: ' + error.message);
        }
    }

    refreshContext() {
        this.loadContext();
    }
}

// Export for use in other modules
export default ContextManager; 