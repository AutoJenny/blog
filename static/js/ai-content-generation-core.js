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
        this.loadPersistedSelection(); // Load any persisted selection
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
    async setSelectedData(data) {
        this.selectedData = data;
        
        // Persist the selection using state manager
        if (window.stateManager && data) {
            const pageType = this.processId === 6 ? 'product_post' : 'blog_post';
            const selectionType = this.processId === 6 ? 'product' : 'section';
            
            await window.stateManager.setSelection(
                pageType, 
                selectionType, 
                data.id, 
                data
            );
            console.log('Selection persisted via state manager:', data.name || data.section_title);
        }
        
        this.updateGenerateButton();
        this.updateContentText();
        this.updateGenerationPromptDisplay(); // Update the generation prompt display
        this.loadExistingContent(); // Load any existing generated content (async)
        // updateAIStatusHeader() will be called by loadExistingContent() after content is loaded
    }
    
    // Load persisted selection from state manager
    async loadPersistedSelection() {
        if (!window.stateManager) {
            console.log('State manager not available, skipping persisted selection load');
            return;
        }
        
        try {
            const pageType = this.processId === 6 ? 'product_post' : 'blog_post';
            const selectionType = this.processId === 6 ? 'product' : 'section';
            
            const selection = await window.stateManager.getSelection(pageType, selectionType);
            
            if (selection && selection.selected_data) {
                console.log('Loading persisted selection:', selection.selected_data.name || selection.selected_data.section_title);
                this.selectedData = selection.selected_data;
                this.updateGenerateButton();
                this.updateContentText();
                this.updateGenerationPromptDisplay();
                this.loadExistingContent(); // This will also update the AI status header
            } else {
                console.log('No persisted selection found');
            }
        } catch (error) {
            console.error('Error loading persisted selection:', error);
        }
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
