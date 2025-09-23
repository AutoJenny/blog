/**
 * AI Content Generation Core Module
 * Main class constructor and initialization
 */
class AIContentGenerationManager {
    constructor() {
        this.selectedContentType = 'feature';
        this.generatedContent = '';
        this.selectedProduct = null;
        this.currentDataPackage = null;
        this.databasePrompts = null; // Store prompts from database
        this.isPromptEditMode = false; // Track if prompt is in edit mode
        
        this.init();
        this.setupLLMControls();
    }
    
    init() {
        this.setupEventListeners();
        this.setupContentTypeButtons();
        this.setupDataListener();
        this.checkOllamaStatus();
    }
    
    // Set the selected product and update UI
    setSelectedProduct(product) {
        this.selectedProduct = product;
        this.updateGenerateButton();
        this.updateContentText();
        this.loadExistingContent(); // Load any existing generated content
        this.updateAIStatusHeader();
    }
    
    // Update the generate button state
    updateGenerateButton() {
        const generateBtn = document.getElementById('generate-content-btn');
        if (generateBtn) {
            generateBtn.disabled = !this.selectedProduct;
        }
    }
    
    // Update content text area with placeholder
    updateContentText() {
        const contentText = document.getElementById('generated-content-text');
        if (contentText) {
            if (this.selectedProduct) {
                contentText.placeholder = `Generated content for ${this.selectedProduct.name} will appear here...`;
            } else {
                contentText.placeholder = 'Please select a product first...';
            }
        }
    }
    
    // Reset form to initial state
    resetForm() {
        this.generatedContent = '';
        const contentText = document.getElementById('content-text');
        if (contentText) {
            contentText.textContent = 'Select a product and click "Generate Post" to create AI-powered content.';
        }
        
        const editBtn = document.getElementById('edit-content-btn');
        if (editBtn) {
            editBtn.style.display = 'none';
            editBtn.disabled = true;
        }
        
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        if (addToQueueBtn) {
            addToQueueBtn.style.display = 'none';
            addToQueueBtn.disabled = true;
        }
        
        this.updateAIStatusHeader();
    }
}

// Initialize AI Content Generation Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.aiContentGenerationManager = new AIContentGenerationManager();
});
