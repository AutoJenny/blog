// Vector Embeddings Panel JavaScript

console.log('[VectorEmbeddingsPanel] Script loading...');

class VectorEmbeddingsPanel {
    constructor() {
        this.postId = window.postId;
        this.year = window.year;
        this.week = window.week;
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        this.statusDiv = document.getElementById('embedding-status');
        this.matchesSection = document.getElementById('matches-section');
        this.bestMatchSection = document.getElementById('best-match-section');
        this.productSelect = document.getElementById('product-select');
        this.supplierSelect = document.getElementById('supplier-select');
        this.categorySelect = document.getElementById('category-select');
        this.bestMatchType = document.getElementById('best-match-type');
        this.bestMatchScore = document.getElementById('best-match-score');
        this.bestMatchOverride = document.getElementById('best-match-override-select');
    }
    
    bindEvents() {
        // Handle manual overrides
        if (this.productSelect) {
            this.productSelect.addEventListener('change', (e) => this.handleProductOverride(e.target.value));
        }
        if (this.supplierSelect) {
            this.supplierSelect.addEventListener('change', (e) => this.handleSupplierOverride(e.target.value));
        }
        if (this.categorySelect) {
            this.categorySelect.addEventListener('change', (e) => this.handleCategoryOverride(e.target.value));
        }
        if (this.bestMatchOverride) {
            this.bestMatchOverride.addEventListener('change', (e) => this.handleBestMatchOverride(e.target.value));
        }
    }
    
    async generateEmbeddings() {
        try {
            // Build URL with week context
            const url = `/header/api/posts/${this.postId}/generate-embeddings?year=${this.year}&week=${this.week}`;
            
            // Show loading state
            this.statusDiv.innerHTML = '<p style="color: #888;">Generating embeddings...</p>';
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data);
            } else {
                this.statusDiv.innerHTML = `<p style="color: #ef4444;">Error: ${data.error || 'Failed to generate embeddings'}</p>`;
            }
        } catch (error) {
            console.error('[VectorEmbeddingsPanel] Error generating embeddings:', error);
            this.statusDiv.innerHTML = `<p style="color: #ef4444;">Error: ${error.message}</p>`;
        }
    }
    
    displayResults(data) {
        // Display embedding confirmation
        const embedding = data.embedding;
        this.statusDiv.className = 'embedding-status success';
        this.statusDiv.innerHTML = `
            <p style="color: #10b981; margin: 0 0 0.5rem 0;">
                <i class="fas fa-check-circle"></i> Embeddings generated successfully
            </p>
            <p style="color: #888; font-size: 0.85rem; margin: 0.25rem 0;">
                <strong>Table:</strong> ${embedding.table}
            </p>
            <p style="color: #888; font-size: 0.85rem; margin: 0.25rem 0;">
                <strong>Filepath:</strong> <span class="filepath">${embedding.filepath}</span>
            </p>
            <p style="color: #888; font-size: 0.85rem; margin: 0.25rem 0;">
                <strong>Model:</strong> ${embedding.model} (${embedding.dimension} dimensions)
            </p>
        `;
        
        // Display matches
        this.displayMatches(data.matches);
        
        // Display best match
        if (data.best_match) {
            this.displayBestMatch(data.best_match);
        }
        
        // Show sections
        this.matchesSection.style.display = 'block';
        this.bestMatchSection.style.display = 'block';
    }
    
    displayMatches(matches) {
        // Populate product select
        if (this.productSelect && matches.products) {
            this.productSelect.innerHTML = '<option value="">Select product...</option>';
            matches.products.forEach((product, index) => {
                const option = document.createElement('option');
                option.value = product.id;
                option.textContent = `${product.name} (score: ${product.score.toFixed(3)})`;
                if (index === 0) {
                    option.selected = true;
                }
                this.productSelect.appendChild(option);
            });
        }
        
        // Populate supplier select
        if (this.supplierSelect && matches.suppliers) {
            this.supplierSelect.innerHTML = '<option value="">Select supplier...</option>';
            matches.suppliers.forEach((supplier, index) => {
                const option = document.createElement('option');
                option.value = supplier.id;
                option.textContent = `${supplier.name} (score: ${supplier.score.toFixed(3)})`;
                if (index === 0) {
                    option.selected = true;
                }
                this.supplierSelect.appendChild(option);
            });
        }
        
        // Populate category select
        if (this.categorySelect && matches.categories) {
            this.categorySelect.innerHTML = '<option value="">Select category...</option>';
            matches.categories.forEach((category, index) => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = `${category.name} (score: ${category.score.toFixed(3)})`;
                if (index === 0) {
                    option.selected = true;
                }
                this.categorySelect.appendChild(option);
            });
        }
    }
    
    displayBestMatch(bestMatch) {
        if (!bestMatch || !bestMatch.match) {
            return;
        }
        
        // Display type
        if (this.bestMatchType) {
            this.bestMatchType.textContent = bestMatch.type.charAt(0).toUpperCase() + bestMatch.type.slice(1);
        }
        
        // Display score
        if (this.bestMatchScore) {
            this.bestMatchScore.textContent = `Score: ${bestMatch.normalized_score.toFixed(3)} (raw: ${bestMatch.match.score.toFixed(3)})`;
        }
        
        // Set override select to match
        if (this.bestMatchOverride) {
            this.bestMatchOverride.value = bestMatch.type;
        }
    }
    
    async handleProductOverride(productId) {
        if (!productId) return;
        await this.saveOverride('product', productId);
    }
    
    async handleSupplierOverride(supplierId) {
        if (!supplierId) return;
        await this.saveOverride('supplier', supplierId);
    }
    
    async handleCategoryOverride(categoryId) {
        if (!categoryId) return;
        await this.saveOverride('category', categoryId);
    }
    
    async handleBestMatchOverride(type) {
        if (!type) return;
        await this.saveOverride('best_match_type', type);
    }
    
    async saveOverride(field, value) {
        // Store override in post_development.embedding_overrides
        try {
            const url = `/header/api/posts/${this.postId}/save-embedding-overrides?year=${this.year}&week=${this.week}`;
            
            const payload = {};
            if (field === 'product') {
                payload.selected_product_id = parseInt(value);
            } else if (field === 'supplier') {
                payload.selected_supplier_id = parseInt(value);
            } else if (field === 'category') {
                payload.selected_category_id = parseInt(value);
            } else if (field === 'best_match_type') {
                payload.selected_type = value;
            }
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            if (data.success) {
                console.log(`[VectorEmbeddingsPanel] Override saved: ${field} = ${value}`);
            } else {
                console.error(`[VectorEmbeddingsPanel] Error saving override:`, data.error);
            }
        } catch (error) {
            console.error(`[VectorEmbeddingsPanel] Error saving override:`, error);
        }
    }
}

