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
        document.addEventListener('sectionSelected', (event) => {
            this.currentSectionId = event.detail.sectionId;
            console.log('[Image Generation Handler] Section selected:', this.currentSectionId);
        });

        // Set up generate button
        const generateBtn = document.getElementById('generate-image-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.handleGenerateImage());
        }
    }

    async handleGenerateImage() {
        if (!this.currentSectionId) {
            this.showError('Please select a section first');
            return;
        }

        try {
            console.log('[Image Generation Handler] Starting image generation');
            
            // Collect all selections
            const selections = this.collectAllSelections();
            console.log('[Image Generation Handler] Collected selections:', selections);

            // Validate selections
            this.validateSelections(selections);

            // Show loading state
            this.setLoadingState(true);

            // Generate image
            const result = await this.callImageGenerationAPI(selections);

            if (result.success) {
                this.showSuccess('Image generated successfully!');
                this.updateImageDisplay(result.image_path);
                
                // Auto-reload page to show the new image
                setTimeout(() => {
                    window.location.reload();
                }, 2000); // Wait 2 seconds to show success message
            } else {
                this.showError(result.error || 'Image generation failed');
            }

        } catch (error) {
            console.error('[Image Generation Handler] Error:', error);
            this.showError(error.message || 'Image generation failed');
        } finally {
            this.setLoadingState(false);
        }
    }

    collectAllSelections() {
        return {
            // Model Selection
            model: this.getSelectedModel(),
            parameters: this.getModelParameters(),
            
            // Prompt Construction
            contentPrompt: this.getContentPrompt(),
            stylePrompt: this.getStylePrompt(),
            
            // Context
            postId: this.currentPostId,
            sectionId: this.currentSectionId,
            
            // Final prompt (combined)
            finalPrompt: this.buildFinalPrompt()
        };
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
                seed: this.getParameterValue('seed') || 42,
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
        const contentEl = document.getElementById('content-prompt');
        return contentEl ? contentEl.value.trim() : '';
    }

    getStylePrompt() {
        const styleEl = document.getElementById('style-prompt');
        return styleEl ? styleEl.value.trim() : '';
    }

    buildFinalPrompt() {
        const content = this.getContentPrompt();
        const style = this.getStylePrompt();
        const model = this.getSelectedModel();
        
        if (!content) {
            throw new Error('Content prompt is required');
        }

        // Combine prompts based on model requirements
        if (model === 'sdxl-lora') {
            // SDXL can use both content and style
            return style ? `${content}, ${style}` : content;
        } else if (model.startsWith('dall-e')) {
            // DALL-E uses content only
            return content;
        }
        
        return content;
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
        const response = await fetch(`/imaging/api/image-generation/posts/${selections.postId}/sections/${selections.sectionId}/generate-image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_name: selections.model,
                parameters: selections.parameters,
                image_prompt: selections.finalPrompt
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    updateImageDisplay(imagePath) {
        const outputPanel = document.getElementById('image-output-panel');
        if (outputPanel) {
            outputPanel.innerHTML = `
                <div class="image-display">
                    <img src="${imagePath}" alt="Generated image" style="max-width: 100%; height: auto;">
                    <p class="image-path">Image: ${imagePath}</p>
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
});
