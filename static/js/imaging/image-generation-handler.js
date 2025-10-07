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
            console.log('[Image Generation Handler] Starting image generation for section:', this.currentSectionId);
            
            // Debug: Check if prompt elements exist
            const promptTextEl = document.querySelector(`[data-section-id="${this.currentSectionId}"] .prompt-text`);
            console.log('[Image Generation Handler] Prompt text element found:', promptTextEl);
            if (promptTextEl) {
                console.log('[Image Generation Handler] Prompt text content:', promptTextEl.textContent.trim());
            }
            
            // Collect all selections
            const selections = await this.collectAllSelections();
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
                
                // Don't auto-reload immediately - let user see the new image
                // setTimeout(() => {
                //     window.location.reload();
                // }, 2000); // Wait 2 seconds to show success message
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
                    const promptData = JSON.parse(section.image_prompts);
                    if (promptData.image_prompt) {
                        console.log('[Image Generation Handler] Found prompt from API:', promptData.image_prompt);
                        return promptData.image_prompt;
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
        console.log('[Image Generation Handler] Updating image display with path:', imagePath);
        
        // Update the imaging output panel (uses #image-display-area in the imaging templates)
        const displayArea = document.getElementById('image-display-area');
        console.log('[Image Generation Handler] Display area element:', displayArea);
        
        if (displayArea) {
            // Add aggressive cache-busting parameter to prevent browser caching
            const cacheBuster = `?v=${Date.now()}&r=${Math.random().toString(36).substr(2, 9)}`;
            const imageUrl = `${imagePath}${cacheBuster}`;
            
            console.log('[Image Generation Handler] Image URL with cache buster:', imageUrl);
            
            displayArea.innerHTML = `
                <div class="image-display">
                    <img src="${imageUrl}" alt="Generated image" style="max-width: 100%; height: auto;" onload="console.log('[Image Generation Handler] Image loaded successfully')" onerror="console.error('[Image Generation Handler] Image failed to load:', this.src)">
                    <p class="image-path">Image: ${imagePath}</p>
                    <p class="image-timestamp">Generated: ${new Date().toLocaleString()}</p>
                </div>
            `;
            
            console.log('[Image Generation Handler] Display area updated');
        } else {
            console.error('[Image Generation Handler] Could not find image-display-area element');
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
