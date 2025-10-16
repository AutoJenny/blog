// Header Image Generation Panel JavaScript

class HeaderImageGenerationPanel {
    constructor() {
        this.postId = window.postId;
        this.compiledPrompt = '';
        this.sourcePrompts = [];
        this.isGenerating = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadExistingHeaderImage();
    }
    
    initializeElements() {
        this.compileBtn = document.getElementById('compile-prompt-btn');
        this.generateBtn = document.getElementById('generate-header-btn');
        this.modelSelect = document.getElementById('model-select');
        this.promptTextarea = document.getElementById('compiled-prompt-textarea');
        this.statusSpan = document.getElementById('image-generation-status');
        this.progressDiv = document.getElementById('generation-progress');
        this.imagePreview = document.getElementById('generated-image');
        this.sourcePromptsList = document.getElementById('source-prompts-list');
    }
    
    bindEvents() {
        if (this.compileBtn) {
            this.compileBtn.addEventListener('click', () => this.compileHeaderPrompt());
        }
        
        if (this.generateBtn) {
            this.generateBtn.addEventListener('click', () => this.generateHeaderImage());
        }
        
        if (this.promptTextarea) {
            this.promptTextarea.addEventListener('input', () => this.updateGenerateButtonState());
        }
    }
    
    async compileHeaderPrompt() {
        try {
            this.updateStatus('Compiling prompts...');
            this.compileBtn.disabled = true;
            
            // Get selected model
            const selectedModel = this.modelSelect ? this.modelSelect.value : 'dall-e-3';
            
            const response = await fetch(`/header/api/posts/${this.postId}/compile-header-prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: selectedModel
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.compiledPrompt = data.compiled_prompt;
                this.promptTextarea.value = this.compiledPrompt;
                this.updateGenerateButtonState();
                this.updateStatus(`Compiled from ${data.source_sections} sections`);
                
                // Load source prompts for display
                await this.loadSourcePrompts();
            } else {
                this.updateStatus('Compilation failed');
                console.error('Compilation error:', data.error);
            }
        } catch (error) {
            this.updateStatus('Compilation failed');
            console.error('Error compiling header prompt:', error);
        } finally {
            this.compileBtn.disabled = false;
        }
    }
    
    async loadSourcePrompts() {
        try {
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections`);
            const sections = await response.json();
            
            this.sourcePromptsList.innerHTML = '';
            
            sections.forEach(section => {
                if (section.image_prompts) {
                    const promptItem = document.createElement('div');
                    promptItem.className = 'source-prompt-item';
                    promptItem.innerHTML = `
                        <strong>Section ${section.section_order}:</strong><br>
                        ${section.image_prompts}
                    `;
                    this.sourcePromptsList.appendChild(promptItem);
                }
            });
        } catch (error) {
            console.error('Error loading source prompts:', error);
        }
    }
    
    async generateHeaderImage() {
        if (this.isGenerating) return;
        
        try {
            this.isGenerating = true;
            this.generateBtn.disabled = true;
            this.progressDiv.style.display = 'block';
            this.updateStatus('Generating image...');
            
            const modelName = this.modelSelect.value;
            const imagePrompt = this.promptTextarea.value.trim();
            
            if (!imagePrompt) {
                throw new Error('No prompt provided');
            }
            
            const parameters = {
                quality: 50,
                watermark: true,
                text_overlay: true,
                overlay_text: 'AI-generated header image'
            };
            
            const response = await fetch(`/header/api/posts/${this.postId}/generate-header-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_prompt: imagePrompt,
                    model_name: modelName,
                    parameters: parameters
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.imagePreview.src = data.optimized_path;
                this.updateStatus(`Generated (${data.dimensions.width}x${data.dimensions.height})`);
            } else {
                this.updateStatus('Generation failed');
                console.error('Generation error:', data.error);
            }
        } catch (error) {
            this.updateStatus('Generation failed');
            console.error('Error generating header image:', error);
        } finally {
            this.isGenerating = false;
            this.generateBtn.disabled = false;
            this.progressDiv.style.display = 'none';
        }
    }
    
    async loadExistingHeaderImage() {
        try {
            const response = await fetch(`/header/api/posts/${this.postId}/get-header-image`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    this.imagePreview.src = data.file_path;
                    this.promptTextarea.value = data.image_prompt || '';
                    this.compiledPrompt = data.image_prompt || '';
                    this.updateGenerateButtonState();
                    this.updateStatus(`Existing image (${data.width}x${data.height})`);
                }
            }
        } catch (error) {
            console.error('Error loading existing header image:', error);
        }
    }
    
    updateGenerateButtonState() {
        const hasPrompt = this.promptTextarea.value.trim().length > 0;
        this.generateBtn.disabled = !hasPrompt || this.isGenerating;
    }
    
    updateStatus(message) {
        if (this.statusSpan) {
            this.statusSpan.textContent = message;
        }
    }
}

// Global functions for accordion and source prompts
function toggleImageGenerationAccordion() {
    const content = document.getElementById('image-generation-content');
    const icon = document.getElementById('image-generation-accordion-icon');
    
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
        
        // Save accordion state
        if (window.headerAccordionManager) {
            const isOpen = !content.classList.contains('collapsed');
            window.headerAccordionManager.saveAccordionState('image-generation', isOpen);
        }
    }
}

function toggleSourcePrompts() {
    const content = document.getElementById('source-prompts-content');
    const icon = document.getElementById('source-prompts-icon');
    
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
    }
}

// Initialize panel when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize accordion with database-backed state persistence
    if (window.headerAccordionManager) {
        window.headerAccordionManager.initializeAccordion(
            'image-generation',
            'image-generation-content',
            'image-generation-accordion-icon'
        );
    } else {
        // Fallback: Initialize accordion as open by default
        const content = document.getElementById('image-generation-content');
        const icon = document.getElementById('image-generation-accordion-icon');
        if (content && icon) {
            content.classList.remove('collapsed');
            icon.classList.add('open');
        }
    }
    
    // Initialize the panel
    window.headerImageGenerationPanel = new HeaderImageGenerationPanel();
});
