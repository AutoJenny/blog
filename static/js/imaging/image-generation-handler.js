// Image Generation Handler - Clean script for collecting selections and generating images
// Collects all UI selections and orchestrates image generation

class ImageGenerationHandler {
    constructor() {
        this.currentPostId = window.postId;
        this.currentSectionId = null;
        this.init();
    }

    init() {
        console.log('[Image Generation Handler] Initializing');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for section selection changes
        const sectionHandler = (event) => {
            this.currentSectionId = event.detail.sectionId;
            window.currentSectionId = event.detail.sectionId;
            console.log('[Image Generation Handler] Section selected:', this.currentSectionId);
        };
        document.addEventListener('sectionSelected', sectionHandler);

        // Set up generate button - remove any existing listeners first
        const generateBtn = document.getElementById('generate-image-btn');
        if (generateBtn) {
            // Remove all existing listeners by cloning
            const newBtn = generateBtn.cloneNode(true);
            generateBtn.parentNode.replaceChild(newBtn, generateBtn);
            
            // Add single listener with preventDefault and stopPropagation
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                if (!this._handlingClick) {
                    this._handlingClick = true;
                    this.handleGenerateImage().finally(() => {
                        this._handlingClick = false;
                    });
                }
            }, true); // Use capture phase
        }
    }

    showTransientMessage(message, duration = 3000) {
        // Remove any existing transient message
        const existing = document.getElementById('transient-message');
        if (existing) {
            existing.remove();
        }
        
        // Create new transient message
        const msg = document.createElement('div');
        msg.id = 'transient-message';
        msg.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #1e293b;
            border: 1px solid #334155;
            color: #e2e8f0;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            font-size: 0.9rem;
            max-width: 400px;
        `;
        msg.textContent = message;
        document.body.appendChild(msg);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (msg.parentNode) {
                msg.parentNode.removeChild(msg);
            }
        }, duration);
    }

    async handleGenerateImage(sectionId = null) {
        // Get current section ID from parameter, window or event listener
        const targetSectionId = sectionId || this.currentSectionId || window.currentSectionId;
        
        if (!targetSectionId) {
            this.showTransientMessage('Please select a section first', 2000);
            return;
        }

        // Get checkbox states
        const landscapeChecked = document.getElementById('landscape-checkbox')?.checked ?? true;
        const portraitChecked = document.getElementById('portrait-checkbox')?.checked ?? true;

        if (!landscapeChecked && !portraitChecked) {
            this.showTransientMessage('Please select at least one orientation (Landscape or Portrait)', 2000);
            return;
        }

        // Get model and parameters from Model Selection Panel
        let model_name = 'gpt-image-1';
        let parameters = {};
        
        if (window.modelSelectionPanel) {
            // Ensure parameters are collected from the UI
            if (typeof window.modelSelectionPanel.collectParameters === 'function') {
                window.modelSelectionPanel.collectParameters();
            }
            
            model_name = window.modelSelectionPanel.currentModel || 'gpt-image-1';
            parameters = window.modelSelectionPanel.parameters || {};
        }

        // Show progress message
        let progressMsg = `Generating images for Section ${targetSectionId}`;
        if (landscapeChecked && portraitChecked) {
            progressMsg += ' (Landscape + Portrait)';
        } else if (landscapeChecked) {
            progressMsg += ' (Landscape)';
        } else {
            progressMsg += ' (Portrait)';
        }
        this.showTransientMessage(progressMsg, 5000);

        // Call API
        try {
            const response = await fetch(`/imaging/api/image-generation/posts/${this.currentPostId}/sections/${targetSectionId}/generate-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model_name: model_name,
                    parameters: parameters,
                    generate_landscape: landscapeChecked,
                    generate_portrait: portraitChecked
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const result = await response.json();
            
            if (result.success) {
                let successMsg = `Section ${targetSectionId}: `;
                const parts = [];
                const errors = [];
                
                if (result.landscape_generated) {
                    parts.push('Landscape');
                } else if (result.landscape_error) {
                    errors.push(`Landscape: ${result.landscape_error}`);
                }
                
                if (result.portrait_generated) {
                    parts.push('Portrait');
                } else if (result.portrait_error) {
                    errors.push(`Portrait: ${result.portrait_error}`);
                }
                
                if (parts.length > 0) {
                    successMsg += parts.join(' + ') + ' generated';
                    this.showTransientMessage(successMsg, 3000);
                }
                
                if (errors.length > 0) {
                    console.error(`[Image Generation Handler] Generation errors for section ${targetSectionId}:`, errors);
                    this.showTransientMessage(`Section ${targetSectionId}: ${errors.join('; ')}`, 8000);
                }
                
                // Notify output panel with full result data
                if (window.imagingOutputPanel && typeof window.imagingOutputPanel.onImageGenerated === 'function') {
                    window.imagingOutputPanel.onImageGenerated({
                        section_id: targetSectionId,
                        landscape_path: result.landscape_path,
                        portrait_path: result.portrait_path,
                        landscape_generated: result.landscape_generated,
                        portrait_generated: result.portrait_generated,
                        // For backward compatibility
                        image_path: result.landscape_path || result.portrait_path
                    });
                }
            } else {
                this.showTransientMessage(`Error: ${result.error || 'Generation failed'}`, 5000);
            }
        } catch (error) {
            console.error('[Image Generation Handler] Error:', error);
            this.showTransientMessage(`Error: ${error.message}`, 5000);
        }
    }

    async collectAllSelections() {
        const contentPrompt = await this.getContentPrompt();
        const stylePrompt = this.getStylePrompt();
        
        return {
            // Model Selection
            model: this.getSelectedModel(),
            parameters: this.getModelParameters(),
            
            // Prompt Construction
            contentPrompt: contentPrompt,
            stylePrompt: stylePrompt,
            
            // Context
            postId: this.currentPostId,
            sectionId: this.currentSectionId,
            
            // Final prompt (combined)
            finalPrompt: this.buildFinalPrompt(contentPrompt, stylePrompt)
        };
    }

    // If an image already exists for the current selection, display it on load/selection
    displayExistingIfAny() {
        try {
            if (!this.currentPostId || !this.currentSectionId) return;
            
            // Skip automatic image loading for now to avoid 404 errors
            // Images will be displayed when generated via the Generate button
            console.log('[Image Generation Handler] Skipping automatic image loading for section:', this.currentSectionId);
            
        } catch (e) {
            console.warn('[Image Generation Handler] displayExistingIfAny failed:', e);
        }
    }

    getSelectedModel() {
        const modelSelect = document.getElementById('image-model-select');
        return modelSelect ? modelSelect.value : 'sdxl-lora';
    }

    getModelParameters() {
        const model = this.getSelectedModel();
        
        if (model === 'sdxl-lora') {
            return {
                width: this.getParameterValue('width') || 1792,
                height: this.getParameterValue('height') || 1024,
                steps: this.getParameterValue('steps') || 30,
                cfg: this.getParameterValue('cfg') || 5.5,
                seed: this.getParameterValue('seed') || null, // Don't use default seed - let SDXL generate random
                lora_scale: this.getParameterValue('lora_scale') || 0.85
            };
        } else if (model.startsWith('dall-e')) {
            return {
                size: this.getParameterValue('size') || '1792x1024',
                quality: this.getParameterValue('quality') || 'standard',
                style: this.getParameterValue('style') || 'natural'
            };
        }
        
        return {};
    }

    getParameterValue(name) {
        const element = document.querySelector(`[name="${name}"]`);
        return element ? element.value : null;
    }

    getContentPrompt() {
        // Try to get prompt from the generated image prompts data
        if (this.currentSectionId) {
            // First try to get from the displayed prompt in the Generated Image Prompts panel
            const promptTextEl = document.querySelector(`[data-section-id="${this.currentSectionId}"] .prompt-text`);
            if (promptTextEl && promptTextEl.textContent.trim()) {
                console.log('[Image Generation Handler] Found prompt from Generated Image Prompts panel:', promptTextEl.textContent.trim());
                return promptTextEl.textContent.trim();
            }
            
            // If not found in the panel, try to get from the section data directly
            console.log('[Image Generation Handler] Prompt not found in panel, trying to fetch from API...');
            return this.fetchPromptFromAPI();
        }
        
        console.warn('[Image Generation Handler] No content prompt found');
        return '';
    }

    async fetchPromptFromAPI() {
        try {
            const response = await fetch(`/imaging/api/posts/${this.currentPostId}/sections`);
            const data = await response.json();
            
            if (data.success && data.sections) {
                const section = data.sections.find(s => s.id == this.currentSectionId);
                if (section && section.image_prompts) {
                    // image_prompts is plain text, not JSON
                    const promptText = section.image_prompts.trim();
                    if (promptText && !promptText.includes("I'm ready to assist") && !promptText.includes("Please provide")) {
                        console.log('[Image Generation Handler] Found prompt from API:', promptText);
                        return promptText;
                    }
                }
            }
        } catch (error) {
            console.error('[Image Generation Handler] Error fetching prompt from API:', error);
        }
        
        // Fallback: try to get from the old manual prompt fields (for backward compatibility)
        const contentEl = document.getElementById('content-prompt');
        if (contentEl && contentEl.value.trim()) {
            console.log('[Image Generation Handler] Found prompt from manual content-prompt field:', contentEl.value.trim());
            return contentEl.value.trim();
        }
        
        return '';
    }

    getStylePrompt() {
        // Try to get style from the generated image prompts data
        if (this.currentSectionId) {
            // First try to get from the displayed style in the Generated Image Prompts panel
            const styleEl = document.querySelector(`[data-section-id="${this.currentSectionId}"] .prompt-style`);
            if (styleEl && styleEl.textContent.trim()) {
                // Extract style text (remove "Style:" prefix)
                const styleText = styleEl.textContent.replace(/^Style:\s*/i, '').trim();
                console.log('[Image Generation Handler] Found style from Generated Image Prompts panel:', styleText);
                return styleText;
            }
            
            // Fallback: try to get from the old manual style field (for backward compatibility)
            const manualStyleEl = document.getElementById('style-prompt');
            if (manualStyleEl && manualStyleEl.value.trim()) {
                console.log('[Image Generation Handler] Found style from manual style-prompt field:', manualStyleEl.value.trim());
                return manualStyleEl.value.trim();
            }
        }
        
        console.log('[Image Generation Handler] No style prompt found');
        return '';
    }

    buildFinalPrompt(contentPrompt, stylePrompt) {
        const model = this.getSelectedModel();
        
        if (!contentPrompt) {
            throw new Error('Content prompt is required');
        }

        // Combine prompts based on model requirements
        if (model === 'sdxl-lora') {
            // SDXL can use both content and style
            return stylePrompt ? `${contentPrompt}, ${stylePrompt}` : contentPrompt;
        } else if (model.startsWith('dall-e')) {
            // DALL-E uses content only
            return contentPrompt;
        }
        
        return contentPrompt;
    }

    validateSelections(selections) {
        if (!selections.sectionId) {
            throw new Error('No section selected');
        }
        if (!selections.contentPrompt) {
            throw new Error('Content prompt is required');
        }
        if (!selections.model) {
            throw new Error('No model selected');
        }
    }

    async callImageGenerationAPI(selections) {
        // Image generation API - REMOVED
        throw new Error('Image generation endpoint has been removed');
    }

    updateImageDisplay(imagePath) {
        console.log('[Image Generation Handler] Updating image display with path:', imagePath);
        
        const displayArea = document.getElementById('image-display-area');
        if (displayArea) {
            const cacheBuster = `?v=${Date.now()}&r=${Math.random().toString(36).substr(2, 9)}`;
            const imageUrl = `${imagePath}${cacheBuster}`;
            
            displayArea.innerHTML = `
                <div class="image-display">
                    <img src="${imageUrl}" alt="Generated image" style="max-width: 100%; height: auto;" onload="console.log('[Image Generation Handler] Image loaded successfully')" onerror="console.error('[Image Generation Handler] Image failed to load:', this.src)">
                    <p class="image-path">Image: ${imagePath}</p>
                    <p class="image-timestamp">Generated: ${new Date().toLocaleString()}</p>
                </div>
            `;
        }
    }


    setLoadingState(loading) {
        const generateBtn = document.getElementById('generate-image-btn');
        if (generateBtn) {
            if (loading) {
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            } else {
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Image';
            }
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            font-size: 0.9rem;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.imageGenerationHandler = new ImageGenerationHandler();
    console.log('[Image Generation Handler] Initialized');
    // Try to display any existing image for a restored selection
    window.imageGenerationHandler.displayExistingIfAny();
});