// Global function for accordion
function toggleVectorEmbeddingsAccordion() {
    const content = document.getElementById('vector-embeddings-content');
    const icon = document.getElementById('vector-embeddings-accordion-icon');
    
    if (content && icon) {
        content.classList.toggle('collapsed');
        icon.classList.toggle('open');
        
        // Save accordion state
        if (window.headerAccordionManager) {
            const isOpen = !content.classList.contains('collapsed');
            window.headerAccordionManager.saveAccordionState('vector-embeddings', isOpen);
        }
    }
}

// Initialize panel
let vectorEmbeddingsPanel;
document.addEventListener('DOMContentLoaded', function() {
    vectorEmbeddingsPanel = new VectorEmbeddingsPanel();
    
    // Expose generateEmbeddings globally for seo-meta-page.js
    window.generatePostEmbeddings = function() {
        if (vectorEmbeddingsPanel) {
            return vectorEmbeddingsPanel.generateEmbeddings();
        }
    };
    
    // Initialize accordion with database-backed state
    if (window.HeaderAccordionManager) {
        window.headerAccordionManager = new window.HeaderAccordionManager();
        window.headerAccordionManager.initializeAccordion(
            'vector-embeddings',
            'vector-embeddings-content',
            'vector-embeddings-accordion-icon',
            toggleVectorEmbeddingsAccordion
        );
    } else {
        // Fallback: restore from sessionStorage
        const savedState = sessionStorage.getItem('header-accordion-vector-embeddings');
        if (savedState === 'open') {
            const content = document.getElementById('vector-embeddings-content');
            const icon = document.getElementById('vector-embeddings-accordion-icon');
            if (content) content.classList.remove('collapsed');
            if (icon) icon.classList.add('open');
        }
    }
});

