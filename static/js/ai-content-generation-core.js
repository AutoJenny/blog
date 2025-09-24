/**
 * AI Content Generation Core Module
 * Main class constructor and initialization
 */
class AIContentGenerationManager {
    constructor() {
        console.log('AIContentGenerationManager constructor called');
        this.selectedContentType = 'feature';
        this.generatedContent = '';
        this.selectedData = null; // Can be product or blog section data
        this.currentDataPackage = null;
        this.databasePrompts = null; // Store prompts from database
        this.isPromptEditMode = false; // Track if prompt is in edit mode
        this.processId = null; // Will be set based on page type
        
        this.init();
        this.setupLLMControls();
    }
    
    init() {
        this.detectPageType(); // Determine if this is product or blog page
        this.setupEventListeners();
        this.setupContentTypeButtons();
        this.setupDataListener();
        this.checkOllamaStatus();
        this.loadDatabasePrompts(); // Load prompts from database
    }
    
    // Detect page type and set appropriate process ID
    detectPageType() {
        const currentPath = window.location.pathname;
        if (currentPath.includes('product_post')) {
            this.processId = 6; // Product posts
        } else if (currentPath.includes('blog_post')) {
            this.processId = 1; // Blog posts
        } else {
            this.processId = 1; // Default to blog posts
        }
        console.log('Page type detected:', currentPath, 'Process ID:', this.processId);
    }
    
    // Set the selected data (product or blog section) and update UI
    setSelectedData(data) {
        this.selectedData = data;
        this.updateGenerateButton();
        this.updateContentText();
        this.updateGenerationPromptDisplay(); // Update the generation prompt display
        this.loadExistingContent(); // Load any existing generated content (async)
        // updateAIStatusHeader() will be called by loadExistingContent() after content is loaded
    }
    
    // Legacy method for backward compatibility
    setSelectedProduct(product) {
        this.setSelectedData(product);
    }
    
    // Update the generate button state
    updateGenerateButton() {
        const generateBtn = document.getElementById('generate-content-btn');
        if (generateBtn) {
            generateBtn.disabled = !this.selectedData;
        }
    }
    
    // Update content text area with placeholder
    updateContentText() {
        const contentText = document.getElementById('content-text');
        if (contentText) {
            if (this.selectedData) {
                const itemName = this.selectedData.name || this.selectedData.section_title || 'item';
                contentText.textContent = `Select ${itemName} and click "Generate Post" to create AI-powered content.`;
            } else {
                contentText.textContent = 'Select an item and click "Generate Post" to create AI-powered content.';
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
    console.log('DOM loaded, initializing AIContentGenerationManager');
    try {
        window.aiContentGenerationManager = new AIContentGenerationManager();
        console.log('AIContentGenerationManager initialized successfully');
    } catch (error) {
        console.error('Error initializing AIContentGenerationManager:', error);
    }
});
