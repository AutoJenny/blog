/**
 * AI Content Generation Manager
 * Handles AI-powered content generation for syndication pages
 */
class AIContentGenerationManager {
    constructor() {
        this.selectedContentType = 'feature';
        this.generatedContent = '';
        this.selectedProduct = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupContentTypeButtons();
    }
    
    setupEventListeners() {
        // Start Ollama button
        const startOllamaBtn = document.getElementById('start-ollama-btn');
        if (startOllamaBtn) {
            startOllamaBtn.addEventListener('click', () => this.startOllama());
        }
        
        // Generate content button
        const generateBtn = document.getElementById('generate-content-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateContent());
        }
        
        // Edit content button
        const editBtn = document.getElementById('edit-content-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => this.editContent());
        }
        
        // Add to queue button
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        if (addToQueueBtn) {
            addToQueueBtn.addEventListener('click', () => this.addToQueue());
        }
    }
    
    setupContentTypeButtons() {
        const buttons = document.querySelectorAll('.content-type-btn');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons
                buttons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                button.classList.add('active');
                // Update selected content type
                this.selectedContentType = button.dataset.type;
            });
        });
    }
    
    startOllama() {
        const btn = document.getElementById('start-ollama-btn');
        const originalText = btn.innerHTML;
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        
        // Simulate Ollama startup
        setTimeout(() => {
            btn.innerHTML = '<i class="fas fa-check"></i> Ollama Ready';
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-success');
            
            // Enable generate button if product is selected
            this.updateGenerateButton();
        }, 2000);
    }
    
    setSelectedProduct(product) {
        this.selectedProduct = product;
        this.updateGenerateButton();
        this.updateContentText();
    }
    
    updateGenerateButton() {
        const generateBtn = document.getElementById('generate-content-btn');
        const ollamaBtn = document.getElementById('start-ollama-btn');
        
        if (generateBtn) {
            const isOllamaReady = ollamaBtn && ollamaBtn.classList.contains('btn-success');
            const hasProduct = this.selectedProduct !== null;
            
            generateBtn.disabled = !(isOllamaReady && hasProduct);
        }
    }
    
    updateContentText() {
        const contentText = document.getElementById('content-text');
        if (contentText) {
            if (this.selectedProduct) {
                contentText.innerHTML = `Ready to generate ${this.selectedContentType} content for: <strong>${this.selectedProduct.name}</strong>`;
            } else {
                contentText.innerHTML = 'Select a product and click "Generate Post" to create AI-powered content.';
            }
        }
    }
    
    async generateContent() {
        if (!this.selectedProduct) {
            alert('Please select a product first.');
            return;
        }
        
        const generateBtn = document.getElementById('generate-content-btn');
        const originalText = generateBtn.innerHTML;
        
        try {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            
            // Simulate AI content generation
            await this.simulateContentGeneration();
            
            // Show generated content
            this.displayGeneratedContent();
            
            // Enable edit and add to queue buttons
            this.enableContentActions();
            
        } catch (error) {
            console.error('Error generating content:', error);
            alert('Error generating content. Please try again.');
            this.updateStatusDisplay('Error generating content');
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = originalText;
        }
    }
    
    async simulateContentGeneration() {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Generate sample content based on content type and product
        const product = this.selectedProduct;
        const contentType = this.selectedContentType;
        
        let content = '';
        
        switch (contentType) {
            case 'feature':
                content = `🔥 Discover ${product.name}! ${product.description || 'Amazing features that will transform your experience.'} Perfect for anyone looking to upgrade their setup. #${product.name.replace(/\s+/g, '')} #Innovation #Tech`;
                break;
            case 'benefit':
                content = `✨ Why ${product.name}? Because it delivers real results! ${product.description || 'Experience the difference with our premium quality and innovative design.'} Don't miss out on this game-changer! #${product.name.replace(/\s+/g, '')} #Benefits #Quality`;
                break;
            case 'story':
                content = `📖 Here's why ${product.name} changed everything for us... ${product.description || 'From the moment we started using it, we knew this was something special.'} Sometimes the best discoveries come from taking a chance. #${product.name.replace(/\s+/g, '')} #Story #Innovation`;
                break;
        }
        
        this.generatedContent = content;
    }
    
    displayGeneratedContent() {
        const contentText = document.getElementById('content-text');
        if (contentText) {
            contentText.innerHTML = `
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin: 10px 0;">
                    <div style="color: #10b981; font-weight: 600; margin-bottom: 8px;">
                        <i class="fas fa-robot"></i> Generated ${this.selectedContentType.charAt(0).toUpperCase() + this.selectedContentType.slice(1)} Content:
                    </div>
                    <div style="color: #f1f5f9; line-height: 1.5;">
                        ${this.generatedContent}
                    </div>
                </div>
            `;
        }
    }
    
    enableContentActions() {
        const editBtn = document.getElementById('edit-content-btn');
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        
        if (editBtn) {
            editBtn.disabled = false;
            editBtn.style.display = 'inline-block';
        }
        
        if (addToQueueBtn) {
            addToQueueBtn.disabled = false;
            addToQueueBtn.style.display = 'inline-block';
        }
    }
    
    editContent() {
        if (!this.generatedContent) {
            alert('No content to edit. Please generate content first.');
            return;
        }
        
        const newContent = prompt('Edit the generated content:', this.generatedContent);
        if (newContent !== null && newContent.trim() !== '') {
            this.generatedContent = newContent.trim();
            this.displayGeneratedContent();
        }
    }
    
    addToQueue() {
        if (!this.generatedContent) {
            alert('No content to add to queue. Please generate content first.');
            return;
        }
        
        if (!this.selectedProduct) {
            alert('No product selected. Please select a product first.');
            return;
        }
        
        // Add to queue logic would go here
        // For now, just show a success message
        alert(`Content added to queue for ${this.selectedProduct.name}!`);
        
        // Reset the form
        this.resetForm();
    }
    
    resetForm() {
        this.generatedContent = '';
        this.selectedProduct = null;
        
        const contentText = document.getElementById('content-text');
        if (contentText) {
            contentText.innerHTML = 'Select a product and click "Generate Post" to create AI-powered content.';
        }
        
        const editBtn = document.getElementById('edit-content-btn');
        const addToQueueBtn = document.getElementById('add-to-queue-btn');
        
        if (editBtn) {
            editBtn.disabled = true;
            editBtn.style.display = 'none';
        }
        
        if (addToQueueBtn) {
            addToQueueBtn.disabled = true;
            addToQueueBtn.style.display = 'none';
        }
        
        this.updateGenerateButton();
    }
}

// Initialize AI Content Generation Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.aiContentGenerationManager = new AIContentGenerationManager();
});
