/**
 * Header Prompt Builder Panel for Image Prompts
 * Adapted for header stage with model selection communication
 */

class HeaderPromptBuilderPanel {
    constructor(postId) {
        this.postId = postId;
        this.currentModel = 'sdxl-lora'; // Default
        this.modelConfig = {
            'sdxl-lora': { limit: 400, style: 'inkwash and watercolour' },
            'dall-e-3': { limit: 4000, style: 'photorealistic' },
            'dall-e-2': { limit: 1000, style: 'artistic' },
            'gpt-image': { limit: 2000, style: 'detailed descriptive' }
        };
        this.isEditMode = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAccordion();
        this.updateModelDisplay();
        console.log('[HeaderPromptBuilderPanel] Initialized for post:', this.postId);
    }

    setupEventListeners() {
        // Listen for model selection changes from Model Selection panel
        document.addEventListener('modelSelectionChanged', (event) => {
            console.log('[HeaderPromptBuilderPanel] Model selection changed:', event.detail);
            this.currentModel = event.detail.model;
            this.updateModelDisplay();
        });

        // Edit compiled prompt button
        const editBtn = document.getElementById('edit-compiled-prompt-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => this.toggleEditMode());
        }

        // Regenerate compiled prompt button
        const regenerateBtn = document.getElementById('regenerate-compiled-prompt-btn');
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => this.generatePrompt());
        }

        // Character count monitoring
        const textarea = document.getElementById('compiled-prompt-textarea');
        if (textarea) {
            textarea.addEventListener('input', () => this.updateCharacterCount());
        }
    }

    setupAccordion() {
        const header = document.querySelector('#prompt-builder-panel .panel-header');
        const content = document.getElementById('prompt-builder-accordion-content');
        const icon = document.getElementById('prompt-builder-accordion-icon');

        if (header && content && icon) {
            // Restore accordion state from DB
            this.restoreAccordionState();
            
            header.addEventListener('click', () => {
                this.toggleAccordion();
            });
        }
    }

    async restoreAccordionState() {
        try {
            const key = `prompt-builder-accordion-state-header-image-prompts`;
            const resp = await fetch(`/header/api/ui/preferences/${encodeURIComponent(key)}`);
            const data = await resp.json();
            const state = data && data.value ? (typeof data.value === 'string' ? data.value : (data.value.state||'')) : '';
            
            const content = document.getElementById('prompt-builder-accordion-content');
            const icon = document.getElementById('prompt-builder-accordion-icon');
            
            if (state === 'open') {
                if (content && icon) {
                    content.style.display = 'block';
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            } else {
                if (content && icon) {
                    content.style.display = 'none';
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                }
            }
        } catch (error) {
            console.error('[HeaderPromptBuilderPanel] Error restoring accordion state:', error);
        }
    }

    async toggleAccordion() {
        const content = document.getElementById('prompt-builder-accordion-content');
        const icon = document.getElementById('prompt-builder-accordion-icon');
        
        if (!content || !icon) return;

        const isCollapsed = content.style.display === 'none';
        
        if (isCollapsed) {
            content.style.display = 'block';
            icon.classList.remove('fa-chevron-up');
            icon.classList.add('fa-chevron-down');
            // Save open state to DB
            try {
                const key = `prompt-builder-accordion-state-header-image-prompts`;
                await fetch(`/header/api/ui/preferences/${encodeURIComponent(key)}`, {
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ value: 'open' })
                });
            } catch (error) {
                console.error('[HeaderPromptBuilderPanel] Error saving accordion state:', error);
            }
        } else {
            content.style.display = 'none';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-up');
            // Save closed state to DB
            try {
                const key = `prompt-builder-accordion-state-header-image-prompts`;
                await fetch(`/header/api/ui/preferences/${encodeURIComponent(key)}`, {
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ value: 'closed' })
                });
            } catch (error) {
                console.error('[HeaderPromptBuilderPanel] Error saving accordion state:', error);
            }
        }
    }

    updateModelDisplay() {
        const config = this.modelConfig[this.currentModel] || this.modelConfig['sdxl-lora'];
        
        // Update model selection display
        const modelDisplay = document.getElementById('current-model-display');
        if (modelDisplay) {
            modelDisplay.textContent = this.currentModel.toUpperCase();
        }
        
        // Update character limit display
        const limitDisplay = document.getElementById('character-limit-display');
        if (limitDisplay) {
            limitDisplay.textContent = `${config.limit} characters`;
        }
        
        // Update style guidelines display
        const styleDisplay = document.getElementById('style-guidelines-display');
        if (styleDisplay) {
            styleDisplay.textContent = config.style;
        }
        
        // Update character count display
        this.updateCharacterCount();
        
        console.log('[HeaderPromptBuilderPanel] Model display updated for:', this.currentModel);
    }

    updateCharacterCount() {
        const textarea = document.getElementById('compiled-prompt-textarea');
        const countElement = document.getElementById('character-count');
        const statusElement = document.getElementById('character-status');
        
        if (!textarea || !countElement || !statusElement) return;

        const currentLength = textarea.value.length;
        const config = this.modelConfig[this.currentModel] || this.modelConfig['sdxl-lora'];
        const limit = config.limit;
        
        countElement.textContent = `${currentLength} / ${limit} chars`;
        
        // Update status with color coding
        if (currentLength <= limit * 0.8) {
            statusElement.textContent = 'Ready';
            statusElement.className = 'character-status success';
        } else if (currentLength <= limit) {
            statusElement.textContent = 'Near Limit';
            statusElement.className = 'character-status warning';
        } else {
            statusElement.textContent = 'Over Limit';
            statusElement.className = 'character-status error';
        }
    }

    toggleEditMode() {
        const textarea = document.getElementById('compiled-prompt-textarea');
        const editBtn = document.getElementById('edit-compiled-prompt-btn');
        
        if (!textarea || !editBtn) return;

        this.isEditMode = !this.isEditMode;
        
        if (this.isEditMode) {
            textarea.readOnly = false;
            editBtn.textContent = 'Save';
            editBtn.classList.remove('btn-secondary');
            editBtn.classList.add('btn-success');
        } else {
            textarea.readOnly = true;
            editBtn.textContent = 'Edit';
            editBtn.classList.remove('btn-success');
            editBtn.classList.add('btn-secondary');
        }
    }

    async generatePrompt() {
        console.log('[HeaderPromptBuilderPanel] Generate prompt requested');
        // This would integrate with header-specific prompt generation
        // For now, just show that it's working
        alert('Prompt generation for header image - this will be implemented');
    }
}

// Global accordion function
function togglePromptBuilderAccordion() {
    if (window.headerPromptBuilderPanel) {
        window.headerPromptBuilderPanel.toggleAccordion();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.currentSubstage === 'header-image') {
        window.headerPromptBuilderPanel = new HeaderPromptBuilderPanel(window.postId);
    }
});
