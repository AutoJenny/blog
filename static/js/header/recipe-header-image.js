// Recipe Header Image Generation - Simplified workflow matching section image generation
class RecipeHeaderImage {
    constructor(postId) {
        this.postId = postId;
        this.heroPrompt = '';
        this.modelName = 'gpt-image-1';
        this.parameters = { size: '1536x1024' }; // Landscape for recipes
        
        this.initializeElements();
        this.loadHeroPrompt();
        this.bindEvents();
    }
    
    initializeElements() {
        this.heroPromptTextarea = document.getElementById('recipe-hero-prompt-textarea');
        this.modelSelect = document.getElementById('image-model-select');
        this.landscapeSizeSelect = document.getElementById('landscape-size');
        this.qualitySelect = document.getElementById('image-quality');
        this.generateBtn = document.getElementById('generate-images-btn');
        
        // Hide portrait size for recipes (only landscape needed)
        const portraitSizeItem = document.querySelector('label[for="portrait-size"]')?.parentElement;
        if (portraitSizeItem) {
            portraitSizeItem.style.display = 'none';
        }
        
        // Set default model to gpt-image-1
        if (this.modelSelect) {
            this.modelSelect.value = 'gpt-image-1';
            this.modelName = 'gpt-image-1';
        }
        
        // Update button text
        const generateBtnText = document.getElementById('generate-btn-text');
        if (generateBtnText) {
            generateBtnText.textContent = 'Generate Hero Image';
        }
    }
    
    async loadHeroPrompt() {
        try {
            console.log('[RecipeHeaderImage] Loading hero prompt for post', this.postId);
            // Fetch hero image prompt from recipe_image_style section
            const response = await fetch(`/authoring/api/posts/${this.postId}/sections?image_context=true`);
            const data = await response.json();
            
            console.log('[RecipeHeaderImage] Sections response:', data);
            
            if (data.success && data.sections) {
                const styleSection = data.sections.find(s => s.section_type === 'recipe_image_style');
                console.log('[RecipeHeaderImage] Style section found:', styleSection);
                
                if (styleSection && styleSection.post_section_elements) {
                    let elements = styleSection.post_section_elements;
                    if (typeof elements === 'string') {
                        elements = JSON.parse(elements);
                    }
                    
                    if (elements && elements.hero_image_prompt) {
                        const heroPrompt = elements.hero_image_prompt;
                        // Extract description if it's an object
                        if (typeof heroPrompt === 'object') {
                            this.heroPrompt = heroPrompt.description || heroPrompt.image_prompt || heroPrompt.prompt || JSON.stringify(heroPrompt);
                        } else {
                            this.heroPrompt = heroPrompt;
                        }
                        
                        console.log('[RecipeHeaderImage] Hero prompt loaded:', this.heroPrompt.substring(0, 100) + '...');
                        
                        if (this.heroPromptTextarea) {
                            this.heroPromptTextarea.value = this.heroPrompt;
                        }
                        
                        // Update button state after prompt is loaded
                        this.updateGenerateButtonState();
                    } else {
                        console.warn('[RecipeHeaderImage] No hero_image_prompt in elements');
                    }
                } else {
                    console.warn('[RecipeHeaderImage] No post_section_elements in style section');
                }
            } else {
                console.warn('[RecipeHeaderImage] No sections found or request failed');
            }
        } catch (error) {
            console.error('[RecipeHeaderImage] Error loading hero prompt:', error);
            if (this.heroPromptTextarea) {
                this.heroPromptTextarea.value = 'Error loading prompt. Please check the Image Style & Prompts stage.';
            }
        }
    }
    
