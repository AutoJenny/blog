// Prompt Preview Panel - Shows rendered prompts with character counts
class PromptPreviewPanel {
    constructor() {
        this.currentModel = 'sdxl-lora';
        this.currentSectionId = null;
        this.init();
    }

    init() {
        console.log('[Prompt Preview] Initializing prompt preview panel');
        this.setupEventListeners();
        this.createPreviewContainer();
    }

    createPreviewContainer() {
        // Find the prompt construction panel and add preview section
        const promptPanel = document.querySelector('#generated-prompts-container');
        if (!promptPanel) return;

        // Create preview container
        const previewContainer = document.createElement('div');
        previewContainer.id = 'prompt-preview-container';
        previewContainer.className = 'prompt-preview-container';
        previewContainer.innerHTML = `
            <div class="preview-header">
                <h5>Rendered Prompt Preview</h5>
                <div class="preview-controls">
                    <button id="refresh-preview-btn" class="btn btn-sm btn-outline-secondary">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
            </div>
            <div class="preview-content">
                <div class="model-info">
                    <span class="model-badge" id="preview-model-badge">No model selected</span>
                    <span class="char-count" id="preview-char-count">0/0 chars</span>
                </div>
                <div class="rendered-prompt" id="rendered-prompt-text">
                    <p class="no-preview">Select a section and model to see rendered prompt</p>
                </div>
                <div class="preview-debug" id="preview-debug-info" style="display: none;">
                    <details>
                        <summary>Debug Info</summary>
                        <pre id="debug-json"></pre>
                    </details>
                </div>
            </div>
        `;

        // Insert after the prompt construction panel
        promptPanel.parentNode.insertBefore(previewContainer, promptPanel.nextSibling);
    }

    setupEventListeners() {
        // Listen for model selection changes
        document.addEventListener('modelSelectionChanged', (event) => {
            this.currentModel = event.detail.model;
            this.updatePreview();
        });

        // Listen for section selection changes
        document.addEventListener('sectionSelected', (event) => {
            this.currentSectionId = event.detail.sectionId;
            this.updatePreview();
        });

        // Refresh button
        document.addEventListener('click', (event) => {
            if (event.target.closest('#refresh-preview-btn')) {
                this.updatePreview();
            }
        });

        // Trigger a render once both section and model are available (initial load)
        const tryInitialRender = () => {
            if (!this.currentSectionId) {
                const selected = document.querySelector('.section-item.selected[data-section-id]');
                if (selected) this.currentSectionId = selected.getAttribute('data-section-id');
            }
            if (!this.currentModel) {
                const modelSelect = document.getElementById('image-model-select');
                if (modelSelect) this.currentModel = modelSelect.value;
            }
            if (this.currentSectionId && this.currentModel) {
                this.updatePreview();
            }
        };
        setTimeout(tryInitialRender, 150);
        setTimeout(tryInitialRender, 400);
    }

    async updatePreview() {
        if (!this.currentSectionId || !this.currentModel) {
            this.showNoPreview();
            return;
        }

        try {
            // Show loading state
            this.showLoading();

            // Get rendered prompt from API
            const response = await fetch(
                `/imaging/api/render-prompt/posts/${window.postId}/sections/${this.currentSectionId}/${this.currentModel}`
            );
            
            const data = await response.json();
            
            if (data.success) {
                this.showRenderedPrompt(data.rendered_prompt, data.debug_info);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            console.error('[Prompt Preview] Error updating preview:', error);
            this.showError(error.message);
        }
    }

    showLoading() {
        const promptText = document.getElementById('rendered-prompt-text');
        const charCount = document.getElementById('preview-char-count');
        const modelBadge = document.getElementById('preview-model-badge');
        
        if (promptText) {
            promptText.innerHTML = '<p class="loading"><i class="fas fa-spinner fa-spin"></i> Rendering prompt...</p>';
        }
        
        if (charCount) {
            charCount.textContent = 'Loading...';
        }
        
        if (modelBadge) {
            modelBadge.textContent = this.currentModel;
            modelBadge.className = 'model-badge loading';
        }
    }

    showRenderedPrompt(prompt, debugInfo) {
        const promptText = document.getElementById('rendered-prompt-text');
        const charCount = document.getElementById('preview-char-count');
        const modelBadge = document.getElementById('preview-model-badge');
        const debugInfoEl = document.getElementById('preview-debug-info');
        const debugJson = document.getElementById('debug-json');
        
        if (promptText) {
            promptText.innerHTML = `<div class="prompt-content">${this.escapeHtml(prompt)}</div>`;
        }
        
        if (charCount) {
            const charCountValue = debugInfo.char_count || 0;
            const maxChars = debugInfo.max_chars || 0;
            const truncated = debugInfo.truncated ? ' (truncated)' : '';
            charCount.textContent = `${charCountValue}/${maxChars} chars${truncated}`;
            charCount.className = `char-count ${debugInfo.truncated ? 'truncated' : 'normal'}`;
        }
        
        if (modelBadge) {
            modelBadge.textContent = this.currentModel;
            modelBadge.className = `model-badge ${debugInfo.source}`;
        }
        
        if (debugInfoEl && debugJson) {
            debugJson.textContent = JSON.stringify(debugInfo, null, 2);
            debugInfoEl.style.display = 'block';
        }
    }

    showNoPreview() {
        const promptText = document.getElementById('rendered-prompt-text');
        const charCount = document.getElementById('preview-char-count');
        const modelBadge = document.getElementById('preview-model-badge');
        const debugInfoEl = document.getElementById('preview-debug-info');
        
        if (promptText) {
            promptText.innerHTML = '<p class="no-preview">Select a section and model to see rendered prompt</p>';
        }
        
        if (charCount) {
            charCount.textContent = '0/0 chars';
            charCount.className = 'char-count';
        }
        
        if (modelBadge) {
            modelBadge.textContent = 'No model selected';
            modelBadge.className = 'model-badge';
        }
        
        if (debugInfoEl) {
            debugInfoEl.style.display = 'none';
        }
    }

    showError(error) {
        const promptText = document.getElementById('rendered-prompt-text');
        const charCount = document.getElementById('preview-char-count');
        const modelBadge = document.getElementById('preview-model-badge');
        
        if (promptText) {
            promptText.innerHTML = `<p class="error"><i class="fas fa-exclamation-triangle"></i> Error: ${this.escapeHtml(error)}</p>`;
        }
        
        if (charCount) {
            charCount.textContent = 'Error';
            charCount.className = 'char-count error';
        }
        
        if (modelBadge) {
            modelBadge.textContent = this.currentModel;
            modelBadge.className = 'model-badge error';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.promptPreviewPanel = new PromptPreviewPanel();
});
