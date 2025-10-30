// Header Image Generation Panel JavaScript

console.log('[HeaderImageGenerationPanel] Script loading...');

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
            this.updateStatus('Generating prompt with Ollama...');
            this.compileBtn.disabled = true;
            
            // Get the compiled prompt from Step 3 in the Prompt Builder Panel
            const compiledResult = document.getElementById('compiled-result');
            if (!compiledResult || !compiledResult.textContent) {
                this.updateStatus('No compiled prompt found in Step 3');
                alert('Please ensure the compiled prompt is displayed in Step 3 above.');
                return;
            }
            
            const fullPrompt = compiledResult.textContent;
            
            // Get the system prompt and task prompt
            const response = await fetch(`/header/api/posts/${this.postId}/prompt-assembly-data`);
            const data = await response.json();
            
            if (!data.success || !data.task_prompt) {
                throw new Error('Could not load task prompt');
            }
            
            // Combine system prompt and task prompt for the LLM
            const systemMessage = data.system_prompt + '\n\n' + data.task_prompt;
            
            // Send to Ollama LLM via header endpoint
            const ollamaResponse = await fetch('/header/api/execute-llm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    provider: 'ollama',
                    model: 'llama3.2:latest',
                    messages: [
                        { role: 'system', content: systemMessage },
                        { role: 'user', content: fullPrompt }
                    ],
                    post_id: this.postId  // Include post_id so we can save the prompt to database
                })
            });
            
            const ollamaData = await ollamaResponse.json();
            
            if (ollamaData.content) {
                this.compiledPrompt = ollamaData.content.trim();
                this.promptTextarea.value = this.compiledPrompt;
                this.updateGenerateButtonState();
                this.updateStatus('Prompt generated successfully');
                // Notify opener (launchpad) that header image prompt is ready
                try { if (window.opener) window.opener.postMessage('header_image_prompt_complete', '*'); } catch(_) {}
            } else {
                this.updateStatus('LLM generation failed');
                console.error('Ollama error:', ollamaData);
            }
        } catch (error) {
            this.updateStatus('Generation failed');
            console.error('Error generating prompt:', error);
            alert(`Error: ${error.message}`);
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
            
            const imagePrompt = this.promptTextarea.value.trim();
            
            if (!imagePrompt) {
                throw new Error('No prompt provided');
            }
            
            // Use gpt-image-1 by default for header images
            const modelName = 'gpt-image-1';
            const parameters = {
                size: '1536x1024',  // Landscape format supported by GPT-Image-1
                quality: 'high'
            };
            
            const response = await fetch(`/header/api/posts/${this.postId}/generate-header-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_prompt: imagePrompt,
                    model_name: modelName,
                    parameters: parameters,
                    use_renderer: false  // Use the exact prompt from the textarea, don't regenerate
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.imagePreview.src = data.optimized_path;
                this.updateStatus(`Generated (${data.dimensions.width}x${data.dimensions.height})`);
                // Notify opener (launchpad) that header image has been generated
                try { if (window.opener) window.opener.postMessage('header_image_generated', '*'); } catch(_) {}
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
    console.log('[HeaderImageGenerationPanel] Initializing panel...');
    window.headerImageGenerationPanel = new HeaderImageGenerationPanel();
    console.log('[HeaderImageGenerationPanel] Panel initialized:', window.headerImageGenerationPanel);
});