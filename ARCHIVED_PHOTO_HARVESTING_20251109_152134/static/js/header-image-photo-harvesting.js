/**
 * Header Image Photo-harvesting Generation
 * Handles photorealistic header image generation for Photo-harvesting route
 * Uses gpt-image-1 model with photorealistic settings
 */

class HeaderImagePhotoHarvesting {
    constructor(postId) {
        this.postId = postId;
        this.illustrationMethod = window.illustrationMethod || 'Photo-harvesting';
        this.init();
    }
    
    init() {
        // Set default model to gpt-image-1 for Photo-harvesting route
        this.setDefaultModel();
        
        // Update prompt builder to use Photo-harvesting prompt
        this.configurePromptBuilder();
        
        // Override image generation panel defaults
        this.configureImageGeneration();
        
        console.log('[HeaderImagePhotoHarvesting] Initialized for Photo-harvesting route');
    }
    
    setDefaultModel() {
        // Wait for model selection panel to be available
        setTimeout(() => {
            const modelSelect = document.getElementById('image-model-select');
            if (modelSelect) {
                // Set gpt-image-1 as default (if option exists)
                // If not, we'll add it
                const gptImage1Option = Array.from(modelSelect.options).find(opt => opt.value === 'gpt-image-1');
                if (gptImage1Option) {
                    modelSelect.value = 'gpt-image-1';
                    // Trigger change event to update parameters
                    modelSelect.dispatchEvent(new Event('change'));
                } else {
                    // Add gpt-image-1 option if it doesn't exist
                    const option = document.createElement('option');
                    option.value = 'gpt-image-1';
                    option.textContent = 'GPT Image 1 (OpenAI)';
                    modelSelect.appendChild(option);
                    modelSelect.value = 'gpt-image-1';
                    modelSelect.dispatchEvent(new Event('change'));
                }
            }
        }, 500);
    }
    
    configurePromptBuilder() {
        // Update prompt builder to use Photo-harvesting prompt
        // This will be handled by the prompt-assembly-data endpoint based on illustration_method
        // But we can set the model style defaults here
        setTimeout(() => {
            const assemblyModelSelect = document.getElementById('assembly-model-select');
            if (assemblyModelSelect) {
                // Set to photorealistic model
                const gptOption = Array.from(assemblyModelSelect.options).find(opt => 
                    opt.value === 'gpt-image-1' || opt.textContent.toLowerCase().includes('photorealistic')
                );
                if (gptOption) {
                    assemblyModelSelect.value = gptOption.value;
                }
            }
            
            // Update requirements checkboxes - remove watercolor/artistic requirements
            const reqWatercolor = document.getElementById('req-watercolor');
            const reqBrushstrokes = document.getElementById('req-brushstrokes');
            
            if (reqWatercolor) {
                reqWatercolor.checked = false;
                reqWatercolor.disabled = true;
            }
            if (reqBrushstrokes) {
                reqBrushstrokes.checked = false;
                reqBrushstrokes.disabled = true;
            }
        }, 1000);
    }
    
    configureImageGeneration() {
        // Override image generation panel to use photorealistic defaults
        // This is handled in the image-generation-panel.js but we can ensure defaults
        setTimeout(() => {
            // The image generation panel will use gpt-image-1 with photorealistic settings
            // when generateHeaderImage is called
        }, 1500);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (window.postId && window.illustrationMethod === 'Photo-harvesting' && window.currentSubstage === 'header-image') {
        window.headerImagePhotoHarvesting = new HeaderImagePhotoHarvesting(window.postId);
    }
});