    bindEvents() {
        if (this.modelSelect) {
            this.modelSelect.addEventListener('change', () => {
                this.modelName = this.modelSelect.value;
                this.updateParameters();
            });
        }
        
        if (this.landscapeSizeSelect) {
            this.landscapeSizeSelect.addEventListener('change', () => {
                this.updateParameters();
            });
        }
        
        if (this.qualitySelect) {
            this.qualitySelect.addEventListener('change', () => {
                this.updateParameters();
            });
        }
        
        if (this.generateBtn) {
            this.generateBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent panel header toggle
                e.preventDefault();
                this.generateImage();
            });
            console.log('[RecipeHeaderImage] Generate button event listener attached');
        } else {
            console.error('[RecipeHeaderImage] Generate button not found during bindEvents!');
        }
        
        // Update button state when prompt is loaded
        if (this.heroPromptTextarea) {
            this.heroPromptTextarea.addEventListener('input', () => {
                this.heroPrompt = this.heroPromptTextarea.value;
                this.updateGenerateButtonState();
            });
        }
    }
    
    updateParameters() {
        this.parameters = {};
        
        // Set size based on model
        if (this.modelName === 'gpt-image-1') {
            this.parameters.size = this.landscapeSizeSelect ? this.landscapeSizeSelect.value : '1536x1024';
        } else if (this.modelName.startsWith('dall-e')) {
            this.parameters.size = this.landscapeSizeSelect ? this.landscapeSizeSelect.value : '1792x1024';
        } else if (this.modelName.startsWith('sdxl')) {
            const size = this.landscapeSizeSelect ? this.landscapeSizeSelect.value : '1792x1024';
            const [width, height] = size.split('x').map(Number);
            this.parameters.width = width;
            this.parameters.height = height;
        }
        
        // Set quality
        if (this.qualitySelect) {
            this.parameters.quality = this.qualitySelect.value;
        }
    }
    
    updateGenerateButtonState() {
        if (this.generateBtn) {
            this.generateBtn.disabled = !this.heroPrompt || !this.heroPrompt.trim();
        }
    }
    
    async generateImage() {
        console.log('[RecipeHeaderImage] Generate button clicked');
        console.log('[RecipeHeaderImage] Hero prompt:', this.heroPrompt ? this.heroPrompt.substring(0, 100) + '...' : 'EMPTY');
        console.log('[RecipeHeaderImage] Model:', this.modelName);
        console.log('[RecipeHeaderImage] Parameters:', this.parameters);
        
        if (!this.heroPrompt || !this.heroPrompt.trim()) {
            alert('No hero image prompt available. Please generate prompts at the Image Style & Prompts stage first.');
            return;
        }
        
        if (!this.generateBtn) {
            console.error('[RecipeHeaderImage] Generate button not found!');
            return;
        }
        
        this.generateBtn.disabled = true;
        const originalHTML = this.generateBtn.innerHTML;
        this.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        
        try {
            this.updateParameters();
            
            const payload = {
                model_name: this.modelName,
                parameters: this.parameters,
                image_prompt: this.heroPrompt,
                use_renderer: false  // Use prompt directly, no collage compilation
            };
            
            console.log('[RecipeHeaderImage] Sending request to API:', payload);
            
            const response = await fetch(`/header/api/posts/${this.postId}/generate-header-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            console.log('[RecipeHeaderImage] Response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('[RecipeHeaderImage] API error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('[RecipeHeaderImage] API response:', data);
            
            if (data.success) {
                console.log('[RecipeHeaderImage] Image generated successfully, reloading page...');
                // Reload page to show generated image
                window.location.reload();
            } else {
                throw new Error(data.error || 'Image generation failed');
            }
        } catch (error) {
            console.error('[RecipeHeaderImage] Error generating image:', error);
            alert(`Error generating image: ${error.message}`);
            this.generateBtn.innerHTML = originalHTML;
        } finally {
            this.generateBtn.disabled = false;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[RecipeHeaderImage] DOM ready, postId:', window.postId, 'postType:', window.postType);
    if (window.postId && window.postType === 'recipe') {
        console.log('[RecipeHeaderImage] Initializing RecipeHeaderImage...');
        window.recipeHeaderImage = new RecipeHeaderImage(window.postId);
    } else {
        console.log('[RecipeHeaderImage] Not initializing - postId:', window.postId, 'postType:', window.postType);
    }
});

